#!/usr/bin/env python3
"""Importa um banco legado SQLite para o IR Flow com backup e migração básica de schema.

Uso:
  python scripts/import_legacy_db.py --legacy /caminho/database_antigo.db
  python scripts/import_legacy_db.py --legacy /caminho/database_antigo.db --target /home/usuario/assistencia_system/database.db
"""

from __future__ import annotations

import argparse
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_TARGET_DB = BASE_DIR / "database.db"
BACKUP_DIR = BASE_DIR / "backups"


CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS reparos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS os (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tipo TEXT,
        cliente TEXT,
        aparelho TEXT,
        tecnico TEXT,
        reparo_id INTEGER,
        status TEXT,
        valor_cobrado REAL,
        valor_descontado REAL,
        custo_pecas REAL,
        data TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS estoque (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT,
        valor REAL,
        fornecedor TEXT,
        quantidade INTEGER,
        data_compra TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS os_pecas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        os_id INTEGER,
        estoque_id INTEGER,
        quantidade INTEGER,
        valor REAL
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS os_reparos (
        os_id INTEGER NOT NULL,
        reparo_id INTEGER NOT NULL,
        PRIMARY KEY (os_id, reparo_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS movimentacoes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        estoque_id INTEGER,
        tipo TEXT,
        quantidade INTEGER,
        data TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS custos_operacionais (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descricao TEXT NOT NULL,
        categoria TEXT,
        valor REAL NOT NULL,
        data TEXT,
        observacoes TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS integracao_sync_estado (
        chave TEXT PRIMARY KEY,
        valor TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS integracao_os_vistas (
        origem TEXT NOT NULL,
        id_externo TEXT NOT NULL,
        primeira_visualizacao TEXT,
        PRIMARY KEY (origem, id_externo)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        usuario TEXT UNIQUE NOT NULL,
        senha_hash TEXT NOT NULL,
        perfil TEXT NOT NULL DEFAULT 'tecnico',
        ativo INTEGER NOT NULL DEFAULT 1
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS os_checklists (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        os_id INTEGER NOT NULL UNIQUE,
        access_token TEXT UNIQUE,
        status_touch TEXT NOT NULL DEFAULT 'nao_testado',
        status_audio TEXT NOT NULL DEFAULT 'nao_testado',
        status_microfone TEXT NOT NULL DEFAULT 'nao_testado',
        status_camera TEXT NOT NULL DEFAULT 'nao_testado',
        status_botoes TEXT NOT NULL DEFAULT 'nao_testado',
        observacoes TEXT NOT NULL DEFAULT '',
        executado_por TEXT NOT NULL DEFAULT '',
        origem TEXT NOT NULL DEFAULT '',
        resultado_json TEXT NOT NULL DEFAULT '{}',
        criado_em TEXT NOT NULL DEFAULT '',
        atualizado_em TEXT NOT NULL DEFAULT ''
    )
    """,
]

REQUIRED_COLUMNS = {
    "os_pecas": [
        ("valor", "REAL"),
        ("peca_descricao", "TEXT"),
        ("peca_fornecedor", "TEXT"),
        ("peca_modelo", "TEXT"),
    ],
    "os": [
        ("data_finalizado", "TEXT"),
        ("modelo", "TEXT"),
        ("cor", "TEXT"),
        ("imei", "TEXT"),
        ("vendedor", "TEXT"),
        ("observacoes", "TEXT"),
        ("origem_integracao", "TEXT"),
        ("id_externo_integracao", "TEXT"),
    ],
    "estoque": [
        ("modelo", "TEXT"),
    ],
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Importa banco legado e atualiza schema do IR Flow")
    parser.add_argument("--legacy", required=True, help="Caminho para o banco legado (.db)")
    parser.add_argument("--target", default=str(DEFAULT_TARGET_DB), help="Caminho do database.db atual")
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Nao cria backup do banco atual antes de substituir",
    )
    return parser.parse_args()


def backup_current_db(target_db: Path) -> Path | None:
    if not target_db.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = BACKUP_DIR / f"database-before-legacy-import-{stamp}.db"
    shutil.copy2(target_db, backup_path)
    return backup_path


def replace_db(legacy_db: Path, target_db: Path) -> None:
    target_db.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(legacy_db, target_db)


def table_columns(cursor: sqlite3.Cursor, table_name: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def ensure_schema(db_path: Path) -> None:
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()

        for sql in CREATE_TABLES_SQL:
            cursor.execute(sql)

        for table_name, columns in REQUIRED_COLUMNS.items():
            existing = table_columns(cursor, table_name)
            for column_name, column_type in columns:
                if column_name not in existing:
                    cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")

        cursor.execute(
            """
            INSERT OR IGNORE INTO os_reparos (os_id, reparo_id)
            SELECT id, reparo_id
            FROM os
            WHERE reparo_id IS NOT NULL
            """
        )

        conn.commit()
    finally:
        conn.close()


def main() -> int:
    args = parse_args()
    legacy_db = Path(args.legacy).expanduser().resolve()
    target_db = Path(args.target).expanduser().resolve()

    if not legacy_db.exists():
        raise FileNotFoundError(f"Banco legado nao encontrado: {legacy_db}")
    if legacy_db.suffix.lower() != ".db":
        raise ValueError("Arquivo legado precisa ter extensao .db")

    backup_path = None
    if not args.no_backup:
        backup_path = backup_current_db(target_db)

    replace_db(legacy_db, target_db)
    ensure_schema(target_db)

    print("Importacao concluida com sucesso.")
    print(f"Banco ativo: {target_db}")
    if backup_path:
        print(f"Backup do banco anterior: {backup_path}")
    else:
        print("Nenhum backup foi criado (banco anterior inexistente ou --no-backup).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
