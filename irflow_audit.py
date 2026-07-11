"""
irflow_audit.py

Auditoria central reutilizável — uma tabela genérica (`audit_log`) em vez de
uma tabela de log por domínio (padrão já usado em `shopping_list_logs`,
`irflow_blueprints_api.py::_log_shopping`, que não é tocado por este módulo
e continua como está).

Novos domínios (Clientes, Estoque/IMEI e futuramente outros) chamam
`registrar_log_auditoria` para registrar create/update/delete/mudança de
status, em vez de cada um criar sua própria tabela `<dominio>_logs`.

Depende de: nenhum outro módulo de domínio.
"""

import json


def registrar_log_auditoria(cursor, entidade, entidade_id, usuario_id, acao, antes=None, depois=None):
    """
    Grava uma linha de auditoria na mesma transação/cursor de quem chamou —
    não faz commit (segue o mesmo contrato de `_log_shopping`: a mudança de
    dado e o log de auditoria são uma única transação atômica).

    `antes`/`depois` aceitam qualquer valor serializável em JSON (ou já uma
    string); em caso de falha de serialização, cai para `str(...)` em vez de
    levantar exceção — auditoria não pode derrubar a operação que está
    registrando.
    """

    def _serializar(valor):
        if valor is None:
            return None
        if isinstance(valor, str):
            return valor
        try:
            return json.dumps(valor, default=str, ensure_ascii=False)
        except Exception:
            return str(valor)

    cursor.execute(
        """
        INSERT INTO audit_log (entidade, entidade_id, usuario_id, acao, valor_anterior, valor_novo)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (entidade, entidade_id, usuario_id, acao, _serializar(antes), _serializar(depois)),
    )
