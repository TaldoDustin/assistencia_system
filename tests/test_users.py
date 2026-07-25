"""
Testes de CRUD de usuarios via API JSON (Sprint 2.3).

Escopo: /api/usuarios (listar, criar, editar, excluir) — a superficie consumida
pelo frontend React (ver ARCHITECTURE.md). As rotas legadas equivalentes
(/usuarios/novo, /usuarios/editar, /usuarios/deletar) ja tem cobertura de
controle de acesso em test_auth.py::TestControleDeAcessoPorPerfil.

Estes testes caracterizam o comportamento atualmente aceito pela aplicacao,
nao um comportamento desejado — nao adicionam nem alteram nenhuma regra de
negocio.
"""

import uuid

from werkzeug.security import check_password_hash

import app as _app


def _buscar_usuario_no_banco(uid):
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, usuario, senha_hash, perfil, ativo FROM usuarios WHERE id = ?",
            (uid,),
        )
        return cursor.fetchone()
    finally:
        conn.close()


def _remover_usuario(uid):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM usuarios WHERE id = ?", (uid,))
        conn.commit()
    finally:
        conn.close()


# ============================================================================
# GET /api/usuarios — listar
# ============================================================================


class TestListarUsuarios:
    def test_admin_lista_usuarios(self, client, login_como, usuario_admin, usuario_tecnico):
        login_como(client, usuario_admin)

        resp = client.get("/api/usuarios")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ok"] is True
        ids = {u["id"] for u in body["usuarios"]}
        assert usuario_admin["id"] in ids
        assert usuario_tecnico["id"] in ids

    def test_listagem_nao_expoe_hash_de_senha(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)

        resp = client.get("/api/usuarios")

        body = resp.get_json()
        for usuario in body["usuarios"]:
            assert "senha_hash" not in usuario
            assert "senha" not in usuario

    def test_tecnico_recebe_acesso_negado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)

        resp = client.get("/api/usuarios")

        assert resp.status_code == 403
        assert resp.get_json()["ok"] is False

    def test_sem_sessao_recebe_acesso_negado(self, client):
        resp = client.get("/api/usuarios")

        assert resp.status_code == 403
        assert resp.get_json()["ok"] is False


# ============================================================================
# POST /api/usuarios — criar
# ============================================================================


class TestCriarUsuario:
    def test_admin_cria_usuario_com_sucesso(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        login_novo = f"novo_{uuid.uuid4().hex[:8]}"

        resp = client.post(
            "/api/usuarios",
            json={"nome": "Fulano", "usuario": login_novo, "senha": "senha_123", "perfil": "tecnico"},
        )

        assert resp.status_code == 201
        body = resp.get_json()
        assert body["ok"] is True
        novo_id = body["id"]

        row = _buscar_usuario_no_banco(novo_id)
        assert row is not None
        assert row[2] == login_novo
        assert row[4] == "tecnico"
        assert check_password_hash(row[3], "senha_123")

        _remover_usuario(novo_id)

    def test_criar_usuario_duplicado_retorna_400(self, client, login_como, usuario_admin, usuario_tecnico):
        login_como(client, usuario_admin)

        resp = client.post(
            "/api/usuarios",
            json={
                "nome": "Duplicado",
                "usuario": usuario_tecnico["usuario"],
                "senha": "outra_senha",
                "perfil": "tecnico",
            },
        )

        assert resp.status_code == 400
        body = resp.get_json()
        assert body["ok"] is False
        assert "já existe" in body["erro"]

    def test_criar_usuario_sem_campos_obrigatorios_retorna_400(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)

        resp = client.post("/api/usuarios", json={"nome": "", "usuario": "", "senha": ""})

        assert resp.status_code == 400
        assert resp.get_json()["ok"] is False

    def test_criar_usuario_com_perfil_desconhecido_usa_tecnico(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        login_novo = f"novo_{uuid.uuid4().hex[:8]}"

        resp = client.post(
            "/api/usuarios",
            json={"nome": "Perfil Invalido", "usuario": login_novo, "senha": "senha_123", "perfil": "estagiario"},
        )

        assert resp.status_code == 201
        novo_id = resp.get_json()["id"]
        row = _buscar_usuario_no_banco(novo_id)
        assert row[4] == "tecnico"

        _remover_usuario(novo_id)

    def test_criar_usuario_com_perfil_estoque_e_aceito(self, client, login_como, usuario_admin):
        """Sprint Segurança 1.0 (2026-07-25): perfil "estoque" adicionado — ver
        docs/security/SECURITY_AUDIT_2026-07.md e irflow_core.py::PERFIS_OPCOES."""
        login_como(client, usuario_admin)
        login_novo = f"novo_{uuid.uuid4().hex[:8]}"

        resp = client.post(
            "/api/usuarios",
            json={"nome": "Estoque Teste", "usuario": login_novo, "senha": "senha_123", "perfil": "estoque"},
        )

        assert resp.status_code == 201
        novo_id = resp.get_json()["id"]
        row = _buscar_usuario_no_banco(novo_id)
        assert row[4] == "estoque"

        _remover_usuario(novo_id)

    def test_tecnico_nao_pode_criar_usuario(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        login_novo = f"novo_{uuid.uuid4().hex[:8]}"

        resp = client.post(
            "/api/usuarios",
            json={"nome": "Nao Deveria Existir", "usuario": login_novo, "senha": "x", "perfil": "tecnico"},
        )

        assert resp.status_code == 403
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT id FROM usuarios WHERE usuario = ?", (login_novo,)).fetchone()
        finally:
            conn.close()
        assert row is None


# ============================================================================
# PUT /api/usuarios/<id> — atualizar
# ============================================================================


class TestAtualizarUsuario:
    def test_admin_atualiza_nome_e_perfil(self, client, login_como, usuario_admin, usuario_tecnico):
        login_como(client, usuario_admin)

        resp = client.put(
            f"/api/usuarios/{usuario_tecnico['id']}",
            json={"nome": "Nome Atualizado", "perfil": "vendedor", "ativo": True},
        )

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        row = _buscar_usuario_no_banco(usuario_tecnico["id"])
        assert row[1] == "Nome Atualizado"
        assert row[4] == "vendedor"

    def test_admin_troca_senha_de_outro_usuario(self, client, login_como, usuario_admin, usuario_tecnico):
        login_como(client, usuario_admin)

        resp = client.put(
            f"/api/usuarios/{usuario_tecnico['id']}",
            json={"nome": usuario_tecnico["nome"], "perfil": "tecnico", "senha_nova": "nova_senha_456", "ativo": True},
        )

        assert resp.status_code == 200
        row = _buscar_usuario_no_banco(usuario_tecnico["id"])
        assert check_password_hash(row[3], "nova_senha_456")

        outro_client = _app.app.test_client()
        login_resp = outro_client.post(
            "/api/auth/login",
            json={"usuario": usuario_tecnico["usuario"], "senha": "nova_senha_456"},
        )
        assert login_resp.status_code == 200

    def test_admin_nao_pode_desativar_a_propria_conta(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)

        resp = client.put(
            f"/api/usuarios/{usuario_admin['id']}",
            json={"nome": usuario_admin["nome"], "perfil": "admin", "ativo": False},
        )

        assert resp.status_code == 400
        assert "não pode desativar" in resp.get_json()["erro"]
        row = _buscar_usuario_no_banco(usuario_admin["id"])
        assert row[5] == 1

    def test_atualizar_usuario_inexistente_responde_ok_sem_efeito(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        uid_inexistente = 9_999_999

        resp = client.put(
            f"/api/usuarios/{uid_inexistente}",
            json={"nome": "Fantasma", "perfil": "tecnico", "ativo": True},
        )

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        assert _buscar_usuario_no_banco(uid_inexistente) is None

    def test_vendedor_nao_pode_atualizar_usuario(self, client, login_como, usuario_vendedor, usuario_tecnico):
        login_como(client, usuario_vendedor)

        resp = client.put(
            f"/api/usuarios/{usuario_tecnico['id']}",
            json={"nome": "Nao Deveria Mudar", "perfil": "admin", "ativo": True},
        )

        assert resp.status_code == 403
        row = _buscar_usuario_no_banco(usuario_tecnico["id"])
        assert row[1] == usuario_tecnico["nome"]
        assert row[4] == "tecnico"


# ============================================================================
# DELETE /api/usuarios/<id> — excluir
# ============================================================================


class TestExcluirUsuario:
    def test_admin_exclui_usuario_com_sucesso(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios (nome, usuario, senha_hash, perfil, ativo) VALUES (?, ?, ?, ?, ?)",
                ("Descartavel", f"descartavel_{uuid.uuid4().hex[:8]}", "hash", "tecnico", 1),
            )
            conn.commit()
            uid = cursor.lastrowid
        finally:
            conn.close()

        resp = client.delete(f"/api/usuarios/{uid}")

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        assert _buscar_usuario_no_banco(uid) is None

    def test_admin_nao_pode_excluir_a_propria_conta(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)

        resp = client.delete(f"/api/usuarios/{usuario_admin['id']}")

        assert resp.status_code == 400
        assert "não pode excluir" in resp.get_json()["erro"]
        assert _buscar_usuario_no_banco(usuario_admin["id"]) is not None

    def test_excluir_usuario_inexistente_responde_ok_sem_efeito(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        uid_inexistente = 9_999_998

        resp = client.delete(f"/api/usuarios/{uid_inexistente}")

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_tecnico_nao_pode_excluir_usuario(self, client, login_como, usuario_tecnico, usuario_vendedor):
        login_como(client, usuario_tecnico)

        resp = client.delete(f"/api/usuarios/{usuario_vendedor['id']}")

        assert resp.status_code == 403
        assert _buscar_usuario_no_banco(usuario_vendedor["id"]) is not None
