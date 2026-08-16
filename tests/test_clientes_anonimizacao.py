"""
Testes de anonimização de cliente (KI-044) --
docs/engineering/plans/PLAN-LGPD-Compliance.md.

Escopo: `POST /api/clientes/<id>/anonimizar` -- complementa, não substitui,
`DELETE /api/clientes/<id>` (que continua servindo só clientes órfãos, sem
histórico vinculado, decisão do CTO registrada no Plano Técnico).
"""

import json
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
        "email": "cliente@example.com",
        "cpf_cnpj": "123.456.789-00",
    }
    payload.update(overrides)
    return client.post("/api/clientes", json=payload)


class TestAnonimizarCliente:
    def test_sem_autenticacao_retorna_403(self, client):
        # Mesmo padrão de DELETE (admin-only): "não logado" e "logado sem admin" compartilham o
        # mesmo guard e o mesmo código de erro.
        resp = client.post("/api/clientes/1/anonimizar")
        assert resp.status_code == 403

    def test_perfil_nao_admin_retorna_403(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.post(f"/api/clientes/{cliente_id}/anonimizar")

        assert resp.status_code == 403
        _limpar_cliente(cliente_id)

    def test_cliente_inexistente_retorna_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post("/api/clientes/999999/anonimizar")
        assert resp.status_code == 404

    def test_anonimizar_mascara_pii_e_preserva_id(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        resp = client.post(f"/api/clientes/{cliente_id}/anonimizar")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

        conn = _app.conectar()
        try:
            row = conn.execute(
                "SELECT id, nome, telefone, email, cpf_cnpj, observacoes FROM clientes WHERE id=?",
                (cliente_id,),
            ).fetchone()
        finally:
            conn.close()

        assert row[0] == cliente_id  # id preservado
        assert row[1] == f"Cliente Anonimizado #{cliente_id}"
        assert row[2] is None
        assert row[3] is None
        assert row[4] is None
        assert row[5] == ""
        _limpar_cliente(cliente_id)

    def test_anonimizar_preserva_os_vinculada(self, client, login_como, usuario_admin, criar_os):
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

        resp = client.post(f"/api/clientes/{cliente_id}/anonimizar")
        assert resp.status_code == 200

        conn = _app.conectar()
        try:
            row = conn.execute("SELECT cliente_id FROM os WHERE id=?", (os_id,)).fetchone()
        finally:
            conn.close()

        assert row[0] == cliente_id  # FK intacta -- histórico de OS não se perde
        _limpar_cliente(cliente_id)

    def test_anonimizar_registra_audit_log(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_cliente(client)
        cliente_id = criado.get_json()["id"]

        client.post(f"/api/clientes/{cliente_id}/anonimizar")

        conn = _app.conectar()
        try:
            row = conn.execute(
                "SELECT acao, valor_anterior FROM audit_log WHERE entidade='cliente' AND entidade_id=? AND acao='anonymize'",
                (cliente_id,),
            ).fetchone()
        finally:
            conn.close()

        assert row is not None
        antes = json.loads(row[1])
        assert antes["cpf_cnpj"] == "123.456.789-00"  # snapshot pré-anonimização preservado no log
        _limpar_cliente(cliente_id)
