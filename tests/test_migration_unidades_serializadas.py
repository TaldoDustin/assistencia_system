"""
Testes do script de migração `scripts/migrate_unidades_serializadas.py`
(ADR-007, docs/engineering/migrations/MIGRATION_unidades_serializadas.md).

Fluxo: banco descartável com o schema ANTIGO de `estoque_unidades`, semeado
com casos de borda -> roda o script de migração de verdade -> compara o
banco resultante. Nunca toca `database.db` real — cada teste cria seu
próprio arquivo SQLite temporário.
"""

import sqlite3

import pytest

from scripts.migrate_unidades_serializadas import migrar

SCHEMA_ANTIGO_SQL = """
CREATE TABLE estoque_unidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    estoque_id INTEGER NOT NULL,
    lote_id INTEGER,
    imei TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'disponivel',
    reservado_por INTEGER,
    reservado_ate TEXT,
    venda_id INTEGER,
    criado_em TEXT NOT NULL DEFAULT (datetime('now')),
    atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

INDICES_ANTIGOS_SQL = [
    "CREATE INDEX idx_estoque_unidades_estoque_id ON estoque_unidades (estoque_id)",
    "CREATE INDEX idx_estoque_unidades_status ON estoque_unidades (status)",
    "CREATE INDEX idx_estoque_unidades_imei ON estoque_unidades (imei)",
]

LINHAS_SEED = [
    # (estoque_id, lote_id, imei, status, reservado_por, reservado_ate, venda_id)
    (1, None, "111111111111111", "disponivel", None, None, None),
    (1, 7, "222222222222222", "em_reparo", None, None, None),
    (2, None, None, "disponivel", None, None, None),
    (2, 3, "444444444444444", "devolvido", None, None, None),
    (3, None, "555555555555555", "disponivel", 9, "2026-08-01 12:00:00", 42),
]


@pytest.fixture
def db_com_schema_antigo(tmp_path):
    db_path = tmp_path / "legado.db"
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(SCHEMA_ANTIGO_SQL)
        for sql in INDICES_ANTIGOS_SQL:
            cursor.execute(sql)
        cursor.executemany(
            """
            INSERT INTO estoque_unidades
                (estoque_id, lote_id, imei, status, reservado_por, reservado_ate, venda_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            LINHAS_SEED,
        )
        conn.commit()
    finally:
        conn.close()
    return db_path


def _linhas_estoque_unidades_antigas(db_path):
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, estoque_id, lote_id, imei, status, reservado_por, reservado_ate, "
            "venda_id, criado_em, atualizado_em FROM estoque_unidades ORDER BY id"
        )
        return cursor.fetchall()
    finally:
        conn.close()


class TestMigracao:
    def test_migracao_preserva_contagem_e_dados(self, db_com_schema_antigo):
        antes = _linhas_estoque_unidades_antigas(db_com_schema_antigo)

        migrar(db_com_schema_antigo)

        conn = sqlite3.connect(db_com_schema_antigo)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, estoque_id, produto_id, lote_id, imei, status, reservado_por, "
                "reservado_ate, venda_id, saude_bateria, localizacao, criado_em, atualizado_em "
                "FROM unidades_serializadas ORDER BY id"
            )
            depois = cursor.fetchall()
        finally:
            conn.close()

        assert len(depois) == len(antes) == len(LINHAS_SEED)
        for linha_antiga, linha_nova in zip(antes, depois, strict=True):
            (id_, estoque_id, lote_id, imei, status, reservado_por, reservado_ate,
             venda_id, criado_em, atualizado_em) = linha_antiga
            assert linha_nova[0] == id_
            assert linha_nova[1] == estoque_id
            assert linha_nova[2] is None  # produto_id
            assert linha_nova[3] == lote_id
            assert linha_nova[4] == imei
            assert linha_nova[5] == status
            assert linha_nova[6] == reservado_por
            assert linha_nova[7] == reservado_ate
            assert linha_nova[8] == venda_id
            assert linha_nova[9] is None  # saude_bateria
            assert linha_nova[10] is None  # localizacao
            assert linha_nova[11] == criado_em
            assert linha_nova[12] == atualizado_em

    def test_migracao_remove_tabela_antiga(self, db_com_schema_antigo):
        migrar(db_com_schema_antigo)

        conn = sqlite3.connect(db_com_schema_antigo)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='estoque_unidades'")
            assert cursor.fetchone() is None
        finally:
            conn.close()

    def test_migracao_recria_indices(self, db_com_schema_antigo):
        migrar(db_com_schema_antigo)

        conn = sqlite3.connect(db_com_schema_antigo)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='unidades_serializadas'"
            )
            indices = {row[0] for row in cursor.fetchall()}
        finally:
            conn.close()

        assert "idx_unidades_serializadas_estoque_id" in indices
        assert "idx_unidades_serializadas_produto_id" in indices
        assert "idx_unidades_serializadas_status" in indices
        assert "idx_unidades_serializadas_imei" in indices

    def test_sqlite_sequence_permite_novo_insert_sem_colisao(self, db_com_schema_antigo):
        migrar(db_com_schema_antigo)

        conn = sqlite3.connect(db_com_schema_antigo)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO unidades_serializadas (estoque_id, imei) VALUES (1, '999999999999999')"
            )
            conn.commit()
            novo_id = cursor.lastrowid

            cursor.execute("SELECT COUNT(*) FROM unidades_serializadas WHERE id = ?", (novo_id,))
            assert cursor.fetchone()[0] == 1
            assert novo_id > len(LINHAS_SEED)
        finally:
            conn.close()

    def test_migracao_e_idempotente(self, db_com_schema_antigo):
        primeira_msg = migrar(db_com_schema_antigo)
        assert "concluída" in primeira_msg

        conn = sqlite3.connect(db_com_schema_antigo)
        try:
            contagem_apos_primeira = conn.execute(
                "SELECT COUNT(*) FROM unidades_serializadas"
            ).fetchone()[0]
        finally:
            conn.close()

        segunda_msg = migrar(db_com_schema_antigo)
        assert "Já migrado" in segunda_msg

        conn = sqlite3.connect(db_com_schema_antigo)
        try:
            contagem_apos_segunda = conn.execute(
                "SELECT COUNT(*) FROM unidades_serializadas"
            ).fetchone()[0]
        finally:
            conn.close()

        assert contagem_apos_segunda == contagem_apos_primeira == len(LINHAS_SEED)

    def test_migracao_sem_tabela_antiga_nao_faz_nada(self, tmp_path):
        db_path = tmp_path / "banco_novo.db"
        conn = sqlite3.connect(db_path)
        conn.execute("CREATE TABLE outra_coisa (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

        msg = migrar(db_path)
        assert "não existe" in msg or "nada para migrar" in msg
