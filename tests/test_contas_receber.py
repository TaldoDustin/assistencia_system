"""
Testes do domínio Contas a Receber (Financeiro Mínimo, BR-067 a BR-069,
docs/engineering/plans/PLAN-financeiro-minimo.md). Espelho de
tests/test_contas_pagar.py.

Escopo: fluxoly_contas_receber_service.py -- CRUD, transição de status, a
baixa (`receber_conta`) lançando a entrada de caixa correspondente, e o
isolamento de BR-068 (nenhuma relação com o domínio Vendas).
"""

import inspect

import pytest

import app as _app
import fluxoly_contas_receber_repository as repo
import fluxoly_contas_receber_service as service

USUARIO_ID_TESTE = 999003


def _limpar_conta(conta_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade='conta_receber' AND entidade_id=?", (conta_id,))
        conn.execute(
            "DELETE FROM audit_log WHERE entidade='movimentacao_caixa' AND entidade_id IN "
            "(SELECT id FROM movimentacoes_caixa WHERE origem='conta_receber' AND origem_id=?)",
            (conta_id,),
        )
        conn.execute("DELETE FROM movimentacoes_caixa WHERE origem='conta_receber' AND origem_id=?", (conta_id,))
        conn.execute("DELETE FROM contas_receber WHERE id=?", (conta_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def conta_pendente():
    conta_id, erro = service.criar_conta_receber(
        _app.conectar, USUARIO_ID_TESTE, "Serviço Prestado Teste", "servicos", 800.0, "2026-09-01"
    )
    assert erro is None, erro
    yield conta_id
    _limpar_conta(conta_id)


class TestCRUD:
    def test_criar_conta_receber_valida(self, conta_pendente):
        conta = service.obter_conta_receber(_app.conectar, conta_pendente)
        assert conta["descricao"] == "Serviço Prestado Teste"
        assert conta["valor"] == 800.0
        assert conta["status"] == "pendente"

    def test_criar_sem_descricao_retorna_erro(self):
        conta_id, erro = service.criar_conta_receber(_app.conectar, USUARIO_ID_TESTE, "", "servicos", 100.0)
        assert conta_id is None
        assert erro

    def test_criar_com_valor_invalido_retorna_erro(self):
        conta_id, erro = service.criar_conta_receber(_app.conectar, USUARIO_ID_TESTE, "Teste", "outros", 0)
        assert conta_id is None
        assert erro

    def test_atualizar_conta_pendente(self, conta_pendente):
        sucesso, erro = service.atualizar_conta_receber(
            _app.conectar, USUARIO_ID_TESTE, conta_pendente, "Descricao Atualizada", "servicos", 900.0, "2026-09-10"
        )
        assert sucesso, erro
        conta = service.obter_conta_receber(_app.conectar, conta_pendente)
        assert conta["descricao"] == "Descricao Atualizada"
        assert conta["valor"] == 900.0

    def test_excluir_conta_pendente(self):
        conta_id, _erro = service.criar_conta_receber(_app.conectar, USUARIO_ID_TESTE, "Excluir Teste", "outros", 50.0)
        sucesso, erro = service.excluir_conta_receber(_app.conectar, USUARIO_ID_TESTE, conta_id)
        assert sucesso, erro
        assert service.obter_conta_receber(_app.conectar, conta_id) is None

    def test_listar_contas_receber_inclui_criada(self, conta_pendente):
        resultado = service.listar_contas_receber(_app.conectar, status="pendente", page=1, per_page=100)
        ids = [item["id"] for item in resultado["items"]]
        assert conta_pendente in ids


class TestBaixa:
    def test_receber_conta_transiciona_status_e_lanca_entrada_de_caixa(self, conta_pendente):
        conta_antes = service.obter_conta_receber(_app.conectar, conta_pendente)
        valor = conta_antes["valor"]

        sucesso, erro = service.receber_conta(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        assert sucesso, erro

        conta = service.obter_conta_receber(_app.conectar, conta_pendente)
        assert conta["status"] == "recebido"
        assert conta["movimentacao_caixa_id"] is not None

        conn = _app.conectar()
        try:
            row = conn.execute(
                "SELECT tipo, valor, estornada FROM movimentacoes_caixa WHERE id=?",
                (conta["movimentacao_caixa_id"],),
            ).fetchone()
        finally:
            conn.close()
        assert row == ("entrada", valor, 0)

    def test_receber_conta_ja_recebida_retorna_erro(self, conta_pendente):
        service.receber_conta(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        sucesso, erro = service.receber_conta(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        assert not sucesso
        assert erro

    def test_editar_conta_recebida_e_rejeitado(self, conta_pendente):
        service.receber_conta(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        sucesso, erro = service.atualizar_conta_receber(
            _app.conectar, USUARIO_ID_TESTE, conta_pendente, "Nova Descricao", "servicos", 999.0
        )
        assert not sucesso
        assert erro

    def test_cancelar_conta_pendente(self):
        conta_id, _erro = service.criar_conta_receber(_app.conectar, USUARIO_ID_TESTE, "Cancelar Teste", "outros", 30.0)
        sucesso, erro = service.cancelar_conta_receber(_app.conectar, USUARIO_ID_TESTE, conta_id)
        assert sucesso, erro
        conta = service.obter_conta_receber(_app.conectar, conta_id)
        assert conta["status"] == "cancelado"
        _limpar_conta(conta_id)

    def test_cancelar_conta_ja_recebida_retorna_erro(self, conta_pendente):
        service.receber_conta(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        sucesso, erro = service.cancelar_conta_receber(_app.conectar, USUARIO_ID_TESTE, conta_pendente)
        assert not sucesso
        assert erro


class TestIsolamentoDeVendasBR068:
    """BR-068 -- Contas a Receber representa só compromissos financeiros
    gerais, sem FK ou qualquer relação com o domínio Vendas."""

    def test_tabela_contas_receber_sem_coluna_de_venda(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(contas_receber)")
            colunas = {row[1] for row in cursor.fetchall()}
        finally:
            conn.close()
        assert not any("venda" in coluna.lower() for coluna in colunas)

    def test_repository_e_service_nao_importam_o_dominio_vendas(self):
        """Isolamento estrutural: nenhum import de fluxoly_vendas_* -- a
        prosa dos docstrings explicando a decisão do BR-068 pode mencionar
        'Vendas' livremente, o que não pode existir é uma dependência de
        código real entre os dois domínios."""
        for modulo in (repo, service):
            imports = [
                nome
                for nome, valor in vars(modulo).items()
                if inspect.ismodule(valor) and valor.__name__.startswith("fluxoly_vendas")
            ]
            assert imports == []

    def test_repository_sem_query_que_referencie_tabela_vendas(self):
        codigo_repo = inspect.getsource(repo)
        assert "vendas_itens" not in codigo_repo
        assert "FROM vendas" not in codigo_repo
        assert "JOIN vendas" not in codigo_repo
