"""
Testes do domínio Clientes (Sprint P0.1, Unidade 5).

Escopo: `GET/POST/PUT/DELETE /api/clientes*` e a integração com `os.cliente_id`.
Primeiro domínio a seguir a convenção controller/service/repository de
`docs/engineering/ENGINEERING_GUIDE.md` §3.1 — ver também `irflow_clientes_service.py`
para a regra de negócio (cadastro mínimo viável, exclusão bloqueada com
histórico) testada aqui via HTTP.
"""

import uuid

import app as _app


def _limpar_cliente(cliente_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade='cliente' AND entidade_id=?", (cliente_id,))
        conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_cliente(client, **overrides):
    payload = {"nome": f"Cliente {uuid.uuid4().hex[:8]}", "telefone": "11999990000"}
    payload.update(overrides)
    return client.post("/api/clientes", json=payload)


class TestListarClientes:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/clientes")
        assert resp.status_code == 401

    def test_listagem_padrao_retorna_estrutura_paginada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/clientes")

        assert resp.status_code == 200
        body = resp.get_json()
        assert "items" in body and "total" in body and "page" in body and "per_page" in body

    def test_busca_por_nome_parcial(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        nome = f"Fulano Unico {uuid.uuid4().hex[:8]}"
        criado = _criar_cliente(client, nome=nome)
        cliente_id = criado.get_json()["id"]

        resp = client.get(f"/api/clientes?q={nome[:10]}")

        nomes = [c["nome"] for c in resp.get_json()["items"]]
        assert nome in nomes
        _limpar_cliente(cliente_id)

    def test_busca_por_telefone_parcial(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        telefone = f"119{uuid.uuid4().hex[:8]}"
        criado = _criar_cliente(client, telefone=telefone)
        cliente_id = criado.get_json()["id"]

        resp = client.get(f"/api/clientes?q={telefone[:6]}")

        telefones = [c["telefone"] for c in resp.get_json()["items"]]
        assert telefone in telefones
        _limpar_cliente(cliente_id)

    def test_page_nao_numerico_retorna_400(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/clientes?page=abc")
        assert resp.status_code == 400


class TestObterCliente:
    def test_cliente_existente(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_cliente(client, email="fulano@example.com")
        cliente_id = criado.get_json()["id"]

        resp = client.get(f"/api/clientes/{cliente_id}")

        assert resp.status_code == 200
        assert resp.get_json()["cliente"]["email"] == "fulano@example.com"
        _limpar_cliente(cliente_id)

    def test_cliente_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/clientes/999999")
        assert resp.status_code == 404


class TestCriarCliente:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/api/clientes", json={"nome": "Teste"})
        assert resp.status_code == 401

    def test_nome_sozinho_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/clientes", json={"nome": "Sem Contato"})
        assert resp.status_code == 400

    def test_sem_nome_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/clientes", json={"telefone": "11999990000"})
        assert resp.status_code == 400

    def test_nome_mais_telefone_e_aceito(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = _criar_cliente(client)
        assert resp.status_code == 200
        _limpar_cliente(resp.get_json()["id"])

    def test_nome_mais_email_e_aceito(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = _criar_cliente(client, telefone=None, email="teste@example.com")
        assert resp.status_code == 200
        _limpar_cliente(resp.get_json()["id"])

    def test_criacao_registra_auditoria(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = _criar_cliente(client)
        cliente_id = resp.get_json()["id"]

        conn = _app.conectar()
        try:
            logs = conn.execute(
                "SELECT acao FROM audit_log WHERE entidade='cliente' AND entidade_id=?", (cliente_id,)
            ).fetchall()
        finally:
            conn.close()

        assert [row[0] for row in logs] == ["create"]
        _limpar_cliente(cliente_id)


class TestAtualizarCliente:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.put("/api/clientes/1", json={"nome": "X", "telefone": "11999990000"})
        assert resp.status_code == 401

    def test_cliente_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.put("/api/clientes/999999", json={"nome": "X", "telefone": "11999990000"})
        assert resp.status_code == 404

    def test_atualizacao_valida_persiste(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.put(
            f"/api/clientes/{cliente_id}", json={"nome": "Nome Atualizado", "telefone": "11988887777"}
        )

        assert resp.status_code == 200
        detalhe = client.get(f"/api/clientes/{cliente_id}").get_json()["cliente"]
        assert detalhe["nome"] == "Nome Atualizado"
        _limpar_cliente(cliente_id)

    def test_remover_todos_os_contatos_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.put(f"/api/clientes/{cliente_id}", json={"nome": "Nome", "telefone": "", "email": ""})

        assert resp.status_code == 400
        _limpar_cliente(cliente_id)


class TestExcluirCliente:
    def test_sem_autenticacao_retorna_403(self, client):
        # Admin-only: usuario_logado() e usuario_admin() sao checados juntos,
        # mesmo padrao de outras rotas admin-only (ex.: GET /api/precos) —
        # sem sessao cai direto no "acesso negado" (403), nao 401.
        resp = client.delete("/api/clientes/1")
        assert resp.status_code == 403

    def test_nao_admin_nao_pode_excluir(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.delete(f"/api/clientes/{cliente_id}")

        assert resp.status_code == 403
        _limpar_cliente(cliente_id)

    def test_cliente_sem_historico_pode_ser_excluido(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.delete(f"/api/clientes/{cliente_id}")

        assert resp.status_code == 200
        assert client.get(f"/api/clientes/{cliente_id}").status_code == 404

    def test_cliente_com_os_vinculada_nao_pode_ser_excluido(self, client, login_como, usuario_admin, criar_os):
        login_como(client, usuario_admin)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]
        os_id = criar_os()

        conn = _app.conectar()
        try:
            conn.execute("UPDATE os SET cliente_id=? WHERE id=?", (cliente_id, os_id))
            conn.commit()
        finally:
            conn.close()

        resp = client.delete(f"/api/clientes/{cliente_id}")

        assert resp.status_code == 409
        _limpar_cliente(cliente_id)


class TestIntegracaoOsClienteId:
    def test_os_criada_sem_cliente_id_continua_funcionando(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os()

        resp = client.get(f"/api/ordens/{os_id}")

        assert resp.status_code == 200

    def test_os_pode_ser_vinculada_a_um_cliente_id(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]
        os_id = criar_os()

        conn = _app.conectar()
        try:
            conn.execute("UPDATE os SET cliente_id=? WHERE id=?", (cliente_id, os_id))
            conn.commit()
            row = conn.execute("SELECT cliente_id FROM os WHERE id=?", (os_id,)).fetchone()
        finally:
            conn.close()

        assert row[0] == cliente_id
        _limpar_cliente(cliente_id)
