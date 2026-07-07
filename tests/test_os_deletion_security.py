"""
Testes de exclusão e segurança de Ordens de Serviço via API JSON (Sprint 2.4).

Escopo: DELETE /api/ordens/<id>, resiliência de entrada em POST/PUT/PATCH.

Achado relevante: DELETE /api/ordens/<id> não tem nenhuma restrição por
perfil (qualquer usuário autenticado — admin, tecnico ou vendedor — pode
excluir qualquer OS, inclusive Finalizada) e não retorna 404 para id
inexistente (responde 200 ok silenciosamente, mesmo padrão já visto em
/api/usuarios na Sprint 2.3). Estes testes caracterizam esse comportamento
tal como ele é hoje — não é uma regra que esta sprint deva alterar.
"""

import app as _app


def _os_existe(os_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT 1 FROM os WHERE id=?", (os_id,)).fetchone() is not None
    finally:
        conn.close()


def _quantidade_estoque(item_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT quantidade FROM estoque WHERE id=?", (item_id,)).fetchone()[0]
    finally:
        conn.close()


# ============================================================================
# DELETE /api/ordens/<id>
# ============================================================================


class TestExcluirOrdem:
    def test_exclusao_valida_remove_a_os(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os()

        resp = client.delete(f"/api/ordens/{os_id}")

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        assert not _os_existe(os_id)

    def test_exclusao_devolve_pecas_ao_estoque_quando_os_esta_em_andamento(
        self, client, login_como, usuario_tecnico, criar_os, criar_item_estoque, payload_os_valido
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=1)
        os_id = criar_os(modelo="iPhone 13", status="Em andamento")
        client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(modelo="iPhone 13", pecas_ids=[peca], status="Em andamento"),
        )
        assert _quantidade_estoque(peca) == 0

        client.delete(f"/api/ordens/{os_id}")

        assert _quantidade_estoque(peca) == 1

    def test_exclusao_nao_devolve_pecas_quando_os_ja_finalizada(
        self, client, login_como, usuario_tecnico, criar_os, criar_item_estoque, payload_os_valido
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=1)
        os_id = criar_os(modelo="iPhone 13", status="Em andamento")
        client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(modelo="iPhone 13", pecas_ids=[peca], status="Finalizado"),
        )
        assert _quantidade_estoque(peca) == 0

        client.delete(f"/api/ordens/{os_id}")

        assert _quantidade_estoque(peca) == 0

    def test_exclusao_de_os_finalizada_e_permitida(self, client, login_como, usuario_tecnico, criar_os):
        """Não existe proteção contra excluir uma OS Finalizada neste sistema."""
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Finalizado")

        resp = client.delete(f"/api/ordens/{os_id}")

        assert resp.status_code == 200
        assert not _os_existe(os_id)

    def test_exclusao_inexistente_retorna_200_sem_erro(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)

        resp = client.delete("/api/ordens/9999999")

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_exclusao_sem_sessao_retorna_401(self, client, criar_os):
        os_id = criar_os()
        resp = client.delete(f"/api/ordens/{os_id}")
        assert resp.status_code == 401
        assert _os_existe(os_id)

    def test_tecnico_pode_excluir_qualquer_os(self, client, login_como, usuario_tecnico, criar_os):
        """Caracterização: não há restrição por perfil para excluir OS (diferente de /api/usuarios)."""
        login_como(client, usuario_tecnico)
        os_id = criar_os()

        resp = client.delete(f"/api/ordens/{os_id}")

        assert resp.status_code == 200
        assert not _os_existe(os_id)

    def test_vendedor_pode_excluir_qualquer_os(self, client, login_como, usuario_vendedor, criar_os):
        login_como(client, usuario_vendedor)
        os_id = criar_os()

        resp = client.delete(f"/api/ordens/{os_id}")

        assert resp.status_code == 200
        assert not _os_existe(os_id)


# ============================================================================
# Parâmetros inválidos (roteamento)
# ============================================================================


class TestParametrosInvalidos:
    def test_id_nao_numerico_em_get_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/ordens/abc")
        assert resp.status_code == 404

    def test_id_nao_numerico_em_delete_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.delete("/api/ordens/abc")
        assert resp.status_code == 404

    def test_id_negativo_em_get_retorna_404(self, client, login_como, usuario_tecnico):
        """O conversor <int:os_id> do Flask não aceita sinal negativo — 404 de roteamento."""
        login_como(client, usuario_tecnico)
        resp = client.get("/api/ordens/-1")
        assert resp.status_code == 404


# ============================================================================
# SQL Injection
# ============================================================================


class TestSqlInjection:
    def test_string_maliciosa_no_cliente_e_armazenada_como_texto_literal(
        self, client, login_como, usuario_tecnico, payload_os_valido
    ):
        login_como(client, usuario_tecnico)
        payload_malicioso = payload_os_valido(cliente="Robert'); DROP TABLE os; --")

        resp = client.post("/api/ordens", json=payload_malicioso)

        assert resp.status_code == 201
        os_id = resp.get_json()["os_id"]
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT cliente FROM os WHERE id=?", (os_id,)).fetchone()
            total_os = conn.execute("SELECT COUNT(*) FROM os").fetchone()[0]
        finally:
            conn.close()
        assert row[0] == "Robert'); DROP TABLE os; --"
        assert total_os >= 1

        conn = _app.conectar()
        conn.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os WHERE id=?", (os_id,))
        conn.commit()
        conn.close()

    def test_injecao_no_filtro_de_busca_nao_quebra_a_listagem(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)

        resp = client.get("/api/ordens", query_string={"q": "' OR '1'='1", "status": "'; DROP TABLE os; --"})

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True

    def test_injecao_no_campo_observacoes_e_armazenada_como_texto_literal(
        self, client, login_como, usuario_tecnico, payload_os_valido
    ):
        login_como(client, usuario_tecnico)
        texto_malicioso = "x' OR '1'='1"

        resp = client.post("/api/ordens", json=payload_os_valido(observacoes=texto_malicioso))

        os_id = resp.get_json()["os_id"]
        conn = _app.conectar()
        try:
            row = conn.execute("SELECT observacoes FROM os WHERE id=?", (os_id,)).fetchone()
        finally:
            conn.close()
        assert row[0] == texto_malicioso

        conn = _app.conectar()
        conn.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os WHERE id=?", (os_id,))
        conn.commit()
        conn.close()


# ============================================================================
# Payload vazio / JSON inválido
# ============================================================================


class TestPayloadInvalido:
    def test_criar_ordem_payload_vazio_retorna_400(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/ordens", json={})
        assert resp.status_code == 400

    def test_criar_ordem_json_malformado_retorna_400_nao_500(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/ordens", data="{tipo: sem aspas}", content_type="application/json")
        assert resp.status_code == 400

    def test_criar_ordem_sem_corpo_retorna_400_nao_500(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/ordens")
        assert resp.status_code == 400

    def test_atualizar_ordem_payload_vazio_retorna_400(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.put(f"/api/ordens/{os_id}", json={})
        assert resp.status_code == 400

    def test_atualizar_status_json_malformado_retorna_400_nao_500(
        self, client, login_como, usuario_tecnico, criar_os
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.patch(
            f"/api/ordens/{os_id}/status", data="{status:}", content_type="application/json"
        )
        assert resp.status_code == 400

    def test_atualizar_status_payload_vazio_retorna_400(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.patch(f"/api/ordens/{os_id}/status", json={})
        assert resp.status_code == 400

    def test_exclusao_ignora_corpo_invalido(self, client, login_como, usuario_tecnico, criar_os):
        """DELETE /api/ordens/<id> não lê o corpo da requisição — payload malformado não importa."""
        login_como(client, usuario_tecnico)
        os_id = criar_os()

        resp = client.delete(f"/api/ordens/{os_id}", data="{isso nao e json}", content_type="application/json")

        assert resp.status_code == 200
        assert not _os_existe(os_id)
