"""
INC-001 — database is locked (docs/operations/INCIDENTS/INC-001-database-is-locked.md).

Escopo: as 4 rotas de checklist não tinham try/except/finally — mesmo mecanismo de
risco já corrigido em auth_login (INC-001). Uma exceção entre abrir e fechar a
conexão vazava o objeto com a transação de escrita ainda aberta, bloqueando todo
escritor seguinte em WAL até o processo coletar aquele objeto via GC (não
determinístico). Duas delas são públicas, sem login (GET/POST /api/checklist/<token>)
— maior risco, expostas a clientes finais via link compartilhado.

Cada rota tem 2 testes:
(a) contrato HTTP inalterado — mesmo status/payload no caminho feliz e no 404,
    confirmando que mover `conn.close()` para dentro de try/except/finally não
    mudou nenhum comportamento observável da API.
(b) uma exceção real injetada no ponto exato onde a rota lê/escreve
    (`_garantir_checklist_os` ou `_buscar_checklist_por_token`) prova que a
    conexão fecha corretamente: um login (escrita em `login_attempts`,
    tabela não relacionada) imediatamente seguinte não trava. Em SQLite/WAL o
    lock de escrita é por arquivo de banco, não por tabela — uma conexão
    vazada com uma transação de escrita pendente em `os_checklists` bloqueia
    também a escrita em `login_attempts`, mesma técnica de
    tests/test_inc001_login_connection_leak.py.

Nas rotas 1 e 2 (`obter_checklist_os`, `gerar_token_checklist_os`),
`_garantir_checklist_os` executa um INSERT real antes do `conn.commit()` da
rota — a exceção injetada ali reproduz fielmente o mecanismo do INC-001
(escrita pendente, sem commit, no momento da exceção). Nas rotas 3 e 4
(`obter_checklist_publico`, `salvar_checklist_publico`), a exceção é injetada
em `_buscar_checklist_por_token` antes de qualquer escrita própria da rota —
o teste (b) ali confirma que o `finally` sempre fecha a conexão
independentemente de onde a exceção ocorre, não que uma escrita específica
tenha vazado (rota 3 é somente leitura).
"""

import sqlite3
import time

import pytest

SENHA_PADRAO = "senha_teste_123"


def _cell_da_closure(func, nome_freevar):
    indice = func.__code__.co_freevars.index(nome_freevar)
    return func.__closure__[indice]


def _instalar_falha_unica(app, view_name, nome_freevar):
    """Substitui a free var `nome_freevar` (compartilhada por todas as rotas que a
    referenciam, já que é definida uma única vez no escopo de create_api_blueprint)
    por uma versão que executa o comportamento original e, em seguida, levanta uma
    exceção — uma única vez. Retorna (cell, original) para restauração no teardown."""
    view = app.view_functions[view_name]
    cell = _cell_da_closure(view, nome_freevar)
    original = cell.cell_contents
    estado = {"ja_falhou": False}

    def com_falha(*args, **kwargs):
        if not estado["ja_falhou"]:
            estado["ja_falhou"] = True
            original(*args, **kwargs)
            raise sqlite3.OperationalError("falha simulada para reproduzir INC-001")
        return original(*args, **kwargs)

    cell.cell_contents = com_falha
    return cell, original


@pytest.fixture
def falha_em_garantir_checklist_os(app):
    """Usada pelas rotas 1 e 2 — ambas chamam _garantir_checklist_os antes do
    commit próprio da rota."""
    cell, original = _instalar_falha_unica(app, "api.obter_checklist_os", "_garantir_checklist_os")
    try:
        yield
    finally:
        cell.cell_contents = original


@pytest.fixture
def falha_em_buscar_checklist_por_token(app):
    """Usada pelas rotas 3 e 4 — ambas chamam _buscar_checklist_por_token."""
    cell, original = _instalar_falha_unica(app, "api.obter_checklist_publico", "_buscar_checklist_por_token")
    try:
        yield
    finally:
        cell.cell_contents = original


def _login_nao_trava(client, usuario_admin):
    """Prova de que a conexão da rota de checklist foi de fato fechada: um login
    imediatamente seguinte (escrita em login_attempts, tabela não relacionada)
    não espera o busy_timeout (30s) antes de responder."""
    inicio = time.monotonic()
    resp = client.post(
        "/api/auth/login",
        json={"usuario": usuario_admin["usuario"], "senha": SENHA_PADRAO},
    )
    duracao = time.monotonic() - inicio
    assert resp.status_code == 200
    assert duracao < 3


class TestObterChecklistOs:
    """GET /api/ordens/<id>/checklist — requer login."""

    def test_contrato_http_inalterado(self, client, login_como, usuario_admin, criar_os):
        login_como(client, usuario_admin)
        os_id = criar_os()

        resp = client.get(f"/api/ordens/{os_id}/checklist")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["ok"] is True
        assert payload["checklist"]["os_id"] == os_id
        assert payload["ordem"]["id"] == os_id

        resp_inexistente = client.get("/api/ordens/999999999/checklist")
        assert resp_inexistente.status_code == 404
        assert resp_inexistente.get_json() == {"ok": False, "erro": "OS não encontrada."}

    def test_excecao_fecha_conexao_login_seguinte_nao_trava(
        self, client, login_como, usuario_admin, criar_os, falha_em_garantir_checklist_os
    ):
        login_como(client, usuario_admin)
        os_id = criar_os()

        client.get(f"/api/ordens/{os_id}/checklist")
        _login_nao_trava(client, usuario_admin)


class TestGerarTokenChecklistOs:
    """POST /api/ordens/<id>/checklist/token — requer login."""

    def test_contrato_http_inalterado(self, client, login_como, usuario_admin, criar_os):
        login_como(client, usuario_admin)
        os_id = criar_os()

        resp = client.post(f"/api/ordens/{os_id}/checklist/token")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["ok"] is True
        assert payload["checklist"]["access_token"]
        assert payload["ordem"]["id"] == os_id

        resp_inexistente = client.post("/api/ordens/999999999/checklist/token")
        assert resp_inexistente.status_code == 404
        assert resp_inexistente.get_json() == {"ok": False, "erro": "OS não encontrada."}

    def test_excecao_fecha_conexao_login_seguinte_nao_trava(
        self, client, login_como, usuario_admin, criar_os, falha_em_garantir_checklist_os
    ):
        login_como(client, usuario_admin)
        os_id = criar_os()

        client.post(f"/api/ordens/{os_id}/checklist/token")
        _login_nao_trava(client, usuario_admin)


class TestObterChecklistPublico:
    """GET /api/checklist/<token> — pública, sem login."""

    def test_contrato_http_inalterado(self, client, login_como, usuario_admin, criar_os):
        login_como(client, usuario_admin)
        os_id = criar_os()
        token = client.post(f"/api/ordens/{os_id}/checklist/token").get_json()["checklist"]["access_token"]

        resp = client.get(f"/api/checklist/{token}")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["ok"] is True
        assert payload["checklist"]["access_token"] == token
        assert payload["ordem"]["id"] == os_id

        resp_invalido = client.get("/api/checklist/token-inexistente")
        assert resp_invalido.status_code == 404
        assert resp_invalido.get_json() == {"ok": False, "erro": "Checklist não encontrado."}

    def test_excecao_fecha_conexao_login_seguinte_nao_trava(
        self, client, login_como, usuario_admin, criar_os, falha_em_buscar_checklist_por_token
    ):
        login_como(client, usuario_admin)
        os_id = criar_os()
        token = client.post(f"/api/ordens/{os_id}/checklist/token").get_json()["checklist"]["access_token"]

        client.get(f"/api/checklist/{token}")
        _login_nao_trava(client, usuario_admin)


class TestSalvarChecklistPublico:
    """POST /api/checklist/<token> — pública, sem login. Maior risco (escreve
    dado enviado por cliente final)."""

    def test_contrato_http_inalterado(self, client, login_como, usuario_admin, criar_os):
        login_como(client, usuario_admin)
        os_id = criar_os()
        token = client.post(f"/api/ordens/{os_id}/checklist/token").get_json()["checklist"]["access_token"]

        resp = client.post(
            f"/api/checklist/{token}",
            json={"testes": {"touch": {"status": "ok"}}, "executado_por": "Cliente Teste"},
        )
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["ok"] is True
        assert payload["checklist"]["status_touch"] == "aprovado"
        assert payload["checklist"]["executado_por"] == "Cliente Teste"

        resp_invalido = client.post("/api/checklist/token-inexistente", json={"testes": {}})
        assert resp_invalido.status_code == 404
        assert resp_invalido.get_json() == {"ok": False, "erro": "Checklist não encontrado."}

    def test_excecao_fecha_conexao_login_seguinte_nao_trava(
        self, client, login_como, usuario_admin, criar_os, falha_em_buscar_checklist_por_token
    ):
        login_como(client, usuario_admin)
        os_id = criar_os()
        token = client.post(f"/api/ordens/{os_id}/checklist/token").get_json()["checklist"]["access_token"]

        client.post(f"/api/checklist/{token}", json={"testes": {"touch": {"status": "ok"}}})
        _login_nao_trava(client, usuario_admin)
