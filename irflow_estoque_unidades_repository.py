"""
irflow_estoque_unidades_repository.py

Único ponto de acesso SQL do domínio `estoque_unidades` (rastreamento
individual por IMEI, `docs/product/features/IMEI.md`). Segue a convenção
de `docs/engineering/ENGINEERING_GUIDE.md` §3.1.

Tabela: `estoque_unidades`. `obter_estoque_requer_imei` lê a coluna
`estoque.requer_imei` — uma única SELECT de coluna, não é acesso ao
repository de outro domínio (Estoque não tem repository formal ainda;
ver `docs/engineering/DOMAIN_MODEL.md` §1.4).

Depende de: nenhum outro módulo de domínio.
"""

_COLUNAS = (
    "id, estoque_id, lote_id, imei, status, reservado_por, reservado_ate, "
    "venda_id, criado_em, atualizado_em"
)


def inserir(cursor, estoque_id, imei, lote_id=None):
    cursor.execute(
        "INSERT INTO estoque_unidades (estoque_id, lote_id, imei) VALUES (?, ?, ?)",
        (estoque_id, lote_id, imei),
    )
    return cursor.lastrowid


def buscar_por_id(cursor, unidade_id):
    cursor.execute(f"SELECT {_COLUNAS} FROM estoque_unidades WHERE id = ?", (unidade_id,))
    return cursor.fetchone()


def buscar_paginado(cursor, imei, estoque_id, status, limit, offset):
    condicoes = []
    params = []
    if imei:
        condicoes.append("imei LIKE ?")
        params.append(f"%{imei}%")
    if estoque_id:
        condicoes.append("estoque_id = ?")
        params.append(estoque_id)
    if status:
        condicoes.append("status = ?")
        params.append(status)

    where_sql = " AND ".join(condicoes) if condicoes else "1=1"
    cursor.execute(
        f"SELECT {_COLUNAS} FROM estoque_unidades WHERE {where_sql} ORDER BY id DESC LIMIT ? OFFSET ?",
        (*params, limit, offset),
    )
    return cursor.fetchall()


def contar(cursor, imei, estoque_id, status):
    condicoes = []
    params = []
    if imei:
        condicoes.append("imei LIKE ?")
        params.append(f"%{imei}%")
    if estoque_id:
        condicoes.append("estoque_id = ?")
        params.append(estoque_id)
    if status:
        condicoes.append("status = ?")
        params.append(status)

    where_sql = " AND ".join(condicoes) if condicoes else "1=1"
    cursor.execute(f"SELECT COUNT(*) FROM estoque_unidades WHERE {where_sql}", tuple(params))
    return cursor.fetchone()[0] or 0


def atualizar_status(cursor, unidade_id, status):
    cursor.execute(
        "UPDATE estoque_unidades SET status = ?, atualizado_em = datetime('now') WHERE id = ?",
        (status, unidade_id),
    )


def obter_estoque_requer_imei(cursor, estoque_id):
    """Retorna None se o item de estoque não existe, senão True/False de `requer_imei`."""
    cursor.execute("SELECT requer_imei FROM estoque WHERE id = ?", (estoque_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return bool(row[0])
