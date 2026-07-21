"""
irflow_produtos_repository.py

Único ponto de acesso SQL do domínio Produtos — segue a convenção de
`docs/engineering/ENGINEERING_GUIDE.md` §3.1 (controller → service →
repository). Nenhuma regra de negócio aqui, só queries parametrizadas.

Tabela: `produtos`. Nenhuma `FOREIGN KEY` declarada, mesma convenção do
resto do schema (`docs/engineering/DATABASE.md` seção 3).

Depende de: nenhum outro módulo de domínio.
"""

_COLUNAS = (
    "id, categoria, marca, modelo, cor, capacidade, condicao, descricao, sku, fornecedor, "
    "preco_custo, preco_venda, quantidade, requer_rastreio_unidade, ativo, criado_em, atualizado_em"
)


def inserir(cursor, categoria, marca, modelo, cor, capacidade, condicao, descricao, sku, fornecedor,
            preco_custo, preco_venda, quantidade, requer_rastreio_unidade):
    cursor.execute(
        """
        INSERT INTO produtos (
            categoria, marca, modelo, cor, capacidade, condicao, descricao, sku, fornecedor,
            preco_custo, preco_venda, quantidade, requer_rastreio_unidade
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (categoria, marca, modelo, cor, capacidade, condicao, descricao, sku, fornecedor,
         preco_custo, preco_venda, quantidade, requer_rastreio_unidade),
    )
    return cursor.lastrowid


def atualizar(cursor, produto_id, categoria, marca, modelo, cor, capacidade, condicao, descricao, sku,
              fornecedor, preco_custo, preco_venda, quantidade, requer_rastreio_unidade, ativo):
    cursor.execute(
        """
        UPDATE produtos
        SET categoria = ?, marca = ?, modelo = ?, cor = ?, capacidade = ?, condicao = ?,
            descricao = ?, sku = ?, fornecedor = ?, preco_custo = ?, preco_venda = ?,
            quantidade = ?, requer_rastreio_unidade = ?, ativo = ?, atualizado_em = datetime('now')
        WHERE id = ?
        """,
        (categoria, marca, modelo, cor, capacidade, condicao, descricao, sku, fornecedor,
         preco_custo, preco_venda, quantidade, requer_rastreio_unidade, ativo, produto_id),
    )


def buscar_por_id(cursor, produto_id):
    cursor.execute(f"SELECT {_COLUNAS} FROM produtos WHERE id = ?", (produto_id,))
    return cursor.fetchone()


def _montar_filtros(termo, categoria, marca, condicao, ativo):
    condicoes = []
    params = []

    if termo:
        padrao = f"%{termo.lower()}%"
        condicoes.append(
            "(lower(descricao) LIKE ? OR lower(COALESCE(modelo, '')) LIKE ? OR lower(COALESCE(sku, '')) LIKE ?)"
        )
        params.extend([padrao, padrao, padrao])
    if categoria:
        condicoes.append("categoria = ?")
        params.append(categoria)
    if marca:
        condicoes.append("lower(COALESCE(marca, '')) = ?")
        params.append(marca.lower())
    if condicao:
        condicoes.append("condicao = ?")
        params.append(condicao)
    if ativo is not None:
        condicoes.append("ativo = ?")
        params.append(1 if ativo else 0)

    where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
    return where, params


def buscar_paginado(cursor, termo, categoria, marca, condicao, ativo, limit, offset):
    where, params = _montar_filtros(termo, categoria, marca, condicao, ativo)
    cursor.execute(
        f"SELECT {_COLUNAS} FROM produtos {where} ORDER BY categoria, modelo, id LIMIT ? OFFSET ?",
        (*params, limit, offset),
    )
    return cursor.fetchall()


def contar(cursor, termo, categoria, marca, condicao, ativo):
    where, params = _montar_filtros(termo, categoria, marca, condicao, ativo)
    cursor.execute(f"SELECT COUNT(*) FROM produtos {where}", params)
    return cursor.fetchone()[0] or 0


def deletar(cursor, produto_id):
    cursor.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
