"""
Testes de autenticacao, sessao e usuarios autenticados (Sprint 2.2).

Escopo desta sprint: login, logout, sessao e controle de acesso por perfil.
Nao cobre estoque, ordens de servico ou lista de compras.
"""

import uuid

import app as _app

# Fixtures de usuario (client, usuario_admin, usuario_tecnico, usuario_inativo, ...)
# vivem em tests/conftest.py — compartilhadas por toda a suite (Sprint 2.3).

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

    def test_login_nao_expoe_mais_limite_desconto_livre(self, client, usuario_vendedor):
        """BR-054 (revisão de 2026-07-29): `limite_desconto_livre` deixou de
        ser lido/exposto por qualquer fluxo -- mesmo com um valor legado
        gravado na coluna deprecada, o login não o retorna mais."""
        conn = _app.conectar()
        try:
            conn.execute(
                "UPDATE usuarios SET limite_desconto_livre = ? WHERE id = ?",
                (300.0, usuario_vendedor["id"]),
            )
            conn.commit()
        finally:
            conn.close()

        resp = client.post(
            "/api/auth/login",
            json={"usuario": usuario_vendedor["usuario"], "senha": usuario_vendedor["senha"]},
        )

        assert resp.status_code == 200
        assert "limite_desconto_livre" not in resp.get_json()["usuario"]


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
        # BR-054 (revisão de 2026-07-29): campo deprecado, não exposto mais.
        assert "limite_desconto_livre" not in body["usuario"]


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
#
# TestControleDeAcessoPorPerfil (POST /usuarios/novo legado) foi removida:
# a rota em si foi removida por vulnerabilidade de CSRF (sem protecao alguma,
# permitia criar usuario admin via form cross-site) — ver KNOWN_ISSUES.md.
# Cobertura equivalente para /api/usuarios em test_users.py.
