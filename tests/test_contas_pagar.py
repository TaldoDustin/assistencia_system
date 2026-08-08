"""
Testes do domínio Contas a Pagar (Financeiro Mínimo, BR-067 a BR-069,
docs/engineering/plans/PLAN-financeiro-minimo.md).

Escopo: fluxoly_contas_pagar_service.py -- CRUD, transição de status, e a
baixa (`pagar_conta`) lançando a saída de caixa correspondente.
"""

import pytest

import app as _app
import fluxoly_contas_pagar_service as service

USUARIO_ID_TESTE = 999002


def _limpar_conta(conta_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade='conta_pagar' AND entidade_id=?", (conta_id,))
        conn.execute(
            "DELETE FROM audit_log WHERE entidade='movimentacao_caixa' AND entidade_id IN "
            "(SELECT id FROM movimentacoes_caixa WHERE origem='conta_pagar' AND origem_id=?)",
            (conta_id,),
        )
        conn.execute("DELETE FROM movimentacoes_caixa WHERE origem='conta_pagar' AND origem_id=?", (conta_id,))
        conn.execute("DELETE FROM contas_pagar WHERE id=?", (conta_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def conta_pendente():
    conta_id, erro = service.criar_conta_pagar(
        _app.conectar, USUARIO_ID_TESTE, "Aluguel Teste", "aluguel", 1500.0, "2026-09-01"
    )
    assert erro is None, erro
    yield conta_id
    _limpar_conta(conta_id)


class TestCRUD:
    def test_criar_conta_pagar_valida(self, conta_pendente):
        conta = service.obter_conta_pagar(_app.conectar, conta_pendente)
        assert conta["descricao"] == "Aluguel Teste"
        assert conta["valor"] == 1500.0
        assert conta["status"] == "pendente"

    def test_criar_sem_descricao_retorna_erro(self):
        conta_id, erro = service.criar_conta_pagar(_app.conectar, USUARIO_ID_TESTE, "", "aluguel", 100.0)
        assert conta_id is None
        assert erro

    def test_criar_com_valor_invalido_retorna_erro(self):
        conta_id, erro = service.criar_conta_pagar(_app.conectar, USUARIO_ID_TESTE, "Teste", "outros", -10.0)
        assert conta_id is None
        assert erro

    def test_atualizar_conta_pendente(self, conta_pendente):
        sucesso, erro = service.atualizar_conta_pagar(
            _app.conectar, USUARIO_ID_TESTE, conta_pendente, "Aluguel Atualizado", "aluguel", 1600.0, "2026-09-05"
        )
        assert sucesso, erro
        conta = service.obter_conta_pagar(_app.conectar, conta_pendente)
        assert conta["descricao"] == "Aluguel Atualizado"
        assert conta["valor"] == 1600.0

    def test_excluir_conta_pendente(self):
        conta_id, _erro = service.criar_conta_pagar(_app.conectar, USUARIO_ID_TESTE, "Excluir Teste", "outros", 50.0)
        sucesso, erro = service.excluir_conta_pagar(_app.conectar, USUARIO_ID_TESTE, conta_id)
        assert sucesso, erro
        assert service.obter_conta_pagar(_app.conectar, conta_id) is None

    def test_listar_contas_pagar_inclui_criada(self, conta_pendente):
        resultado = service.listar_contas_pagar(_app.conectar, status="pendente", page=1, per_page=100)
        ids = [item["id"] for item in resultado["items"]]
        assert conta_pendente in ids


class TestBaixa:
    def test_pagar_conta_transiciona_status_e_lanca_saida_de_caixa(self, conta_pendente):
        saldo_antes = service.obter_conta_pagar(_app.conectar, conta_pendente)
        valor = saldo_antes["valor"]

        sucesso, erro = service.pagar_conta(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        assert sucesso, erro

        conta = service.obter_conta_pagar(_app.conectar, conta_pendente)
        assert conta["status"] == "pago"
        assert conta["movimentacao_caixa_id"] is not None

        conn = _app.conectar()
        try:
            row = conn.execute(
                "SELECT tipo, valor, estornada FROM movimentacoes_caixa WHERE id=?",
                (conta["movimentacao_caixa_id"],),
            ).fetchone()
        finally:
            conn.close()
        assert row == ("saida", valor, 0)

    def test_pagar_conta_ja_paga_retorna_erro(self, conta_pendente):
        service.pagar_conta(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        sucesso, erro = service.pagar_conta(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        assert not sucesso
        assert erro

    def test_editar_conta_paga_e_rejeitado(self, conta_pendente):
        service.pagar_conta(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        sucesso, erro = service.atualizar_conta_pagar(
            _app.conectar, USUARIO_ID_TESTE, conta_pendente, "Nova Descricao", "aluguel", 999.0
        )
        assert not sucesso
        assert erro

    def test_cancelar_conta_pendente(self):
        conta_id, _erro = service.criar_conta_pagar(_app.conectar, USUARIO_ID_TESTE, "Cancelar Teste", "outros", 30.0)
        sucesso, erro = service.cancelar_conta_pagar(_app.conectar, USUARIO_ID_TESTE, conta_id)
        assert sucesso, erro
        conta = service.obter_conta_pagar(_app.conectar, conta_id)
        assert conta["status"] == "cancelado"
        _limpar_conta(conta_id)

    def test_cancelar_conta_ja_paga_retorna_erro(self, conta_pendente):
        service.pagar_conta(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        sucesso, erro = service.cancelar_conta_pagar(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        assert not sucesso
        assert erro
