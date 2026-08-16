"""
fluxoly_audit.py

Auditoria central reutilizável — uma tabela genérica (`audit_log`) em vez de
uma tabela de log por domínio (padrão já usado em `shopping_list_logs`,
`fluxoly_blueprints_api.py::_log_shopping`, que não é tocado por este módulo
e continua como está).

Novos domínios (Clientes, Estoque/IMEI e futuramente outros) chamam
`registrar_log_auditoria` para registrar create/update/delete/mudança de
status, em vez de cada um criar sua própria tabela `<dominio>_logs`.

Depende de: nenhum outro módulo de domínio.

Decisão 6 (docs/engineering/plans/PLAN-LGPD-Compliance.md, 2026-08-16): `audit_log` guarda PII completa
de cliente (nome/telefone/email/cpf_cnpj) em `valor_anterior`/`valor_novo`, sem nenhuma retenção -- as
funções `mascarar_audit_log_pii_expirado`/`expurgar_audit_log_expirado` e a thread
`iniciar_thread_manutencao_audit_log` abaixo implementam o mecanismo, mas ficam **inativas por padrão**:
os prazos (`AUDIT_LOG_PII_MASK_APOS_DIAS`/`AUDIT_LOG_EXPURGO_APOS_DIAS`, `fluxoly_config.py`) não têm
default -- decisão jurídica/operacional pendente, não de engenharia. Nenhum deploy deve inventar um
número só para "ativar" a rotina (requisito explícito do CTO, ver Plano Técnico).
"""

import json
import threading
import time

from fluxoly_logging import get_logger

logger = get_logger("fluxoly.audit")

_ENTIDADE_COM_PII = "cliente"
_CAMPOS_PII_CLIENTE = ("nome", "telefone", "email", "cpf_cnpj")
_PLACEHOLDER_PII = "[PII removida -- retenção de auditoria]"


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


def _mascarar_campos_pii(valor_json):
    if not valor_json:
        return valor_json
    try:
        dado = json.loads(valor_json)
    except (ValueError, TypeError):
        return valor_json
    if not isinstance(dado, dict):
        return valor_json

    alterado = False
    for campo in _CAMPOS_PII_CLIENTE:
        if dado.get(campo):
            dado[campo] = _PLACEHOLDER_PII
            alterado = True
    if not alterado:
        return valor_json
    return json.dumps(dado, ensure_ascii=False)


def mascarar_audit_log_pii_expirado(cursor, dias):
    """Mascara PII de registros de auditoria de cliente mais antigos que `dias`, preservando
    acao/entidade_id/usuario_id/criado_em -- a trilha de "o que aconteceu, quando, quem fez" continua
    íntegra, só o conteúdo pessoal é mascarado. `dias` é obrigatório e positivo -- o chamador
    (`iniciar_thread_manutencao_audit_log`) só invoca isto quando um prazo real está configurado."""
    cursor.execute(
        "SELECT id, valor_anterior, valor_novo FROM audit_log WHERE entidade = ? AND criado_em < datetime('now', ?)",
        (_ENTIDADE_COM_PII, f"-{dias} days"),
    )
    linhas = cursor.fetchall()
    for linha_id, valor_anterior, valor_novo in linhas:
        novo_anterior = _mascarar_campos_pii(valor_anterior)
        novo_novo = _mascarar_campos_pii(valor_novo)
        if novo_anterior != valor_anterior or novo_novo != valor_novo:
            cursor.execute(
                "UPDATE audit_log SET valor_anterior = ?, valor_novo = ? WHERE id = ?",
                (novo_anterior, novo_novo, linha_id),
            )
    return len(linhas)


def expurgar_audit_log_expirado(cursor, dias):
    """Remove por completo registros de auditoria de cliente mais antigos que `dias`. `dias` é
    obrigatório e positivo -- mesma condição de chamada de `mascarar_audit_log_pii_expirado`."""
    cursor.execute(
        "DELETE FROM audit_log WHERE entidade = ? AND criado_em < datetime('now', ?)",
        (_ENTIDADE_COM_PII, f"-{dias} days"),
    )
    return cursor.rowcount


def iniciar_thread_manutencao_audit_log(
    conectar, dias_mascaramento, dias_expurgo, intervalo_verificacao_segundos=3600
):
    """Decisão 6 (PLAN-LGPD-Compliance.md): thread daemon que roda mascaramento/expurgo periodicamente
    -- só é chamada pelo boot (app.py) quando pelo menos um dos dois prazos está configurado
    (AUDIT_LOG_PII_MASK_APOS_DIAS/AUDIT_LOG_EXPURGO_APOS_DIAS, fluxoly_config.py, sem default). Sem
    nenhum dos dois configurados, esta função nunca é chamada -- fail-safe por ausência de invocação,
    não por uma checagem interna que poderia ser esquecida."""

    def _loop():
        time.sleep(30)  # mesmo padrão de iniciar_thread_backup_automatico -- não competir com o boot
        while True:
            try:
                conn = conectar()
                try:
                    cursor = conn.cursor()
                    if dias_mascaramento:
                        n = mascarar_audit_log_pii_expirado(cursor, dias_mascaramento)
                        if n:
                            logger.info("audit_log_pii_mascarada", extra={"linhas": n})
                    if dias_expurgo:
                        n = expurgar_audit_log_expirado(cursor, dias_expurgo)
                        if n:
                            logger.info("audit_log_expurgado", extra={"linhas": n})
                    conn.commit()
                finally:
                    conn.close()
            except Exception as exc:
                logger.error("audit_log_manutencao_erro_inesperado", extra={"erro": str(exc)}, exc_info=True)

            time.sleep(intervalo_verificacao_segundos)

    t = threading.Thread(target=_loop, daemon=True, name="audit-log-manutencao")
    t.start()
    return t
