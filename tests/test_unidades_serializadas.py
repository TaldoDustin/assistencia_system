"""
Testes do domínio `unidades_serializadas` — rastreamento individual por
IMEI/serial, evoluído de `estoque_unidades` na migração ADR-007
(docs/engineering/migrations/MIGRATION_unidades_serializadas.md).

Escopo: `GET/POST /api/unidades-serializadas*` e
`PATCH /api/unidades-serializadas/<id>/status`. Uma unidade tem origem em
`estoque_id` OU `produto_id`, nunca os dois (invariante validada no
service). `reservado`/`vendido` existem no schema
(`docs/product/features/IMEI.md`) mas nenhum endpoint desta sprint produz
ou aceita esses estados — reservados para o futuro módulo de Vendas.
"""

import uuid

import app as _app


def _criar_item_estoque(requer_imei=1, **overrides):
    conn = _app.conectar()
    cursor = conn.cursor()
    dados = {
        "descricao": "iPhone Teste",
        "valor": 3000.0,
        "fornecedor": "Fornecedor Teste",
        "quantidade": 1,
        "modelo": "iPhone 13",
        "sku": f"SKU-{uuid.uuid4().hex[:8]}",
        "tipo": "Aparelho",
        "qualidade": "Novo",
    }
    dados.update(overrides)
    cursor.execute(
        """
        INSERT INTO estoque (descricao, valor, fornecedor, quantidade, modelo, sku, tipo, qualidade, requer_imei)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            dados["descricao"], dados["valor"], dados["fornecedor"], dados["quantidade"],
            dados["modelo"], dados["sku"], dados["tipo"], dados["qualidade"], requer_imei,
        ),
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id


def _limpar_item_estoque(estoque_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade='unidade_serializada' AND entidade_id IN (SELECT id FROM unidades_serializadas WHERE estoque_id=?)", (estoque_id,))
        conn.execute("DELETE FROM unidades_serializadas WHERE estoque_id=?", (estoque_id,))
        conn.execute("DELETE FROM estoque WHERE id=?", (estoque_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_produto(requer_rastreio_unidade=True, **overrides):
    conn = _app.conectar()
    cursor = conn.cursor()
    dados = {
        "categoria": "iPhone",
        "modelo": f"iPhone Teste {uuid.uuid4().hex[:8]}",
        "condicao": "Seminovo",
        "preco_custo": 2000.0,
        "preco_venda": 2999.0,
        "quantidade": 1,
    }
    dados.update(overrides)
    cursor.execute(
        """
        INSERT INTO produtos (categoria, modelo, condicao, preco_custo, preco_venda, quantidade, requer_rastreio_unidade)
        VALUES (?,?,?,?,?,?,?)
        """,
        (
            dados["categoria"], dados["modelo"], dados["condicao"], dados["preco_custo"],
            dados["preco_venda"], dados["quantidade"], 1 if requer_rastreio_unidade else 0,
        ),
    )
    conn.commit()
    produto_id = cursor.lastrowid
    conn.close()
    return produto_id


def _limpar_produto(produto_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade='unidade_serializada' AND entidade_id IN (SELECT id FROM unidades_serializadas WHERE produto_id=?)", (produto_id,))
        conn.execute("DELETE FROM unidades_serializadas WHERE produto_id=?", (produto_id,))
        conn.execute("DELETE FROM audit_log WHERE entidade='produto' AND entidade_id=?", (produto_id,))
        conn.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_unidade(client, estoque_id=None, imei=None):
    estoque_id = estoque_id or _criar_item_estoque()
    imei = imei or "".join(str((int(uuid.uuid4().hex[:1], 16) + i) % 10) for i in range(15))
    resp = client.post("/api/unidades-serializadas", json={"estoque_id": estoque_id, "imei": imei})
    return resp, estoque_id


def _criar_unidade_de_produto(client, produto_id=None, imei=None):
    produto_id = produto_id or _criar_produto()
    imei = imei or "".join(str((int(uuid.uuid4().hex[:1], 16) + i) % 10) for i in range(15))
    resp = client.post("/api/unidades-serializadas", json={"produto_id": produto_id, "imei": imei})
    return resp, produto_id


class TestListarUnidades:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/unidades-serializadas")
        assert resp.status_code == 401

    def test_listagem_padrao_retorna_estrutura_paginada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/unidades-serializadas")

        assert resp.status_code == 200
        body = resp.get_json()
        assert "items" in body and "total" in body

    def test_busca_por_imei_parcial(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client, imei="352099001761481")

        resp = client.get("/api/unidades-serializadas?imei=176148")

        imeis = [u["imei"] for u in resp.get_json()["items"]]
        assert "352099001761481" in imeis
        _limpar_item_estoque(estoque_id)

    def test_filtro_por_produto_id(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, produto_id = _criar_unidade_de_produto(client)
        assert criado.status_code == 200

        resp = client.get(f"/api/unidades-serializadas?produto_id={produto_id}")

        body = resp.get_json()
        assert body["total"] == 1
        assert body["items"][0]["produto_id"] == produto_id
        assert body["items"][0]["estoque_id"] is None
        _limpar_produto(produto_id)


class TestObterUnidade:
    def test_unidade_existente(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.get(f"/api/unidades-serializadas/{unidade_id}")

        assert resp.status_code == 200
        assert resp.get_json()["unidade"]["status"] == "disponivel"
        _limpar_item_estoque(estoque_id)

    def test_unidade_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/unidades-serializadas/999999")
        assert resp.status_code == 404


class TestCriarUnidade:
    def test_sem_autenticacao_retorna_403(self, client):
        resp = client.post("/api/unidades-serializadas", json={"estoque_id": 1, "imei": "123"})
        assert resp.status_code == 403

    def test_vendedor_nao_pode_criar(self, client, login_como, usuario_vendedor):
        login_como(client, usuario_vendedor)
        resp = client.post("/api/unidades-serializadas", json={"estoque_id": 1, "imei": "123"})
        assert resp.status_code == 403

    def test_item_sem_requer_imei_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        estoque_id = _criar_item_estoque(requer_imei=0)

        resp = client.post("/api/unidades-serializadas", json={"estoque_id": estoque_id, "imei": "123456789012345"})

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)

    def test_item_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/unidades-serializadas", json={"estoque_id": 999999, "imei": "123456789012345"})
        assert resp.status_code == 404

    def test_criacao_valida_com_sucesso(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp, estoque_id = _criar_unidade(client)

        assert resp.status_code == 200
        assert resp.get_json()["id"]
        _limpar_item_estoque(estoque_id)

    def test_imei_duplicado_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        imei = "999888777666555"
        primeiro, estoque_id = _criar_unidade(client, imei=imei)
        assert primeiro.status_code == 200

        segundo_estoque = _criar_item_estoque()
        segundo = client.post("/api/unidades-serializadas", json={"estoque_id": segundo_estoque, "imei": imei})

        assert segundo.status_code == 400
        _limpar_item_estoque(estoque_id)
        _limpar_item_estoque(segundo_estoque)

    def test_criacao_registra_auditoria(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp, estoque_id = _criar_unidade(client)
        unidade_id = resp.get_json()["id"]

        conn = _app.conectar()
        try:
            logs = conn.execute(
                "SELECT acao FROM audit_log WHERE entidade='unidade_serializada' AND entidade_id=?", (unidade_id,)
            ).fetchall()
        finally:
            conn.close()

        assert [row[0] for row in logs] == ["create"]
        _limpar_item_estoque(estoque_id)

    def test_sem_origem_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/unidades-serializadas", json={"imei": "123456789012345"})
        assert resp.status_code == 400

    def test_ambas_origens_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        estoque_id = _criar_item_estoque()
        produto_id = _criar_produto()

        resp = client.post(
            "/api/unidades-serializadas",
            json={"estoque_id": estoque_id, "produto_id": produto_id, "imei": "123456789012345"},
        )

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)
        _limpar_produto(produto_id)

    def test_produto_sem_requer_rastreio_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        produto_id = _criar_produto(requer_rastreio_unidade=False)

        resp = client.post(
            "/api/unidades-serializadas", json={"produto_id": produto_id, "imei": "123456789012345"}
        )

        assert resp.status_code == 400
        _limpar_produto(produto_id)

    def test_produto_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post(
            "/api/unidades-serializadas", json={"produto_id": 999999, "imei": "123456789012345"}
        )
        assert resp.status_code == 404

    def test_criacao_valida_via_produto_com_sucesso(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp, produto_id = _criar_unidade_de_produto(client)

        assert resp.status_code == 200
        assert resp.get_json()["id"]
        _limpar_produto(produto_id)


class TestTransicaoStatus:
    def test_sem_autenticacao_retorna_403(self, client):
        resp = client.patch("/api/unidades-serializadas/1/status", json={"status": "em_reparo"})
        assert resp.status_code == 403

    def test_unidade_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.patch("/api/unidades-serializadas/999999/status", json={"status": "em_reparo"})
        assert resp.status_code == 404

    def test_disponivel_para_em_reparo_e_valido(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})

        assert resp.status_code == 200
        assert client.get(f"/api/unidades-serializadas/{unidade_id}").get_json()["unidade"]["status"] == "em_reparo"
        _limpar_item_estoque(estoque_id)

    def test_em_reparo_para_devolvido_e_valido(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]
        client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "devolvido"})

        assert resp.status_code == 200
        _limpar_item_estoque(estoque_id)

    def test_devolvido_para_disponivel_e_direto(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]
        client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})
        client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "devolvido"})

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "disponivel"})

        assert resp.status_code == 200
        _limpar_item_estoque(estoque_id)

    def test_disponivel_para_devolvido_direto_e_invalido(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "devolvido"})

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)

    def test_transicao_para_reservado_e_rejeitada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "reservado"})

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)

    def test_transicao_registra_auditoria(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})

        conn = _app.conectar()
        try:
            acoes = [
                row[0]
                for row in conn.execute(
                    "SELECT acao FROM audit_log WHERE entidade='unidade_serializada' AND entidade_id=? ORDER BY id",
                    (unidade_id,),
                ).fetchall()
            ]
        finally:
            conn.close()

        assert acoes == ["create", "status_change"]
        _limpar_item_estoque(estoque_id)

    def test_transicao_via_unidade_de_produto(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, produto_id = _criar_unidade_de_produto(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})

        assert resp.status_code == 200
        _limpar_produto(produto_id)
