"""
fluxoly_caixa_repository.py

Único ponto de acesso SQL do domínio Caixa -- segue a convenção de
docs/engineering/ENGINEERING_GUIDE.md §3.1 (controller → service →
repository). Nenhuma regra de negócio aqui, só queries parametrizadas.

Tabela: `movimentacoes_caixa`. Nenhuma `FOREIGN KEY` declarada, mesma
convenção do resto do schema -- `origem_id` é FK lógica polimórfica (aponta
para `vendas`, `contas_pagar` ou `contas_receber` conforme `origem`).

Depende de: nenhum outro módulo de domínio.
"""

_COLUNAS = "id, tipo, valor, descricao, origem, origem_id, estornada, usuario_id, criado_em"


def inserir(cursor, tipo, valor, descricao, origem, origem_id, usuario_id):
    cursor.execute(
        """
        INSERT INTO movimentacoes_caixa (tipo, valor, descricao, origem, origem_id, usuario_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (tipo, valor, descricao, origem, origem_id, usuario_id),
    )
    return cursor.lastrowid


def buscar_por_id(cursor, movimentacao_id):
    cursor.execute(f"SELECT {_COLUNAS} FROM movimentacoes_caixa WHERE id = ?", (movimentacao_id,))
    return cursor.fetchone()


def buscar_ativa_por_origem(cursor, origem, origem_id):
    cursor.execute(
        f"SELECT {_COLUNAS} FROM movimentacoes_caixa WHERE origem = ? AND origem_id = ? AND estornada = 0",
        (origem, origem_id),
    )
    return cursor.fetchone()


def estornar(cursor, movimentacao_id):
    cursor.execute(
        "UPDATE movimentacoes_caixa SET estornada = 1 WHERE id = ? AND estornada = 0",
        (movimentacao_id,),
    )
    return cursor.rowcount


def buscar_paginado(cursor, tipo, origem, data_inicio, data_fim, limit, offset):
    condicoes = []
    params = []
    if tipo:
        condicoes.append("tipo = ?")
        params.append(tipo)
    if origem:
        condicoes.append("origem = ?")
        params.append(origem)
    if data_inicio:
        condicoes.append("criado_em >= ?")
        params.append(data_inicio)
    if data_fim:
        condicoes.append("criado_em <= ?")
        params.append(data_fim)
    where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
    params.extend([limit, offset])
    cursor.execute(
        f"SELECT {_COLUNAS} FROM movimentacoes_caixa {where} ORDER BY criado_em DESC, id DESC LIMIT ? OFFSET ?",
        params,
    )
    return cursor.fetchall()


def contar(cursor, tipo, origem, data_inicio, data_fim):
    condicoes = []
    params = []
    if tipo:
        condicoes.append("tipo = ?")
        params.append(tipo)
    if origem:
        condicoes.append("origem = ?")
        params.append(origem)
    if data_inicio:
        condicoes.append("criado_em >= ?")
        params.append(data_inicio)
    if data_fim:
        condicoes.append("criado_em <= ?")
        params.append(data_fim)
    where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
    cursor.execute(f"SELECT COUNT(*) FROM movimentacoes_caixa {where}", params)
    return cursor.fetchone()[0] or 0


def calcular_saldo(cursor):
    """BR-069 -- SOMA(entradas não estornadas) - SOMA(saídas não estornadas)."""
    cursor.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN valor ELSE 0 END), 0)
            - COALESCE(SUM(CASE WHEN tipo = 'saida' THEN valor ELSE 0 END), 0)
        FROM movimentacoes_caixa
        WHERE estornada = 0
        """
    )
    return cursor.fetchone()[0] or 0.0


def agrupar_por_periodo(cursor, data_inicio, data_fim):
    """Fluxo de caixa simples: totais de entrada/saída agrupados por dia
    (`substr(criado_em, 1, 10)`), só movimentações não estornadas."""
    condicoes = ["estornada = 0"]
    params = []
    if data_inicio:
        condicoes.append("criado_em >= ?")
        params.append(data_inicio)
    if data_fim:
        condicoes.append("criado_em <= ?")
        params.append(data_fim)
    where = f"WHERE {' AND '.join(condicoes)}"
    cursor.execute(
        f"""
        SELECT
            substr(criado_em, 1, 10) AS dia,
            COALESCE(SUM(CASE WHEN tipo = 'entrada' THEN valor ELSE 0 END), 0) AS entradas,
            COALESCE(SUM(CASE WHEN tipo = 'saida' THEN valor ELSE 0 END), 0) AS saidas
        FROM movimentacoes_caixa
        {where}
        GROUP BY dia
        ORDER BY dia
        """,
        params,
    )
    return cursor.fetchall()
