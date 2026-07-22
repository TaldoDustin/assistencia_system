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

# Colunas + LEFT JOIN em estoque/produtos só para exibição (label de origem) —
# não introduz filtro novo, mesma invariante de origem do resto do módulo.
_COLUNAS_COM_ORIGEM = (
    "u.id, u.estoque_id, u.produto_id, u.lote_id, u.imei, u.status, u.reservado_por, "
    "u.reservado_ate, u.venda_id, u.saude_bateria, u.localizacao, u.criado_em, u.atualizado_em, "
    "e.modelo AS estoque_modelo, e.descricao AS estoque_descricao, "
    "p.modelo AS produto_modelo, p.descricao AS produto_descricao, "
    "p.categoria AS produto_categoria, p.marca AS produto_marca"
)
_JOIN_ORIGEM = (
    "FROM unidades_serializadas u "
    "LEFT JOIN estoque e ON u.estoque_id = e.id "
    "LEFT JOIN produtos p ON u.produto_id = p.id"
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


def buscar_por_id_com_origem(cursor, unidade_id):
    """Mesma unidade de `buscar_por_id`, com colunas de origem (join) para exibição
    de detalhe — mesma invariante/join de `buscar_paginado`."""
    cursor.execute(
        f"SELECT {_COLUNAS_COM_ORIGEM} {_JOIN_ORIGEM} WHERE u.id = ?",
        (unidade_id,),
    )
    return cursor.fetchone()


def buscar_historico(cursor, unidade_id):
    """Histórico de auditoria da unidade (criação + mudanças de status),
    mais recente primeiro. Junta `usuarios` só para exibir o nome de quem
    fez a alteração — não é acesso ao repository de outro domínio (mesma
    justificativa de `obter_estoque_requer_imei`)."""
    cursor.execute(
        """
        SELECT a.id, a.acao, a.valor_anterior, a.valor_novo, a.criado_em,
               COALESCE(us.nome, '')
        FROM audit_log a
        LEFT JOIN usuarios us ON a.usuario_id = us.id
        WHERE a.entidade = 'unidade_serializada' AND a.entidade_id = ?
        ORDER BY a.id DESC
        """,
        (unidade_id,),
    )
    return cursor.fetchall()


# Ordenações permitidas (C1.3.3) — whitelist explícita, nunca interpolar valor
# vindo do cliente direto no SQL. "modelo" ordena pela mesma expressão de
# fallback usada em `_origem_label` (Python), só que em SQL.
_ORDENACOES = {
    "recente": "u.id DESC",
    "antigo": "u.id ASC",
    "imei": "u.imei ASC",
    "modelo": "COALESCE(e.modelo, e.descricao, p.modelo, p.descricao) ASC",
    "status": "u.status ASC",
}


def _montar_filtros_avancados(termo, origem, status, saude_min, saude_max, saude_nao_informado, localizacao):
    condicoes = []
    params = []
    if termo:
        padrao = f"%{termo.lower()}%"
        condicoes.append(
            "(lower(u.imei) LIKE ? OR lower(COALESCE(e.modelo, '')) LIKE ? "
            "OR lower(COALESCE(e.descricao, '')) LIKE ? OR lower(COALESCE(p.modelo, '')) LIKE ? "
            "OR lower(COALESCE(p.descricao, '')) LIKE ? OR lower(COALESCE(p.marca, '')) LIKE ? "
            "OR lower(COALESCE(u.localizacao, '')) LIKE ?)"
        )
        params.extend([padrao] * 7)
    if origem == "estoque":
        condicoes.append("u.estoque_id IS NOT NULL")
    elif origem == "produto":
        condicoes.append("u.produto_id IS NOT NULL")
    if status:
        condicoes.append("u.status = ?")
        params.append(status)
    if saude_nao_informado:
        condicoes.append("(u.saude_bateria IS NULL OR u.saude_bateria = '')")
    else:
        if saude_min is not None:
            condicoes.append("CAST(u.saude_bateria AS INTEGER) >= ?")
            params.append(saude_min)
        if saude_max is not None:
            condicoes.append("CAST(u.saude_bateria AS INTEGER) <= ?")
            params.append(saude_max)
    if localizacao:
        condicoes.append("lower(COALESCE(u.localizacao, '')) LIKE ?")
        params.append(f"%{localizacao.lower()}%")

    where_sql = " AND ".join(condicoes) if condicoes else "1=1"
    return where_sql, params


def buscar_paginado(
    cursor, termo="", estoque_id=None, produto_id=None, origem=None, status="",
    saude_min=None, saude_max=None, saude_nao_informado=False, localizacao="",
    sort="recente", limit=20, offset=0,
):
    where_sql, params = _montar_filtros_avancados(
        termo, origem, status, saude_min, saude_max, saude_nao_informado, localizacao
    )
    condicoes_extra = []
    if estoque_id:
        condicoes_extra.append("u.estoque_id = ?")
        params.append(estoque_id)
    if produto_id:
        condicoes_extra.append("u.produto_id = ?")
        params.append(produto_id)
    if condicoes_extra:
        where_sql = f"{where_sql} AND {' AND '.join(condicoes_extra)}"

    order_sql = _ORDENACOES.get(sort, _ORDENACOES["recente"])
    cursor.execute(
        f"SELECT {_COLUNAS_COM_ORIGEM} {_JOIN_ORIGEM} WHERE {where_sql} "
        f"ORDER BY {order_sql} LIMIT ? OFFSET ?",
        (*params, limit, offset),
    )
    return cursor.fetchall()


def contar(
    cursor, termo="", estoque_id=None, produto_id=None, origem=None, status="",
    saude_min=None, saude_max=None, saude_nao_informado=False, localizacao="",
):
    where_sql, params = _montar_filtros_avancados(
        termo, origem, status, saude_min, saude_max, saude_nao_informado, localizacao
    )
    condicoes_extra = []
    if estoque_id:
        condicoes_extra.append("u.estoque_id = ?")
        params.append(estoque_id)
    if produto_id:
        condicoes_extra.append("u.produto_id = ?")
        params.append(produto_id)
    if condicoes_extra:
        where_sql = f"{where_sql} AND {' AND '.join(condicoes_extra)}"

    cursor.execute(f"SELECT COUNT(*) {_JOIN_ORIGEM} WHERE {where_sql}", tuple(params))
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
