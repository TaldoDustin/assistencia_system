"""
Testes do sistema de migrations (TD-03, Fase 2 Fatia 1).

Escopo desta fatia: só o mecanismo novo (migrations/), isolado -- app.py não
foi alterado, então nenhum teste aqui usa a fixture `app`/`client` de
conftest.py. Ver docs/operations/SPRINTS/SPRINT_TD03_MIGRATIONS_FORMAIS.md
seção 12 para a lista de testes obrigatórios desta fatia.
"""

import sqlite3

import pytest

from migrations.registry import MIGRATIONS
from migrations.runner import run_migrations

TABELAS_ESPERADAS = {
    "reparos",
    "os",
    "estoque",
    "estoque_lotes",
    "os_pecas",
    "os_reparos",
    "movimentacoes",
    "custos_operacionais",
    "integracao_sync_estado",
    "integracao_os_vistas",
    "compras",
    "usuarios",
    "os_checklists",
    "login_attempts",
    "audit_log",
    "password_reset_tokens",
    "clientes",
    "unidades_serializadas",
    "produtos",
    "vendas",
    "vendas_itens",
    "tipos_garantia",
    "shopping_list",
    "shopping_list_logs",
}

INDICES_ESPERADOS = {
    "idx_login_attempts_identificador_criado_em",
    "idx_audit_log_entidade",
    "idx_password_reset_tokens_usuario_id",
    "idx_clientes_telefone",
    "idx_clientes_cpf_cnpj",
    "idx_clientes_nome",
    "idx_unidades_serializadas_estoque_id",
    "idx_unidades_serializadas_produto_id",
    "idx_unidades_serializadas_status",
    "idx_unidades_serializadas_imei",
    "idx_produtos_categoria",
    "idx_produtos_sku",
    "idx_produtos_ativo",
    "idx_vendas_cliente_id",
    "idx_vendas_vendedor_id",
    "idx_vendas_itens_venda_id",
    "idx_vendas_itens_unidade_ativa",
    "idx_os_origem_id_externo",
    "idx_estoque_sku",
    "idx_estoque_tripla",
    "idx_lotes_estoque_id",
    "idx_shopping_list_os_produto",
}


@pytest.fixture
def conn():
    conexao = sqlite3.connect(":memory:")
    yield conexao
    conexao.close()


class TestBaselineEmBancoVazio:
    def test_cria_as_24_tabelas_esperadas(self, conn):
        run_migrations(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = {row[0] for row in cursor.fetchall()}
        assert tabelas >= TABELAS_ESPERADAS

    def test_cria_os_22_indices_esperados(self, conn):
        run_migrations(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = {row[0] for row in cursor.fetchall()}
        assert indices >= INDICES_ESPERADOS

    def test_retorna_id_da_migration_aplicada(self, conn):
        executadas = run_migrations(conn)
        assert executadas == ["0001"]


class TestIdempotencia:
    def test_rodar_duas_vezes_nao_reaplica_nem_falha(self, conn):
        primeira = run_migrations(conn)
        segunda = run_migrations(conn)
        assert primeira == ["0001"]
        assert segunda == []

    def test_schema_migrations_fica_com_exatamente_0001(self, conn):
        run_migrations(conn)
        run_migrations(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM schema_migrations")
        assert cursor.fetchall() == [("0001",)]

    def test_reaplicar_a_migration_direto_nao_duplica_backfill(self, conn):
        # Backfill de estoque_lotes é condicional (WHERE NOT EXISTS) -- roda
        # sem duplicar mesmo se a migration em si fosse chamada de novo (o
        # que run_migrations() nunca faz, mas o backfill é seguro por
        # conteúdo, não só por schema_migrations).
        run_migrations(conn)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO estoque (descricao, quantidade) VALUES ('Tela iPhone', 5)")
        conn.commit()
        MIGRATIONS[0].apply(cursor, conn)
        MIGRATIONS[0].apply(cursor, conn)
        cursor.execute("SELECT id FROM estoque WHERE descricao = 'Tela iPhone'")
        estoque_id = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM estoque_lotes WHERE estoque_id = ?", (estoque_id,))
        assert cursor.fetchone()[0] == 1


class TestBancoAtrasado:
    def test_baseline_completa_banco_sem_colunas_recentes(self, conn):
        """Simula um banco 'atrasado' -- schema mínimo original, sem os 37
        ALTER TABLE aditivos -- e confirma que run_migrations() completa
        corretamente (prova direta da decisão da Phase 1 seção 6: a baseline
        não pode assumir que as colunas aditivas já existem)."""
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE os (
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
            """
        )
        cursor.execute(
            """
            CREATE TABLE estoque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT,
                valor REAL,
                fornecedor TEXT,
                quantidade INTEGER,
                data_compra TEXT,
                sku TEXT,
                modelo TEXT,
                tipo TEXT,
                qualidade TEXT
            )
            """
        )
        cursor.execute(
            "CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nome TEXT NOT NULL, "
            "usuario TEXT UNIQUE NOT NULL, senha_hash TEXT NOT NULL, "
            "perfil TEXT NOT NULL DEFAULT 'tecnico', ativo INTEGER NOT NULL DEFAULT 1)"
        )
        conn.commit()

        run_migrations(conn)

        cursor.execute("PRAGMA table_info(os)")
        colunas_os = {row[1] for row in cursor.fetchall()}
        assert {"data_finalizado", "modelo", "cliente_id", "id_externo_integracao"} <= colunas_os

        cursor.execute("PRAGMA table_info(estoque)")
        colunas_estoque = {row[1] for row in cursor.fetchall()}
        assert {"requer_imei"} <= colunas_estoque

        cursor.execute("PRAGMA table_info(usuarios)")
        colunas_usuarios = {row[1] for row in cursor.fetchall()}
        assert "limite_desconto_livre" in colunas_usuarios


class TestOrdemDeExecucao:
    def test_registry_nao_esta_vazio_e_comeca_pela_0001(self):
        assert len(MIGRATIONS) >= 1
        assert MIGRATIONS[0].ID == "0001"

    def test_ids_sao_unicos_e_crescentes(self):
        ids = [m.ID for m in MIGRATIONS]
        assert len(ids) == len(set(ids))
        assert ids == sorted(ids)


class TestProtecaoContraLocked:
    def test_operational_error_locked_retorna_lista_vazia_sem_propagar(self, conn, monkeypatch):
        class _MigracaoQueTrava:
            ID = "9999"

            @staticmethod
            def apply(cursor, conn):
                raise sqlite3.OperationalError("database is locked")

        monkeypatch.setattr("migrations.runner.MIGRATIONS", [_MigracaoQueTrava])
        resultado = run_migrations(conn)
        assert resultado == []

    def test_operational_error_sem_locked_propaga(self, conn, monkeypatch):
        class _MigracaoComErroReal:
            ID = "9999"

            @staticmethod
            def apply(cursor, conn):
                raise sqlite3.OperationalError("syntax error near FOO")

        monkeypatch.setattr("migrations.runner.MIGRATIONS", [_MigracaoComErroReal])
        with pytest.raises(sqlite3.OperationalError):
            run_migrations(conn)


class TestEquivalenciaComOMecanismoAntigo:
    def test_schema_gerado_bate_com_criar_tabelas_original(self, conn):
        """Comparação byte-a-byte (após normalizar espaços) contra o schema
        real produzido por app.py::criar_tabelas() -- prova que a Fatia 1
        preserva o comportamento verbatim, não só 'parece igual'."""
        import re

        import app as appmod

        def normalizar(sql):
            return re.sub(r"\s+", " ", sql).strip()

        conn_app = appmod.conectar()
        cursor_app = conn_app.cursor()
        cursor_app.execute(
            "SELECT name, sql FROM sqlite_master WHERE type IN ('table','index') "
            "AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )
        schema_original = {nome: normalizar(sql) for nome, sql in cursor_app.fetchall() if sql}
        conn_app.close()

        run_migrations(conn)
        cursor_novo = conn.cursor()
        cursor_novo.execute(
            "SELECT name, sql FROM sqlite_master WHERE type IN ('table','index') "
            "AND name NOT LIKE 'sqlite_%' AND name != 'schema_migrations' ORDER BY name"
        )
        schema_novo = {nome: normalizar(sql) for nome, sql in cursor_novo.fetchall() if sql}

        assert set(schema_original.keys()) == set(schema_novo.keys())
        divergentes = {
            nome: (schema_original[nome], schema_novo[nome])
            for nome in schema_original
            if schema_original[nome] != schema_novo[nome]
        }
        assert divergentes == {}
