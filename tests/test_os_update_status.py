"""
Testes de atualização e transição de status de Ordens de Serviço via API JSON
(Sprint 2.4).

Escopo: PUT /api/ordens/<id> e PATCH /api/ordens/<id>/status.

Não existe máquina de estados para status neste sistema — a partir de
qualquer status atual, tanto PUT quanto PATCH aceitam qualquer um dos 4
status válidos (Em andamento, Aguardando peca, Finalizado, Cancelado), sem
restrição de origem. "Transição inválida" aqui significa apenas um valor de
status desconhecido/lixo — que, após os fixes desta sprint (commits
c85a321 e e755f25), é rejeitado com 400 em ambas as rotas. Antes desses
fixes, um status desconhecido era silenciosamente normalizado para "Em
andamento" (ver commits para detalhes e reprodução).
"""

import app as _app

STATUS_VALIDOS = ["Em andamento", "Aguardando peca", "Finalizado", "Cancelado"]


def _obter_status_e_finalizado(os_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT status, COALESCE(data_finalizado,'') FROM os WHERE id=?", (os_id,)
        ).fetchone()
    finally:
        conn.close()


_COLUNAS_CONSULTAVEIS = {"cliente", "tecnico", "observacoes", "modelo", "aparelho"}


def _obter_campo(os_id, campo):
    assert campo in _COLUNAS_CONSULTAVEIS
    conn = _app.conectar()
    try:
        return conn.execute(f"SELECT {campo} FROM os WHERE id=?", (os_id,)).fetchone()[0]
    finally:
        conn.close()


def _quantidade_estoque(item_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT quantidade FROM estoque WHERE id=?", (item_id,)).fetchone()[0]
    finally:
        conn.close()


# ============================================================================
# PUT /api/ordens/<id> — atualização de dados
# ============================================================================


class TestAtualizarOrdem:
    def test_atualizar_dados_basicos_com_sucesso(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()

        resp = client.put(
            f"/api/ordens/{os_id}", json=payload_os_valido(cliente="Cliente Atualizado", status="Em andamento")
        )

        assert resp.status_code == 200
        assert _obter_campo(os_id, "cliente") == "Cliente Atualizado"

    def test_alterar_tecnico(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os(tecnico="ISAQUE SOUZA")

        client.put(f"/api/ordens/{os_id}", json=payload_os_valido(tecnico="RUAM SOARES", status="Em andamento"))

        assert _obter_campo(os_id, "tecnico") == "RUAM SOARES"

    def test_alterar_observacoes(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()

        client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(observacoes="Cliente pediu para revisar a câmera também.", status="Em andamento"),
        )

        assert _obter_campo(os_id, "observacoes") == "Cliente pediu para revisar a câmera também."

    def test_alterar_modelo_equipamento(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os(modelo="iPhone 11")

        client.put(f"/api/ordens/{os_id}", json=payload_os_valido(modelo="iPhone 15 Pro", status="Em andamento"))

        assert _obter_campo(os_id, "modelo") == "iPhone 15 Pro"
        assert _obter_campo(os_id, "aparelho") == "iPhone 15 Pro"

    def test_atualizar_ordem_inexistente_retorna_404(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)

        resp = client.put("/api/ordens/9999999", json=payload_os_valido(status="Em andamento"))

        assert resp.status_code == 404

    def test_atualizar_sem_sessao_retorna_401(self, client, criar_os, payload_os_valido):
        os_id = criar_os()
        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(status="Em andamento"))
        assert resp.status_code == 401


class TestAtualizarOrdemAlteracaoInvalida:
    def test_sem_status_retorna_400(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        payload = payload_os_valido()
        payload.pop("status", None)

        resp = client.put(f"/api/ordens/{os_id}", json=payload)

        assert resp.status_code == 400

    def test_status_desconhecido_retorna_400(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()

        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(status="lixo_invalido_xyz"))

        assert resp.status_code == 400

    def test_sem_tipo_retorna_400(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(tipo="", status="Em andamento"))
        assert resp.status_code == 400

    def test_sem_cliente_retorna_400(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(cliente="", status="Em andamento"))
        assert resp.status_code == 400

    def test_sem_modelo_retorna_400(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(modelo="", status="Em andamento"))
        assert resp.status_code == 400

    def test_sem_tecnico_retorna_400(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(tecnico="", status="Em andamento"))
        assert resp.status_code == 400

    def test_sem_reparo_ids_retorna_400(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(reparo_ids=[], status="Em andamento"))
        assert resp.status_code == 400

    def test_reparo_inexistente_retorna_400(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.put(
            f"/api/ordens/{os_id}", json=payload_os_valido(reparo_ids=[9_999_999], status="Em andamento")
        )
        assert resp.status_code == 400

    def test_vendedor_invalido_retorna_400(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(cliente="Cliente Comum", vendedor="Inexistente", status="Em andamento"),
        )
        assert resp.status_code == 400


class TestAtualizarOrdemDataFinalizado:
    def test_atualizar_para_finalizado_define_data_finalizado(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento")

        client.put(f"/api/ordens/{os_id}", json=payload_os_valido(status="Finalizado"))

        status, data_finalizado = _obter_status_e_finalizado(os_id)
        assert status == "Finalizado"
        assert data_finalizado != ""

    def test_reabrir_finalizada_e_permitido_e_limpa_data_finalizado(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido
    ):
        """
        Não há restrição de transição — reabrir uma OS Finalizada é permitido
        quando o status é enviado explicitamente (diferente do bug corrigido
        no commit e755f25, que reabria mesmo sem o campo ser enviado).
        """
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Finalizado")
        conn = _app.conectar()
        conn.execute("UPDATE os SET data_finalizado=? WHERE id=?", ("2026-01-01", os_id))
        conn.commit()
        conn.close()

        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(status="Em andamento"))

        assert resp.status_code == 200
        status, data_finalizado = _obter_status_e_finalizado(os_id)
        assert status == "Em andamento"
        assert data_finalizado == ""


class TestAtualizarOrdemPecas:
    def test_troca_de_peca_devolve_a_antiga_e_consome_a_nova(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca_antiga = criar_item_estoque(modelo="iPhone 13", quantidade=2)
        peca_nova = criar_item_estoque(modelo="iPhone 13", quantidade=2)
        os_id = criar_os(modelo="iPhone 13")
        client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(modelo="iPhone 13", pecas_ids=[peca_antiga], status="Em andamento"),
        )
        assert _quantidade_estoque(peca_antiga) == 1

        resp = client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(modelo="iPhone 13", pecas_ids=[peca_nova], status="Em andamento"),
        )

        assert resp.status_code == 200
        assert _quantidade_estoque(peca_antiga) == 2
        assert _quantidade_estoque(peca_nova) == 1


# ============================================================================
# PATCH /api/ordens/<id>/status — transições
# ============================================================================


class TestTransicoesDeStatus:
    def test_todas_as_transicoes_entre_status_validos_sao_permitidas(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_tecnico)

        for origem in STATUS_VALIDOS:
            for destino in STATUS_VALIDOS:
                os_id = criar_os(status=origem)

                body = {"status": destino}
                if destino == "Finalizado" and origem != "Finalizado":
                    # BR-061 -- só exige garantia na transição PARA Finalizado.
                    body["garantias"] = {str(reparo_padrao_id): tipo_garantia_padrao_id}
                resp = client.patch(f"/api/ordens/{os_id}/status", json=body)

                assert resp.status_code == 200, f"{origem} -> {destino} deveria ser aceito"
                status_final, _ = _obter_status_e_finalizado(os_id)
                assert status_final == destino

    def test_status_desconhecido_retorna_400_e_nao_altera_estado(
        self, client, login_como, usuario_tecnico, criar_os
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento")

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "lixo_invalido_xyz"})

        assert resp.status_code == 400
        status_final, _ = _obter_status_e_finalizado(os_id)
        assert status_final == "Em andamento"

    def test_status_vazio_retorna_400(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": ""})
        assert resp.status_code == 400

    def test_os_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.patch("/api/ordens/9999999/status", json={"status": "Finalizado"})
        assert resp.status_code == 404

    def test_sem_sessao_retorna_401(self, client, criar_os):
        os_id = criar_os()
        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Finalizado"})
        assert resp.status_code == 401

    def test_definir_o_mesmo_status_atual_e_idempotente(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Aguardando peca")

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Aguardando peca"})

        assert resp.status_code == 200
        status_final, _ = _obter_status_e_finalizado(os_id)
        assert status_final == "Aguardando peca"

    def test_cancelar_devolve_pecas_ao_estoque(
        self, client, login_como, usuario_tecnico, criar_os, criar_item_estoque, payload_os_valido
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=1)
        os_id = criar_os(modelo="iPhone 13")
        client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(modelo="iPhone 13", pecas_ids=[peca], status="Em andamento"),
        )
        assert _quantidade_estoque(peca) == 0

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Cancelado"})

        assert resp.status_code == 200
        assert _quantidade_estoque(peca) == 1

    def test_reativar_de_cancelado_nao_re_consome_estoque_via_api(
        self, client, login_como, usuario_tecnico, criar_os, criar_item_estoque, payload_os_valido
    ):
        """
        Caracterização: diferente da rota legada POST /atualizar_status
        (irflow_blueprints_orders.py), que re-consome peças e valida estoque
        suficiente ao reativar uma OS Cancelada, a rota da API
        (PATCH /api/ordens/<id>/status) não faz nenhum ajuste de estoque ao
        sair do status Cancelado — só ajusta ao ENTRAR em Cancelado. As
        peças devolvidas pelo cancelamento permanecem no estoque.
        """
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=1)
        os_id = criar_os(modelo="iPhone 13")
        client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(modelo="iPhone 13", pecas_ids=[peca], status="Em andamento"),
        )
        client.patch(f"/api/ordens/{os_id}/status", json={"status": "Cancelado"})
        assert _quantidade_estoque(peca) == 1

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Em andamento"})

        assert resp.status_code == 200
        assert _quantidade_estoque(peca) == 1
