"""
fluxoly_produtos_service.py

Regra de negócio pura do domínio Produtos — não conhece Flask, `request`
nem `jsonify` (`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Responsabilidade: catálogo comercial (SKU de venda — iPhone, Apple Watch,
AirPods, Acessório), distinto do domínio Estoque (`irflow_blueprints_api.py`,
peças de reparo — `Tela`/`Bateria`/etc.). `categoria` e `condicao` são
validadas contra lista fechada e **rejeitadas** (não normalizadas) quando
inválidas — ao contrário de `_normalizar_tipo_estoque`/`_normalizar_qualidade_estoque`,
que mascaram entrada desconhecida com um valor default; essa coerção
silenciosa já causou duas dívidas reais neste projeto (KI-015, KI-016), não
repetida aqui. `margem` nunca é persistida — sempre calculada a partir de
`preco_venda`/`preco_custo`, mesmo princípio do `vendas.margem` especificado
em `docs/product/features/VENDAS.md` (BR-019).

Tabelas usadas: `produtos` (via `fluxoly_produtos_repository.py`).

Depende de: `fluxoly_produtos_repository.py` (SQL), `fluxoly_reference_data.py`
(listas fechadas `PRODUTOS_CATEGORIAS`/`PRODUTOS_CONDICOES`), `fluxoly_audit.py`
(auditoria — create/update/delete).
"""

import fluxoly_produtos_repository as repo
from fluxoly_audit import registrar_log_auditoria
from fluxoly_reference_data import PRODUTOS_CATEGORIAS, PRODUTOS_CONDICOES

PAGINA_PADRAO = 1
POR_PAGINA_PADRAO = 20
CONDICAO_PADRAO = "Novo"


def _produto_para_dict(row):
    if not row:
        return None
    preco_custo = row[10]
    preco_venda = row[11]
    return {
        "id": row[0],
        "categoria": row[1],
        "marca": row[2] or "",
        "modelo": row[3] or "",
        "cor": row[4] or "",
        "capacidade": row[5] or "",
        "condicao": row[6],
        "descricao": row[7] or "",
        "sku": row[8] or "",
        "fornecedor": row[9] or "",
        "preco_custo": preco_custo,
        "preco_venda": preco_venda,
        "margem": (preco_venda - preco_custo) if preco_custo is not None else None,
        "quantidade": row[12],
        "requer_rastreio_unidade": bool(row[13]),
        "ativo": bool(row[14]),
        "criado_em": row[15],
        "atualizado_em": row[16],
    }


def _validar_campos(categoria, condicao, preco_custo, preco_venda, quantidade):
    if categoria not in PRODUTOS_CATEGORIAS:
        return f"Categoria inválida. Use uma de: {', '.join(PRODUTOS_CATEGORIAS)}."
    if condicao not in PRODUTOS_CONDICOES:
        return f"Condição inválida. Use uma de: {', '.join(PRODUTOS_CONDICOES)}."
    if preco_venda is None or preco_venda <= 0:
        return "Preço de venda é obrigatório e deve ser maior que zero."
    if preco_custo is not None and preco_custo < 0:
        return "Preço de custo não pode ser negativo."
    if quantidade is not None and quantidade < 0:
        return "Quantidade não pode ser negativa."
    return None


def listar_produtos(conectar, termo="", categoria=None, marca=None, condicao=None, ativo=None,
                     page=None, per_page=None):
    page = page or PAGINA_PADRAO
    per_page = per_page or POR_PAGINA_PADRAO
    offset = (max(1, page) - 1) * per_page

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar(cursor, termo, categoria, marca, condicao, ativo)
        rows = repo.buscar_paginado(cursor, termo, categoria, marca, condicao, ativo, per_page, offset)
    finally:
        conn.close()

    return {
        "items": [_produto_para_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def obter_produto(conectar, produto_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id(cursor, produto_id)
    finally:
        conn.close()
    return _produto_para_dict(row)


def criar_produto(conectar, usuario_id, categoria, marca="", modelo="", cor="", capacidade="",
                   condicao=None, descricao="", sku="", fornecedor="", preco_custo=None,
                   preco_venda=None, quantidade=0, requer_rastreio_unidade=False):
    """Retorna (produto_id, erro). `erro` é None em caso de sucesso."""
    categoria = (categoria or "").strip()
    marca = (marca or "").strip()
    modelo = (modelo or "").strip()
    cor = (cor or "").strip()
    capacidade = (capacidade or "").strip()
    condicao = (condicao or CONDICAO_PADRAO).strip()
    descricao = (descricao or "").strip()
    sku = (sku or "").strip()
    fornecedor = (fornecedor or "").strip()
    quantidade = quantidade if quantidade is not None else 0
    requer_rastreio_unidade = 1 if requer_rastreio_unidade else 0

    erro = _validar_campos(categoria, condicao, preco_custo, preco_venda, quantidade)
    if erro:
        return None, erro

    conn = conectar()
    try:
        cursor = conn.cursor()
        produto_id = repo.inserir(
            cursor, categoria, marca, modelo, cor, capacidade, condicao, descricao, sku, fornecedor,
            preco_custo, preco_venda, quantidade, requer_rastreio_unidade,
        )
        registrar_log_auditoria(
            cursor,
            "produto",
            produto_id,
            usuario_id,
            "create",
            depois={"categoria": categoria, "modelo": modelo, "preco_venda": preco_venda},
        )
        conn.commit()
    finally:
        conn.close()

    return produto_id, None


def atualizar_produto(conectar, usuario_id, produto_id, categoria, marca="", modelo="", cor="",
                       capacidade="", condicao=None, descricao="", sku="", fornecedor="",
                       preco_custo=None, preco_venda=None, quantidade=0,
                       requer_rastreio_unidade=False, ativo=True):
    """Retorna (sucesso, erro). `erro` é None em caso de sucesso."""
    categoria = (categoria or "").strip()
    marca = (marca or "").strip()
    modelo = (modelo or "").strip()
    cor = (cor or "").strip()
    capacidade = (capacidade or "").strip()
    condicao = (condicao or CONDICAO_PADRAO).strip()
    descricao = (descricao or "").strip()
    sku = (sku or "").strip()
    fornecedor = (fornecedor or "").strip()
    quantidade = quantidade if quantidade is not None else 0
    requer_rastreio_unidade = 1 if requer_rastreio_unidade else 0
    ativo = 1 if ativo else 0

    erro = _validar_campos(categoria, condicao, preco_custo, preco_venda, quantidade)
    if erro:
        return False, erro

    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, produto_id)
        if not antes:
            return False, "Produto não encontrado."

        repo.atualizar(
            cursor, produto_id, categoria, marca, modelo, cor, capacidade, condicao, descricao, sku,
            fornecedor, preco_custo, preco_venda, quantidade, requer_rastreio_unidade, ativo,
        )
        registrar_log_auditoria(
            cursor,
            "produto",
            produto_id,
            usuario_id,
            "update",
            antes=_produto_para_dict(antes),
            depois={"categoria": categoria, "modelo": modelo, "preco_venda": preco_venda, "ativo": bool(ativo)},
        )
        conn.commit()
    finally:
        conn.close()

    return True, None


def excluir_produto(conectar, usuario_id, produto_id):
    """Retorna (sucesso, erro). `erro` é None em caso de sucesso."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, produto_id)
        if not antes:
            return False, "Produto não encontrado."

        repo.deletar(cursor, produto_id)
        registrar_log_auditoria(
            cursor, "produto", produto_id, usuario_id, "delete", antes=_produto_para_dict(antes)
        )
        conn.commit()
    finally:
        conn.close()

    return True, None
