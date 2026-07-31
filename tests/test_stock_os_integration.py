"""
Testes de integração Estoque × Ordem de Serviço (Sprint 2.5).

Escopo: consumo automático de peças ao criar/editar OS (POST/PUT
/api/ordens), devolução ao estoque (cancelamento via PATCH .../status,
exclusão via DELETE), alteração/remoção/substituição de peças numa OS já
existente, concorrência entre OS pelo mesmo item, e compatibilidade de
peça por modelo (modelo_compativel em irflow_os.py).

Cria e limpa suas próprias Ordens de Serviço via API (não usa um fixture
de bypass do banco) — é exatamente o caminho de integração real sendo
testado.
"""

import uuid

import app as _app


def _payload_os(reparo_padrao_id, **overrides):
    payload = {
        "tipo": "Assistencia",
        "cliente": f"Cliente {uuid.uuid4().hex[:6]}",
        "modelo": "iPhone 13",
        "tecnico": "ISAQUE SOUZA",
        "vendedor": "Camila",
        "reparo_ids": [reparo_padrao_id],
    }
    payload.update(overrides)
    return payload


def _limpar_os(os_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM os_pecas WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os_checklists WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os WHERE id=?", (os_id,))
        conn.commit()
    finally:
        conn.close()


def _saldo(item_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT quantidade FROM estoque WHERE id=?", (item_id,)).fetchone()[0]
    finally:
        conn.close()


def _pecas_da_os(os_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT estoque_id FROM os_pecas WHERE os_id=?", (os_id,)).fetchall()
    finally:
        conn.close()


# ============================================================================
# Consumo automático ao criar OS
# ============================================================================


class TestConsumoAutomatico:
    def test_criar_os_com_peca_consome_uma_unidade_do_estoque(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=3)

        resp = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca]))

        assert resp.status_code == 201
        assert _saldo(peca) == 2
        _limpar_os(resp.get_json()["os_id"])

    def test_criar_os_com_multiplas_pecas_consome_todas(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca_a = criar_item_estoque(modelo="iPhone 13", quantidade=2)
        peca_b = criar_item_estoque(modelo="iPhone 13", quantidade=2)

        resp = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca_a, peca_b]))

        assert resp.status_code == 201
        assert _saldo(peca_a) == 1
        assert _saldo(peca_b) == 1
        _limpar_os(resp.get_json()["os_id"])

    def test_criar_os_sem_pecas_nao_afeta_estoque(self, client, login_como, usuario_tecnico, reparo_padrao_id):
        login_como(client, usuario_tecnico)

        resp = client.post("/api/ordens", json=_payload_os(reparo_padrao_id))

        assert resp.status_code == 201
        _limpar_os(resp.get_json()["os_id"])


# ============================================================================
# Mesma peça em mais de uma OS / concorrência sequencial
# ============================================================================


class TestMesmaPecaEmMultiplasOS:
    def test_duas_os_consomem_a_mesma_peca_enquanto_ha_estoque(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=2)

        resp1 = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca]))
        resp2 = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca]))

        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert _saldo(peca) == 0
        _limpar_os(resp1.get_json()["os_id"])
        _limpar_os(resp2.get_json()["os_id"])

    def test_terceira_os_falha_quando_a_peca_se_esgota(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=1)

        resp1 = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca]))
        resp2 = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca]))

        assert resp1.status_code == 201
        assert resp2.status_code == 400
        assert _saldo(peca) == 0
        _limpar_os(resp1.get_json()["os_id"])


# ============================================================================
# Cancelamento e exclusão devolvem ao estoque
# ============================================================================


class TestDevolucaoAoEstoque:
    def test_cancelar_os_via_status_devolve_peca_ao_estoque(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=1)
        os_id = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca])).get_json()["os_id"]
        assert _saldo(peca) == 0

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Cancelado"})

        assert resp.status_code == 200
        assert _saldo(peca) == 1
        _limpar_os(os_id)

    def test_excluir_os_em_andamento_devolve_peca_ao_estoque(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=1)
        os_id = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca])).get_json()["os_id"]

        resp = client.delete(f"/api/ordens/{os_id}")

        assert resp.status_code == 200
        assert _saldo(peca) == 1

    def test_excluir_os_finalizada_nao_devolve_peca(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=1)
        os_id = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca])).get_json()["os_id"]
        client.patch(
            f"/api/ordens/{os_id}/status",
            json={"status": "Finalizado", "garantias": {str(reparo_padrao_id): tipo_garantia_padrao_id}},
        )
        assert _saldo(peca) == 0

        client.delete(f"/api/ordens/{os_id}")

        assert _saldo(peca) == 0


# ============================================================================
# Alteração, remoção e substituição de peças numa OS existente
# ============================================================================


class TestAlteracaoDePecasNaOS:
    def test_editar_os_repetindo_peca_consome_uma_unidade_a_mais(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=5)
        os_id = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca])).get_json()["os_id"]
        assert _saldo(peca) == 4

        resp = client.put(
            f"/api/ordens/{os_id}",
            json=_payload_os(reparo_padrao_id, pecas_ids=[peca, peca], status="Em andamento"),
        )

        assert resp.status_code == 200
        assert _saldo(peca) == 3
        assert len(_pecas_da_os(os_id)) == 2
        _limpar_os(os_id)

    def test_editar_os_removendo_peca_devolve_ao_estoque(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=3)
        os_id = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca])).get_json()["os_id"]
        assert _saldo(peca) == 2

        resp = client.put(
            f"/api/ordens/{os_id}", json=_payload_os(reparo_padrao_id, pecas_ids=[], status="Em andamento")
        )

        assert resp.status_code == 200
        assert _saldo(peca) == 3
        assert _pecas_da_os(os_id) == []
        _limpar_os(os_id)

    def test_editar_os_substituindo_peca_por_outra(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca_antiga = criar_item_estoque(modelo="iPhone 13", quantidade=2)
        peca_nova = criar_item_estoque(modelo="iPhone 13", quantidade=2)
        os_id = client.post(
            "/api/ordens", json=_payload_os(reparo_padrao_id, pecas_ids=[peca_antiga])
        ).get_json()["os_id"]
        assert _saldo(peca_antiga) == 1

        resp = client.put(
            f"/api/ordens/{os_id}",
            json=_payload_os(reparo_padrao_id, pecas_ids=[peca_nova], status="Em andamento"),
        )

        assert resp.status_code == 200
        assert _saldo(peca_antiga) == 2
        assert _saldo(peca_nova) == 1
        _limpar_os(os_id)


# ============================================================================
# Compatibilidade de peça por modelo
# ============================================================================


class TestCompatibilidade:
    def test_peca_universal_sem_modelo_e_compativel_com_qualquer_os(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca_universal = criar_item_estoque(modelo="", quantidade=1)

        resp = client.post(
            "/api/ordens", json=_payload_os(reparo_padrao_id, modelo="iPhone 15 Pro Max", pecas_ids=[peca_universal])
        )

        assert resp.status_code == 201
        assert _saldo(peca_universal) == 0
        _limpar_os(resp.get_json()["os_id"])

    def test_peca_especifica_compativel_com_modelo_correspondente(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 13", quantidade=1)

        resp = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, modelo="iPhone 13", pecas_ids=[peca]))

        assert resp.status_code == 201
        _limpar_os(resp.get_json()["os_id"])

    def test_peca_incompativel_com_modelo_diferente_bloqueia_consumo(
        self, client, login_como, usuario_tecnico, reparo_padrao_id, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        peca = criar_item_estoque(modelo="iPhone 8", quantidade=1)

        resp = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, modelo="iPhone 15", pecas_ids=[peca]))

        assert resp.status_code == 400
        assert _saldo(peca) == 1

    def test_atualizar_modelo_da_peca_via_put_muda_compatibilidade_futura(
        self, client, login_como, usuario_admin, reparo_padrao_id, criar_item_estoque
    ):
        """Editar o modelo de uma peça (PUT /api/estoque/<id>) muda o resultado de modelo_compativel() em consumos futuros."""
        # admin: unico perfil com acesso a OS (admin/tecnico) e Estoque (admin/estoque) ao mesmo tempo
        login_como(client, usuario_admin)
        peca = criar_item_estoque(modelo="iPhone 8", quantidade=2)

        bloqueado = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, modelo="iPhone 13", pecas_ids=[peca]))
        assert bloqueado.status_code == 400

        client.put(
            f"/api/estoque/{peca}",
            json={"descricao": "Peca Teste", "valor": 50.0, "modelo": "iPhone 13", "quantidade": 2},
        )

        permitido = client.post("/api/ordens", json=_payload_os(reparo_padrao_id, modelo="iPhone 13", pecas_ids=[peca]))
        assert permitido.status_code == 201
        _limpar_os(permitido.get_json()["os_id"])
