"""
Testes de /health e /ready (Sprint Observabilidade, 2026-07-25).

Escopo: liveness (/health) e readiness (/ready) -- ambos sem autenticacao,
usados por probes de infraestrutura.
"""

import app as _app


class TestHealth:
    def test_health_retorna_200_sem_sessao(self, client):
        resp = client.get("/health")

        assert resp.status_code == 200
        assert resp.get_json() == {"status": "ok"}

    def test_health_nao_exige_login(self, client):
        # Nenhum login_como() chamado -- confirma que o before_request de
        # autenticacao nao bloqueia este endpoint.
        resp = client.get("/health")
        assert resp.status_code == 200


class TestReady:
    def test_ready_retorna_200_com_banco_acessivel(self, client):
        resp = client.get("/ready")

        assert resp.status_code == 200
        assert resp.get_json() == {"status": "ok"}

    def test_ready_nao_exige_login(self, client):
        resp = client.get("/ready")
        assert resp.status_code == 200

    def test_ready_retorna_503_quando_banco_falha(self, client, monkeypatch):
        def _conectar_com_falha():
            raise RuntimeError("banco indisponivel")

        monkeypatch.setattr(_app, "conectar", _conectar_com_falha)

        resp = client.get("/ready")

        assert resp.status_code == 503
        assert resp.get_json() == {"status": "unavailable"}
