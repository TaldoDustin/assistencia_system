"""
fluxoly_vendas_repository.py

Único ponto de acesso SQL do domínio Vendas (docs/product/features/VENDAS.md).
Primeiro módulo a nascer com o prefixo `fluxoly_` (ADR-008,
docs/engineering/adr/ADR-008.md) — segue a mesma convenção de camadas de
`docs/engineering/ENGINEERING_GUIDE.md` §3.1 (controller → service →
repository), só muda o prefixo de nome.

Tabelas: `vendas`, `vendas_itens`. `vendas_itens.unidade_serializada_id` tem
índice UNIQUE (app.py::criar_tabelas()) — a mesma unidade nunca pode aparecer
em duas vendas, garantido pelo banco, não só pela camada de serviço (ver
ADR-009 para o plano de evolução dessa proteção quando cancelamento existir).

Sprint Vendas 1.1 (Histórico + Detalhe): só consulta, nenhuma mudança de
schema. `nome` de cliente/vendedor e `imei` do item são obtidos via LEFT JOIN
em `clientes`/`usuarios`/`unidades_serializadas` só para exibição -- mesma
justificativa já usada em `irflow_unidades_serializadas_repository.py`
(join de origem) e `shopping_list_logs` (join de usuário para nome).
"""

# Colunas + JOIN de vendas com nome de cliente/vendedor, só para exibição --
# não introduz filtro novo por si (filtros são aplicados via WHERE separado).
_COLUNAS_VENDA_COM_NOMES = (
    "v.id, v.cliente_id, v.vendedor_id, v.forma_pagamento, v.valor_total, v.status, "
    "v.observacoes, v.criado_em, "
    "c.nome AS cliente_nome, c.telefone AS cliente_telefone, u.nome AS vendedor_nome"
)
_JOIN_VENDA_COM_NOMES = (
    "FROM vendas v "
    "LEFT JOIN clientes c ON v.cliente_id = c.id "
    "LEFT JOIN usuarios u ON v.vendedor_id = u.id"
)


def inserir_venda(cursor, cliente_id, vendedor_id, forma_pagamento, valor_total, observacoes=""):
    cursor.execute(
        """
        INSERT INTO vendas (cliente_id, vendedor_id, forma_pagamento, valor_total, observacoes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (cliente_id, vendedor_id, forma_pagamento, valor_total, observacoes or ""),
    )
    return cursor.lastrowid


def inserir_item(cursor, venda_id, unidade_serializada_id, produto_id, produto_nome, produto_sku, valor_tabela, valor_unitario):
    """`quantidade` é sempre 1 nesta fatia — uma unidade serializada não é
    fungível (uma linha de item = uma unidade física). `subtotal` calculado
    aqui, não recebido do chamador, para nunca divergir de `valor_unitario *
    quantidade`. `valor_tabela` é o preço de catálogo no momento da venda
    (nullable — item pode não ter preço cadastrado); `valor_unitario` é o
    preço efetivo, pode divergir de `valor_tabela` (negociação) -- nenhum dos
    dois sobrescreve o outro."""
    quantidade = 1
    subtotal = valor_unitario * quantidade
    cursor.execute(
        """
        INSERT INTO vendas_itens (
            venda_id, unidade_serializada_id, produto_id, produto_nome, produto_sku,
            quantidade, valor_tabela, valor_unitario, subtotal
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            venda_id, unidade_serializada_id, produto_id, produto_nome, produto_sku,
            quantidade, valor_tabela, valor_unitario, subtotal,
        ),
    )
    return cursor.lastrowid


def buscar_por_id(cursor, venda_id):
    cursor.execute(
        f"SELECT {_COLUNAS_VENDA_COM_NOMES} {_JOIN_VENDA_COM_NOMES} WHERE v.id = ?",
        (venda_id,),
    )
    return cursor.fetchone()


def buscar_itens_por_venda(cursor, venda_id):
    """`imei` vem do join com `unidades_serializadas` -- estável (imutável
    após o cadastro, decisão já registrada em C1.3.4), seguro de exibir ao
    vivo mesmo para vendas antigas, diferente de `produto_nome`/`produto_sku`
    (snapshot, podem divergir do cadastro atual)."""
    cursor.execute(
        """
        SELECT vi.id, vi.venda_id, vi.unidade_serializada_id, vi.produto_id, vi.produto_nome,
               vi.produto_sku, vi.quantidade, vi.valor_tabela, vi.valor_unitario, vi.subtotal,
               vi.criado_em, u.imei
        FROM vendas_itens vi
        LEFT JOIN unidades_serializadas u ON vi.unidade_serializada_id = u.id
        WHERE vi.venda_id = ?
        ORDER BY vi.id
        """,
        (venda_id,),
    )
    return cursor.fetchall()


def _montar_filtros(cliente_id, vendedor_id, forma_pagamento, status, data_inicio, data_fim, termo):
    condicoes = []
    params = []

    if cliente_id:
        condicoes.append("v.cliente_id = ?")
        params.append(cliente_id)
    if vendedor_id:
        condicoes.append("v.vendedor_id = ?")
        params.append(vendedor_id)
    if forma_pagamento:
        condicoes.append("v.forma_pagamento = ?")
        params.append(forma_pagamento)
    if status:
        condicoes.append("v.status = ?")
        params.append(status)
    if data_inicio:
        condicoes.append("v.criado_em >= ?")
        params.append(data_inicio)
    if data_fim:
        condicoes.append("v.criado_em <= ?")
        params.append(data_fim)
    if termo:
        condicoes.append(
            "(c.nome LIKE ? OR EXISTS ("
            "SELECT 1 FROM vendas_itens vi LEFT JOIN unidades_serializadas u2 "
            "ON vi.unidade_serializada_id = u2.id "
            "WHERE vi.venda_id = v.id AND (u2.imei LIKE ? OR vi.produto_nome LIKE ?)"
            "))"
        )
        coringa = f"%{termo}%"
        params.extend([coringa, coringa, coringa])

    where_sql = " AND ".join(condicoes) if condicoes else "1=1"
    return where_sql, params


_ORDENACOES = {
    "recente": "v.criado_em DESC, v.id DESC",
    "antigo": "v.criado_em ASC, v.id ASC",
}


def contar_vendas(cursor, cliente_id=None, vendedor_id=None, forma_pagamento=None, status=None,
                   data_inicio=None, data_fim=None, termo=None):
    where_sql, params = _montar_filtros(
        cliente_id, vendedor_id, forma_pagamento, status, data_inicio, data_fim, termo
    )
    cursor.execute(f"SELECT COUNT(*) {_JOIN_VENDA_COM_NOMES} WHERE {where_sql}", params)
    return cursor.fetchone()[0] or 0


def buscar_paginado(cursor, cliente_id=None, vendedor_id=None, forma_pagamento=None, status=None,
                     data_inicio=None, data_fim=None, termo=None, sort="recente", limit=20, offset=0):
    where_sql, params = _montar_filtros(
        cliente_id, vendedor_id, forma_pagamento, status, data_inicio, data_fim, termo
    )
    order_sql = _ORDENACOES.get(sort, _ORDENACOES["recente"])
    cursor.execute(
        f"SELECT {_COLUNAS_VENDA_COM_NOMES} {_JOIN_VENDA_COM_NOMES} WHERE {where_sql} "
        f"ORDER BY {order_sql} LIMIT ? OFFSET ?",
        [*params, limit, offset],
    )
    return cursor.fetchall()


def buscar_itens_por_vendas(cursor, venda_ids):
    """Busca os itens de várias vendas de uma vez (evita N+1 na listagem do
    histórico) -- mesmo `imei` ao vivo via join, ver `buscar_itens_por_venda`."""
    if not venda_ids:
        return []
    marcadores = ",".join("?" * len(venda_ids))
    cursor.execute(
        f"""
        SELECT vi.id, vi.venda_id, vi.unidade_serializada_id, vi.produto_id, vi.produto_nome,
               vi.produto_sku, vi.quantidade, vi.valor_tabela, vi.valor_unitario, vi.subtotal,
               vi.criado_em, u.imei
        FROM vendas_itens vi
        LEFT JOIN unidades_serializadas u ON vi.unidade_serializada_id = u.id
        WHERE vi.venda_id IN ({marcadores})
        ORDER BY vi.venda_id, vi.id
        """,
        venda_ids,
    )
    return cursor.fetchall()
