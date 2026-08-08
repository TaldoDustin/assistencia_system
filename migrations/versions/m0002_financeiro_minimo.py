"""
Financeiro Mínimo (Caixa, Contas a Pagar/Receber) -- primeira migration de
negócio sobre o mecanismo formal da TD-03, ver
docs/engineering/plans/PLAN-financeiro-minimo.md e BR-067 a BR-069
(docs/product/BUSINESS_RULES.md).

DDL puro, sem backfill -- tabelas novas, sem dado legado a migrar.
"""

import sqlite3

ID = "0002"
DESCRICAO = "Financeiro mínimo: movimentacoes_caixa, contas_pagar, contas_receber"


def apply(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS movimentacoes_caixa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT NOT NULL,
        valor REAL NOT NULL,
        descricao TEXT,
        origem TEXT NOT NULL DEFAULT 'manual',
        origem_id INTEGER,
        estornada INTEGER NOT NULL DEFAULT 0,
        usuario_id INTEGER,
        criado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_movimentacoes_caixa_origem ON movimentacoes_caixa (origem, origem_id)"
    )
    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_movimentacoes_caixa_tipo_estornada " "ON movimentacoes_caixa (tipo, estornada)"
    )

    # Guardião real de BR-069 ("uma venda nunca gera duas entradas ativas") no banco,
    # não só na aplicação -- mesmo padrão de idx_vendas_itens_unidade_ativa (V1.2).
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_movimentacoes_caixa_venda_ativa "
        "ON movimentacoes_caixa (origem_id) WHERE origem = 'venda' AND estornada = 0"
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS contas_pagar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        categoria TEXT,
        valor REAL NOT NULL,
        data_vencimento TEXT,
        status TEXT NOT NULL DEFAULT 'pendente',
        movimentacao_caixa_id INTEGER,
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )

    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS contas_receber (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        categoria TEXT,
        valor REAL NOT NULL,
        data_vencimento TEXT,
        status TEXT NOT NULL DEFAULT 'pendente',
        movimentacao_caixa_id INTEGER,
        criado_em TEXT NOT NULL DEFAULT (datetime('now')),
        atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )
