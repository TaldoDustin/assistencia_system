"""
Testes de recuperação de senha via token gerado pelo admin (Sprint 3 — Unidade 4).

Escopo: POST /api/usuarios/<id>/reset-token (admin-only) e
POST /api/password-reset/<token> (pública). Mecanismo escolhido: link/token
gerado manualmente pelo admin — não self-service por e-mail (decisão
explícita, ver docs/product/PRODUCT_BACKLOG.md e o plano desta sprint).
"""

from datetime import datetime, timedelta

import app as _app


def _obter_token_db(usuario_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT id, token, expira_em, usado_em FROM password_reset_tokens "
            "WHERE usuario_id=? ORDER BY id DESC LIMIT 1",
            (usuario_id,),
        ).fetchone()
    finally:
        conn.close()


def _expirar_token(token):
    conn = _app.conectar()
    try:
        conn.execute(
            "UPDATE password_reset_tokens SET expira_em=? WHERE token=?",
            ((datetime.now() - timedelta(hours=1)).isoformat(), token),
        )
        conn.commit()
    finally:
        conn.close()


class TestGerarTokenReset:
    def test_sem_autenticacao_retorna_403(self, client, usuario_tecnico):
        resp = client.post(f"/api/usuarios/{usuario_tecnico['id']}/reset-token")
        assert resp.status_code == 403

    def test_nao_admin_nao_pode_gerar_token(self, client, login_como, usuario_tecnico, usuario_vendedor):
        login_como(client, usuario_tecnico)
        resp = client.post(f"/api/usuarios/{usuario_vendedor['id']}/reset-token")
        assert resp.status_code == 403

    def test_usuario_inexistente_retorna_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post("/api/usuarios/999999/reset-token")
        assert resp.status_code == 404

    def test_admin_gera_token_com_sucesso(self, client, login_como, usuario_admin, usuario_tecnico):
        login_como(client, usuario_admin)

        resp = client.post(f"/api/usuarios/{usuario_tecnico['id']}/reset-token")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["token"]
        assert body["expira_em"]

        linha = _obter_token_db(usuario_tecnico["id"])
        assert linha[1] == body["token"]
        assert linha[3] is None  # usado_em

    def test_gerar_novo_token_invalida_o_anterior(self, client, login_como, usuario_admin, usuario_tecnico):
        login_como(client, usuario_admin)

        primeiro = client.post(f"/api/usuarios/{usuario_tecnico['id']}/reset-token").get_json()["token"]
        client.post(f"/api/usuarios/{usuario_tecnico['id']}/reset-token")

        resp = client.post(f"/api/password-reset/{primeiro}", json={"senha_nova": "NovaSenha123"})

        assert resp.status_code == 410
        assert "já foi usado" in resp.get_json()["erro"]


class TestConsumirTokenReset:
    def test_token_inexistente_retorna_404(self, client):
        resp = client.post("/api/password-reset/token-que-nao-existe", json={"senha_nova": "NovaSenha123"})
        assert resp.status_code == 404

    def test_sem_senha_nova_retorna_400(self, client, login_como, usuario_admin, usuario_tecnico):
        login_como(client, usuario_admin)
        token = client.post(f"/api/usuarios/{usuario_tecnico['id']}/reset-token").get_json()["token"]

        resp = client.post(f"/api/password-reset/{token}", json={})

        assert resp.status_code == 400

    def test_token_expirado_e_rejeitado(self, client, login_como, usuario_admin, usuario_tecnico):
        login_como(client, usuario_admin)
        token = client.post(f"/api/usuarios/{usuario_tecnico['id']}/reset-token").get_json()["token"]
        _expirar_token(token)

        resp = client.post(f"/api/password-reset/{token}", json={"senha_nova": "NovaSenha123"})

        assert resp.status_code == 410
        assert "expirou" in resp.get_json()["erro"]

    def test_token_valido_troca_senha_e_permite_login(self, client, login_como, usuario_admin, usuario_tecnico):
        login_como(client, usuario_admin)
        token = client.post(f"/api/usuarios/{usuario_tecnico['id']}/reset-token").get_json()["token"]

        resp = client.post(f"/api/password-reset/{token}", json={"senha_nova": "NovaSenhaForte456"})
        assert resp.status_code == 200

        client.get("/logout")
        login_resp = client.post(
            "/api/auth/login",
            json={"usuario": usuario_tecnico["usuario"], "senha": "NovaSenhaForte456"},
        )
        assert login_resp.status_code == 200

    def test_token_ja_usado_e_rejeitado_na_segunda_tentativa(
        self, client, login_como, usuario_admin, usuario_tecnico
    ):
        login_como(client, usuario_admin)
        token = client.post(f"/api/usuarios/{usuario_tecnico['id']}/reset-token").get_json()["token"]

        primeira = client.post(f"/api/password-reset/{token}", json={"senha_nova": "Senha111"})
        assert primeira.status_code == 200

        segunda = client.post(f"/api/password-reset/{token}", json={"senha_nova": "Senha222"})
        assert segunda.status_code == 410
