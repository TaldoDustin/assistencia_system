"""
Testes de regressao para os call sites de parsing ja seguros que foram
deduplicados no commit refactor(api) da Sprint 2.6 (shopping-list e
config do MercadoPhone).
"""

import uuid


def _criar_item_shopping(client, os_id=0, produto_nome=None, quantidade=1):
    payload = {
        "os_id": os_id,
        "produto_nome": produto_nome or f"Peca Teste {uuid.uuid4().hex[:8]}",
        "quantidade_solicitada": quantidade,
    }
    return client.post("/api/shopping-list", json=payload)


def test_shopping_create_aceita_dados_validos(auth_client):
    resp = _criar_item_shopping(auth_client)
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_shopping_create_retorna_erro_quando_os_id_invalido(auth_client):
    resp = auth_client.post(
        "/api/shopping-list",
        json={"os_id": "abc", "produto_nome": "Peca X", "quantidade_solicitada": 1},
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_shopping_create_retorna_erro_quando_quantidade_invalida(auth_client):
    resp = auth_client.post(
        "/api/shopping-list",
        json={"os_id": 0, "produto_nome": "Peca Y", "quantidade_solicitada": "abc"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_shopping_update_aceita_quantidade_valida(auth_client):
    criado = _criar_item_shopping(auth_client).get_json()
    item_id = criado["id"]
    resp = auth_client.put(f"/api/shopping-list/{item_id}", json={"quantidade_solicitada": 5})
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_shopping_update_retorna_erro_quando_quantidade_invalida(auth_client):
    criado = _criar_item_shopping(auth_client).get_json()
    item_id = criado["id"]
    resp = auth_client.put(f"/api/shopping-list/{item_id}", json={"quantidade_solicitada": "abc"})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_salvar_config_mercadophone_aceita_intervalo_valido(auth_client):
    resp = auth_client.post("/api/integracoes/mercadophone/config", json={"sync_interval_seconds": 300})
    assert resp.status_code == 200
    assert resp.get_json()["ok"] is True


def test_salvar_config_mercadophone_retorna_erro_quando_intervalo_invalido(auth_client):
    resp = auth_client.post("/api/integracoes/mercadophone/config", json={"sync_interval_seconds": "abc"})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_salvar_config_mercadophone_retorna_erro_quando_timeout_invalido(auth_client):
    resp = auth_client.post("/api/integracoes/mercadophone/config", json={"sync_timeout_seconds": "abc"})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False
