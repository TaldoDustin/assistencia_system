"""
Testes de fail-secure para o webhook MercadoPhone (POST /api/integracoes/mercadophone/os).

Antes desta correção, `autenticar_integracao_mercado_phone()` (app.py) tinha um
early-return quando `MERCADO_PHONE_WEBHOOK_TOKEN` estava vazio/nao configurado,
deixando o endpoint aberto sem autenticacao. Corrigido para negar por padrao
(fail secure) quando o token nao esta configurado, e para comparar o token em
tempo constante (hmac.compare_digest) em vez de `in`/`==`.
"""

import app as _app

PAYLOAD_VALIDO = {"codigo": "MP-TESTE-1", "cliente": "Cliente Teste", "aparelho": "iPhone 13"}


def test_webhook_rejeita_quando_token_nao_configurado(client, monkeypatch):
    monkeypatch.setattr(_app, "MERCADO_PHONE_WEBHOOK_TOKEN", "")

    resp = client.post("/api/integracoes/mercadophone/os", json=PAYLOAD_VALIDO)

    assert resp.status_code == 401


def test_webhook_rejeita_token_incorreto(client, monkeypatch):
    monkeypatch.setattr(_app, "MERCADO_PHONE_WEBHOOK_TOKEN", "token-correto-forte")

    resp = client.post(
        "/api/integracoes/mercadophone/os",
        json=PAYLOAD_VALIDO,
        headers={"X-Webhook-Token": "token-errado"},
    )

    assert resp.status_code == 401


def test_webhook_aceita_token_correto(client, monkeypatch):
    monkeypatch.setattr(_app, "MERCADO_PHONE_WEBHOOK_TOKEN", "token-correto-forte")

    resp = client.post(
        "/api/integracoes/mercadophone/os",
        json=PAYLOAD_VALIDO,
        headers={"X-Webhook-Token": "token-correto-forte"},
    )

    assert resp.status_code in (200, 201)
