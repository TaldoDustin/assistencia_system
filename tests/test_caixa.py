"""
Testes do domínio Caixa (Financeiro Mínimo, BR-067 a BR-069,
docs/engineering/plans/PLAN-financeiro-minimo.md).

Escopo: fluxoly_caixa_service.py -- CRUD de movimentação manual, saldo, e o
hook de Vendas (registrar_entrada_de_venda/estornar_entrada_de_venda)
exercitado através de fluxoly_vendas_service.iniciar_venda/cancelar_venda
reais -- não uma chamada solta do hook -- para provar o comportamento real
da integração aprovada no plano.
"""

import sqlite3
import uuid

import pytest

import app as _app
import fluxoly_caixa_repository as caixa_repo
import fluxoly_caixa_service as caixa_service
import fluxoly_vendas_service as vendas_service

USUARIO_ID_TESTE = 999001


def _criar_cliente():
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (nome, telefone) VALUES (?, ?)",
            (f"Cliente Caixa {uuid.uuid4().hex[:8]}", "11999998888"),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _criar_item_estoque_rastreavel():
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO estoque (descricao, valor, fornecedor, quantidade, modelo, sku, tipo, qualidade, requer_imei)
            VALUES (?,?,?,?,?,?,?,?,1)
            """,
            (
                "iPhone Teste Caixa",
                3000.0,
                "Fornecedor Teste",
                1,
                "iPhone 13",
                f"SKU-{uuid.uuid4().hex[:8]}",
                "Aparelho",
                "Novo",
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _criar_unidade_disponivel(estoque_id):
    imei = "".join(str((int(uuid.uuid4().hex[:1], 16) + i) % 10) for i in range(15))
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


def _criar_tipo_garantia():
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tipos_garantia (nome, duracao_meses) VALUES (?, ?)",
            (f"Garantia Teste Caixa {uuid.uuid4().hex[:8]}", 12),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _limpar_venda(venda_id, item_id, unidade_id, cliente_id, estoque_id, tipo_garantia_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade='venda' AND entidade_id=?", (venda_id,))
        if item_id:
            conn.execute("DELETE FROM audit_log WHERE entidade='venda_item' AND entidade_id=?", (item_id,))
        conn.execute(
            "DELETE FROM audit_log WHERE entidade='movimentacao_caixa' AND entidade_id IN "
            "(SELECT id FROM movimentacoes_caixa WHERE origem='venda' AND origem_id=?)",
            (venda_id,),
        )
        conn.execute("DELETE FROM movimentacoes_caixa WHERE origem='venda' AND origem_id=?", (venda_id,))
        conn.execute("DELETE FROM vendas_itens WHERE venda_id=?", (venda_id,))
        conn.execute("DELETE FROM vendas WHERE id=?", (venda_id,))
        conn.execute("DELETE FROM unidades_serializadas WHERE id=?", (unidade_id,))
        conn.execute("DELETE FROM estoque WHERE id=?", (estoque_id,))
        conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
        conn.execute("DELETE FROM tipos_garantia WHERE id=?", (tipo_garantia_id,))
        conn.commit()
    finally:
        conn.close()


def _limpar_movimentacao(movimentacao_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade='movimentacao_caixa' AND entidade_id=?", (movimentacao_id,))
        conn.execute("DELETE FROM movimentacoes_caixa WHERE id=?", (movimentacao_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def venda_pronta():
    """Venda real, criada via fluxoly_vendas_service.iniciar_venda -- exercita
    o hook de caixa (BR-069) pelo caminho de produção, não uma chamada solta."""
    cliente_id = _criar_cliente()
    estoque_id = _criar_item_estoque_rastreavel()
    unidade_id = _criar_unidade_disponivel(estoque_id)
    tipo_garantia_id = _criar_tipo_garantia()
    valor = 3000.0

    venda_id, erro = vendas_service.iniciar_venda(
        _app.conectar,
        USUARIO_ID_TESTE,
        cliente_id,
        unidade_id,
        "pix",
        valor,
        tipo_garantia_id,
    )
    assert erro is None, erro

    conn = _app.conectar()
    try:
        row = conn.execute("SELECT id FROM vendas_itens WHERE venda_id=?", (venda_id,)).fetchone()
        item_id = row[0] if row else None
    finally:
        conn.close()

    yield {
        "venda_id": venda_id,
        "item_id": item_id,
        "cliente_id": cliente_id,
        "unidade_id": unidade_id,
        "estoque_id": estoque_id,
        "tipo_garantia_id": tipo_garantia_id,
        "valor": valor,
    }

    _limpar_venda(venda_id, item_id, unidade_id, cliente_id, estoque_id, tipo_garantia_id)


class TestHookDeVendas:
    def test_venda_concluida_cria_entrada_de_caixa(self, venda_pronta):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            row = caixa_repo.buscar_ativa_por_origem(cursor, "venda", venda_pronta["venda_id"])
        finally:
            conn.close()

        assert row is not None
        assert row[1] == "entrada"
        assert row[2] == venda_pronta["valor"]
        assert row[4] == "venda"
        assert row[5] == venda_pronta["venda_id"]
        assert row[6] == 0

    def test_idempotencia_chamar_hook_direto_duas_vezes_nao_duplica(self, venda_pronta):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            id1 = caixa_service.registrar_entrada_de_venda(
                cursor, venda_pronta["venda_id"], venda_pronta["valor"], USUARIO_ID_TESTE
            )
            conn.commit()
            id2 = caixa_service.registrar_entrada_de_venda(
                cursor, venda_pronta["venda_id"], venda_pronta["valor"], USUARIO_ID_TESTE
            )
            conn.commit()
            assert id1 == id2

            cursor.execute(
                "SELECT COUNT(*) FROM movimentacoes_caixa WHERE origem='venda' AND origem_id=? AND estornada=0",
                (venda_pronta["venda_id"],),
            )
            assert cursor.fetchone()[0] == 1
        finally:
            conn.close()

    def test_indice_unico_rejeita_segunda_entrada_ativa_direto_no_banco(self, venda_pronta):
        """Prova o guardião real de BR-069 no banco -- um INSERT direto que
        ignore a checagem de aplicação ainda é rejeitado pelo índice único
        parcial `idx_movimentacoes_caixa_venda_ativa`."""
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            with pytest.raises(sqlite3.IntegrityError):
                cursor.execute(
                    "INSERT INTO movimentacoes_caixa (tipo, valor, origem, origem_id) "
                    "VALUES ('entrada', 1.0, 'venda', ?)",
                    (venda_pronta["venda_id"],),
                )
        finally:
            conn.rollback()
            conn.close()

    def test_cancelamento_estorna_entrada_sem_apagar(self, venda_pronta):
        sucesso, erro = vendas_service.cancelar_venda(
            _app.conectar,
            venda_pronta["venda_id"],
            USUARIO_ID_TESTE,
            "admin",
            "cliente_desistiu",
        )
        assert sucesso, erro

        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT estornada FROM movimentacoes_caixa WHERE origem='venda' AND origem_id=?",
                (venda_pronta["venda_id"],),
            )
            row = cursor.fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row[0] == 1

    def test_estorno_some_do_saldo(self, venda_pronta):
        saldo_antes = caixa_service.obter_saldo(_app.conectar)
        sucesso, erro = vendas_service.cancelar_venda(
            _app.conectar,
            venda_pronta["venda_id"],
            USUARIO_ID_TESTE,
            "admin",
            "cliente_desistiu",
        )
        assert sucesso, erro
        saldo_depois = caixa_service.obter_saldo(_app.conectar)
        assert saldo_depois == pytest.approx(saldo_antes - venda_pronta["valor"])

    def test_estornar_venda_ja_cancelada_e_idempotente_no_hook(self, venda_pronta):
        vendas_service.cancelar_venda(
            _app.conectar,
            venda_pronta["venda_id"],
            USUARIO_ID_TESTE,
            "admin",
            "cliente_desistiu",
        )
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            caixa_service.estornar_entrada_de_venda(cursor, venda_pronta["venda_id"], USUARIO_ID_TESTE)
            conn.commit()
        finally:
            conn.close()


class TestSaldo:
    def test_saldo_soma_entradas_e_subtrai_saidas_nao_estornadas(self):
        saldo_antes = caixa_service.obter_saldo(_app.conectar)
        id_entrada, erro1 = caixa_service.criar_movimentacao_manual(
            _app.conectar, USUARIO_ID_TESTE, "entrada", 500.0, "Teste entrada"
        )
        id_saida, erro2 = caixa_service.criar_movimentacao_manual(
            _app.conectar, USUARIO_ID_TESTE, "saida", 200.0, "Teste saida"
        )
        assert erro1 is None
        assert erro2 is None

        saldo_depois = caixa_service.obter_saldo(_app.conectar)
        assert saldo_depois == pytest.approx(saldo_antes + 500.0 - 200.0)

        _limpar_movimentacao(id_entrada)
        _limpar_movimentacao(id_saida)

    def test_movimentacao_estornada_nao_conta_no_saldo(self):
        saldo_antes = caixa_service.obter_saldo(_app.conectar)
        id_entrada, _erro = caixa_service.criar_movimentacao_manual(
            _app.conectar, USUARIO_ID_TESTE, "entrada", 300.0, "Teste"
        )
        caixa_service.estornar_movimentacao_manual(_app.conectar, USUARIO_ID_TESTE, id_entrada)

        saldo_depois = caixa_service.obter_saldo(_app.conectar)
        assert saldo_depois == pytest.approx(saldo_antes)

        _limpar_movimentacao(id_entrada)


class TestMovimentacaoManualCRUD:
    def test_criar_movimentacao_manual_valida(self):
        movimentacao_id, erro = caixa_service.criar_movimentacao_manual(
            _app.conectar, USUARIO_ID_TESTE, "entrada", 100.0, "Teste"
        )
        assert erro is None
        assert movimentacao_id is not None
        _limpar_movimentacao(movimentacao_id)

    def test_tipo_invalido_retorna_erro(self):
        movimentacao_id, erro = caixa_service.criar_movimentacao_manual(
            _app.conectar, USUARIO_ID_TESTE, "invalido", 100.0
        )
        assert movimentacao_id is None
        assert erro

    def test_valor_zero_ou_negativo_retorna_erro(self):
        movimentacao_id, erro = caixa_service.criar_movimentacao_manual(_app.conectar, USUARIO_ID_TESTE, "entrada", 0)
        assert movimentacao_id is None
        assert erro

    def test_estornar_movimentacao_ja_estornada_retorna_erro(self):
        movimentacao_id, _erro = caixa_service.criar_movimentacao_manual(
            _app.conectar, USUARIO_ID_TESTE, "entrada", 50.0
        )
        caixa_service.estornar_movimentacao_manual(_app.conectar, USUARIO_ID_TESTE, movimentacao_id)
        sucesso, erro = caixa_service.estornar_movimentacao_manual(_app.conectar, USUARIO_ID_TESTE, movimentacao_id)
        assert not sucesso
        assert erro
        _limpar_movimentacao(movimentacao_id)

    def test_listar_movimentacoes_pagina_resultado(self):
        movimentacao_id, _erro = caixa_service.criar_movimentacao_manual(
            _app.conectar, USUARIO_ID_TESTE, "entrada", 75.0, "Teste listagem"
        )
        resultado = caixa_service.listar_movimentacoes(
            _app.conectar, tipo="entrada", origem="manual", page=1, per_page=50
        )
        ids = [item["id"] for item in resultado["items"]]
        assert movimentacao_id in ids
        _limpar_movimentacao(movimentacao_id)
