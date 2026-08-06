"""
INC-001 — database is locked (docs/operations/INCIDENTS/INC-001-database-is-locked.md).

Escopo: POST /api/auth/login (fluxoly_blueprints_api.py::auth_login) era a rota
de escrita de maior frequência do sistema sem try/except/finally — uma
exceção entre abrir e fechar a conexão vazava o objeto com a transação de
escrita ainda aberta, bloqueando todo escritor seguinte em WAL até o
processo coletar aquele objeto via GC (não determinístico).

Este teste reproduz o mecanismo exato: injeta uma exceção na escrita real de
`registrar_tentativa` (INSERT INTO login_attempts). `registrar_tentativa` é
vinculada como closure a partir de `deps` uma única vez na criação do
blueprint (no import do módulo `app`) — não é um atributo de módulo
monkeypatch-ável depois (`monkeypatch.setattr` falha com AttributeError).
`sqlite3.Cursor.execute` também não é patchável (tipo C-extension imutável).
O único ponto de interceptação viável é a própria cell da closure: desde o
Python 3.7, `cell.cell_contents` é gravável, o que permite substituir a
função vinculada dentro de `auth_login` sem alterar seu código-fonte.

Confirma que uma requisição de escrita imediatamente seguinte não trava —
prova de que a conexão foi de fato fechada, não só que a resposta HTTP teve
o código certo.
"""

import sqlite3
import time

import pytest

SENHA_PADRAO = "senha_teste_123"


def _cell_da_closure(func, nome_freevar):
    indice = func.__code__.co_freevars.index(nome_freevar)
    return func.__closure__[indice]


@pytest.fixture
def falha_no_registrar_tentativa(app):
    """Faz a próxima chamada a `registrar_tentativa` (INSERT em login_attempts
    dentro de auth_login) levantar exceção uma única vez — mesmo ponto da
    causa raiz do INC-001 — e restaura a função original ao final do teste,
    mesmo se o teste falhar."""
    view = app.view_functions["api_auth.auth_login"]
    cell = _cell_da_closure(view, "registrar_tentativa")
    original = cell.cell_contents
    estado = {"ja_falhou": False}

    def registrar_tentativa_com_falha(cursor, identificador, sucesso):
        if not estado["ja_falhou"]:
            estado["ja_falhou"] = True
            raise sqlite3.OperationalError("falha simulada para reproduzir INC-001")
        return original(cursor, identificador, sucesso)

    cell.cell_contents = registrar_tentativa_com_falha
    try:
        yield
    finally:
        cell.cell_contents = original


class TestConexaoDeLoginFechaComExcecao:
    def test_excecao_durante_login_retorna_erro_sem_travar(self, client, falha_no_registrar_tentativa):
        resp = client.post("/api/auth/login", json={"usuario": "inexistente", "senha": "errada"})

        # Antes da correção, essa exceção propagava sem finally: a conexão
        # nunca fechava. Aqui só confirmamos que a rota responde com erro
        # tratado (não um 500 não tratado) — a prova real está no teste
        # seguinte (escrita imediata não trava).
        assert resp.status_code == 400

    def test_escrita_seguinte_nao_trava_apos_excecao_no_login(
        self, client, falha_no_registrar_tentativa, usuario_admin
    ):
        client.post("/api/auth/login", json={"usuario": "inexistente", "senha": "errada"})

        inicio = time.monotonic()
        resp = client.post(
            "/api/auth/login",
            json={"usuario": usuario_admin["usuario"], "senha": SENHA_PADRAO},
        )
        duracao = time.monotonic() - inicio

        assert resp.status_code == 200
        # Se a conexão da tentativa anterior tivesse vazado com a transação de
        # escrita aberta, esta requisição esperaria até o busy_timeout (30s,
        # SQLITE_TIMEOUT_SECONDS) antes de falhar com "database is locked".
        # Terminar rápido é a prova de que a conexão anterior foi fechada.
        assert duracao < 3
