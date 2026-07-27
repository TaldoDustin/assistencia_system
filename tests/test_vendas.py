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


def _criar_produto_rastreavel(**overrides):
    dados = {
        "categoria": "iPhone",
        "marca": "Apple",
        "modelo": "iPhone 14",
        "preco_venda": 4500.0,
        "quantidade": 1,
    }
    dados.update(overrides)
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO produtos (categoria, marca, modelo, preco_venda, quantidade, requer_rastreio_unidade)
            VALUES (?,?,?,?,?,1)
            """,
            (dados["categoria"], dados["marca"], dados["modelo"], dados["preco_venda"], dados["quantidade"]),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _limpar_produto(produto_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_unidade_disponivel(estoque_id=None, produto_id=None, imei=None):
    imei = imei or "".join(str((int(uuid.uuid4().hex[:1], 16) + i) % 10) for i in range(15))
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO unidades_serializadas (estoque_id, produto_id, imei, status) VALUES (?, ?, ?, 'disponivel')",
            (estoque_id, produto_id, imei),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _valor_tabela_do_item(unidade_id):
    conn = _app.conectar()
    try:
        row = conn.execute(
            "SELECT vi.valor_tabela, vi.valor_unitario, v.observacoes FROM vendas_itens vi "
            "JOIN vendas v ON v.id = vi.venda_id WHERE vi.unidade_serializada_id=?",
            (unidade_id,),
        ).fetchone()
        return row
    finally:
        conn.close()


def _status_unidade(unidade_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT status FROM unidades_serializadas WHERE id=?", (unidade_id,)).fetchone()[0]
    finally:
        conn.close()


def _limpar_tudo(cliente_id=None, estoque_id=None, unidade_id=None, produto_id=None):
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
        if produto_id:
            conn.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
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
                "SELECT unidade_serializada_id, produto_nome, produto_sku, quantidade, valor_tabela, "
                "valor_unitario, subtotal FROM vendas_itens WHERE venda_id=?",
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
        # valor_tabela (preço de catálogo, estoque.valor=3000) != valor_unitario (preço
        # efetivo da venda, 3200 no payload) -- prova de que o vendedor pode negociar sem
        # um sobrescrever o outro.
        assert item[4] == 3000.0
        assert item[5] == 3200.0
        assert item[6] == 3200.0

        assert _status_unidade(cenario_venda["unidade_id"]) == "vendido"

    def test_valor_tabela_via_origem_produto(self, client, login_como, usuario_admin):
        """valor_tabela também é derivado corretamente quando a unidade tem
        origem em produtos (preco_venda), não só em estoque (valor)."""
        cliente_id = _criar_cliente()
        produto_id = _criar_produto_rastreavel(preco_venda=4500.0)
        unidade_id = _criar_unidade_disponivel(produto_id=produto_id)
        login_como(client, usuario_admin)
        try:
            resp = client.post(
                "/api/vendas",
                json={
                    "cliente_id": cliente_id,
                    "unidade_serializada_id": unidade_id,
                    "forma_pagamento": "pix",
                    "valor_unitario": 4500.0,
                },
            )
            assert resp.status_code == 201
            valor_tabela, valor_unitario, _ = _valor_tabela_do_item(unidade_id)
            assert valor_tabela == 4500.0
            assert valor_unitario == 4500.0
        finally:
            _limpar_tudo(cliente_id, unidade_id=unidade_id, produto_id=produto_id)

    def test_valor_tabela_nulo_quando_item_sem_preco_cadastrado(
        self, client, login_como, usuario_admin
    ):
        """Item de estoque genuinamente sem valor cadastrado (NULL, nunca
        preenchido) -- valor_tabela fica NULL, a venda continua funcionando
        normalmente (não é bloqueante)."""
        cliente_id = _criar_cliente()
        estoque_id = _criar_item_estoque_rastreavel(valor=None)
        unidade_id = _criar_unidade_disponivel(estoque_id=estoque_id)
        login_como(client, usuario_admin)
        try:
            resp = client.post(
                "/api/vendas",
                json={
                    "cliente_id": cliente_id,
                    "unidade_serializada_id": unidade_id,
                    "forma_pagamento": "pix",
                    "valor_unitario": 3200.0,
                },
            )
            assert resp.status_code == 201
            valor_tabela, valor_unitario, _ = _valor_tabela_do_item(unidade_id)
            assert valor_tabela is None
            assert valor_unitario == 3200.0
        finally:
            _limpar_tudo(cliente_id, estoque_id=estoque_id, unidade_id=unidade_id)

    def test_valor_tabela_zero_e_preservado_nao_tratado_como_ausente(
        self, client, login_como, usuario_admin
    ):
        """Prova direta do ajuste pedido: valor=0 é um preço real (ainda que
        incomum), não deve cair no fallback como se estivesse ausente --
        `is not None`, nunca `or`."""
        cliente_id = _criar_cliente()
        estoque_id = _criar_item_estoque_rastreavel(valor=0)
        unidade_id = _criar_unidade_disponivel(estoque_id=estoque_id)
        login_como(client, usuario_admin)
        try:
            resp = client.post(
                "/api/vendas",
                json={
                    "cliente_id": cliente_id,
                    "unidade_serializada_id": unidade_id,
                    "forma_pagamento": "pix",
                    "valor_unitario": 100.0,
                },
            )
            assert resp.status_code == 201
            valor_tabela, _, _ = _valor_tabela_do_item(unidade_id)
            assert valor_tabela == 0
        finally:
            _limpar_tudo(cliente_id, estoque_id=estoque_id, unidade_id=unidade_id)

    def test_observacoes_persistidas(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, observacoes="Retirada amanhã"))
        assert resp.status_code == 201
        _, _, observacoes = _valor_tabela_do_item(cenario_venda["unidade_id"])
        assert observacoes == "Retirada amanhã"

    def test_observacoes_omitidas_persiste_string_vazia(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda))
        assert resp.status_code == 201
        _, _, observacoes = _valor_tabela_do_item(cenario_venda["unidade_id"])
        assert observacoes == ""

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
        venda_id = client.post(
            "/api/vendas", json=_payload(cenario_venda, observacoes="Retirada amanhã")
        ).get_json()["id"]

        resp = client.get(f"/api/vendas/{venda_id}")

        assert resp.status_code == 200
        corpo = resp.get_json()
        venda = corpo["venda"]
        assert venda["id"] == venda_id
        assert venda["status"] == "concluida"
        assert venda["forma_pagamento"] == "pix"
        assert venda["observacoes"] == "Retirada amanhã"

        # itens vem como lista separada, não achatado dentro de venda -- já
        # pensado para múltiplos itens por venda, mesmo com 1 item hoje.
        itens = corpo["itens"]
        assert isinstance(itens, list)
        assert len(itens) == 1
        assert itens[0]["unidade_serializada_id"] == cenario_venda["unidade_id"]
        assert itens[0]["valor_tabela"] == 3000.0
        assert itens[0]["valor_unitario"] == 3200.0

    def test_detalhe_inclui_nomes_de_cliente_vendedor_imei_e_desconto(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        """Sprint Vendas 1.1: o detalhe passa a expor os campos de exibição
        (join) além dos já existentes -- cliente_nome/vendedor_nome na venda,
        imei/desconto em cada item."""
        login_como(client, usuario_admin)
        cliente_nome = client.get(f"/api/clientes/{cenario_venda['cliente_id']}").get_json()["cliente"]["nome"]
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        resp = client.get(f"/api/vendas/{venda_id}")

        assert resp.status_code == 200
        corpo = resp.get_json()
        venda = corpo["venda"]
        assert venda["cliente_nome"] == cliente_nome
        assert venda["vendedor_nome"] == usuario_admin["nome"]

        item = corpo["itens"][0]
        assert len(item["imei"]) == 15
        assert item["desconto"] == round(3000.0 - 3200.0, 2)


def _criar_venda_via_api(client, login_como, usuario, **overrides):
    """Cria cliente + item de estoque rastreável + unidade disponível e
    vende via API, autenticado como `usuario`. Devolve um dict com os ids e
    a resposta da criação, para os testes de listagem/detalhe montarem
    cenários com várias vendas."""
    cliente_id = _criar_cliente(nome=overrides.pop("cliente_nome", None) or f"Cliente Teste {uuid.uuid4().hex[:8]}")
    estoque_id = _criar_item_estoque_rastreavel()
    unidade_id = _criar_unidade_disponivel(estoque_id)
    login_como(client, usuario)
    resp = client.post(
        "/api/vendas",
        json={
            "cliente_id": cliente_id,
            "unidade_serializada_id": unidade_id,
            "forma_pagamento": overrides.pop("forma_pagamento", "pix"),
            "valor_unitario": overrides.pop("valor_unitario", 3200.0),
            **overrides,
        },
    )
    return {
        "cliente_id": cliente_id,
        "estoque_id": estoque_id,
        "unidade_id": unidade_id,
        "venda_id": resp.get_json()["id"] if resp.status_code == 201 else None,
        "resp": resp,
    }


class TestListarVendas:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/vendas")
        assert resp.status_code == 401

    def test_tecnico_pode_listar_historico(
        self, client, login_como, usuario_admin, usuario_tecnico, cenario_venda
    ):
        """A restrição admin/vendedor vale só para criar venda -- o histórico
        (só consulta) é liberado para qualquer perfil autenticado."""
        login_como(client, usuario_admin)
        client.post("/api/vendas", json=_payload(cenario_venda))

        login_como(client, usuario_tecnico)
        resp = client.get("/api/vendas", query_string={"cliente_id": cenario_venda["cliente_id"]})

        assert resp.status_code == 200
        assert resp.get_json()["total"] == 1

    def test_filtro_por_cliente_id_isola_a_venda_certa(self, client, login_como, usuario_admin):
        a = _criar_venda_via_api(client, login_como, usuario_admin)
        b = _criar_venda_via_api(client, login_como, usuario_admin)
        try:
            resp = client.get("/api/vendas", query_string={"cliente_id": a["cliente_id"]})
            corpo = resp.get_json()
            assert corpo["total"] == 1
            assert corpo["items"][0]["id"] == a["venda_id"]
            assert corpo["items"][0]["id"] != b["venda_id"]
        finally:
            _limpar_tudo(a["cliente_id"], a["estoque_id"], a["unidade_id"])
            _limpar_tudo(b["cliente_id"], b["estoque_id"], b["unidade_id"])

    def test_filtro_por_forma_pagamento(self, client, login_como, usuario_admin):
        pix = _criar_venda_via_api(client, login_como, usuario_admin, forma_pagamento="pix")
        dinheiro = _criar_venda_via_api(client, login_como, usuario_admin, forma_pagamento="dinheiro")
        try:
            resp = client.get(
                "/api/vendas",
                query_string={"forma_pagamento": "dinheiro", "cliente_id": dinheiro["cliente_id"]},
            )
            corpo = resp.get_json()
            assert corpo["total"] == 1
            assert corpo["items"][0]["id"] == dinheiro["venda_id"]
            assert corpo["items"][0]["id"] != pix["venda_id"]
        finally:
            _limpar_tudo(pix["cliente_id"], pix["estoque_id"], pix["unidade_id"])
            _limpar_tudo(dinheiro["cliente_id"], dinheiro["estoque_id"], dinheiro["unidade_id"])

    def test_busca_por_termo_nome_do_cliente(self, client, login_como, usuario_admin):
        nome_unico = f"Zeferino {uuid.uuid4().hex[:8]}"
        alvo = _criar_venda_via_api(client, login_como, usuario_admin, cliente_nome=nome_unico)
        outro = _criar_venda_via_api(client, login_como, usuario_admin)
        try:
            resp = client.get("/api/vendas", query_string={"q": "Zeferino"})
            corpo = resp.get_json()
            ids = [v["id"] for v in corpo["items"]]
            assert alvo["venda_id"] in ids
            assert outro["venda_id"] not in ids
        finally:
            _limpar_tudo(alvo["cliente_id"], alvo["estoque_id"], alvo["unidade_id"])
            _limpar_tudo(outro["cliente_id"], outro["estoque_id"], outro["unidade_id"])

    def test_busca_por_termo_imei(self, client, login_como, usuario_admin):
        cliente_id = _criar_cliente()
        estoque_id = _criar_item_estoque_rastreavel()
        imei_unico = "9" * 15
        unidade_id = _criar_unidade_disponivel(estoque_id, imei=imei_unico)
        login_como(client, usuario_admin)
        venda_id = client.post(
            "/api/vendas",
            json={
                "cliente_id": cliente_id,
                "unidade_serializada_id": unidade_id,
                "forma_pagamento": "pix",
                "valor_unitario": 3200.0,
            },
        ).get_json()["id"]
        try:
            resp = client.get("/api/vendas", query_string={"q": imei_unico})
            corpo = resp.get_json()
            assert corpo["total"] == 1
            assert corpo["items"][0]["id"] == venda_id
        finally:
            _limpar_tudo(cliente_id, estoque_id, unidade_id)

    def test_paginacao_e_total(self, client, login_como, usuario_admin):
        cliente_id = _criar_cliente()
        criados = []
        try:
            for _ in range(3):
                estoque_id = _criar_item_estoque_rastreavel()
                unidade_id = _criar_unidade_disponivel(estoque_id)
                login_como(client, usuario_admin)
                venda_id = client.post(
                    "/api/vendas",
                    json={
                        "cliente_id": cliente_id,
                        "unidade_serializada_id": unidade_id,
                        "forma_pagamento": "pix",
                        "valor_unitario": 3200.0,
                    },
                ).get_json()["id"]
                criados.append((estoque_id, unidade_id, venda_id))

            pagina_1 = client.get(
                "/api/vendas", query_string={"cliente_id": cliente_id, "page": 1, "per_page": 2}
            ).get_json()
            pagina_2 = client.get(
                "/api/vendas", query_string={"cliente_id": cliente_id, "page": 2, "per_page": 2}
            ).get_json()

            assert pagina_1["total"] == 3
            assert len(pagina_1["items"]) == 2
            assert pagina_1["page"] == 1
            assert pagina_1["per_page"] == 2
            assert len(pagina_2["items"]) == 1
            ids_das_duas_paginas = {v["id"] for v in pagina_1["items"]} | {v["id"] for v in pagina_2["items"]}
            assert ids_das_duas_paginas == {venda_id for _, _, venda_id in criados}
        finally:
            for estoque_id, unidade_id, _ in criados:
                _limpar_tudo(unidade_id=unidade_id, estoque_id=estoque_id)
            _limpar_tudo(cliente_id=cliente_id)

    def test_ordenacao_recente_e_antigo(self, client, login_como, usuario_admin):
        cliente_id = _criar_cliente()
        criados = []
        try:
            for _ in range(3):
                estoque_id = _criar_item_estoque_rastreavel()
                unidade_id = _criar_unidade_disponivel(estoque_id)
                login_como(client, usuario_admin)
                venda_id = client.post(
                    "/api/vendas",
                    json={
                        "cliente_id": cliente_id,
                        "unidade_serializada_id": unidade_id,
                        "forma_pagamento": "pix",
                        "valor_unitario": 3200.0,
                    },
                ).get_json()["id"]
                criados.append((estoque_id, unidade_id, venda_id))
            ids_em_ordem_de_criacao = [venda_id for _, _, venda_id in criados]

            recente = client.get(
                "/api/vendas", query_string={"cliente_id": cliente_id, "sort": "recente", "per_page": 10}
            ).get_json()
            antigo = client.get(
                "/api/vendas", query_string={"cliente_id": cliente_id, "sort": "antigo", "per_page": 10}
            ).get_json()

            assert [v["id"] for v in recente["items"]] == list(reversed(ids_em_ordem_de_criacao))
            assert [v["id"] for v in antigo["items"]] == ids_em_ordem_de_criacao
        finally:
            for estoque_id, unidade_id, _ in criados:
                _limpar_tudo(unidade_id=unidade_id, estoque_id=estoque_id)
            _limpar_tudo(cliente_id=cliente_id)

    def test_itens_resumo_inclui_desconto_calculado(self, client, login_como, usuario_admin):
        venda = _criar_venda_via_api(client, login_como, usuario_admin, valor_unitario=2800.0)
        try:
            resp = client.get("/api/vendas", query_string={"cliente_id": venda["cliente_id"]})
            item = resp.get_json()["items"][0]["itens_resumo"][0]
            assert item["valor_tabela"] == 3000.0
            assert item["valor_unitario"] == 2800.0
            assert item["desconto"] == 200.0
        finally:
            _limpar_tudo(venda["cliente_id"], venda["estoque_id"], venda["unidade_id"])
