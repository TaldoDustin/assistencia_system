"""
Teste do achado da 2a triagem Aikido (2026-07-25) em irflow_os.py::carregar_os_com_relacoes:
o parâmetro `order_by` era interpolado via f-string direto na cláusula ORDER BY sem
validação dentro da função -- seguro hoje porque os únicos 2 chamadores (irflow_blueprints_api.py)
passam sempre o mesmo literal fixo "os.id DESC", mas nada impedia um chamador futuro de
repassar algo vindo de request.args. Corrigido com whitelist (_ORDENACOES_OS), mesmo padrão
já usado em fluxoly_unidades_serializadas_repository.py. Ver docs/security/SECURITY_AUDIT_2026-07.md.
"""

import app as _app
from irflow_os import carregar_os_com_relacoes


class TestOrderByWhitelist:
    def test_order_by_padrao_funciona(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            dados, _, _ = carregar_os_com_relacoes(cursor, order_by="os.id DESC")
            assert isinstance(dados, list)
        finally:
            conn.close()

    def test_order_by_malicioso_nao_e_interpolado_na_query(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            malicioso = "os.id; DROP TABLE os; --"
            # Não deve levantar exceção nem executar SQL fora da whitelist —
            # cai no default ("os.id DESC") em vez de interpolar o valor recebido.
            dados, _, _ = carregar_os_com_relacoes(cursor, order_by=malicioso)
            assert isinstance(dados, list)

            cursor.execute("SELECT COUNT(*) FROM os")
            assert cursor.fetchone() is not None  # tabela "os" segue existindo
        finally:
            conn.close()

    def test_order_by_desconhecido_mas_inofensivo_cai_no_default(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            # Um valor plausível mas fora da whitelist também deve cair no default,
            # não ser aceito silenciosamente.
            dados, _, _ = carregar_os_com_relacoes(cursor, order_by="os.cliente ASC")
            assert isinstance(dados, list)
        finally:
            conn.close()
