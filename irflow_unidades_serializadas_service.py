"""
irflow_unidades_serializadas_service.py

Regra de negócio pura do domínio `unidades_serializadas` (rastreamento
individual por IMEI/serial) — não conhece Flask, `request` nem `jsonify`
(`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Responsabilidade: registrar unidades individuais originadas de `estoque`
(peças que exigem rastreamento por IMEI, `estoque.requer_imei = 1`) OU de
`produtos` (catálogo comercial que exige rastreamento por unidade,
`produtos.requer_rastreio_unidade = 1`), e suas transições manuais de
status. Uma unidade tem origem em exatamente um dos dois — nunca ambos,
nunca nenhum (Regra de Ouro / invariante de origem, ver ADR-007). `reservado`/
`vendido` existem no schema para o futuro módulo de Vendas, mas nenhuma
função aqui produz ou aceita esses estados — só `disponivel`, `em_reparo` e
`devolvido` são alcançáveis nesta sprint.

Tabelas usadas: `unidades_serializadas` (via
`irflow_unidades_serializadas_repository.py`), leitura de
`estoque.requer_imei` e `produtos.requer_rastreio_unidade`.

Depende de: `irflow_unidades_serializadas_repository.py` (SQL),
`irflow_audit.py` (auditoria — create/status_change).
"""

import irflow_unidades_serializadas_repository as repo
from irflow_audit import registrar_log_auditoria

PAGINA_PADRAO = 1
POR_PAGINA_PADRAO = 20

# Estados alcançáveis nesta sprint — 'reservado'/'vendido' ficam de fora até
# o módulo de Vendas existir (nem como origem, nem como destino).
TRANSICOES_VALIDAS = {
    "disponivel": {"em_reparo"},
    "em_reparo": {"disponivel", "devolvido"},
    "devolvido": {"disponivel"},
}


def _unidade_para_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "estoque_id": row[1],
        "produto_id": row[2],
        "lote_id": row[3],
        "imei": row[4] or "",
        "status": row[5],
        "reservado_por": row[6],
        "reservado_ate": row[7],
        "venda_id": row[8],
        "saude_bateria": row[9],
        "localizacao": row[10],
        "criado_em": row[11],
        "atualizado_em": row[12],
    }


def _origem_label(estoque_modelo, estoque_descricao, produto_modelo, produto_descricao):
    """Label de exibição da origem — modelo com fallback para descrição, por domínio."""
    return (estoque_modelo or estoque_descricao) or (produto_modelo or produto_descricao) or ""


def _unidade_com_origem_para_dict(row):
    """Mesma forma de `_unidade_para_dict`, com campos de origem (join) para listagem/exibição."""
    if not row:
        return None
    base = _unidade_para_dict(row)
    (_estoque_modelo, _estoque_descricao, _produto_modelo, _produto_descricao,
     _produto_categoria, _produto_marca) = row[13:19]
    base["origem_tipo"] = "estoque" if base["estoque_id"] else ("produto" if base["produto_id"] else None)
    base["origem_label"] = _origem_label(_estoque_modelo, _estoque_descricao, _produto_modelo, _produto_descricao)
    base["produto_categoria"] = _produto_categoria
    base["produto_marca"] = _produto_marca
    return base


def listar_unidades(
    conectar, imei="", estoque_id=None, produto_id=None, status="", page=None, per_page=None
):
    page = page or PAGINA_PADRAO
    per_page = per_page or POR_PAGINA_PADRAO
    offset = (max(1, page) - 1) * per_page

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar(cursor, imei, estoque_id, produto_id, status)
        rows = repo.buscar_paginado(cursor, imei, estoque_id, produto_id, status, per_page, offset)
    finally:
        conn.close()

    return {
        "items": [_unidade_com_origem_para_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def obter_unidade(conectar, unidade_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id_com_origem(cursor, unidade_id)
    finally:
        conn.close()
    return _unidade_com_origem_para_dict(row)


def _evento_historico_para_dict(row):
    return {
        "id": row[0],
        "acao": row[1],
        "valor_anterior": row[2],
        "valor_novo": row[3],
        "criado_em": row[4],
        "usuario_nome": row[5] or "",
    }


def obter_historico(conectar, unidade_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        rows = repo.buscar_historico(cursor, unidade_id)
    finally:
        conn.close()
    return [_evento_historico_para_dict(r) for r in rows]


def criar_unidade(conectar, usuario_id, estoque_id, produto_id, imei, lote_id=None):
    """Retorna (unidade_id, erro). `erro` é None em caso de sucesso.

    Exatamente um de `estoque_id`/`produto_id` deve estar preenchido —
    rejeitado com erro explícito se nenhum ou ambos estiverem (nunca
    coagido silenciosamente, mesma filosofia de KI-015/KI-016).
    """
    imei = (imei or "").strip()
    if not estoque_id and not produto_id:
        return None, "Informe estoque_id ou produto_id."
    if estoque_id and produto_id:
        return None, "Informe apenas um de estoque_id ou produto_id, não os dois."
    if not imei:
        return None, "IMEI é obrigatório."

    conn = conectar()
    try:
        cursor = conn.cursor()
        if estoque_id:
            requer_rastreio = repo.obter_estoque_requer_imei(cursor, estoque_id)
            if requer_rastreio is None:
                return None, "Item de estoque não encontrado."
            if not requer_rastreio:
                return None, "Este item de estoque não está marcado para rastreamento por IMEI."
        else:
            requer_rastreio = repo.obter_produto_requer_rastreio_unidade(cursor, produto_id)
            if requer_rastreio is None:
                return None, "Produto não encontrado."
            if not requer_rastreio:
                return None, "Este produto não está marcado para rastreamento por unidade."

        try:
            unidade_id = repo.inserir(
                cursor, estoque_id=estoque_id, produto_id=produto_id, imei=imei, lote_id=lote_id
            )
        except Exception:
            conn.rollback()
            return None, "IMEI já cadastrado."

        registrar_log_auditoria(
            cursor,
            "unidade_serializada",
            unidade_id,
            usuario_id,
            "create",
            depois={"estoque_id": estoque_id, "produto_id": produto_id, "imei": imei},
        )
        conn.commit()
    finally:
        conn.close()

    return unidade_id, None


def transicionar_status(conectar, usuario_id, unidade_id, novo_status):
    """Retorna (sucesso, erro). `erro` é None em caso de sucesso."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, unidade_id)
        if not antes:
            return False, "Unidade não encontrada."

        status_atual = antes[5]
        destinos_validos = TRANSICOES_VALIDAS.get(status_atual, set())
        if novo_status not in destinos_validos:
            return False, f"Transição inválida de '{status_atual}' para '{novo_status}'."

        repo.atualizar_status(cursor, unidade_id, novo_status)
        registrar_log_auditoria(
            cursor,
            "unidade_serializada",
            unidade_id,
            usuario_id,
            "status_change",
            antes=status_atual,
            depois=novo_status,
        )
        conn.commit()
    finally:
        conn.close()

    return True, None
