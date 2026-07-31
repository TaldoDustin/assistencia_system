"""
fluxoly_clientes_repository.py

Único ponto de acesso SQL do domínio Clientes — segue a convenção de
`docs/engineering/ENGINEERING_GUIDE.md` §3.1 (controller → service →
repository). Nenhuma regra de negócio aqui, só queries parametrizadas.

Tabela: `clientes`. Nenhuma `FOREIGN KEY` declarada, mesma convenção do
resto do schema (`docs/engineering/DATABASE.md` seção 3).

Depende de: nenhum outro módulo de domínio.
"""

_COLUNAS = "id, nome, telefone, email, cpf_cnpj, observacoes, criado_em, atualizado_em"


def inserir(cursor, nome, telefone, email, cpf_cnpj, observacoes):
    cursor.execute(
        """
        INSERT INTO clientes (nome, telefone, email, cpf_cnpj, observacoes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nome, telefone, email, cpf_cnpj, observacoes),
    )
    return cursor.lastrowid


def atualizar(cursor, cliente_id, nome, telefone, email, cpf_cnpj, observacoes):
    cursor.execute(
        """
        UPDATE clientes
        SET nome = ?, telefone = ?, email = ?, cpf_cnpj = ?, observacoes = ?,
            atualizado_em = datetime('now')
        WHERE id = ?
        """,
        (nome, telefone, email, cpf_cnpj, observacoes, cliente_id),
    )


def buscar_por_id(cursor, cliente_id):
    cursor.execute(f"SELECT {_COLUNAS} FROM clientes WHERE id = ?", (cliente_id,))
    return cursor.fetchone()


def buscar_paginado(cursor, termo, limit, offset):
    if termo:
        padrao = f"%{termo.lower()}%"
        cursor.execute(
            f"""
            SELECT {_COLUNAS} FROM clientes
            WHERE lower(nome) LIKE ? OR lower(COALESCE(telefone, '')) LIKE ? OR lower(COALESCE(cpf_cnpj, '')) LIKE ?
            ORDER BY nome
            LIMIT ? OFFSET ?
            """,
            (padrao, padrao, padrao, limit, offset),
        )
    else:
        cursor.execute(f"SELECT {_COLUNAS} FROM clientes ORDER BY nome LIMIT ? OFFSET ?", (limit, offset))
    return cursor.fetchall()


def contar(cursor, termo):
    if termo:
        padrao = f"%{termo.lower()}%"
        cursor.execute(
            """
            SELECT COUNT(*) FROM clientes
            WHERE lower(nome) LIKE ? OR lower(COALESCE(telefone, '')) LIKE ? OR lower(COALESCE(cpf_cnpj, '')) LIKE ?
            """,
            (padrao, padrao, padrao),
        )
    else:
        cursor.execute("SELECT COUNT(*) FROM clientes")
    return cursor.fetchone()[0] or 0


def possui_os_vinculada(cursor, cliente_id):
    cursor.execute("SELECT 1 FROM os WHERE cliente_id = ? LIMIT 1", (cliente_id,))
    return cursor.fetchone() is not None


def deletar(cursor, cliente_id):
    cursor.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
