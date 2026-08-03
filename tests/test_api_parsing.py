"""
Testes de regressao para o parsing de entrada nas rotas de fluxoly_blueprints_api.py
(Sprint 2.6 — fix: substituir int()/float() nao tratados por parse_int/parse_float).

Antes da correcao, um valor nao numerico nesses campos derrubava a rota com
500 nao tratado, fora do contrato JSON {"ok": false, "erro": ...} da API.
Agora retorna 400 com mensagem clara.
"""


def test_shopping_list_retorna_400_quando_page_invalido(auth_client):
    resp = auth_client.get("/api/shopping-list?page=abc")
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_shopping_list_aceita_page_valido(auth_client):
    resp = auth_client.get("/api/shopping-list?page=1&per_page=5")
    assert resp.status_code == 200


def test_reposicao_sugerida_retorna_400_quando_dias_invalido(auth_client):
    resp = auth_client.get("/api/estoque/reposicao-sugerida?dias=abc")
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_reposicao_sugerida_aceita_dias_valido(auth_client):
    resp = auth_client.get("/api/estoque/reposicao-sugerida?dias=30")
    assert resp.status_code == 200


def test_criar_ordem_retorna_400_quando_valor_cobrado_invalido(auth_client):
    resp = auth_client.post(
        "/api/ordens",
        json={
            "tipo": "Assistencia",
            "cliente": "Cliente Teste",
            "modelo": "iPhone 11",
            "tecnico": "Tec",
            "valor_cobrado": "abc",
        },
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_atualizar_ordem_retorna_400_quando_valor_invalido(auth_client):
    resp = auth_client.put(
        "/api/ordens/999999",
        json={
            "tipo": "Assistencia",
            "cliente": "Cliente Teste",
            "modelo": "iPhone 11",
            "tecnico": "Tec",
            "status": "Em andamento",
            "valor_descontado": "abc",
        },
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_criar_estoque_retorna_400_quando_valor_invalido(auth_client):
    resp = auth_client.post(
        "/api/estoque",
        json={"descricao": "Tela iPhone 11", "valor": "abc", "quantidade": 1},
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_criar_estoque_retorna_400_quando_quantidade_invalida(auth_client):
    resp = auth_client.post(
        "/api/estoque",
        json={"descricao": "Tela iPhone 11", "valor": 100, "quantidade": "abc"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_criar_estoque_aceita_valores_validos(auth_client):
    resp = auth_client.post(
        "/api/estoque",
        json={"descricao": "Tela iPhone 11 Teste", "valor": 150.5, "quantidade": 3},
    )
    assert resp.status_code == 201
    assert resp.get_json()["ok"] is True


def test_atualizar_estoque_retorna_400_quando_valor_invalido(auth_client):
    resp = auth_client.put(
        "/api/estoque/999999",
        json={"descricao": "Tela", "valor": "abc", "quantidade": 1},
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_criar_custo_retorna_400_quando_valor_invalido(auth_client):
    resp = auth_client.post("/api/custos", json={"descricao": "Aluguel", "valor": "abc"})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_atualizar_custo_retorna_400_quando_valor_invalido(auth_client):
    resp = auth_client.put("/api/custos/999999", json={"descricao": "Aluguel", "valor": "abc"})
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False


def test_salvar_preco_retorna_400_quando_valor_invalido(auth_client):
    resp = auth_client.post(
        "/api/precos",
        json={"tabela": "clientes", "servico": "TELA", "modelo": "iPhone 11", "valor": "abc"},
    )
    assert resp.status_code == 400
    assert resp.get_json()["ok"] is False
