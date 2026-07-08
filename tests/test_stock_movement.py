"""
Testes de movimentação de estoque via API JSON (Sprint 2.5).

Escopo: PUT /api/estoque/<id> (ajustes de quantidade), GET /api/estoque/movimentacoes.

Regra de isolamento desta sprint: nenhum teste depende da ordem cronológica
das movimentações globais. GET /api/estoque/movimentacoes retorna sempre as
últimas 30 movimentações do sistema inteiro (sem filtro por item — ver
relatório final da sprint) — o volume de movimentações produzido por outros
testes na mesma sessão está fora do controle de qualquer teste individual.
Por isso, saldo/histórico por item são sempre verificados via consulta
direta ao banco filtrada por estoque_id (nunca via esse endpoint global), e
o próprio endpoint só é testado quanto à forma da resposta, não ao
conteúdo específico.

Não existe um tipo de movimentação dedicado a "perda" — um ajuste negativo
via PUT é o mecanismo real para registrar perda, quebra ou extravio; é
isso que os testes de saída cobrem.
"""

import app as _app


def _saldo(item_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT quantidade FROM estoque WHERE id=?", (item_id,)).fetchone()[0]
    finally:
        conn.close()


def _movimentacoes_do_item(item_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT tipo, quantidade FROM movimentacoes WHERE estoque_id=? ORDER BY id", (item_id,)
        ).fetchall()
    finally:
        conn.close()


def _lotes_do_item(item_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT quantidade, quantidade_disponivel FROM estoque_lotes WHERE estoque_id=? ORDER BY id",
            (item_id,),
        ).fetchall()
    finally:
        conn.close()


def _payload_base(item_id, **overrides):
    conn = _app.conectar()
    try:
        row = conn.execute(
            "SELECT descricao, valor, modelo, fornecedor FROM estoque WHERE id=?", (item_id,)
        ).fetchone()
    finally:
        conn.close()
    payload = {"descricao": row[0], "valor": row[1], "modelo": row[2], "fornecedor": row[3]}
    payload.update(overrides)
    return payload


# ============================================================================
# Entrada — ajuste positivo via PUT
# ============================================================================


class TestEntradaEstoque:
    def test_ajuste_positivo_registra_movimentacao_entrada(
        self, client, login_como, usuario_tecnico, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(quantidade=2)

        resp = client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=5))

        assert resp.status_code == 200
        assert _saldo(item_id) == 5
        assert _movimentacoes_do_item(item_id)[-1] == ("entrada", 3)

    def test_ajuste_positivo_cria_novo_lote(self, client, login_como, usuario_tecnico, criar_item_estoque):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(quantidade=1)
        lotes_antes = len(_lotes_do_item(item_id))

        client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=4))

        assert len(_lotes_do_item(item_id)) == lotes_antes + 1


# ============================================================================
# Saída — ajuste negativo via PUT (mecanismo de perda/quebra/extravio)
# ============================================================================


class TestSaidaEstoque:
    def test_ajuste_negativo_registra_movimentacao_saida_correta(
        self, client, login_como, usuario_tecnico, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(quantidade=5)

        resp = client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=2))

        assert resp.status_code == 200
        assert _saldo(item_id) == 2
        assert _movimentacoes_do_item(item_id)[-1] == ("saida", 3)

    def test_ajuste_negativo_consome_lotes_em_ordem_fifo(self, client, login_como, usuario_tecnico, criar_item_estoque):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(quantidade=0)
        client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=2))  # lote 1: +2
        client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=5))  # lote 2: +3

        client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=3))  # -2: consome todo o lote 1

        lotes = _lotes_do_item(item_id)
        assert lotes[0][1] == 0
        assert lotes[1][1] == 3

    def test_quantidade_muito_negativa_nunca_deixa_saldo_abaixo_de_zero(
        self, client, login_como, usuario_tecnico, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(quantidade=3)

        resp = client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=-100))

        assert resp.status_code == 200
        assert _saldo(item_id) == 0

    def test_quantidade_muito_negativa_registra_saida_igual_ao_saldo_real(
        self, client, login_como, usuario_tecnico, criar_item_estoque
    ):
        """Regressão do hotfix 584c501 — saida registrada deve refletir o saldo real consumido, não o valor bruto enviado."""
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(quantidade=3)

        client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=-100))

        assert _movimentacoes_do_item(item_id)[-1] == ("saida", 3)


# ============================================================================
# Saldo final após sequência de ajustes
# ============================================================================


class TestSaldoFinal:
    def test_saldo_final_apos_sequencia_de_entradas_e_saidas(
        self, client, login_como, usuario_tecnico, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(quantidade=10)

        client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=15))  # +5
        client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=8))  # -7
        client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=12))  # +4

        assert _saldo(item_id) == 12
        tipos = [m[0] for m in _movimentacoes_do_item(item_id)]
        assert tipos == ["entrada", "saida", "entrada"]

    def test_ajuste_para_o_mesmo_valor_nao_gera_movimentacao(
        self, client, login_como, usuario_tecnico, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(quantidade=7)
        total_antes = len(_movimentacoes_do_item(item_id))

        client.put(f"/api/estoque/{item_id}", json=_payload_base(item_id, quantidade=7))

        assert len(_movimentacoes_do_item(item_id)) == total_antes


# ============================================================================
# GET /api/estoque/movimentacoes — forma da resposta (sem depender de ordem global)
# ============================================================================


class TestHistoricoMovimentacoesGlobal:
    def test_sem_sessao_retorna_401(self, client):
        resp = client.get("/api/estoque/movimentacoes")
        assert resp.status_code == 401

    def test_resposta_tem_formato_esperado_e_respeita_limite(
        self, client, login_como, usuario_tecnico, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        criar_item_estoque(quantidade=1)  # garante ao menos 1 movimentacao no sistema

        resp = client.get("/api/estoque/movimentacoes")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["ok"] is True
        assert isinstance(body["movimentacoes"], list)
        assert len(body["movimentacoes"]) <= 30
        if body["movimentacoes"]:
            chaves_esperadas = {"id", "estoque_id", "tipo", "quantidade", "data", "descricao"}
            assert chaves_esperadas <= set(body["movimentacoes"][0].keys())
