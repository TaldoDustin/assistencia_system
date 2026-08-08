"""Runner do sistema de migrations (TD-03, Fase 2 Fatia 1).

run_migrations() é a única função pública. Idempotente -- seguro rodar em
banco vazio, atrasado, ou já atualizado (ver
docs/operations/SPRINTS/SPRINT_TD03_MIGRATIONS_FORMAIS.md seção 6).

Este módulo não importa nada de app.py deliberadamente -- app.py é quem vai
importar migrations.runner na Fatia 2, nunca o contrário (evita import
circular). Por isso duplica localmente o mínimo de configuração de conexão
SQLite (busy_timeout/WAL) que também existe em app.py::_configurar_conexao_sqlite
-- consolidar os dois num único lugar fica para quando a Fatia 2 unificar a
camada de conexão, não é escopo desta fatia.
"""

import os
import sqlite3

from fluxoly_config import DB_PATH
from migrations.registry import MIGRATIONS

_SQLITE_TIMEOUT_SECONDS = max(5, int(os.environ.get("IR_FLOW_SQLITE_TIMEOUT_SECONDS", "30")))


def _abrir_conexao_propria() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=_SQLITE_TIMEOUT_SECONDS)
    conn.execute(f"PRAGMA busy_timeout = {_SQLITE_TIMEOUT_SECONDS * 1000}")
    conn.execute("PRAGMA synchronous = NORMAL")
    try:
        conn.execute("PRAGMA journal_mode = WAL")
    except sqlite3.OperationalError as exc:
        if "locked" not in str(exc).lower():
            raise
    return conn


def run_migrations(conn: sqlite3.Connection | None = None) -> list[str]:
    """Aplica migrations pendentes em ordem. Idempotente -- seguro em banco
    vazio, atrasado, ou já atualizado. `conn=None` abre conexão própria
    contra DB_PATH (mesmo padrão de app.py::criar_tabelas() hoje); `conn`
    explícito existe para testes (:memory:/tmp) e para reaproveitar uma
    conexão já aberta pelo chamador.

    Retorna a lista de IDs de migration efetivamente aplicadas nesta
    chamada (lista vazia se já estava tudo em dia, ou se outro worker
    estava migrando neste instante -- ver tratamento de "locked" abaixo).
    """
    conn_propria = conn is None
    if conn_propria:
        conn = _abrir_conexao_propria()

    try:
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "id TEXT PRIMARY KEY, aplicada_em TEXT NOT NULL DEFAULT (datetime('now')))"
        )
        conn.commit()

        cursor.execute("SELECT id FROM schema_migrations")
        aplicadas = {row[0] for row in cursor.fetchall()}

        executadas = []
        for modulo in MIGRATIONS:
            if modulo.ID in aplicadas:
                continue
            modulo.apply(cursor, conn)
            cursor.execute("INSERT INTO schema_migrations (id) VALUES (?)", (modulo.ID,))
            conn.commit()
            executadas.append(modulo.ID)
        return executadas
    except sqlite3.OperationalError as exc:
        if "locked" in str(exc).lower():
            # Outro worker pode estar aplicando migrations neste instante --
            # mesmo tratamento que app.py::criar_tabelas() já usa hoje.
            return []
        raise
    finally:
        if conn_propria:
            conn.close()
