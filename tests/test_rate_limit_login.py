"""
Testes de rate limiting em login (Sprint 3 — Unidade 1).

Escopo: POST /api/auth/login (rota real usada pelo frontend) e POST /login
(rota legada), ambas usando o contador em `login_attempts`
(`fluxoly_rate_limit.py`) em vez de armazenamento em memória — ver
docstring do módulo para o motivo (Gunicorn roda com --workers 2).

Isolamento: `tests/conftest.py` limpa `login_attempts` antes de cada teste
(fixture autouse `_limpar_login_attempts`), já que o cliente de teste do
Flask sempre usa o mesmo IP.
"""

import app as _app


def _tentar_login(client, usuario="inexistente", senha="errada"):
    return client.post("/api/auth/login", json={"usuario": usuario, "senha": senha})


class TestRateLimitLoginApi:
    def test_ate_5_tentativas_nao_bloqueia(self, client):
        for _ in range(5):
            resp = _tentar_login(client)
            assert resp.status_code == 401

    def test_sexta_tentativa_em_menos_de_um_minuto_e_bloqueada(self, client):
        for _ in range(5):
            _tentar_login(client)

        resp = _tentar_login(client)

        assert resp.status_code == 429
        assert "Muitas tentativas" in resp.get_json()["erro"]

    def test_login_bem_sucedido_conta_para_o_limite(self, client, login_como, usuario_tecnico):
        for _ in range(4):
            _tentar_login(client)

        resp = login_como(client, usuario_tecnico)

        assert resp.status_code == 200

        bloqueado = _tentar_login(client)
        assert bloqueado.status_code == 429

    def test_tentativa_apos_a_janela_expirar_e_permitida(self, client):
        for _ in range(5):
            _tentar_login(client)
        assert _tentar_login(client).status_code == 429

        # Simula o tempo passando: empurra os registros existentes para fora da janela de 1 minuto
        conn = _app.conectar()
        try:
            conn.execute("UPDATE login_attempts SET criado_em = datetime('now', '-2 minutes')")
            conn.commit()
        finally:
            conn.close()

        resp = _tentar_login(client)
        assert resp.status_code == 401

    def test_campos_ausentes_tambem_contam_para_o_limite(self, client):
        for _ in range(5):
            resp = client.post("/api/auth/login", json={})
            assert resp.status_code == 400

        resp = _tentar_login(client)
        assert resp.status_code == 429

    def test_fly_client_ip_diferentes_nao_se_bloqueiam_entre_si(self, client):
        for _ in range(5):
            client.post(
                "/api/auth/login",
                json={"usuario": "inexistente", "senha": "errada"},
                headers={"Fly-Client-IP": "1.1.1.1"},
            )

        bloqueado = client.post(
            "/api/auth/login",
            json={"usuario": "inexistente", "senha": "errada"},
            headers={"Fly-Client-IP": "1.1.1.1"},
        )
        assert bloqueado.status_code == 429

        ainda_livre = client.post(
            "/api/auth/login",
            json={"usuario": "inexistente", "senha": "errada"},
            headers={"Fly-Client-IP": "2.2.2.2"},
        )
        assert ainda_livre.status_code == 401


class TestRateLimitLoginLegado:
    def test_sexta_tentativa_e_bloqueada_e_redireciona_com_erro(self, client):
        for _ in range(5):
            client.post("/login", data={"usuario": "inexistente", "senha": "errada"})

        resp = client.post("/login", data={"usuario": "inexistente", "senha": "errada"})

        assert resp.status_code == 302
        assert "erro=" in resp.headers["Location"]
