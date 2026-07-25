"""
Testes de correlation ID por request (Sprint Observabilidade, 2026-07-25).

Escopo: header X-Request-Id ecoado/gerado em toda resposta -- ver
app.py::_iniciar_request_id / _logar_acesso.
"""


class TestRequestId:
    def test_resposta_sempre_tem_x_request_id(self, client):
        resp = client.get("/api/constantes")

        assert resp.headers.get("X-Request-Id")

    def test_request_id_valido_enviado_pelo_cliente_e_ecoado(self, client):
        resp = client.get("/api/constantes", headers={"X-Request-Id": "meu-id-123"})

        assert resp.headers.get("X-Request-Id") == "meu-id-123"

    def test_request_id_invalido_e_substituido(self, client):
        # Werkzeug ja rejeita valor de header com quebra de linha literal --
        # o caso relevante de validar aqui e formato fora do esperado
        # (alfanumerico + hifen), que um cliente HTTP legitimo consegue
        # enviar sem violar a spec de HTTP.
        malicioso = "<script>alert(1)</script>"

        resp = client.get("/api/constantes", headers={"X-Request-Id": malicioso})

        recebido = resp.headers.get("X-Request-Id")
        assert recebido != malicioso
        assert "<" not in recebido

    def test_request_id_muito_longo_e_substituido(self, client):
        longo_demais = "a" * 200

        resp = client.get("/api/constantes", headers={"X-Request-Id": longo_demais})

        assert resp.headers.get("X-Request-Id") != longo_demais

    def test_request_id_muda_entre_requests_sem_header(self, client):
        resp1 = client.get("/api/constantes")
        resp2 = client.get("/api/constantes")

        assert resp1.headers.get("X-Request-Id") != resp2.headers.get("X-Request-Id")
