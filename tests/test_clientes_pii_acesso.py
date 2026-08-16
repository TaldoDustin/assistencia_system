"""
Testes de controle de acesso a CPF/CNPJ de cliente (KI-045) --
docs/engineering/plans/PLAN-LGPD-Compliance.md.

Decisão do CTO: restringe só LEITURA de cpf_cnpj a admin/financeiro. Escrita
(criar/atualizar) permanece liberada a todo perfil autenticado -- inclusive
quando o valor atual não é visível para quem está editando, caso em que o
frontend omite a chave do payload e o backend preserva o valor existente em
vez de apagá-lo silenciosamente.
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
    payload = {
        "nome": f"Cliente {uuid.uuid4().hex[:8]}",
        "telefone": "11999990000",
        "cpf_cnpj": "123.456.789-00",
    }
    payload.update(overrides)
    return client.post("/api/clientes", json=payload)


class TestLeituraRestritaPorPerfil:
    def test_admin_ve_cpf_na_listagem(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.get("/api/clientes")
        item = next(c for c in resp.get_json()["items"] if c["id"] == cliente_id)
        assert item["cpf_cnpj"] == "123.456.789-00"
        _limpar_cliente(cliente_id)

    def test_financeiro_ve_cpf_no_detalhe(self, client, login_como, usuario_financeiro):
        login_como(client, usuario_financeiro)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.get(f"/api/clientes/{cliente_id}")
        assert resp.get_json()["cliente"]["cpf_cnpj"] == "123.456.789-00"
        _limpar_cliente(cliente_id)

    def test_tecnico_nao_ve_cpf_na_listagem(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.get("/api/clientes")
        item = next(c for c in resp.get_json()["items"] if c["id"] == cliente_id)
        assert "cpf_cnpj" not in item
        _limpar_cliente(cliente_id)

    def test_vendedor_nao_ve_cpf_no_detalhe(self, client, login_como, usuario_vendedor):
        login_como(client, usuario_vendedor)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.get(f"/api/clientes/{cliente_id}")
        assert "cpf_cnpj" not in resp.get_json()["cliente"]
        _limpar_cliente(cliente_id)

    def test_estoque_nao_ve_cpf_no_detalhe(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.get(f"/api/clientes/{cliente_id}")
        assert "cpf_cnpj" not in resp.get_json()["cliente"]
        _limpar_cliente(cliente_id)


class TestEscritaPermaneceLiberada:
    def test_vendedor_pode_criar_cliente_com_cpf(self, client, login_como, usuario_vendedor):
        login_como(client, usuario_vendedor)
        criado = _criar_cliente(client)
        assert criado.status_code == 200
        cliente_id = criado.get_json()["id"]

        conn = _app.conectar()
        try:
            row = conn.execute("SELECT cpf_cnpj FROM clientes WHERE id=?", (cliente_id,)).fetchone()
        finally:
            conn.close()
        assert row[0] == "123.456.789-00"  # persistido mesmo sem o perfil poder ler de volta pela API
        _limpar_cliente(cliente_id)

    def test_vendedor_pode_sobrescrever_cpf_ao_editar(self, client, login_como, usuario_vendedor):
        login_como(client, usuario_vendedor)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.put(
            f"/api/clientes/{cliente_id}",
            json={"nome": "Novo Nome", "telefone": "11988887777", "cpf_cnpj": "999.999.999-99"},
        )
        assert resp.status_code == 200

        conn = _app.conectar()
        try:
            row = conn.execute("SELECT cpf_cnpj FROM clientes WHERE id=?", (cliente_id,)).fetchone()
        finally:
            conn.close()
        assert row[0] == "999.999.999-99"
        _limpar_cliente(cliente_id)


class TestEdicaoSemTocarNoCpfNaoApaga:
    def test_edicao_por_perfil_restrito_sem_cpf_no_payload_preserva_valor(
        self, client, login_como, usuario_tecnico
    ):
        """KI-045: o frontend omite cpf_cnpj do payload quando o campo não foi digitado por quem não
        pode ver o valor atual -- o backend precisa tratar isso como "preservar", não "limpar"."""
        login_como(client, usuario_tecnico)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.put(
            f"/api/clientes/{cliente_id}",
            json={"nome": "Nome Atualizado", "telefone": "11988887777"},  # sem cpf_cnpj
        )
        assert resp.status_code == 200

        conn = _app.conectar()
        try:
            row = conn.execute("SELECT nome, cpf_cnpj FROM clientes WHERE id=?", (cliente_id,)).fetchone()
        finally:
            conn.close()
        assert row[0] == "Nome Atualizado"
        assert row[1] == "123.456.789-00"  # não foi apagado
        _limpar_cliente(cliente_id)

    def test_admin_ainda_consegue_limpar_cpf_explicitamente(self, client, login_como, usuario_admin):
        """Comportamento pré-existente preservado: cpf_cnpj="" explícito continua limpando o campo."""
        login_como(client, usuario_admin)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.put(
            f"/api/clientes/{cliente_id}",
            json={"nome": "Nome Atualizado", "telefone": "11988887777", "cpf_cnpj": ""},
        )
        assert resp.status_code == 200

        conn = _app.conectar()
        try:
            row = conn.execute("SELECT cpf_cnpj FROM clientes WHERE id=?", (cliente_id,)).fetchone()
        finally:
            conn.close()
        assert row[0] == ""
        _limpar_cliente(cliente_id)
