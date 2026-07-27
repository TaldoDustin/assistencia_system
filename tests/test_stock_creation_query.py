"""
Testes de cadastro e consulta de itens de estoque via API JSON (Sprint 2.5).

Escopo: POST /api/estoque, GET /api/estoque.

Cobre apenas comportamento oficial — regra de negócio e transformação real
de dados (normalização de tipo/qualidade/modelo, truncamento de quantidade
decimal, etc.). Limitações atuais da implementação que não fazem parte do
contrato funcional (ausência de GET /api/estoque/<id> individual, ausência
de paginação, ausência de ordenação customizável) são características da
API, não regras de negócio — documentadas apenas no relatório final da
sprint, sem teste dedicado (orientação explícita do usuário: um teste não
deve existir só para provar que uma limitação existe).
"""

import uuid

import app as _app


def _obter_item(item_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT descricao, valor, quantidade, modelo, tipo, qualidade, fornecedor FROM estoque WHERE id=?",
            (item_id,),
        ).fetchone()
    finally:
        conn.close()


def _obter_requer_imei(item_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT requer_imei FROM estoque WHERE id=?", (item_id,)).fetchone()[0]
    finally:
        conn.close()


def _contar_lotes(item_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT COUNT(*) FROM estoque_lotes WHERE estoque_id=?", (item_id,)).fetchone()[0]
    finally:
        conn.close()


def _contar_movimentacoes(item_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT COUNT(*) FROM movimentacoes WHERE estoque_id=?", (item_id,)).fetchone()[0]
    finally:
        conn.close()


def _limpar_item(item_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM estoque_lotes WHERE estoque_id=?", (item_id,))
        conn.execute("DELETE FROM movimentacoes WHERE estoque_id=?", (item_id,))
        conn.execute("DELETE FROM estoque WHERE id=?", (item_id,))
        conn.commit()
    finally:
        conn.close()


# ============================================================================
# POST /api/estoque — cadastro
# ============================================================================


class TestCriarItemEstoque:
    def test_criacao_valida_retorna_201_e_persiste_dados(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)

        resp = client.post(
            "/api/estoque",
            json={"descricao": "Tela iPhone 13", "valor": 150.0, "quantidade": 5, "modelo": "iPhone 13"},
        )

        assert resp.status_code == 201
        item_id = resp.get_json()["id"]
        row = _obter_item(item_id)
        assert row[0] == "Tela iPhone 13"
        assert row[2] == 5
        _limpar_item(item_id)

    def test_criacao_com_quantidade_inicial_registra_lote_e_movimentacao_entrada(
        self, client, login_como, usuario_estoque
    ):
        login_como(client, usuario_estoque)

        resp = client.post("/api/estoque", json={"descricao": "Bateria", "valor": 80.0, "quantidade": 3})

        item_id = resp.get_json()["id"]
        assert _contar_lotes(item_id) == 1
        assert _contar_movimentacoes(item_id) == 1
        _limpar_item(item_id)

    def test_criacao_com_quantidade_zero_nao_registra_lote_nem_movimentacao(
        self, client, login_como, usuario_estoque
    ):
        login_como(client, usuario_estoque)

        resp = client.post("/api/estoque", json={"descricao": "Peca Sem Estoque", "valor": 10.0, "quantidade": 0})

        assert resp.status_code == 201
        item_id = resp.get_json()["id"]
        assert _contar_lotes(item_id) == 0
        assert _contar_movimentacoes(item_id) == 0
        _limpar_item(item_id)

    def test_sem_descricao_retorna_400(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.post("/api/estoque", json={"descricao": "", "valor": 10.0, "quantidade": 1})
        assert resp.status_code == 400

    def test_valor_zero_retorna_400(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.post("/api/estoque", json={"descricao": "Peca", "valor": 0, "quantidade": 1})
        assert resp.status_code == 400

    def test_valor_negativo_retorna_400(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.post("/api/estoque", json={"descricao": "Peca", "valor": -10, "quantidade": 1})
        assert resp.status_code == 400

    def test_quantidade_negativa_retorna_400(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.post("/api/estoque", json={"descricao": "Peca", "valor": 10, "quantidade": -1})
        assert resp.status_code == 400

    def test_peca_duplicada_e_permitida(self, client, login_como, usuario_estoque):
        """
        Não há constraint de unicidade em `estoque` (sku e a tripla
        modelo/tipo/qualidade têm apenas índices não-únicos — ver
        DATABASE.md). Cadastrar duas peças idênticas é aceito e produz duas
        linhas distintas.
        """
        login_como(client, usuario_estoque)
        payload = {
            "descricao": "Tela Duplicada",
            "valor": 100.0,
            "quantidade": 1,
            "modelo": "iPhone 13",
            "sku": "SKU-DUPLICADO",
        }

        resp1 = client.post("/api/estoque", json=payload)
        resp2 = client.post("/api/estoque", json=payload)

        assert resp1.status_code == 201
        assert resp2.status_code == 201
        id1, id2 = resp1.get_json()["id"], resp2.get_json()["id"]
        assert id1 != id2
        _limpar_item(id1)
        _limpar_item(id2)

    def test_fornecedor_e_texto_livre_sem_validacao(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)

        resp = client.post(
            "/api/estoque",
            json={"descricao": "Peca", "valor": 10, "quantidade": 1, "fornecedor": "Fornecedor Nunca Cadastrado Antes"},
        )

        assert resp.status_code == 201
        item_id = resp.get_json()["id"]
        assert _obter_item(item_id)[6] == "Fornecedor Nunca Cadastrado Antes"
        _limpar_item(item_id)

    def test_fornecedor_padrao_quando_omitido(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)

        resp = client.post("/api/estoque", json={"descricao": "Peca", "valor": 10, "quantidade": 1})

        item_id = resp.get_json()["id"]
        assert _obter_item(item_id)[6] == "Nao informado"
        _limpar_item(item_id)

    def test_tipo_desconhecido_normaliza_para_outros(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)

        resp = client.post(
            "/api/estoque", json={"descricao": "Peca", "valor": 10, "quantidade": 1, "tipo": "Categoria Inexistente"}
        )

        item_id = resp.get_json()["id"]
        assert _obter_item(item_id)[4] == "Outros"
        _limpar_item(item_id)

    def test_qualidade_desconhecida_normaliza_para_padrao(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)

        resp = client.post(
            "/api/estoque", json={"descricao": "Peca", "valor": 10, "quantidade": 1, "qualidade": "Nivel Inexistente"}
        )

        item_id = resp.get_json()["id"]
        assert _obter_item(item_id)[5] == "Padrao"
        _limpar_item(item_id)

    def test_modelo_desconhecido_e_aceito_como_texto_livre(self, client, login_como, usuario_estoque):
        """
        Diferente da rota legada POST /estoque/cadastro (que rejeita modelo
        fora da lista oficial de iPhones), a API aceita e armazena qualquer
        texto como modelo quando não reconhece um iPhone conhecido.
        """
        login_como(client, usuario_estoque)
        modelo_desconhecido = "Peça Genérica Sem Modelo Oficial"

        resp = client.post(
            "/api/estoque", json={"descricao": "Peca", "valor": 10, "quantidade": 1, "modelo": modelo_desconhecido}
        )

        assert resp.status_code == 201
        item_id = resp.get_json()["id"]
        assert _obter_item(item_id)[3] == modelo_desconhecido
        _limpar_item(item_id)

    def test_quantidade_decimal_trunca_para_inteiro(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)

        resp = client.post("/api/estoque", json={"descricao": "Peca", "valor": 10, "quantidade": 3.7})

        assert resp.status_code == 201
        item_id = resp.get_json()["id"]
        assert _obter_item(item_id)[2] == 3
        _limpar_item(item_id)

    def test_quantidade_extremamente_alta_e_aceita_com_precisao(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        quantidade_alta = 10**15

        resp = client.post("/api/estoque", json={"descricao": "Peca", "valor": 10, "quantidade": quantidade_alta})

        assert resp.status_code == 201
        item_id = resp.get_json()["id"]
        assert _obter_item(item_id)[2] == quantidade_alta
        _limpar_item(item_id)

    def test_sem_sessao_retorna_401(self, client):
        resp = client.post("/api/estoque", json={"descricao": "Peca", "valor": 10, "quantidade": 1})
        assert resp.status_code == 401


# ============================================================================
# requer_imei — rastreabilidade individual (IMEI/serial hoje, ver KI-020/C1.3.5)
# ============================================================================


class TestRastreabilidadeIndividualEstoque:
    """`requer_imei` é a flag que habilita rastreamento por unidade
    (`unidades_serializadas.estoque_id`, ver `irflow_unidades_serializadas_service.py`).
    O conceito é rastreabilidade individual do item -- hoje via IMEI/serial, o nome
    da coluna é histórico (mantido por compatibilidade)."""

    def test_criar_com_requer_imei_true_persiste_como_1(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)

        resp = client.post(
            "/api/estoque",
            json={"descricao": "iPhone 13 Seminovo", "valor": 3000, "quantidade": 1, "requer_imei": True},
        )

        assert resp.status_code == 201
        item_id = resp.get_json()["id"]
        assert _obter_requer_imei(item_id) == 1
        _limpar_item(item_id)

    def test_criar_sem_requer_imei_persiste_como_0(self, client, login_como, usuario_estoque):
        """Regressão: payload igual ao usado antes desta feature existir continua
        criando o item com requer_imei=0, sem exigir o campo novo."""
        login_como(client, usuario_estoque)

        resp = client.post("/api/estoque", json={"descricao": "Tela Generica", "valor": 50, "quantidade": 10})

        assert resp.status_code == 201
        item_id = resp.get_json()["id"]
        assert _obter_requer_imei(item_id) == 0
        _limpar_item(item_id)

    def test_listar_expoe_requer_imei_como_booleano(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp_criar = client.post(
            "/api/estoque",
            json={"descricao": "Apple Watch Seminovo", "valor": 1500, "quantidade": 1, "requer_imei": True},
        )
        item_id = resp_criar.get_json()["id"]

        resp = client.get("/api/estoque")

        item = next(i for i in resp.get_json()["itens"] if i["id"] == item_id)
        assert item["requer_imei"] is True
        _limpar_item(item_id)


# ============================================================================
# GET /api/estoque — consulta
# ============================================================================


class TestListarEstoque:
    def test_sem_sessao_retorna_401(self, client):
        resp = client.get("/api/estoque")
        assert resp.status_code == 401

    def test_listar_inclui_item_criado(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        item_id = criar_item_estoque(descricao=f"Item Listagem {uuid.uuid4().hex[:8]}")

        resp = client.get("/api/estoque")

        assert resp.status_code == 200
        ids = {i["id"] for i in resp.get_json()["itens"]}
        assert item_id in ids

    def test_filtro_por_modelo(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        marcador = f"Marca {uuid.uuid4().hex[:8]}"
        item_alvo = criar_item_estoque(descricao=marcador, modelo="iPhone 15")
        item_outro = criar_item_estoque(descricao=marcador, modelo="iPhone 11")

        resp = client.get("/api/estoque", query_string={"modelo": "iPhone 15", "q": marcador})

        ids = {i["id"] for i in resp.get_json()["itens"]}
        assert item_alvo in ids
        assert item_outro not in ids

    def test_filtro_por_tipo(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        marcador = f"Marca {uuid.uuid4().hex[:8]}"
        item_alvo = criar_item_estoque(descricao=marcador, tipo="Bateria")
        item_outro = criar_item_estoque(descricao=marcador, tipo="Tela")

        resp = client.get("/api/estoque", query_string={"tipo": "Bateria", "q": marcador})

        ids = {i["id"] for i in resp.get_json()["itens"]}
        assert item_alvo in ids
        assert item_outro not in ids

    def test_filtro_por_qualidade(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        marcador = f"Marca {uuid.uuid4().hex[:8]}"
        item_alvo = criar_item_estoque(descricao=marcador, qualidade="Original")
        item_outro = criar_item_estoque(descricao=marcador, qualidade="Paralelo")

        resp = client.get("/api/estoque", query_string={"qualidade": "Original", "q": marcador})

        ids = {i["id"] for i in resp.get_json()["itens"]}
        assert item_alvo in ids
        assert item_outro not in ids

    def test_filtro_texto_busca_por_descricao(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        marcador = f"BuscaUnica{uuid.uuid4().hex[:8]}"
        item_alvo = criar_item_estoque(descricao=marcador)

        resp = client.get("/api/estoque", query_string={"q": marcador.lower()})

        ids = {i["id"] for i in resp.get_json()["itens"]}
        assert item_alvo in ids

    def test_itens_zerados_ficam_ocultos_por_padrao(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        marcador = f"Marca {uuid.uuid4().hex[:8]}"
        item_zerado = criar_item_estoque(descricao=marcador, quantidade=0)

        resp = client.get("/api/estoque", query_string={"q": marcador})

        ids = {i["id"] for i in resp.get_json()["itens"]}
        assert item_zerado not in ids

    def test_include_zerados_mostra_itens_sem_estoque(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        marcador = f"Marca {uuid.uuid4().hex[:8]}"
        item_zerado = criar_item_estoque(descricao=marcador, quantidade=0)

        resp = client.get("/api/estoque", query_string={"q": marcador, "include_zerados": "1"})

        ids = {i["id"] for i in resp.get_json()["itens"]}
        assert item_zerado in ids

    def test_payload_inclui_totais_agregados(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        criar_item_estoque(quantidade=2, valor=10.0)

        body = client.get("/api/estoque").get_json()

        assert "total_lotes" in body
        assert "total_unidades" in body
        assert "valor_total" in body
        assert "criticos" in body
