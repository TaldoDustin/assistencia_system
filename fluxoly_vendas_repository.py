"""
fluxoly_vendas_repository.py

Único ponto de acesso SQL do domínio Vendas (docs/product/features/VENDAS.md).
Primeiro módulo a nascer com o prefixo `fluxoly_` (ADR-008,
docs/engineering/adr/ADR-008.md) — segue a mesma convenção de camadas de
`docs/engineering/ENGINEERING_GUIDE.md` §3.1 (controller → service →
repository), só muda o prefixo de nome.

Tabelas: `vendas`, `vendas_itens`. `vendas_itens.unidade_serializada_id` tem
índice UNIQUE (app.py::criar_tabelas()) — a mesma unidade nunca pode aparecer
em duas vendas, garantido pelo banco, não só pela camada de serviço.
"""


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
        "SELECT id, cliente_id, vendedor_id, forma_pagamento, valor_total, status, observacoes, criado_em "
        "FROM vendas WHERE id = ?",
        (venda_id,),
    )
    return cursor.fetchone()


def buscar_itens_por_venda(cursor, venda_id):
    cursor.execute(
        """
        SELECT id, venda_id, unidade_serializada_id, produto_id, produto_nome, produto_sku,
               quantidade, valor_tabela, valor_unitario, subtotal, criado_em
        FROM vendas_itens
        WHERE venda_id = ?
        ORDER BY id
        """,
        (venda_id,),
    )
    return cursor.fetchall()
