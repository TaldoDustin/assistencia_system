"""
Testes de segurança e exclusão de itens de estoque via API JSON (Sprint 2.5).

Escopo: sem sessão, sem permissão, payload inválido, JSON inválido,
SQL injection, Content-Type incorreto, DELETE /api/estoque/<id>.

Achado histórico (Sprint 2.5, resolvido em 2026-07-25 — Sprint Segurança 1.0,
docs/security/SECURITY_AUDIT_2026-07.md): a API não restringia mutação de
Estoque por perfil, diferente da rota legada POST /estoque/deletar/<id>
(ROUTE_PERMISSIONS, admin only). Corrigido: rotas de mutação de Estoque
(POST/PUT/DELETE /api/estoque*) agora exigem perfil admin ou estoque — ver
TestPermissaoPorPerfil abaixo.
"""

import json

import app as _app


def _item_existe(item_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT 1 FROM estoque WHERE id=?", (item_id,)).fetchone() is not None
    finally:
        conn.close()


def _payload_os_minimo(reparo_padrao_id, pecas_ids=None):
    return {
        "tipo": "Assistencia",
        "cliente": "Cliente Teste",
        "modelo": "iPhone 13",
        "tecnico": "ISAQUE SOUZA",
        "vendedor": "Camila",
        "reparo_ids": [reparo_padrao_id],
        "pecas_ids": pecas_ids or [],
    }


def _limpar_os(os_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM os_pecas WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os WHERE id=?", (os_id,))
        conn.commit()
    finally:
        conn.close()


# ============================================================================
# Sem sessão
# ============================================================================


class TestSemSessao:
    def test_atualizar_sem_sessao_retorna_401(self, client, criar_item_estoque):
        item_id = criar_item_estoque()
        resp = client.put(f"/api/estoque/{item_id}", json={"descricao": "X", "valor": 10, "quantidade": 1})
        assert resp.status_code == 401

    def test_deletar_sem_sessao_retorna_401(self, client, criar_item_estoque):
        item_id = criar_item_estoque()
        resp = client.delete(f"/api/estoque/{item_id}")
        assert resp.status_code == 401
        assert _item_existe(item_id)


# ============================================================================
# DELETE /api/estoque/<id>
# ============================================================================


class TestExcluirItemEstoque:
    def test_exclusao_valida_remove_o_item(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        item_id = criar_item_estoque()

        resp = client.delete(f"/api/estoque/{item_id}")

        assert resp.status_code == 200
        assert not _item_existe(item_id)

    def test_exclusao_bloqueada_quando_peca_em_uso_em_os_aberta(
        self, client, login_como, usuario_admin, reparo_padrao_id, criar_item_estoque
    ):
        # admin: unico perfil com acesso a OS (admin/tecnico) e Estoque (admin/estoque)
        login_como(client, usuario_admin)
        item_id = criar_item_estoque(modelo="iPhone 13", quantidade=1)
        os_id = client.post("/api/ordens", json=_payload_os_minimo(reparo_padrao_id, [item_id])).get_json()["os_id"]

        resp = client.delete(f"/api/estoque/{item_id}")

        assert resp.status_code == 400
        assert _item_existe(item_id)
        _limpar_os(os_id)

    def test_exclusao_permitida_quando_os_esta_finalizada(
        self, client, login_como, usuario_admin, reparo_padrao_id, criar_item_estoque, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_admin)
        item_id = criar_item_estoque(modelo="iPhone 13", quantidade=1)
        os_id = client.post("/api/ordens", json=_payload_os_minimo(reparo_padrao_id, [item_id])).get_json()["os_id"]
        client.patch(
            f"/api/ordens/{os_id}/status",
            json={"status": "Finalizado", "garantias": {str(reparo_padrao_id): tipo_garantia_padrao_id}},
        )

        resp = client.delete(f"/api/estoque/{item_id}")

        assert resp.status_code == 200
        assert not _item_existe(item_id)
        _limpar_os(os_id)

    def test_exclusao_inexistente_retorna_200_sem_erro(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.delete("/api/estoque/9999999")
        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True


class TestPermissaoPorPerfil:
    """Sprint Segurança 1.0 (2026-07-25): POST/PUT/DELETE /api/estoque* agora exigem
    perfil admin ou estoque — decisão do usuário (CTO), docs/security/SECURITY_AUDIT_2026-07.md."""

    def test_admin_pode_excluir_item_de_estoque(self, client, login_como, usuario_admin, criar_item_estoque):
        login_como(client, usuario_admin)
        item_id = criar_item_estoque()

        resp = client.delete(f"/api/estoque/{item_id}")

        assert resp.status_code == 200
        assert not _item_existe(item_id)

    def test_tecnico_nao_pode_excluir_item_de_estoque(self, client, login_como, usuario_tecnico, criar_item_estoque):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque()

        resp = client.delete(f"/api/estoque/{item_id}")

        assert resp.status_code == 403
        assert _item_existe(item_id)

    def test_vendedor_nao_pode_excluir_item_de_estoque(self, client, login_como, usuario_vendedor, criar_item_estoque):
        login_como(client, usuario_vendedor)
        item_id = criar_item_estoque()

        resp = client.delete(f"/api/estoque/{item_id}")

        assert resp.status_code == 403
        assert _item_existe(item_id)

    def test_tecnico_nao_pode_criar_item_de_estoque(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/estoque", json={"descricao": "Peca", "valor": 10, "quantidade": 1})
        assert resp.status_code == 403


# ============================================================================
# Payload vazio / JSON inválido
# ============================================================================


class TestPayloadInvalido:
    def test_criar_payload_vazio_retorna_400(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.post("/api/estoque", json={})
        assert resp.status_code == 400

    def test_criar_sem_corpo_retorna_400_nao_500(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.post("/api/estoque")
        assert resp.status_code == 400

    def test_criar_json_malformado_retorna_400_nao_500(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.post("/api/estoque", data="{descricao: sem aspas}", content_type="application/json")
        assert resp.status_code == 400

    def test_atualizar_payload_vazio_retorna_400(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        item_id = criar_item_estoque()
        resp = client.put(f"/api/estoque/{item_id}", json={})
        assert resp.status_code == 400

    def test_atualizar_item_inexistente_retorna_404(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.put("/api/estoque/9999999", json={"descricao": "X", "valor": 10, "quantidade": 1})
        assert resp.status_code == 404

    def test_atualizar_json_malformado_retorna_400_nao_500(self, client, login_como, usuario_estoque, criar_item_estoque):
        login_como(client, usuario_estoque)
        item_id = criar_item_estoque()
        resp = client.put(f"/api/estoque/{item_id}", data="{invalido", content_type="application/json")
        assert resp.status_code == 400


# ============================================================================
# Content-Type incorreto
# ============================================================================


class TestContentTypeIncorreto:
    def test_form_urlencoded_nao_e_interpretado_como_json(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.post("/api/estoque", data={"descricao": "Peca", "valor": "10", "quantidade": "1"})
        assert resp.status_code == 400

    def test_json_valido_com_content_type_text_plain_retorna_400(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)
        resp = client.post(
            "/api/estoque",
            data=json.dumps({"descricao": "Peca", "valor": 10, "quantidade": 1}),
            content_type="text/plain",
        )
        assert resp.status_code == 400


# ============================================================================
# SQL Injection
# ============================================================================


class TestSqlInjection:
    def test_string_maliciosa_na_descricao_e_armazenada_como_texto_literal(
        self, client, login_como, usuario_estoque
    ):
        login_como(client, usuario_estoque)
        texto_malicioso = "Tela'); DROP TABLE estoque; --"

        resp = client.post("/api/estoque", json={"descricao": texto_malicioso, "valor": 10, "quantidade": 1})

        assert resp.status_code == 201
        item_id = resp.get_json()["id"]
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT descricao FROM estoque WHERE id=?", (item_id,)).fetchone()
            total = conn.execute("SELECT COUNT(*) FROM estoque").fetchone()[0]
        finally:
            conn.close()
        assert row[0] == texto_malicioso
        assert total >= 1
        conn = _app.conectar()
        conn.execute("DELETE FROM estoque WHERE id=?", (item_id,))
        conn.commit()
        conn.close()

    def test_string_maliciosa_no_fornecedor_e_armazenada_como_texto_literal(
        self, client, login_como, usuario_estoque
    ):
        login_como(client, usuario_estoque)
        texto_malicioso = "x' OR '1'='1"

        resp = client.post(
            "/api/estoque", json={"descricao": "Peca", "valor": 10, "quantidade": 1, "fornecedor": texto_malicioso}
        )

        item_id = resp.get_json()["id"]
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT fornecedor FROM estoque WHERE id=?", (item_id,)).fetchone()
        finally:
            conn.close()
        assert row[0] == texto_malicioso
        conn = _app.conectar()
        conn.execute("DELETE FROM estoque WHERE id=?", (item_id,))
        conn.commit()
        conn.close()

    def test_injecao_no_filtro_de_busca_nao_quebra_a_listagem(self, client, login_como, usuario_estoque):
        login_como(client, usuario_estoque)

        resp = client.get("/api/estoque", query_string={"q": "' OR '1'='1", "modelo": "'; DROP TABLE estoque; --"})

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
