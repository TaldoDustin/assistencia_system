"""
Testes dos headers de seguranca aplicados em todas as respostas (Sprint
Seguranca 1.0, 2026-07-25) -- ver docs/security/SECURITY_AUDIT_2026-07.md
itens 10 (CSP ausente) e 11 (sem protecao contra clickjacking).
"""


class TestSecurityHeaders:
    def test_resposta_da_api_inclui_csp(self, client):
        resp = client.get("/api/constantes")

        csp = resp.headers.get("Content-Security-Policy")
        assert csp is not None
        assert "default-src 'self'" in csp
        assert "frame-ancestors 'none'" in csp

    def test_resposta_da_api_inclui_x_content_type_options(self, client):
        resp = client.get("/api/constantes")

        assert resp.headers.get("X-Content-Type-Options") == "nosniff"

    def test_resposta_da_api_inclui_x_frame_options(self, client):
        resp = client.get("/api/constantes")

        assert resp.headers.get("X-Frame-Options") == "DENY"

    def test_resposta_da_api_inclui_referrer_policy(self, client):
        resp = client.get("/api/constantes")

        assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_resposta_de_erro_tambem_inclui_headers(self, client):
        resp = client.get("/api/ordens/abc")

        assert resp.status_code == 404
        assert resp.headers.get("Content-Security-Policy") is not None
        assert resp.headers.get("X-Frame-Options") == "DENY"
