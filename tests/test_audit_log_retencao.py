"""
Testes de retenção/mascaramento do audit_log (Decisão 6, PLAN-LGPD-Compliance.md).

Duas camadas testadas separadamente:
1. fluxoly_config.py -- AUDIT_LOG_PII_MASK_APOS_DIAS/AUDIT_LOG_EXPURGO_APOS_DIAS resolvem para None sem
   env var configurada (fail-safe), mesmo padrão de subprocesso isolado de
   tests/test_ambiente_preview.py.
2. fluxoly_audit.py -- mascarar_audit_log_pii_expirado/expurgar_audit_log_expirado são funções puras
   testadas contra um cursor real (conftest.py), sem depender de nenhuma thread/timing.
"""

import json
import os
import subprocess
import sys

import app as _app
from fluxoly_audit import expurgar_audit_log_expirado, mascarar_audit_log_pii_expirado

_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _rodar(codigo, env_extra):
    env = {"PATH": os.environ.get("PATH", "")}
    env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=_RAIZ_PROJETO,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


class TestFailSafeSemPrazoConfigurado:
    def test_mask_fica_none_sem_env_var(self):
        resultado = _rodar(
            "import fluxoly_config; print(fluxoly_config.AUDIT_LOG_PII_MASK_APOS_DIAS)", {}
        )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "None"

    def test_expurgo_fica_none_sem_env_var(self):
        resultado = _rodar(
            "import fluxoly_config; print(fluxoly_config.AUDIT_LOG_EXPURGO_APOS_DIAS)", {}
        )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "None"

    def test_valor_invalido_fica_none(self):
        resultado = _rodar(
            "import fluxoly_config; print(fluxoly_config.AUDIT_LOG_PII_MASK_APOS_DIAS)",
            {"AUDIT_LOG_PII_MASK_APOS_DIAS": "nao-e-numero"},
        )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "None"

    def test_valor_negativo_fica_none(self):
        resultado = _rodar(
            "import fluxoly_config; print(fluxoly_config.AUDIT_LOG_PII_MASK_APOS_DIAS)",
            {"AUDIT_LOG_PII_MASK_APOS_DIAS": "-5"},
        )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "None"

    def test_valor_positivo_e_aceito(self):
        resultado = _rodar(
            "import fluxoly_config; print(fluxoly_config.AUDIT_LOG_PII_MASK_APOS_DIAS)",
            {"AUDIT_LOG_PII_MASK_APOS_DIAS": "365"},
        )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "365"


def _inserir_audit_log(cursor, entidade, dias_atras, cpf_cnpj="123.456.789-00"):
    valor_anterior = json.dumps({"nome": "Fulano", "telefone": "119999", "cpf_cnpj": cpf_cnpj})
    cursor.execute(
        """
        INSERT INTO audit_log (entidade, entidade_id, usuario_id, acao, valor_anterior, criado_em)
        VALUES (?, 1, 1, 'update', ?, datetime('now', ?))
        """,
        (entidade, valor_anterior, f"-{dias_atras} days"),
    )
    return cursor.lastrowid


class TestMascaramento:
    def test_mascara_registro_antigo_preserva_metadados(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            log_id = _inserir_audit_log(cursor, "cliente", dias_atras=400)
            conn.commit()

            n = mascarar_audit_log_pii_expirado(cursor, dias=365)
            conn.commit()
            assert n == 1

            row = cursor.execute(
                "SELECT acao, entidade_id, usuario_id, criado_em, valor_anterior FROM audit_log WHERE id=?",
                (log_id,),
            ).fetchone()
            assert row[0] == "update"
            assert row[1] == 1
            assert row[2] == 1
            assert row[3] is not None
            dado = json.loads(row[4])
            assert dado["nome"] == "[PII removida -- retenção de auditoria]"
            assert dado["cpf_cnpj"] == "[PII removida -- retenção de auditoria]"
        finally:
            cursor.execute("DELETE FROM audit_log WHERE entidade='cliente' AND entidade_id=1")
            conn.commit()
            conn.close()

    def test_nao_mascara_registro_recente(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            log_id = _inserir_audit_log(cursor, "cliente", dias_atras=1)
            conn.commit()

            n = mascarar_audit_log_pii_expirado(cursor, dias=365)
            conn.commit()
            assert n == 0

            row = cursor.execute("SELECT valor_anterior FROM audit_log WHERE id=?", (log_id,)).fetchone()
            dado = json.loads(row[0])
            assert dado["cpf_cnpj"] == "123.456.789-00"
        finally:
            cursor.execute("DELETE FROM audit_log WHERE entidade='cliente' AND entidade_id=1")
            conn.commit()
            conn.close()

    def test_nao_mascara_outras_entidades(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            log_id = _inserir_audit_log(cursor, "estoque_unidade", dias_atras=400)
            conn.commit()

            n = mascarar_audit_log_pii_expirado(cursor, dias=365)
            conn.commit()
            assert n == 0

            row = cursor.execute("SELECT valor_anterior FROM audit_log WHERE id=?", (log_id,)).fetchone()
            dado = json.loads(row[0])
            assert dado["cpf_cnpj"] == "123.456.789-00"
        finally:
            cursor.execute("DELETE FROM audit_log WHERE entidade='estoque_unidade' AND entidade_id=1")
            conn.commit()
            conn.close()


class TestExpurgo:
    def test_expurga_registro_antigo(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            log_id = _inserir_audit_log(cursor, "cliente", dias_atras=1000)
            conn.commit()

            n = expurgar_audit_log_expirado(cursor, dias=730)
            conn.commit()
            assert n == 1

            row = cursor.execute("SELECT id FROM audit_log WHERE id=?", (log_id,)).fetchone()
            assert row is None
        finally:
            conn.close()

    def test_nao_expurga_registro_dentro_do_prazo(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            log_id = _inserir_audit_log(cursor, "cliente", dias_atras=10)
            conn.commit()

            n = expurgar_audit_log_expirado(cursor, dias=730)
            conn.commit()
            assert n == 0

            row = cursor.execute("SELECT id FROM audit_log WHERE id=?", (log_id,)).fetchone()
            assert row is not None
        finally:
            cursor.execute("DELETE FROM audit_log WHERE entidade='cliente' AND entidade_id=1")
            conn.commit()
            conn.close()
