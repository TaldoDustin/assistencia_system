"""
INC-001 — instrumentação de conexões (docs/operations/INCIDENTS/INC-001-database-is-locked.md,
seção "Critérios de aceitação — instrumentação de conexões").

Escopo: `_ConexaoRastreada` (app.py) envolve `conectar()` para logar OPEN/COMMIT/ROLLBACK/CLOSE
e avisar quando uma conexão é coletada pelo GC sem `close()` explícito -- evidência de runtime
para o mecanismo suspeito do INC-001, sem alterar nenhum comportamento funcional. Desligada por
padrão (`IR_FLOW_DEBUG_CONN_TRACE`); estes testes ligam/desligam via monkeypatch do módulo, nunca
da variável de ambiente (o valor já foi lido uma única vez na importação de `app.py`).

Cada teste corresponde diretamente a um critério de aceitação (C-1 a C-9):
- C-1/C-3: desligada, `conectar()` devolve uma `sqlite3.Connection` normal.
- C-2/C-9 (transparência): ligada, o wrapper delega cursor/execute/atributos não instrumentados
  à conexão real -- comportamento indistinguível de um `sqlite3.Connection` normal.
- Ausência de falso positivo: 100 conexões abertas e fechadas corretamente não geram nenhum aviso.
- Detecção real: uma conexão não fechada gera o aviso, com stack resumida e os campos esperados.
- C-4: milhares de ciclos open/cursor/commit/close não explodem o tempo de execução.
"""

import gc
import logging
import sqlite3
import time

import pytest

import app as _app


@pytest.fixture
def conn_trace_ligado():
    """Liga a instrumentação para o teste, restaurando o estado original ao final --
    nunca mexe na variável de ambiente (já lida uma única vez na importação do módulo)."""
    original = _app._CONN_TRACE_ATIVO
    _app._CONN_TRACE_ATIVO = True
    try:
        yield
    finally:
        _app._CONN_TRACE_ATIVO = original


class TestDesligadaPorPadrao:
    def test_conectar_devolve_conexao_normal_quando_desligada(self):
        assert _app._CONN_TRACE_ATIVO is False
        conn = _app.conectar()
        try:
            assert type(conn) is sqlite3.Connection
            assert not isinstance(conn, _app._ConexaoRastreada)
        finally:
            conn.close()


class TestTransparenciaDoWrapper:
    def test_conectar_devolve_wrapper_quando_ligada(self, conn_trace_ligado):
        conn = _app.conectar()
        try:
            assert isinstance(conn, _app._ConexaoRastreada)
        finally:
            conn.close()

    def test_cursor_e_execute_funcionam_normalmente(self, conn_trace_ligado):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            assert cursor.fetchone() == (1,)

            conn.execute("SELECT 2")
        finally:
            conn.close()

    def test_atributo_nao_instrumentado_e_delegado_a_conexao_real(self, conn_trace_ligado):
        """Requisito de transparência (C-2/C-9): setar um atributo não conhecido pelo
        wrapper (ex. row_factory) deve propagar para a conexão real, não ficar preso
        só no objeto wrapper."""
        conn = _app.conectar()
        try:
            conn.row_factory = sqlite3.Row
            assert conn._conn.row_factory is sqlite3.Row

            cursor = conn.cursor()
            cursor.execute("SELECT 1 AS um")
            row = cursor.fetchone()
            assert row["um"] == 1
        finally:
            conn.close()

    def test_commit_e_rollback_delegam_para_conexao_real(self, conn_trace_ligado):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS _inc001_teste_trace (id INTEGER)")
            cursor.execute("INSERT INTO _inc001_teste_trace (id) VALUES (1)")
            conn.commit()

            cursor.execute("INSERT INTO _inc001_teste_trace (id) VALUES (2)")
            conn.rollback()

            cursor.execute("SELECT COUNT(*) FROM _inc001_teste_trace")
            assert cursor.fetchone() == (1,)
        finally:
            conn.execute("DROP TABLE IF EXISTS _inc001_teste_trace")
            conn.commit()
            conn.close()


class TestAusenciaDeFalsoPositivo:
    def test_cem_conexoes_fechadas_corretamente_nao_geram_aviso(self, conn_trace_ligado, caplog):
        with caplog.at_level(logging.WARNING, logger="app"):
            for _ in range(100):
                conn = _app.conectar()
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                conn.commit()
                conn.close()
            gc.collect()

        avisos_de_vazamento = [
            r for r in caplog.records if "coletada pelo GC sem close()" in r.getMessage()
        ]
        assert avisos_de_vazamento == []


class TestDeteccaoDeVazamentoReal:
    def test_conexao_nao_fechada_gera_aviso_com_stack_resumida(self, conn_trace_ligado, caplog):
        with caplog.at_level(logging.WARNING, logger="app"):
            conn = _app.conectar()
            conn.cursor().execute("SELECT 1")
            conn_id_esperado = conn._id
            del conn
            gc.collect()

        avisos = [r for r in caplog.records if "coletada pelo GC sem close()" in r.getMessage()]
        assert len(avisos) == 1

        aviso = avisos[0]
        assert aviso.inc001_connection_id == conn_id_esperado
        assert aviso.inc001_close_called is False
        assert aviso.inc001_route  # thread de teste, sem contexto HTTP -- ainda assim não vazio
        assert "test_conexao_nao_fechada_gera_aviso_com_stack_resumida" in aviso.inc001_stack


class TestOverhead:
    def test_milhares_de_ciclos_nao_explodem_tempo(self, conn_trace_ligado):
        """Sanity check, não benchmark: só confirma que ligar a instrumentação não
        introduz um custo absurdo por conexão (C-4)."""
        inicio = time.monotonic()
        for _ in range(2000):
            conn = _app.conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            conn.commit()
            conn.close()
        duracao = time.monotonic() - inicio

        assert duracao < 15
