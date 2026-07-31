"""
Testes do cadastro Tipos de Garantia (V1.5 -- Garantia, BR-055,
docs/engineering/plans/PLAN-V1.5-Garantia.md).

Escopo: GET/POST/PUT /api/tipos-garantia -- CRUD simples (sem DELETE, usar
`ativo=0`), restrito a `admin` para escrita, leitura aberta a qualquer
autenticado. Cadastro compartilhado entre Vendas (Garantia de Venda) e
Assistência (Garantia de Reparo) -- nenhum dos dois é dono.
"""

import uuid

import app as _app


def _limpar_tipo_garantia(tipo_garantia_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM tipos_garantia WHERE id=?", (tipo_garantia_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_tipo_garantia(client, **overrides):
    payload = {"nome": f"Tipo Garantia Teste {uuid.uuid4().hex[:8]}", "duracao_meses": 12}
    payload.update(overrides)
    return client.post("/api/tipos-garantia", json=payload)


class TestListarTiposGarantia:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/tipos-garantia")
        assert resp.status_code == 401

    def test_listagem_aberta_a_qualquer_autenticado(self, client, login_como, usuario_tecnico, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_tipo_garantia(client)
        tipo_garantia_id = criado.get_json()["id"]
        try:
            login_como(client, usuario_tecnico)
            resp = client.get("/api/tipos-garantia")
            assert resp.status_code == 200
            assert any(t["id"] == tipo_garantia_id for t in resp.get_json()["items"])
        finally:
            _limpar_tipo_garantia(tipo_garantia_id)

    def test_inativo_nao_aparece_por_padrao(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_tipo_garantia(client)
        tipo_garantia_id = criado.get_json()["id"]
        try:
            client.put(f"/api/tipos-garantia/{tipo_garantia_id}", json={"nome": "X", "duracao_meses": 12, "ativo": False})
            resp = client.get("/api/tipos-garantia")
            assert all(t["id"] != tipo_garantia_id for t in resp.get_json()["items"])
        finally:
            _limpar_tipo_garantia(tipo_garantia_id)

    def test_admin_pode_incluir_inativos(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        criado = _criar_tipo_garantia(client)
        tipo_garantia_id = criado.get_json()["id"]
        try:
            client.put(f"/api/tipos-garantia/{tipo_garantia_id}", json={"nome": "X", "duracao_meses": 12, "ativo": False})
            resp = client.get("/api/tipos-garantia?incluir_inativos=1")
            assert any(t["id"] == tipo_garantia_id for t in resp.get_json()["items"])
        finally:
            _limpar_tipo_garantia(tipo_garantia_id)

    def test_nao_admin_ignora_incluir_inativos(self, client, login_como, usuario_admin, usuario_tecnico):
        """Mesmo enviando o parâmetro, um perfil não-admin nunca vê
        inativos -- só a tela de cadastro (admin) precisa dessa visão."""
        login_como(client, usuario_admin)
        criado = _criar_tipo_garantia(client)
        tipo_garantia_id = criado.get_json()["id"]
        try:
            client.put(f"/api/tipos-garantia/{tipo_garantia_id}", json={"nome": "X", "duracao_meses": 12, "ativo": False})
            login_como(client, usuario_tecnico)
            resp = client.get("/api/tipos-garantia?incluir_inativos=1")
            assert all(t["id"] != tipo_garantia_id for t in resp.get_json()["items"])
        finally:
            _limpar_tipo_garantia(tipo_garantia_id)


class TestCriarTipoGarantia:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/api/tipos-garantia", json={"nome": "X", "duracao_meses": 12})
        assert resp.status_code == 401

    def test_vendedor_nao_pode_criar(self, client, login_como, usuario_vendedor):
        login_como(client, usuario_vendedor)
        resp = _criar_tipo_garantia(client)
        assert resp.status_code == 403

    def test_admin_cria_com_sucesso(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = _criar_tipo_garantia(client)
        assert resp.status_code == 201
        _limpar_tipo_garantia(resp.get_json()["id"])

    def test_nome_vazio_retorna_400(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = _criar_tipo_garantia(client, nome="")
        assert resp.status_code == 400

    def test_duracao_negativa_retorna_400(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = _criar_tipo_garantia(client, duracao_meses=-1)
        assert resp.status_code == 400

    def test_duracao_zero_e_aceita(self, client, login_como, usuario_admin):
        """BR-055 -- 0 meses representa "sem garantia", uma política que a
        loja pode cadastrar, nunca obrigatória."""
        login_como(client, usuario_admin)
        resp = _criar_tipo_garantia(client, duracao_meses=0)
        assert resp.status_code == 201
        _limpar_tipo_garantia(resp.get_json()["id"])


class TestAtualizarTipoGarantia:
    def test_vendedor_nao_pode_atualizar(self, client, login_como, usuario_admin, usuario_vendedor):
        login_como(client, usuario_admin)
        tipo_garantia_id = _criar_tipo_garantia(client).get_json()["id"]
        try:
            login_como(client, usuario_vendedor)
            resp = client.put(
                f"/api/tipos-garantia/{tipo_garantia_id}", json={"nome": "Y", "duracao_meses": 6}
            )
            assert resp.status_code == 403
        finally:
            _limpar_tipo_garantia(tipo_garantia_id)

    def test_admin_atualiza_com_sucesso(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        tipo_garantia_id = _criar_tipo_garantia(client).get_json()["id"]
        try:
            resp = client.put(
                f"/api/tipos-garantia/{tipo_garantia_id}", json={"nome": "Seminovo 6m", "duracao_meses": 6}
            )
            assert resp.status_code == 200
            item = next(t for t in client.get("/api/tipos-garantia").get_json()["items"] if t["id"] == tipo_garantia_id)
            assert item["nome"] == "Seminovo 6m"
            assert item["duracao_meses"] == 6
        finally:
            _limpar_tipo_garantia(tipo_garantia_id)

    def test_tipo_garantia_inexistente_retorna_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.put("/api/tipos-garantia/999999", json={"nome": "Y", "duracao_meses": 6})
        assert resp.status_code == 404
