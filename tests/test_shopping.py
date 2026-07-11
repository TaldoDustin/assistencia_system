"""
Testes de Lista de Compras / Shopping List (Sprint 2 — Restante).

Escopo: CRUD completo de `/api/shopping-list` e o workflow de transição de status
(`PATCH /api/shopping-list/<id>/status`), incluindo o bloqueio de compra simultânea e a
auditoria de mudanças (BR-015, BR-016 em `docs/product/BUSINESS_RULES.md`).

Isolamento: cada teste cria seus próprios itens e limpa via `_limpar_item` ao final —
nenhum teste depende de estado deixado por outro (`ENGINEERING_GUIDE.md` seção 6).
"""

import uuid

import app as _app


def _obter_item_db(item_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT status, responsavel_id, quantidade_recebida, cancelled_at FROM shopping_list WHERE id=?",
            (item_id,),
        ).fetchone()
    finally:
        conn.close()


def _contar_logs(item_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT COUNT(*) FROM shopping_list_logs WHERE shopping_list_id=?", (item_id,)
        ).fetchone()[0]
    finally:
        conn.close()


def _forcar_status(item_id, status, responsavel_id=None):
    conn = _app.conectar()
    try:
        conn.execute(
            "UPDATE shopping_list SET status=?, responsavel_id=? WHERE id=?", (status, responsavel_id, item_id)
        )
        conn.commit()
    finally:
        conn.close()


def _limpar_item(item_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM shopping_list_logs WHERE shopping_list_id=?", (item_id,))
        conn.execute("DELETE FROM shopping_list WHERE id=?", (item_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_item(client, **overrides):
    payload = {"produto_nome": f"Peca {uuid.uuid4().hex[:8]}", "quantidade_solicitada": 2}
    payload.update(overrides)
    resp = client.post("/api/shopping-list", json=payload)
    return resp


# ============================================================================
# GET /api/shopping-list — listagem e paginação
# ============================================================================


class TestListarShoppingList:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/shopping-list")
        assert resp.status_code == 401

    def test_listagem_padrao_retorna_estrutura_paginada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/shopping-list")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ok"] is True
        assert "items" in body and "total" in body and "page" in body and "per_page" in body

    def test_filtro_por_produto_encontra_item_criado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        nome = f"Tela Unica {uuid.uuid4().hex[:8]}"
        criado = _criar_item(client, produto_nome=nome)
        item_id = criado.get_json()["id"]

        resp = client.get(f"/api/shopping-list?produto={nome[:8]}")

        assert resp.status_code == 200
        nomes = [item["produto_nome"] for item in resp.get_json()["items"]]
        assert nome in nomes
        _limpar_item(item_id)

    def test_page_nao_numerico_retorna_erro_400(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/shopping-list?page=abc")
        assert resp.status_code == 400


class TestObterShoppingItem:
    def test_item_existente_retorna_dados_completos(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client, quantidade_solicitada=3, prioridade="URGENTE")
        item_id = criado.get_json()["id"]

        resp = client.get(f"/api/shopping-list/{item_id}")

        assert resp.status_code == 200
        item = resp.get_json()["item"]
        assert item["quantidade_solicitada"] == 3
        assert item["prioridade"] == "URGENTE"
        assert item["status"] == "PENDENTE"
        _limpar_item(item_id)

    def test_item_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/shopping-list/999999")
        assert resp.status_code == 404


# ============================================================================
# POST /api/shopping-list — criação
# ============================================================================


class TestCriarShoppingItem:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/api/shopping-list", json={"produto_nome": "Tela"})
        assert resp.status_code == 401

    def test_criacao_valida_persiste_com_prioridade_padrao(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = _criar_item(client, prioridade=None)

        assert resp.status_code == 200
        item_id = resp.get_json()["id"]
        detalhe = client.get(f"/api/shopping-list/{item_id}").get_json()["item"]
        assert detalhe["prioridade"] == "NORMAL"
        _limpar_item(item_id)

    def test_prioridade_invalida_e_normalizada_para_normal(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = _criar_item(client, prioridade="MUITO_URGENTE_INVALIDA")

        item_id = resp.get_json()["id"]
        detalhe = client.get(f"/api/shopping-list/{item_id}").get_json()["item"]
        assert detalhe["prioridade"] == "NORMAL"
        _limpar_item(item_id)

    def test_quantidade_zero_ou_negativa_e_rejeitada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = _criar_item(client, quantidade_solicitada=0)
        assert resp.status_code == 400

    def test_quantidade_nao_numerica_e_rejeitada_sem_erro_500(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = _criar_item(client, quantidade_solicitada="abc")
        assert resp.status_code == 400

    def test_mesmo_produto_nome_na_mesma_os_e_bloqueado_como_duplicata(
        self, client, login_como, usuario_tecnico, criar_os
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        nome = f"Peca Duplicada {uuid.uuid4().hex[:8]}"

        primeiro = _criar_item(client, produto_nome=nome, os_id=os_id)
        segundo = _criar_item(client, produto_nome=nome, os_id=os_id)

        assert primeiro.status_code == 200
        assert segundo.status_code == 400
        _limpar_item(primeiro.get_json()["id"])

    def test_produto_cancelado_nao_bloqueia_nova_entrada_equivalente(
        self, client, login_como, usuario_tecnico, criar_os
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        nome = f"Peca Recriada {uuid.uuid4().hex[:8]}"

        primeiro = _criar_item(client, produto_nome=nome, os_id=os_id)
        item_id = primeiro.get_json()["id"]
        client.delete(f"/api/shopping-list/{item_id}")  # cancela (soft delete)

        segundo = _criar_item(client, produto_nome=nome, os_id=os_id)

        assert segundo.status_code == 200
        _limpar_item(item_id)
        _limpar_item(segundo.get_json()["id"])


# ============================================================================
# PUT /api/shopping-list/<id> — edição
# ============================================================================


class TestAtualizarShoppingItem:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.put("/api/shopping-list/1", json={"quantidade_solicitada": 5})
        assert resp.status_code == 401

    def test_item_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.put("/api/shopping-list/999999", json={"quantidade_solicitada": 5})
        assert resp.status_code == 404

    def test_atualiza_quantidade_e_registra_log(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client, quantidade_solicitada=1)
        item_id = criado.get_json()["id"]

        resp = client.put(f"/api/shopping-list/{item_id}", json={"quantidade_solicitada": 9})

        assert resp.status_code == 200
        detalhe = client.get(f"/api/shopping-list/{item_id}").get_json()["item"]
        assert detalhe["quantidade_solicitada"] == 9
        assert _contar_logs(item_id) == 2  # create + update
        _limpar_item(item_id)

    def test_quantidade_negativa_e_rejeitada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client)
        item_id = criado.get_json()["id"]

        resp = client.put(f"/api/shopping-list/{item_id}", json={"quantidade_solicitada": -1})

        assert resp.status_code == 400
        _limpar_item(item_id)


# ============================================================================
# PATCH /api/shopping-list/<id>/status — workflow
# ============================================================================


class TestPatchStatusShoppingItem:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.patch("/api/shopping-list/1/status", json={"status": "EM_COTACAO"})
        assert resp.status_code == 401

    def test_status_invalido_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client)
        item_id = criado.get_json()["id"]

        resp = client.patch(f"/api/shopping-list/{item_id}/status", json={"status": "NAO_EXISTE"})

        assert resp.status_code == 400
        _limpar_item(item_id)

    def test_perfil_vendedor_nao_pode_alterar_status(self, client, login_como, usuario_tecnico, usuario_vendedor):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client)
        item_id = criado.get_json()["id"]

        login_como(client, usuario_vendedor)
        resp = client.patch(f"/api/shopping-list/{item_id}/status", json={"status": "EM_COTACAO"})

        assert resp.status_code == 403
        _limpar_item(item_id)

    def test_item_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.patch("/api/shopping-list/999999/status", json={"status": "EM_COTACAO"})
        assert resp.status_code == 404

    def test_transicao_valida_pendente_para_em_cotacao(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client)
        item_id = criado.get_json()["id"]

        resp = client.patch(f"/api/shopping-list/{item_id}/status", json={"status": "EM_COTACAO"})

        assert resp.status_code == 200
        assert resp.get_json()["status"] == "EM_COTACAO"
        _limpar_item(item_id)

    def test_transicao_invalida_pula_etapas_e_e_rejeitada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client)
        item_id = criado.get_json()["id"]

        # PENDENTE -> RECEBIDO nao e uma transicao valida (precisa passar por EM_COMPRA/COMPRADO)
        resp = client.patch(f"/api/shopping-list/{item_id}/status", json={"status": "RECEBIDO"})

        assert resp.status_code == 400
        _limpar_item(item_id)

    def test_transicao_idempotente_para_o_mesmo_status_e_permitida(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client)
        item_id = criado.get_json()["id"]

        resp = client.patch(f"/api/shopping-list/{item_id}/status", json={"status": "PENDENTE"})

        assert resp.status_code == 200
        _limpar_item(item_id)

    def test_receber_com_quantidade_recebida_persiste_o_valor(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client, quantidade_solicitada=5)
        item_id = criado.get_json()["id"]
        _forcar_status(item_id, "COMPRADO")

        resp = client.patch(
            f"/api/shopping-list/{item_id}/status", json={"status": "RECEBIDO", "quantidade_recebida": 5}
        )

        assert resp.status_code == 200
        row = _obter_item_db(item_id)
        assert row[2] == 5  # quantidade_recebida
        _limpar_item(item_id)

    def test_cancelado_e_estado_terminal_sem_transicao_de_volta(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client)
        item_id = criado.get_json()["id"]
        _forcar_status(item_id, "CANCELADO")

        resp = client.patch(f"/api/shopping-list/{item_id}/status", json={"status": "PENDENTE"})

        assert resp.status_code == 400
        _limpar_item(item_id)

    def test_compra_simultanea_pelo_mesmo_item_e_bloqueada(
        self, client, login_como, usuario_tecnico, usuario_admin
    ):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client)
        item_id = criado.get_json()["id"]

        primeira = client.patch(f"/api/shopping-list/{item_id}/status", json={"status": "EM_COMPRA"})
        assert primeira.status_code == 200

        login_como(client, usuario_admin)
        segunda = client.patch(f"/api/shopping-list/{item_id}/status", json={"status": "EM_COMPRA"})

        assert segunda.status_code == 400
        assert usuario_tecnico["nome"] in segunda.get_json()["erro"]
        _limpar_item(item_id)


# ============================================================================
# DELETE /api/shopping-list/<id> — cancelamento (soft delete)
# ============================================================================


class TestDeletarShoppingItem:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.delete("/api/shopping-list/1")
        assert resp.status_code == 401

    def test_item_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.delete("/api/shopping-list/999999")
        assert resp.status_code == 404

    def test_cancelamento_marca_status_e_timestamp(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client)
        item_id = criado.get_json()["id"]

        resp = client.delete(f"/api/shopping-list/{item_id}")

        assert resp.status_code == 200
        row = _obter_item_db(item_id)
        assert row[0] == "CANCELADO"
        assert row[3] is not None  # cancelled_at
        _limpar_item(item_id)


# ============================================================================
# GET /api/shopping-list/grouped e /logs — agregação e auditoria (BR-016)
# ============================================================================


class TestShoppingGroupedELogs:
    def test_grouped_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/shopping-list/grouped")
        assert resp.status_code == 401

    def test_grouped_soma_quantidade_do_mesmo_produto_entre_os(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        nome = f"Peca Agrupada {uuid.uuid4().hex[:8]}"
        os_a, os_b = criar_os(), criar_os()
        item_a = _criar_item(client, produto_nome=nome, os_id=os_a, quantidade_solicitada=2)
        item_b = _criar_item(client, produto_nome=nome, os_id=os_b, quantidade_solicitada=3)

        resp = client.get("/api/shopping-list/grouped")

        assert resp.status_code == 200
        grupo = next(g for g in resp.get_json()["grouped"] if g["produto_nome"] == nome)
        assert grupo["quantidade_total"] == 5
        assert grupo["os_count"] == 2
        _limpar_item(item_a.get_json()["id"])
        _limpar_item(item_b.get_json()["id"])

    def test_logs_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/shopping-list/1/logs")
        assert resp.status_code == 401

    def test_logs_registra_criacao_e_mudanca_de_status_em_ordem(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_item(client)
        item_id = criado.get_json()["id"]
        client.patch(f"/api/shopping-list/{item_id}/status", json={"status": "EM_COTACAO"})

        resp = client.get(f"/api/shopping-list/{item_id}/logs")

        assert resp.status_code == 200
        acoes = [log["acao"] for log in resp.get_json()["logs"]]
        assert "create" in acoes
        assert "status_change" in acoes
        _limpar_item(item_id)
