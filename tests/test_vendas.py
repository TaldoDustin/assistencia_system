"""
Testes do domínio Vendas MVP (docs/product/features/VENDAS.md,
docs/operations/SPRINTS/SPRINT_COMERCIAL_VENDAS_MVP.md).

Escopo: POST/GET /api/vendas. Venda de um único aparelho (unidade
serializada) por vez, sem desconto/comissão/garantia/troca/reserva com
timeout -- dependem de decisões de negócio ainda pendentes do Product Owner.

O teste mais importante desta suíte é a corrida real (threads, não só
chamada sequencial): duas vendas concorrentes da mesma unidade nunca podem
ambas ter sucesso -- garantido em duas camadas (UNIQUE em
vendas_itens.unidade_serializada_id + WHERE status='disponivel' no UPDATE
de marcar_como_vendida), a mesma classe de proteção que faltou no INC-002.
"""

import threading
import uuid

import pytest

import app as _app
import fluxoly_vendas_repository as vendas_repo
import irflow_unidades_serializadas_service as unidades_service

SENHA_PADRAO = "senha_teste_123"


def _criar_cliente(**overrides):
    dados = {"nome": f"Cliente Teste {uuid.uuid4().hex[:8]}", "telefone": "11999998888"}
    dados.update(overrides)
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (nome, telefone) VALUES (?, ?)",
            (dados["nome"], dados["telefone"]),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _limpar_cliente(cliente_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_item_estoque_rastreavel(**overrides):
    dados = {
        "descricao": "iPhone 13 Seminovo",
        "valor": 3000.0,
        "fornecedor": "Fornecedor Teste",
        "quantidade": 1,
        "modelo": "iPhone 13",
        "sku": f"SKU-{uuid.uuid4().hex[:8]}",
        "tipo": "Aparelho",
        "qualidade": "Novo",
    }
    dados.update(overrides)
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO estoque (descricao, valor, fornecedor, quantidade, modelo, sku, tipo, qualidade, requer_imei)
            VALUES (?,?,?,?,?,?,?,?,1)
            """,
            (
                dados["descricao"], dados["valor"], dados["fornecedor"], dados["quantidade"],
                dados["modelo"], dados["sku"], dados["tipo"], dados["qualidade"],
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _criar_unidade_disponivel(estoque_id, imei=None):
    imei = imei or "".join(str((int(uuid.uuid4().hex[:1], 16) + i) % 10) for i in range(15))
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO unidades_serializadas (estoque_id, imei, status) VALUES (?, ?, 'disponivel')",
            (estoque_id, imei),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _status_unidade(unidade_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT status FROM unidades_serializadas WHERE id=?", (unidade_id,)).fetchone()[0]
    finally:
        conn.close()


def _limpar_tudo(cliente_id=None, estoque_id=None, unidade_id=None):
    conn = _app.conectar()
    try:
        if unidade_id:
            venda_ids = [
                row[0]
                for row in conn.execute(
                    "SELECT DISTINCT venda_id FROM vendas_itens WHERE unidade_serializada_id=?", (unidade_id,)
                ).fetchall()
            ]
            for venda_id in venda_ids:
                conn.execute("DELETE FROM audit_log WHERE entidade='venda' AND entidade_id=?", (venda_id,))
            conn.execute("DELETE FROM vendas_itens WHERE unidade_serializada_id=?", (unidade_id,))
            if venda_ids:
                conn.execute(
                    f"DELETE FROM vendas WHERE id IN ({','.join('?' * len(venda_ids))})", venda_ids
                )
            conn.execute("DELETE FROM audit_log WHERE entidade='unidade_serializada' AND entidade_id=?", (unidade_id,))
            conn.execute("DELETE FROM unidades_serializadas WHERE id=?", (unidade_id,))
        if estoque_id:
            conn.execute("DELETE FROM estoque WHERE id=?", (estoque_id,))
        if cliente_id:
            conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def cenario_venda():
    """Cliente + item de estoque rastreável + unidade disponível, prontos
    para uma venda. Limpa tudo ao final, inclusive a venda/item se criados."""
    cliente_id = _criar_cliente()
    estoque_id = _criar_item_estoque_rastreavel()
    unidade_id = _criar_unidade_disponivel(estoque_id)
    yield {"cliente_id": cliente_id, "estoque_id": estoque_id, "unidade_id": unidade_id}
    _limpar_tudo(cliente_id, estoque_id, unidade_id)


def _payload(cenario, **overrides):
    base = {
        "cliente_id": cenario["cliente_id"],
        "unidade_serializada_id": cenario["unidade_id"],
        "forma_pagamento": "pix",
        "valor_unitario": 3200.0,
    }
    base.update(overrides)
    return base


class TestCriarVenda:
    def test_sem_autenticacao_retorna_401(self, client, cenario_venda):
        resp = client.post("/api/vendas", json=_payload(cenario_venda))
        assert resp.status_code == 401

    def test_tecnico_nao_pode_vender(self, client, login_como, usuario_tecnico, cenario_venda):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/vendas", json=_payload(cenario_venda))
        assert resp.status_code == 403

    def test_vendedor_pode_vender(self, client, login_como, usuario_vendedor, cenario_venda):
        login_como(client, usuario_vendedor)
        resp = client.post("/api/vendas", json=_payload(cenario_venda))
        assert resp.status_code == 201

    def test_criacao_valida_persiste_venda_item_e_marca_unidade_vendida(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        login_como(client, usuario_admin)

        resp = client.post("/api/vendas", json=_payload(cenario_venda))

        assert resp.status_code == 201
        venda_id = resp.get_json()["id"]

        conn = _app.conectar()
        try:
            venda = conn.execute(
                "SELECT cliente_id, vendedor_id, forma_pagamento, valor_total, status FROM vendas WHERE id=?",
                (venda_id,),
            ).fetchone()
            item = conn.execute(
                "SELECT unidade_serializada_id, produto_nome, produto_sku, quantidade, valor_unitario, subtotal "
                "FROM vendas_itens WHERE venda_id=?",
                (venda_id,),
            ).fetchone()
        finally:
            conn.close()

        assert venda[0] == cenario_venda["cliente_id"]
        assert venda[2] == "pix"
        assert venda[3] == 3200.0
        assert venda[4] == "concluida"

        assert item[0] == cenario_venda["unidade_id"]
        assert item[1] == "iPhone 13"  # snapshot: origem_label vem do modelo do estoque
        assert item[2]  # snapshot de SKU presente
        assert item[3] == 1
        assert item[4] == 3200.0
        assert item[5] == 3200.0

        assert _status_unidade(cenario_venda["unidade_id"]) == "vendido"

    def test_cliente_inexistente_retorna_404(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, cliente_id=999999))
        assert resp.status_code == 404

    def test_unidade_inexistente_retorna_404(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, unidade_serializada_id=999999))
        assert resp.status_code == 404

    def test_unidade_ja_vendida_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        primeira = client.post("/api/vendas", json=_payload(cenario_venda))
        assert primeira.status_code == 201

        segunda = client.post("/api/vendas", json=_payload(cenario_venda))
        assert segunda.status_code == 400

    def test_forma_pagamento_invalida_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, forma_pagamento="boleto"))
        assert resp.status_code == 400
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

    def test_valor_zero_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, valor_unitario=0))
        assert resp.status_code == 400
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

    def test_erro_na_criacao_do_item_causa_rollback_unidade_continua_disponivel(
        self, client, login_como, usuario_admin, cenario_venda, monkeypatch
    ):
        """Prova de atomicidade: uma exceção real dentro da transação (após a
        venda já ter sido inserida, antes da unidade ser marcada) reverte
        tudo -- nenhuma venda órfã, unidade continua disponível."""

        def _falha(*args, **kwargs):
            raise RuntimeError("falha simulada na criação do item")

        monkeypatch.setattr(vendas_repo, "inserir_item", _falha)
        login_como(client, usuario_admin)

        resp = client.post("/api/vendas", json=_payload(cenario_venda))

        assert resp.status_code in (400, 500)
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

        conn = _app.conectar()
        try:
            vendas_do_cliente = conn.execute(
                "SELECT COUNT(*) FROM vendas WHERE cliente_id=?", (cenario_venda["cliente_id"],)
            ).fetchone()[0]
            vendas_da_unidade = conn.execute(
                "SELECT COUNT(*) FROM vendas_itens WHERE unidade_serializada_id=?",
                (cenario_venda["unidade_id"],),
            ).fetchone()[0]
        finally:
            conn.close()
        assert vendas_do_cliente == 0
        assert vendas_da_unidade == 0

    def test_erro_em_marcar_como_vendida_causa_rollback_sem_venda_orfa(
        self, client, login_como, usuario_admin, cenario_venda, monkeypatch
    ):
        """Segunda variação da prova de atomicidade: a exceção ocorre no passo
        seguinte da transação (INSERT venda e INSERT item já rodaram, sem
        commit, quando a marcação da unidade falha) -- mesmo resultado, nada
        persiste."""

        def _falha(*args, **kwargs):
            raise RuntimeError("falha simulada em marcar_como_vendida")

        monkeypatch.setattr(unidades_service, "marcar_como_vendida", _falha)
        login_como(client, usuario_admin)

        resp = client.post("/api/vendas", json=_payload(cenario_venda))

        assert resp.status_code in (400, 500)
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

        conn = _app.conectar()
        try:
            vendas_do_cliente = conn.execute(
                "SELECT COUNT(*) FROM vendas WHERE cliente_id=?", (cenario_venda["cliente_id"],)
            ).fetchone()[0]
            vendas_da_unidade = conn.execute(
                "SELECT COUNT(*) FROM vendas_itens WHERE unidade_serializada_id=?",
                (cenario_venda["unidade_id"],),
            ).fetchone()[0]
        finally:
            conn.close()
        assert vendas_do_cliente == 0
        assert vendas_da_unidade == 0

    def test_patch_status_generico_continua_rejeitando_vendido(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        """Prova de que a rota genérica de transição não abriu uma porta
        lateral para 'vendido' -- só fluxoly_vendas_service.py pode chegar lá."""
        login_como(client, usuario_admin)
        resp = client.patch(
            f"/api/unidades-serializadas/{cenario_venda['unidade_id']}/status",
            json={"status": "vendido"},
        )
        assert resp.status_code == 400
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

    def test_duas_vendas_concorrentes_mesma_unidade_so_uma_sucede(
        self, app, login_como, usuario_vendedor, cenario_venda
    ):
        client_a = app.test_client()
        client_b = app.test_client()
        login_como(client_a, usuario_vendedor)
        login_como(client_b, usuario_vendedor)

        payload = _payload(cenario_venda)
        resultados = {}

        def _post(nome, client):
            resultados[nome] = client.post("/api/vendas", json=payload)

        t_a = threading.Thread(target=_post, args=("a", client_a))
        t_b = threading.Thread(target=_post, args=("b", client_b))
        t_a.start()
        t_b.start()
        t_a.join()
        t_b.join()

        codigos = sorted(r.status_code for r in resultados.values())
        assert codigos == [201, 400]
        assert _status_unidade(cenario_venda["unidade_id"]) == "vendido"

        conn = _app.conectar()
        try:
            total_itens = conn.execute(
                "SELECT COUNT(*) FROM vendas_itens WHERE unidade_serializada_id=?",
                (cenario_venda["unidade_id"],),
            ).fetchone()[0]
        finally:
            conn.close()
        assert total_itens == 1


class TestObterVenda:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/vendas/1")
        assert resp.status_code == 401

    def test_venda_inexistente_retorna_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.get("/api/vendas/999999")
        assert resp.status_code == 404

    def test_obter_venda_existente(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        resp = client.get(f"/api/vendas/{venda_id}")

        assert resp.status_code == 200
        payload = resp.get_json()["venda"]
        assert payload["id"] == venda_id
        assert payload["status"] == "concluida"
        assert payload["forma_pagamento"] == "pix"
