"""
Testes do formatter de log JSON (Sprint Observabilidade, 2026-07-25).

Escopo: fluxoly_logging.py -- formato da linha emitida e correlação com o
request_id de flask.g quando existe um request ativo.
"""

import json
import logging

from fluxoly_logging import JSONFormatter, get_logger


def _formatar(record):
    return json.loads(JSONFormatter().format(record))


def _criar_record(msg="mensagem de teste", level=logging.INFO, **extra):
    record = logging.LogRecord(
        name="teste.logger",
        level=level,
        pathname=__file__,
        lineno=1,
        msg=msg,
        args=None,
        exc_info=None,
    )
    for chave, valor in extra.items():
        setattr(record, chave, valor)
    return record


class TestJSONFormatter:
    def test_campos_basicos_presentes(self):
        linha = _formatar(_criar_record("ola mundo"))

        assert linha["message"] == "ola mundo"
        assert linha["level"] == "INFO"
        assert linha["logger"] == "teste.logger"
        assert "timestamp" in linha

    def test_sem_request_ativo_nao_tem_request_id(self):
        linha = _formatar(_criar_record())

        assert "request_id" not in linha

    def test_campo_extra_e_incluido(self):
        linha = _formatar(_criar_record("evento", origem="mercadophone"))

        assert linha["origem"] == "mercadophone"

    def test_exc_info_e_formatado_quando_presente(self):
        try:
            raise ValueError("erro de teste")
        except ValueError:
            import sys

            record = logging.LogRecord(
                name="teste.logger",
                level=logging.ERROR,
                pathname=__file__,
                lineno=1,
                msg="falhou",
                args=None,
                exc_info=sys.exc_info(),
            )
        linha = _formatar(record)

        assert "ValueError" in linha["exc_info"]
        assert "erro de teste" in linha["exc_info"]

    def test_saida_e_json_valido_mesmo_com_mensagem_com_aspas(self):
        linha_bruta = JSONFormatter().format(_criar_record('mensagem com "aspas" e \n quebra de linha'))
        parsed = json.loads(linha_bruta)

        assert "aspas" in parsed["message"]


class TestRequestIdDentroDeRequest:
    def test_log_dentro_de_uma_request_carrega_request_id(self, client, app):
        capturado = {}

        class _Handler(logging.Handler):
            def emit(self, record):
                capturado["linha"] = JSONFormatter().format(record)

        logger = get_logger("teste.request_id")
        handler = _Handler()
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        try:
            with app.test_request_context("/api/constantes"):
                from flask import g

                g.request_id = "abc-123"
                logger.info("evento durante request")
        finally:
            logger.removeHandler(handler)

        linha = json.loads(capturado["linha"])
        assert linha["request_id"] == "abc-123"
