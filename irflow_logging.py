"""
irflow_logging.py

Responsabilidade: logging estruturado em JSON, uma linha por evento, em vez
dos `print()` espalhados pelo backend (Sprint Observabilidade, 2026-07-25).
Cada linha carrega `request_id` quando emitida dentro de uma requisição
Flask (correlação entre linhas do mesmo request) e campos extras via
`logger.info(msg, extra={...})` do `logging` padrão.

Por quê JSON: Render captura stdout como log — uma linha JSON por evento é
consultável/filtrável (por `request_id`, `level`, `logger`) sem depender de
parsing de texto livre. Sem dependência nova: só a biblioteca `logging` da
stdlib.

Depende de: nenhum outro módulo de domínio. Importa `flask` só para checar
o contexto de request (`has_request_context`/`g`) — opcional: logs emitidos
fora de uma request (ex. a thread de sincronização do Mercado Phone) saem
sem `request_id`, não quebram.
"""

import json
import logging
import sys
from datetime import UTC, datetime

_CAMPOS_PADRAO_LOGRECORD = frozenset(logging.LogRecord("", 0, "", 0, "", None, None).__dict__.keys())


class JSONFormatter(logging.Formatter):
    def format(self, record):
        try:
            from flask import g, has_request_context

            request_id = getattr(g, "request_id", None) if has_request_context() else None
        except RuntimeError:
            # has_request_context() pode levantar fora de um app context ativo
            # (ex. import isolado, script avulso) -- log continua sem request_id.
            request_id = None

        linha = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if request_id:
            linha["request_id"] = request_id

        for chave, valor in record.__dict__.items():
            if chave not in _CAMPOS_PADRAO_LOGRECORD and chave not in linha:
                linha[chave] = valor

        if record.exc_info:
            linha["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(linha, default=str, ensure_ascii=False)


def configurar_logging(nivel=logging.INFO):
    """
    Configura o logger raiz da aplicação para emitir JSON em stdout.
    Idempotente -- chamar mais de uma vez (ex. em testes que reimportam
    `app`) não duplica handlers.
    """
    raiz = logging.getLogger()
    raiz.setLevel(nivel)

    ja_configurado = any(isinstance(h.formatter, JSONFormatter) for h in raiz.handlers)
    if ja_configurado:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    raiz.handlers.clear()
    raiz.addHandler(handler)


def get_logger(nome):
    return logging.getLogger(nome)
