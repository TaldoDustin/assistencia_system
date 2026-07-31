"""
Testes do dominio Produtos (Sprint Comercial 0.1).

Escopo: GET/POST/PUT/DELETE /api/produtos* -- catalogo comercial de venda
(iPhone/Apple Watch/AirPods/Acessorio), dominio novo e separado de Estoque
(pecas de reparo). Ver fluxoly_produtos_service.py para a regra de negocio
(categoria/condicao validadas contra lista fechada, sem coercao silenciosa;
margem calculada, nunca persistida) testada aqui via HTTP.
"""

import uuid

import app as _app


def _limpar_produto(produto_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade='produto' AND entidade_id=?", (produto_id,))
        conn.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_produto(client, **overrides):
    payload = {
        "categoria": "iPhone",
        "modelo": f"iPhone Teste {uuid.uuid4().hex[:8]}",
        "condicao": "Seminovo",
        "preco_custo": 2000.0,
        "preco_venda": 2999.0,
        "quantidade": 1,
    }
    payload.update(overrides)
    return client.post("/api/produtos", json=payload)


class TestListarProdutos:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/produtos")
        assert resp.status_code == 401

    def test_listagem_padrao_retorna_estrutura_paginada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/produtos")

        assert resp.status_code == 200
        body = resp.get_json()
        assert "items" in body and "total" in body and "page" in body and "per_page" in body

    def test_filtro_por_categoria(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        modelo = f"AirPods Teste {uuid.uuid4().hex[:8]}"
        criado = _criar_produto(client, categoria="AirPods", modelo=modelo, condicao="Novo")
        produto_id = criado.get_json()["id"]

        resp = client.get("/api/produtos?categoria=AirPods")

        modelos = [p["modelo"] for p in resp.get_json()["items"]]
        assert modelo in modelos
        _limpar_produto(produto_id)

    def test_busca_por_modelo_parcial(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        modelo = f"iPhone Busca Unica {uuid.uuid4().hex[:8]}"
        criado = _criar_produto(client, modelo=modelo)
        produto_id = criado.get_json()["id"]

        resp = client.get(f"/api/produtos?q={modelo[:12]}")

        modelos = [p["modelo"] for p in resp.get_json()["items"]]
        assert modelo in modelos
        _limpar_produto(produto_id)

    def test_page_nao_numerico_retorna_400(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/produtos?page=abc")
        assert resp.status_code == 400


class TestObterProduto:
    def test_produto_existente(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_produto(client, descricao="Descricao unica de teste")
        produto_id = criado.get_json()["id"]

        resp = client.get(f"/api/produtos/{produto_id}")

        assert resp.status_code == 200
        assert resp.get_json()["produto"]["descricao"] == "Descricao unica de teste"
        _limpar_produto(produto_id)

    def test_produto_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/produtos/999999")
        assert resp.status_code == 404


class TestCriarProduto:
    def test_sem_autenticacao_retorna_403(self, client):
        resp = client.post("/api/produtos", json={"categoria": "iPhone", "preco_venda": 100})
        assert resp.status_code == 403

    def test_nao_admin_nao_pode_criar(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = _criar_produto(client)
        assert resp.status_code == 403

    def test_categoria_ausente_e_rejeitada(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post("/api/produtos", json={"preco_venda": 100})
        assert resp.status_code == 400

    def test_categoria_invalida_e_rejeitada_sem_coercao(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = _criar_produto(client, categoria="Categoria Inventada")
        assert resp.status_code == 400

    def test_condicao_invalida_e_rejeitada_sem_coercao(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = _criar_produto(client, condicao="Condicao Inventada")
        assert resp.status_code == 400

    def test_preco_venda_ausente_e_rejeitado(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post("/api/produtos", json={"categoria": "iPhone"})
        assert resp.status_code == 400

    def test_preco_venda_zero_e_rejeitado(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = _criar_produto(client, preco_venda=0)
        assert resp.status_code == 400

    def test_preco_custo_negativo_e_rejeitado(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = _criar_produto(client, preco_custo=-1)
        assert resp.status_code == 400

    def test_criacao_valida_calcula_margem(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = _criar_produto(client, preco_custo=2000.0, preco_venda=2999.0)
        assert resp.status_code == 200
        produto_id = resp.get_json()["id"]

        detalhe = client.get(f"/api/produtos/{produto_id}").get_json()["produto"]
        assert detalhe["margem"] == 999.0
        _limpar_produto(produto_id)

    def test_criacao_sem_preco_custo_margem_e_none(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = _criar_produto(client, preco_custo=None)
        assert resp.status_code == 200
        produto_id = resp.get_json()["id"]

        detalhe = client.get(f"/api/produtos/{produto_id}").get_json()["produto"]
        assert detalhe["margem"] is None
        _limpar_produto(produto_id)

    def test_criacao_registra_auditoria(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = _criar_produto(client)
        produto_id = resp.get_json()["id"]

        conn = _app.conectar()
        try:
            logs = conn.execute(
                "SELECT acao FROM audit_log WHERE entidade='produto' AND entidade_id=?", (produto_id,)
            ).fetchall()
        finally:
            conn.close()

        assert [row[0] for row in logs] == ["create"]
        _limpar_produto(produto_id)


class TestAtualizarProduto:
    def test_sem_autenticacao_retorna_403(self, client):
        resp = client.put("/api/produtos/1", json={"categoria": "iPhone", "preco_venda": 100})
        assert resp.status_code == 403

    def test_produto_inexistente_retorna_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.put("/api/produtos/999999", json={"categoria": "iPhone", "preco_venda": 100})
        assert resp.status_code == 404

    def test_atualizacao_valida_persiste(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_produto(client)
        produto_id = criado.get_json()["id"]

        resp = client.put(
            f"/api/produtos/{produto_id}",
            json={"categoria": "iPhone", "modelo": "Modelo Atualizado", "preco_venda": 3500.0},
        )

        assert resp.status_code == 200
        detalhe = client.get(f"/api/produtos/{produto_id}").get_json()["produto"]
        assert detalhe["modelo"] == "Modelo Atualizado"
        assert detalhe["preco_venda"] == 3500.0
        _limpar_produto(produto_id)

    def test_categoria_invalida_e_rejeitada_na_atualizacao(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_produto(client)
        produto_id = criado.get_json()["id"]

        resp = client.put(
            f"/api/produtos/{produto_id}", json={"categoria": "Invalida", "preco_venda": 100}
        )

        assert resp.status_code == 400
        _limpar_produto(produto_id)

    def test_desativar_produto(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_produto(client)
        produto_id = criado.get_json()["id"]

        resp = client.put(
            f"/api/produtos/{produto_id}",
            json={"categoria": "iPhone", "preco_venda": 2999.0, "ativo": False},
        )

        assert resp.status_code == 200
        detalhe = client.get(f"/api/produtos/{produto_id}").get_json()["produto"]
        assert detalhe["ativo"] is False
        _limpar_produto(produto_id)


class TestExcluirProduto:
    def test_sem_autenticacao_retorna_403(self, client):
        resp = client.delete("/api/produtos/1")
        assert resp.status_code == 403

    def test_nao_admin_nao_pode_excluir(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.delete("/api/produtos/1")
        assert resp.status_code == 403

    def test_admin_pode_excluir(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_produto(client)
        produto_id = criado.get_json()["id"]

        resp = client.delete(f"/api/produtos/{produto_id}")

        assert resp.status_code == 200
        assert client.get(f"/api/produtos/{produto_id}").status_code == 404

    def test_excluir_produto_inexistente_retorna_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.delete("/api/produtos/999999")
        assert resp.status_code == 404


class TestConstantesExpoeCategoriaCondicao:
    """Sprint tecnica de centralizacao de referencias: PRODUTOS_CATEGORIAS/CONDICOES
    precisam estar em GET /api/constantes para o frontend nao manter copia propria."""

    def test_constantes_inclui_categorias_e_condicoes_de_produtos(self, client, login_como, usuario_tecnico):
        from irflow_reference_data import PRODUTOS_CATEGORIAS, PRODUTOS_CONDICOES

        login_como(client, usuario_tecnico)
        resp = client.get("/api/constantes")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["produtos_categorias"] == PRODUTOS_CATEGORIAS
        assert body["produtos_condicoes"] == PRODUTOS_CONDICOES
