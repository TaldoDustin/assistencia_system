"""
Testes de matriz de permissoes por perfil (Sprint 2.3).

Cobre rotas protegidas por ROUTE_PERMISSIONS (rotas legadas, app.py) e por
checagem manual usuario_admin()/usuario_logado() (API JSON), validando as
combinacoes 200/401/403/404 conforme sessao e perfil.

Perfis validos no sistema: admin, tecnico, vendedor (ver DATABASE.md e
ENGINEERING_GUIDE.md) — nao existe perfil "atendente". O caso "usuario sem
permissao" e coberto com tecnico/vendedor tentando rotas admin-only, e com
um perfil desconhecido gravado diretamente no banco (fora da validacao da
propria aplicacao) tentando uma rota admin-only, para confirmar que a
checagem de autorizacao nao depende de uma lista fechada de perfis validos.
"""

import uuid

from werkzeug.security import generate_password_hash

import app as _app


def _login_legado(client, usuario):
    return client.post("/login", data={"usuario": usuario["usuario"], "senha": usuario["senha"]})


def _criar_os_minima():
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO os (tipo, cliente, status) VALUES (?, ?, ?)",
            ("Assistencia", "Cliente Teste", "Aberto"),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _remover_os(os_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM os WHERE id = ?", (os_id,))
        conn.commit()
    finally:
        conn.close()


# ============================================================================
# Rotas legadas admin-only — /usuarios, /usuarios/editar, /usuarios/deletar
# (/usuarios/novo ja tem cobertura de tecnico em test_auth.py)
# ============================================================================


class TestPermissoesListagemLegada:
    """
    GET /usuarios e um path conhecido de LEGACY_REACT_REDIRECTS (app.py): toda
    requisicao GET/HEAD para ele e desviada para /app/usuarios antes mesmo do
    before_request de autenticacao rodar — o mesmo padrao ja documentado em
    test_auth.py::TestLegacyLogin.test_get_login_ja_autenticado_ainda_redireciona_para_spa
    para /login. Por isso o redirecionamento e identico com ou sem sessao: a
    guarda de acesso real acontece no SPA (/app/usuarios) e na API
    (/api/usuarios, ver TestListarUsuarios em test_users.py).
    """

    def test_sem_sessao_redireciona_para_spa(self, client):
        resp = client.get("/usuarios")

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app/usuarios"

    def test_vendedor_tambem_redireciona_para_spa(self, client, usuario_vendedor):
        _login_legado(client, usuario_vendedor)

        resp = client.get("/usuarios")

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app/usuarios"

    def test_admin_tambem_redireciona_para_spa(self, client, usuario_admin):
        _login_legado(client, usuario_admin)

        resp = client.get("/usuarios")

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app/usuarios"


class TestPermissoesEditarUsuarioLegado:
    def test_sem_sessao_redireciona_para_login(self, client, usuario_tecnico):
        resp = client.post(
            f"/usuarios/editar/{usuario_tecnico['id']}",
            data={"nome": "Tentativa", "perfil": "tecnico", "ativo": "on"},
        )

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app/login"

    def test_vendedor_recebe_acesso_negado_e_nao_altera_dados(self, client, usuario_vendedor, usuario_tecnico):
        _login_legado(client, usuario_vendedor)

        resp = client.post(
            f"/usuarios/editar/{usuario_tecnico['id']}",
            data={"nome": "Nao Deveria Mudar", "perfil": "admin", "ativo": "on"},
        )

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app"
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT nome, perfil FROM usuarios WHERE id = ?", (usuario_tecnico["id"],)).fetchone()
        finally:
            conn.close()
        assert row[0] == usuario_tecnico["nome"]
        assert row[1] == "tecnico"

    def test_admin_edita_com_sucesso(self, client, usuario_admin, usuario_tecnico):
        _login_legado(client, usuario_admin)

        resp = client.post(
            f"/usuarios/editar/{usuario_tecnico['id']}",
            data={"nome": "Editado Pelo Admin", "perfil": "tecnico", "ativo": "on"},
        )

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/usuarios"
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT nome FROM usuarios WHERE id = ?", (usuario_tecnico["id"],)).fetchone()
        finally:
            conn.close()
        assert row[0] == "Editado Pelo Admin"


class TestPermissoesDeletarUsuarioLegado:
    def test_sem_sessao_redireciona_para_login(self, client, usuario_tecnico):
        resp = client.post(f"/usuarios/deletar/{usuario_tecnico['id']}")

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app/login"

    def test_tecnico_recebe_acesso_negado_e_nao_remove(self, client, usuario_tecnico, usuario_vendedor):
        _login_legado(client, usuario_tecnico)

        resp = client.post(f"/usuarios/deletar/{usuario_vendedor['id']}")

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/app"
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT id FROM usuarios WHERE id = ?", (usuario_vendedor["id"],)).fetchone()
        finally:
            conn.close()
        assert row is not None

    def test_admin_remove_com_sucesso(self, client, usuario_admin):
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

        _login_legado(client, usuario_admin)
        resp = client.post(f"/usuarios/deletar/{uid}")

        assert resp.status_code == 302
        assert resp.headers["Location"] == "/usuarios"
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT id FROM usuarios WHERE id = ?", (uid,)).fetchone()
        finally:
            conn.close()
        assert row is None


# ============================================================================
# Perfil desconhecido — defesa contra dados fora da whitelist da aplicacao
# ============================================================================


class TestPermissaoPerfilDesconhecido:
    """
    A aplicacao normaliza qualquer perfil fora de {admin, tecnico, vendedor}
    para "tecnico" ao CRIAR/EDITAR usuarios (ver irflow_blueprints_auth.py e
    irflow_blueprints_api.py). Este teste confirma que, mesmo que um registro
    com perfil fora dessa whitelist exista no banco (por exemplo, dado legado
    ou editado fora da aplicacao), a checagem de autorizacao admin-only
    continua negando acesso — ela compara literalmente contra "admin", nao
    contra uma lista de perfis validos.
    """

    def test_perfil_desconhecido_no_banco_recebe_acesso_negado(self, client, login_como):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO usuarios (nome, usuario, senha_hash, perfil, ativo) VALUES (?, ?, ?, ?, ?)",
                (
                    "Perfil Legado",
                    f"perfil_legado_{uuid.uuid4().hex[:8]}",
                    generate_password_hash("senha_teste_123"),
                    "gerente",
                    1,
                ),
            )
            conn.commit()
            uid = cursor.lastrowid
            usuario_txt = conn.execute("SELECT usuario FROM usuarios WHERE id = ?", (uid,)).fetchone()[0]
        finally:
            conn.close()

        usuario = {"usuario": usuario_txt, "senha": "senha_teste_123"}
        login_resp = login_como(client, usuario)
        assert login_resp.status_code == 200

        resp = client.get("/api/usuarios")

        assert resp.status_code == 403
        conn = _app.conectar()
        try:
            conn.execute("DELETE FROM usuarios WHERE id = ?", (uid,))
            conn.commit()
        finally:
            conn.close()


# ============================================================================
# Matriz de status codes (200/401/404) — GET /api/ordens/<id>
# ============================================================================


class TestMatrizStatusCodesOrdens:
    """
    /api/ordens/<id> exige apenas sessao ativa (qualquer perfil) — usado aqui
    para cobrir 200/401/404 de forma complementar aos 403 ja exercitados nas
    rotas admin-only de usuarios acima.
    """

    def test_sem_sessao_retorna_401(self, client):
        os_id = _criar_os_minima()
        try:
            resp = client.get(f"/api/ordens/{os_id}")
            assert resp.status_code == 401
        finally:
            _remover_os(os_id)

    def test_autenticado_com_os_existente_retorna_200(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        os_id = _criar_os_minima()
        try:
            resp = client.get(f"/api/ordens/{os_id}")
            assert resp.status_code == 200
            assert resp.get_json()["ok"] is True
        finally:
            _remover_os(os_id)

    def test_autenticado_com_os_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)

        resp = client.get("/api/ordens/9999999")

        assert resp.status_code == 404
        assert resp.get_json()["ok"] is False
