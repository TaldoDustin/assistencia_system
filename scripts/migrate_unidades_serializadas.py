#!/usr/bin/env python3
"""
Migração `estoque_unidades` -> `unidades_serializadas` (ADR-007, ver
docs/engineering/migrations/MIGRATION_unidades_serializadas.md).

Recria a tabela (SQLite não permite relaxar NOT NULL via ALTER TABLE):
cria `unidades_serializadas_new`, copia os dados de `estoque_unidades`
(produto_id/saude_bateria/localizacao ficam NULL para linhas migradas),
valida a contagem, remove a tabela antiga, renomeia a nova e recria os
índices. Tudo dentro de uma única transação — uma falha em qualquer ponto
reverte por completo, sem estado intermediário.

Idempotente: se `unidades_serializadas` já existe e `estoque_unidades` não
existe mais, o script não faz nada (permite reexecução segura em deploy).

Use: python scripts/migrate_unidades_serializadas.py --db-path caminho/para/database.db
"""

import argparse
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_DB_PATH = BASE_DIR / "database.db"

NOVA_TABELA_SQL = """
CREATE TABLE unidades_serializadas_new (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estoque_id INTEGER,
    produto_id INTEGER,
    lote_id INTEGER,
    imei TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'disponivel',
    reservado_por INTEGER,
    reservado_ate TEXT,
    venda_id INTEGER,
    saude_bateria TEXT,
    localizacao TEXT,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

COPIA_DADOS_SQL = """
INSERT INTO unidades_serializadas_new
    (id, estoque_id, produto_id, lote_id, imei, status, reservado_por, reservado_ate,
     venda_id, saude_bateria, localizacao, criado_em, atualizado_em)
SELECT
    id, estoque_id, NULL, lote_id, imei, status, reservado_por, reservado_ate,
    venda_id, NULL, NULL, criado_em, atualizado_em
FROM estoque_unidades
"""

INDICES_SQL = [
    "CREATE INDEX idx_unidades_serializadas_estoque_id ON unidades_serializadas (estoque_id)",
    "CREATE INDEX idx_unidades_serializadas_produto_id ON unidades_serializadas (produto_id)",
    "CREATE INDEX idx_unidades_serializadas_status ON unidades_serializadas (status)",
    "CREATE INDEX idx_unidades_serializadas_imei ON unidades_serializadas (imei)",
]


class MigracaoAbortadaError(Exception):
    """Levantado quando uma validação falha e a migração deve ser abortada sem commit."""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migra estoque_unidades para unidades_serializadas (ADR-007)"
    )
    parser.add_argument("--db-path", default=str(DEFAULT_DB_PATH), help="Caminho do arquivo SQLite")
    return parser.parse_args()


def tabela_existe(cursor: sqlite3.Cursor, nome: str) -> bool:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (nome,))
    return cursor.fetchone() is not None


def ja_migrado(cursor: sqlite3.Cursor) -> bool:
    return tabela_existe(cursor, "unidades_serializadas") and not tabela_existe(
        cursor, "estoque_unidades"
    )


def contar_linhas(cursor: sqlite3.Cursor, tabela: str) -> int:
    cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
    return cursor.fetchone()[0]


def corrigir_sqlite_sequence(cursor: sqlite3.Cursor) -> None:
    """Garante que o próximo AUTOINCREMENT não colida com um id já usado."""
    cursor.execute("SELECT COALESCE(MAX(id), 0) FROM unidades_serializadas")
    max_id = cursor.fetchone()[0]

    cursor.execute("SELECT seq FROM sqlite_sequence WHERE name = 'unidades_serializadas'")
    row = cursor.fetchone()
    seq_atual = row[0] if row else None

    if seq_atual is None:
        cursor.execute(
            "INSERT INTO sqlite_sequence (name, seq) VALUES ('unidades_serializadas', ?)", (max_id,)
        )
    elif seq_atual < max_id:
        cursor.execute(
            "UPDATE sqlite_sequence SET seq = ? WHERE name = 'unidades_serializadas'", (max_id,)
        )


def migrar(db_path: Path) -> str:
    # isolation_level=None (autocommit) entrega o controle total da
    # transação para os comandos BEGIN/COMMIT/ROLLBACK explícitos abaixo —
    # necessário porque o modo implícito padrão do módulo sqlite3 pode
    # commitar antes de um DDL (CREATE/DROP/ALTER) mesmo dentro de uma
    # transação Python aberta, o que quebraria a garantia de tudo-ou-nada.
    conn = sqlite3.connect(db_path, isolation_level=None)
    try:
        cursor = conn.cursor()

        if ja_migrado(cursor):
            return "Já migrado — nenhuma ação necessária (script é idempotente)."

        if not tabela_existe(cursor, "estoque_unidades"):
            return "Tabela estoque_unidades não existe neste banco — nada para migrar."

        cursor.execute("BEGIN")

        contagem_antes = contar_linhas(cursor, "estoque_unidades")

        cursor.execute(NOVA_TABELA_SQL)
        cursor.execute(COPIA_DADOS_SQL)

        contagem_depois = contar_linhas(cursor, "unidades_serializadas_new")
        if contagem_depois != contagem_antes:
            conn.rollback()
            raise MigracaoAbortadaError(
                f"Contagem divergente: estoque_unidades tinha {contagem_antes} linhas, "
                f"unidades_serializadas_new ficou com {contagem_depois}. Migração abortada, "
                "nenhuma alteração foi commitada."
            )

        cursor.execute("DROP TABLE estoque_unidades")
        cursor.execute("ALTER TABLE unidades_serializadas_new RENAME TO unidades_serializadas")

        for sql in INDICES_SQL:
            cursor.execute(sql)

        corrigir_sqlite_sequence(cursor)

        conn.commit()
        return f"Migração concluída — {contagem_depois} unidade(s) migrada(s)."
    finally:
        conn.close()


def main() -> int:
    args = parse_args()
    db_path = Path(args.db_path).expanduser().resolve()

    if not db_path.exists():
        raise FileNotFoundError(f"Banco não encontrado: {db_path}")

    resultado = migrar(db_path)
    print(resultado)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
