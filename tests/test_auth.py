"""
Testes de autenticacao, sessao e usuarios autenticados (Sprint 2.2).

Escopo desta sprint: login, logout, sessao e controle de acesso por perfil.
Nao cobre estoque, ordens de servico ou lista de compras.
"""

import uuid

import pytest
from werkzeug.security import generate_password_hash

import app as _app

SENHA_PADRAO = "senha_teste_123"


@pytest.fixture
def client(app):
    """Cliente HTTP isolado por teste — nao reutiliza sessao de outros testes."""
    return app.test_client()


def _criar_usuario(nome, perfil="tecnico", ativo=1):
    login = f"user_{uuid.uuid4().hex[:10]}"
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, usuario, senha_hash, perfil, ativo) VALUES (?, ?, ?, ?, ?)",
            (nome, login, generate_password_hash(SENHA_PADRAO), perfil, ativo),
        )
        conn.commit()
        user_id = cursor.lastrowid
    finally:
        conn.close()
    return {"id": user_id, "nome": nome, "usuario": login, "senha": SENHA_PADRAO}


def _remover_usuario(user_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def usuario_tecnico():
    dados = _criar_usuario("Tecnico Teste", perfil="tecnico", ativo=1)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def usuario_admin():
    dados = _criar_usuario("Admin Teste", perfil="admin", ativo=1)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def usuario_inativo():
    dados = _criar_usuario("Usuario Inativo", perfil="tecnico", ativo=0)
    yield dados
    _remover_usuario(dados["id"])


# ============================================================================
# API JSON — /api/auth/login, /api/auth/logout, /api/auth/me
# ============================================================================


class TestApiAuthLogin:
    def test_login_com_credenciais_validas_retorna_dados_do_usuario(self, client, usuario_tecnico):
        resp = client.post(
            "/api/auth/login",
            json={"usuario": usuario_tecnico["usuario"], "senha": usuario_tecnico["senha"]},
        )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ok"] is True
        assert body["usuario"]["id"] == usuario_tecnico["id"]
        assert body["usuario"]["perfil"] == "tecnico"

    def test_login_com_senha_incorreta_retorna_401(self, client, usuario_tecnico):
        resp = client.post(
            "/api/auth/login",
            json={"usuario": usuario_tecnico["usuario"], "senha": "senha_errada"},
        )

        assert resp.status_code == 401
        body = resp.get_json()
        assert body["ok"] is False

    def test_login_com_usuario_inexistente_retorna_401(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"usuario": f"fantasma_{uuid.uuid4().hex[:8]}", "senha": "qualquer"},
        )

        assert resp.status_code == 401

    def test_login_sem_usuario_ou_senha_retorna_400(self, client):
        resp = client.post("/api/auth/login", json={"usuario": "", "senha": ""})

        assert resp.status_code == 400
        body = resp.get_json()
        assert body["ok"] is False

    def test_login_de_usuario_inativo_retorna_401(self, client, usuario_inativo):
        resp = client.post(
            "/api/auth/login",
            json={"usuario": usuario_inativo["usuario"], "senha": usuario_inativo["senha"]},
        )

        assert resp.status_code == 401

    def test_login_bem_sucedido_nao_expoe_hash_de_senha(self, client, usuario_tecnico):
        resp = client.post(
            "/api/auth/login",
            json={"usuario": usuario_tecnico["usuario"], "senha": usuario_tecnico["senha"]},
        )

        body = resp.get_json()
        assert "senha_hash" not in body["usuario"]
        assert "senha" not in body["usuario"]


class TestApiAuthMe:
    def test_me_sem_sessao_retorna_401(self, client):
        resp = client.get("/api/auth/me")

        assert resp.status_code == 401
        assert resp.get_json()["ok"] is False

    def test_me_com_sessao_ativa_retorna_usuario_logado(self, client, usuario_tecnico):
        client.post(
            "/api/auth/login",
            json={"usuario": usuario_tecnico["usuario"], "senha": usuario_tecnico["senha"]},
        )

        resp = client.get("/api/auth/me")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["usuario"]["id"] == usuario_tecnico["id"]
        assert body["usuario"]["nome"] == usuario_tecnico["nome"]
        assert body["usuario"]["perfil"] == "tecnico"


class TestApiAuthLogout:
    def test_logout_encerra_sessao(self, client, usuario_tecnico):
        client.post(
            "/api/auth/login",
            json={"usuario": usuario_tecnico["usuario"], "senha": usuario_tecnico["senha"]},
        )
        assert client.get("/api/auth/me").status_code == 200

        resp = client.post("/api/auth/logout")

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        assert client.get("/api/auth/me").status_code == 401

    def test_logout_sem_sessao_ativa_nao_falha(self, client):
        resp = client.post("/api/auth/logout")

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True


# ============================================================================
# Rotas legadas (formulario) — /login, /logout
# ============================================================================


class TestLegacyLogin:
    def test_get_login_redireciona_para_spa(self, client):
        resp = client.get("/login")

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app/login"

    def test_post_login_com_credenciais_validas_cria_sessao(self, client, usuario_tecnico):
        resp = client.post(
            "/login",
            data={"usuario": usuario_tecnico["usuario"], "senha": usuario_tecnico["senha"]},
        )

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app"
        with client.session_transaction() as sess:
            assert sess["usuario_id"] == usuario_tecnico["id"]
            assert sess["usuario_perfil"] == "tecnico"

    def test_post_login_com_credenciais_invalidas_nao_cria_sessao(self, client, usuario_tecnico):
        resp = client.post(
            "/login",
            data={"usuario": usuario_tecnico["usuario"], "senha": "senha_errada"},
        )

        assert resp.status_code == 302
        assert resp.headers["Location"].startswith("/app/login")
        with client.session_transaction() as sess:
            assert "usuario_id" not in sess

    def test_get_login_ja_autenticado_ainda_redireciona_para_spa(self, client, usuario_tecnico):
        """
        O before_request (verificar_autenticacao em app.py) intercepta qualquer GET/HEAD
        para "/login" e redireciona para "/app/login" antes do view rodar — o desvio
        "ja logado -> /app" dentro de auth_views.login() e inalcancavel via HTTP para
        requisicoes GET. A guarda real de "ja autenticado" acontece no SPA (AuthContext).
        """
        client.post(
            "/login",
            data={"usuario": usuario_tecnico["usuario"], "senha": usuario_tecnico["senha"]},
        )

        resp = client.get("/login")

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app/login"


class TestLegacyLogout:
    def test_logout_limpa_sessao(self, client, usuario_tecnico):
        client.post(
            "/login",
            data={"usuario": usuario_tecnico["usuario"], "senha": usuario_tecnico["senha"]},
        )

        resp = client.get("/logout")

        assert resp.status_code == 302
        with client.session_transaction() as sess:
            assert "usuario_id" not in sess


# ============================================================================
# Controle de acesso por perfil — usuarios autenticados
# ============================================================================


class TestControleDeAcessoPorPerfil:
    """
    POST /usuarios/novo exige perfil admin (ROUTE_PERMISSIONS em app.py).
    Ao contrario das rotas GET legadas (interceptadas por LEGACY_REACT_REDIRECTS antes
    da checagem de sessao), POST nao entra nesse redirecionamento — exercita o
    before_request de autenticacao/autorizacao de fato.
    """

    def test_sem_sessao_redireciona_para_login(self, client):
        resp = client.post(
            "/usuarios/novo",
            data={"nome": "Novo", "usuario": f"novo_{uuid.uuid4().hex[:8]}", "senha": "x", "perfil": "tecnico"},
        )

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app/login"

    def test_usuario_nao_admin_recebe_acesso_negado(self, client, usuario_tecnico):
        client.post(
            "/login",
            data={"usuario": usuario_tecnico["usuario"], "senha": usuario_tecnico["senha"]},
        )
        login_novo = f"novo_{uuid.uuid4().hex[:8]}"

        resp = client.post(
            "/usuarios/novo",
            data={"nome": "Novo", "usuario": login_novo, "senha": "x", "perfil": "tecnico"},
        )

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app"
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT id FROM usuarios WHERE usuario = ?", (login_novo,)).fetchone()
        finally:
            conn.close()
        assert row is None

    def test_usuario_admin_pode_criar_novo_usuario(self, client, usuario_admin):
        client.post(
            "/login",
            data={"usuario": usuario_admin["usuario"], "senha": usuario_admin["senha"]},
        )
        login_novo = f"novo_{uuid.uuid4().hex[:8]}"

        resp = client.post(
            "/usuarios/novo",
            data={"nome": "Novo", "usuario": login_novo, "senha": "x", "perfil": "tecnico"},
        )

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/usuarios"
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT id FROM usuarios WHERE usuario = ?", (login_novo,)).fetchone()
            assert row is not None
        finally:
            conn.execute("DELETE FROM usuarios WHERE usuario = ?", (login_novo,))
            conn.commit()
            conn.close()
