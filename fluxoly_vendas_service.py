"""
fluxoly_vendas_service.py

Regra de negócio pura do domínio Vendas MVP (docs/product/features/VENDAS.md)
— não conhece Flask, `request` nem `jsonify` (ENGINEERING_GUIDE.md §3.1).
Primeiro módulo a nascer com o prefixo `fluxoly_` (ADR-008).

Escopo desta fatia (aprovado em conversa, 2026-07-27): venda de um único
aparelho (unidade serializada) por vez, sem desconto/aprovação, comissão,
garantia, troca ou reserva com timeout -- todos dependem de decisões de
negócio ainda pendentes do Product Owner (VENDAS.md "O que ainda está em
aberto"). `status` da venda é deliberadamente 'concluida', não 'paga' --
venda e pagamento são conceitos diferentes, não misturados aqui.

`valor_tabela` (preço de catálogo no momento da venda, de
`unidades_serializadas_service.py::preco_catalogo`) e `valor_unitario`
(preço efetivo, editável pelo vendedor) são guardados separados em
`vendas_itens` -- nenhuma autorização de desconto nesta fatia (qualquer
vendedor pode alterar o preço livremente), mas o schema já preserva os dois
valores para relatórios futuros de desconto/margem sem migração.

Sequência transacional de `iniciar_venda` (única transação, cliente -> venda
-> item -> unidade -> auditoria -> commit): validações de leitura (cliente,
unidade) rodam antes, em conexões próprias e curtas; a escrita real
(inserir_venda, inserir_item, marcar_como_vendida) roda inteira dentro de uma
única conexão/transação -- qualquer falha no meio reverte tudo, a unidade
nunca fica "vendida" sem uma `venda`/`vendas_itens` real por trás, nem uma
`venda` órfã sem a unidade marcada.

Depende de: `irflow_clientes_service.py` (validar cliente),
`irflow_unidades_serializadas_service.py` (validar/marcar unidade --
`marcar_como_vendida`, exclusiva deste domínio por ADR-007), `irflow_audit.py`.
"""

import sqlite3

import irflow_clientes_service as clientes_service
import irflow_unidades_serializadas_service as unidades_service
from irflow_audit import registrar_log_auditoria

import fluxoly_vendas_repository as repo

FORMAS_PAGAMENTO_VALIDAS = {"pix", "cartao", "dinheiro", "transferencia"}


class VendaConflitoError(Exception):
    """A unidade deixou de estar disponível entre a pré-checagem e a
    transação de escrita -- outra venda venceu a corrida."""


def _venda_para_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "cliente_id": row[1],
        "vendedor_id": row[2],
        "forma_pagamento": row[3],
        "valor_total": row[4],
        "status": row[5],
        "observacoes": row[6] or "",
        "criado_em": row[7],
    }


def _item_para_dict(row):
    return {
        "id": row[0],
        "venda_id": row[1],
        "unidade_serializada_id": row[2],
        "produto_id": row[3],
        "produto_nome": row[4],
        "produto_sku": row[5] or "",
        "quantidade": row[6],
        "valor_tabela": row[7],
        "valor_unitario": row[8],
        "subtotal": row[9],
        "criado_em": row[10],
    }


def iniciar_venda(
    conectar, usuario_id, cliente_id, unidade_serializada_id, forma_pagamento, valor_unitario, observacoes=""
):
    """Retorna (venda_id, erro). `erro` é None em caso de sucesso.

    `usuario_id` é sempre o vendedor (sessão logada) -- nunca escolhido no
    payload, mesmo padrão de auditoria já usado no resto do sistema.
    """
    forma_pagamento = (forma_pagamento or "").strip().lower()
    if forma_pagamento not in FORMAS_PAGAMENTO_VALIDAS:
        return None, "Forma de pagamento inválida."
    if not isinstance(valor_unitario, (int, float)) or valor_unitario <= 0:
        return None, "Valor deve ser maior que zero."

    cliente = clientes_service.obter_cliente(conectar, cliente_id)
    if not cliente:
        return None, "Cliente não encontrado."

    unidade = unidades_service.obter_unidade(conectar, unidade_serializada_id)
    if not unidade:
        return None, "Unidade não encontrada."
    if unidade["status"] != "disponivel":
        return None, "Unidade não está disponível para venda."

    produto_nome = unidade["origem_label"] or "Aparelho"
    produto_sku = unidade["origem_sku"] or None
    produto_id = unidade["produto_id"]
    valor_tabela = unidade["preco_catalogo"]

    conn = conectar()
    try:
        cursor = conn.cursor()
        venda_id = repo.inserir_venda(
            cursor, cliente_id, usuario_id, forma_pagamento, valor_unitario, observacoes
        )
        repo.inserir_item(
            cursor, venda_id, unidade_serializada_id, produto_id, produto_nome, produto_sku,
            valor_tabela, valor_unitario,
        )

        sucesso, erro = unidades_service.marcar_como_vendida(cursor, unidade_serializada_id, venda_id, usuario_id)
        if not sucesso:
            raise VendaConflitoError(erro)

        registrar_log_auditoria(
            cursor,
            "venda",
            venda_id,
            usuario_id,
            "create",
            depois={
                # venda_id/vendedor_id já são entidade_id/usuario_id da própria linha de
                # audit_log, mas repetidos aqui dentro do JSON para quem filtra/grepa o
                # conteúdo de valor_novo diretamente, sem cruzar com as colunas de fora.
                "venda_id": venda_id,
                "cliente_id": cliente_id,
                "vendedor_id": usuario_id,
                "unidade_serializada_id": unidade_serializada_id,
                "valor_tabela": valor_tabela,
                "valor_total": valor_unitario,
            },
        )
        conn.commit()
    except VendaConflitoError as exc:
        conn.rollback()
        return None, str(exc)
    except sqlite3.IntegrityError:
        # UNIQUE em vendas_itens.unidade_serializada_id -- outra venda já
        # commitou para esta unidade entre a pré-checagem e esta transação
        # (mesma corrida que marcar_como_vendida também protege).
        conn.rollback()
        return None, "Unidade não está mais disponível."
    except Exception as exc:
        conn.rollback()
        return None, str(exc)
    finally:
        conn.close()

    return venda_id, None


def obter_venda_com_itens(conectar, venda_id):
    """Retorna (venda, itens). `venda` é `None` se não encontrada (`itens`
    vem vazio nesse caso). Pensado desde já para múltiplos itens por venda,
    mesmo que esta fatia sempre crie exatamente um."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        venda_row = repo.buscar_por_id(cursor, venda_id)
        if not venda_row:
            return None, []
        itens_rows = repo.buscar_itens_por_venda(cursor, venda_id)
    finally:
        conn.close()
    return _venda_para_dict(venda_row), [_item_para_dict(r) for r in itens_rows]
