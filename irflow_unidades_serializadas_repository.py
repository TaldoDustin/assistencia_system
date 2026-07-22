"""
irflow_unidades_serializadas_repository.py

Único ponto de acesso SQL do domínio `unidades_serializadas` (rastreamento
individual por IMEI/serial, `docs/product/features/IMEI.md`, evoluído na
migração `docs/engineering/migrations/MIGRATION_unidades_serializadas.md`
per ADR-007). Segue a convenção de `docs/engineering/ENGINEERING_GUIDE.md`
§3.1.

Tabela: `unidades_serializadas`. Uma unidade tem origem em `estoque_id` OU
`produto_id` (nunca os dois — invariante validada na camada de serviço).
`obter_estoque_requer_imei`/`obter_produto_requer_rastreio_unidade` leem,
cada uma, uma única coluna de outro domínio — não é acesso ao repository
de outro domínio (Estoque não tem repository formal ainda; ver
`docs/engineering/DOMAIN_MODEL.md` §1.4).

Depende de: nenhum outro módulo de domínio.
"""

_COLUNAS = (
    "id, estoque_id, produto_id, lote_id, imei, status, reservado_por, reservado_ate, "
    "venda_id, saude_bateria, localizacao, criado_em, atualizado_em"
)


def inserir(cursor, estoque_id=None, produto_id=None, imei=None, lote_id=None):
    cursor.execute(
        "INSERT INTO unidades_serializadas (estoque_id, produto_id, lote_id, imei) "
        "VALUES (?, ?, ?, ?)",
        (estoque_id, produto_id, lote_id, imei),
    )
    return cursor.lastrowid


def buscar_por_id(cursor, unidade_id):
    cursor.execute(f"SELECT {_COLUNAS} FROM unidades_serializadas WHERE id = ?", (unidade_id,))
    return cursor.fetchone()


def buscar_paginado(cursor, imei, estoque_id, produto_id, status, limit, offset):
    condicoes = []
    params = []
    if imei:
        condicoes.append("imei LIKE ?")
        params.append(f"%{imei}%")
    if estoque_id:
        condicoes.append("estoque_id = ?")
        params.append(estoque_id)
    if produto_id:
        condicoes.append("produto_id = ?")
        params.append(produto_id)
    if status:
        condicoes.append("status = ?")
        params.append(status)

    where_sql = " AND ".join(condicoes) if condicoes else "1=1"
    cursor.execute(
        f"SELECT {_COLUNAS} FROM unidades_serializadas WHERE {where_sql} "
        "ORDER BY id DESC LIMIT ? OFFSET ?",
        (*params, limit, offset),
    )
    return cursor.fetchall()


def contar(cursor, imei, estoque_id, produto_id, status):
    condicoes = []
    params = []
    if imei:
        condicoes.append("imei LIKE ?")
        params.append(f"%{imei}%")
    if estoque_id:
        condicoes.append("estoque_id = ?")
        params.append(estoque_id)
    if produto_id:
        condicoes.append("produto_id = ?")
        params.append(produto_id)
    if status:
        condicoes.append("status = ?")
        params.append(status)

    where_sql = " AND ".join(condicoes) if condicoes else "1=1"
    cursor.execute(f"SELECT COUNT(*) FROM unidades_serializadas WHERE {where_sql}", tuple(params))
    return cursor.fetchone()[0] or 0


def atualizar_status(cursor, unidade_id, status):
    cursor.execute(
        "UPDATE unidades_serializadas SET status = ?, atualizado_em = datetime('now') WHERE id = ?",
        (status, unidade_id),
    )


def obter_estoque_requer_imei(cursor, estoque_id):
    """Retorna None se o item de estoque não existe, senão True/False de `requer_imei`."""
    cursor.execute("SELECT requer_imei FROM estoque WHERE id = ?", (estoque_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return bool(row[0])


def obter_produto_requer_rastreio_unidade(cursor, produto_id):
    """Retorna None se o produto não existe, senão True/False de `requer_rastreio_unidade`."""
    cursor.execute("SELECT requer_rastreio_unidade FROM produtos WHERE id = ?", (produto_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return bool(row[0])
