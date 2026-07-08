"""
Testes de sessao (Sprint 2.3): expiracao, cookie invalido, logout multiplo,
acesso apos logout e acesso sem sessao.

Sessao e via Flask session (cookie assinado com FLASK_SECRET_KEY, ver
ARCHITECTURE.md secao 4). Nao ha expiracao configurada explicitamente em
app.py (PERMANENT_SESSION_LIFETIME usa o default do Flask, 31 dias) — o
teste de sessao expirada forja um cookie assinado com timestamp antigo para
exercitar esse caminho sem depender de tempo real decorrido.
"""

import time
from datetime import timedelta

from itsdangerous import URLSafeTimedSerializer

import app as _app


def _forjar_cookie_sessao_expirada(app, dados_sessao, dias_no_passado=40):
    """
    Assina os dados de sessao com um timestamp no passado, usando o mesmo
    serializer/segredo que o Flask usaria — mas sobrescrevendo o timestamp
    embutido na assinatura para simular uma sessao ja expirada segundo
    PERMANENT_SESSION_LIFETIME (default: 31 dias).
    """
    iface = app.session_interface
    base = iface.get_signing_serializer(app)

    class SignerComTimestampAntigo(base.signer):
        def get_timestamp(self):
            return int(time.time()) - int(timedelta(days=dias_no_passado).total_seconds())

    serializer = URLSafeTimedSerializer(
        app.secret_key,
        salt=iface.salt,
        serializer=iface.serializer,
        signer_kwargs={"key_derivation": iface.key_derivation, "digest_method": iface.digest_method},
    )
    serializer.signer = SignerComTimestampAntigo
    return serializer.dumps(dict(dados_sessao))


def _nome_cookie_sessao(app):
    return app.config.get("SESSION_COOKIE_NAME", "session")


# ============================================================================
# Acesso sem sessao
# ============================================================================


class TestAcessoSemSessao:
    def test_api_me_sem_sessao_retorna_401(self, client):
        resp = client.get("/api/auth/me")

        assert resp.status_code == 401
        assert resp.get_json()["ok"] is False

    def test_cookie_jar_vazio_nao_contem_dados_de_sessao(self, client):
        client.get("/api/auth/me")

        with client.session_transaction() as sess:
            assert "usuario_id" not in sess


# ============================================================================
# Acesso apos logout
# ============================================================================


class TestAcessoAposLogout:
    def test_endpoint_autenticado_fica_inacessivel_apos_logout(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        assert client.get("/api/auth/me").status_code == 200

        client.post("/api/auth/logout")

        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_endpoint_admin_only_fica_inacessivel_apos_logout(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        assert client.get("/api/usuarios").status_code == 200

        client.post("/api/auth/logout")

        resp = client.get("/api/usuarios")
        assert resp.status_code == 403


# ============================================================================
# Logout multiplo
# ============================================================================


class TestLogoutMultiplo:
    def test_logout_chamado_duas_vezes_seguidas_nao_falha(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)

        primeiro = client.post("/api/auth/logout")
        segundo = client.post("/api/auth/logout")

        assert primeiro.status_code == 200
        assert primeiro.get_json()["ok"] is True
        assert segundo.status_code == 200
        assert segundo.get_json()["ok"] is True

    def test_logout_multiplo_mantem_sessao_encerrada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)

        client.post("/api/auth/logout")
        client.post("/api/auth/logout")

        assert client.get("/api/auth/me").status_code == 401


# ============================================================================
# Cookie invalido / adulterado
# ============================================================================


class TestCookieInvalido:
    def test_cookie_com_assinatura_adulterada_e_tratado_como_anonimo(self, client, login_como, usuario_tecnico, app):
        login_como(client, usuario_tecnico)
        assert client.get("/api/auth/me").status_code == 200

        nome_cookie = _nome_cookie_sessao(app)
        cookie_valido = client.get_cookie(nome_cookie, domain="localhost").value

        # Adultera um caractere dentro do payload (nao no ultimo caractere da
        # assinatura base64url, onde bits de padding podem manter o byte
        # decodificado igual e tornar o teste instavel).
        posicao = len(cookie_valido) // 3
        substituto = "a" if cookie_valido[posicao] != "a" else "b"
        cookie_adulterado = cookie_valido[:posicao] + substituto + cookie_valido[posicao + 1 :]

        client2 = _app.app.test_client()
        client2.set_cookie(key=nome_cookie, value=cookie_adulterado, domain="localhost")

        resp = client2.get("/api/auth/me")

        assert resp.status_code == 401
        assert resp.get_json()["ok"] is False

    def test_cookie_arbitrario_nao_assinado_e_tratado_como_anonimo(self, client, app):
        nome_cookie = _nome_cookie_sessao(app)

        client2 = _app.app.test_client()
        client2.set_cookie(key=nome_cookie, value="valor-qualquer-nao-assinado", domain="localhost")

        resp = client2.get("/api/auth/me")

        assert resp.status_code == 401


# ============================================================================
# Sessao expirada
# ============================================================================


class TestSessaoExpirada:
    def test_cookie_com_timestamp_expirado_e_tratado_como_anonimo(self, app, usuario_tecnico):
        cookie_expirado = _forjar_cookie_sessao_expirada(
            app,
            {
                "usuario_id": usuario_tecnico["id"],
                "usuario_nome": usuario_tecnico["nome"],
                "usuario_perfil": "tecnico",
                "_permanent": True,
            },
        )

        client = _app.app.test_client()
        client.set_cookie(key=_nome_cookie_sessao(app), value=cookie_expirado, domain="localhost")

        resp = client.get("/api/auth/me")

        assert resp.status_code == 401
        assert resp.get_json()["ok"] is False

    def test_cookie_com_timestamp_recente_ainda_e_valido(self, app, usuario_tecnico):
        """Controle: o mesmo forjamento, com um timestamp recente, deve autenticar normalmente."""
        cookie_recente = _forjar_cookie_sessao_expirada(
            app,
            {
                "usuario_id": usuario_tecnico["id"],
                "usuario_nome": usuario_tecnico["nome"],
                "usuario_perfil": "tecnico",
                "_permanent": True,
            },
            dias_no_passado=0,
        )

        client = _app.app.test_client()
        client.set_cookie(key=_nome_cookie_sessao(app), value=cookie_recente, domain="localhost")

        resp = client.get("/api/auth/me")

        assert resp.status_code == 200
        assert resp.get_json()["usuario"]["id"] == usuario_tecnico["id"]
