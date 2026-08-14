"""
Testes do Ambiente de Demonstração/Homologação (ADR-012) --
docs/engineering/plans/PLAN-ambiente-demo-homologacao.md.

IR_FLOW_ENVIRONMENT/IS_DEMO_ENVIRONMENT/BACKGROUND_JOBS_ENABLED/environment do
Sentry são decididos no momento do import do módulo -- mesmo padrão de
tests/test_ambiente_preview.py, cada cenário roda `import fluxoly_config`/
`import app` num subprocesso isolado.
"""

import json
import os
import subprocess
import sys
import tempfile

_RAIZ_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DSN_FALSO = "https://examplePublicKey@o0.ingest.sentry.io/0"


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


def _eventos_json(stdout):
    eventos = []
    for linha in stdout.splitlines():
        linha = linha.strip()
        if not linha:
            continue
        try:
            eventos.append(json.loads(linha))
        except ValueError:
            continue
    return eventos


class TestBackgroundJobsEnabledComDemo:
    def test_ir_flow_environment_demo_desliga_mesmo_com_flag_manual_ligada(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import fluxoly_config; print(fluxoly_config.BACKGROUND_JOBS_ENABLED)",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_ENVIRONMENT": "demo",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "1",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "False"

    def test_sem_ir_flow_environment_comportamento_identico_ao_de_hoje(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import fluxoly_config; print(fluxoly_config.BACKGROUND_JOBS_ENABLED)",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "1",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "True"

    def test_ir_flow_environment_com_outro_valor_comportamento_identico_ao_de_hoje(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import fluxoly_config; print(fluxoly_config.BACKGROUND_JOBS_ENABLED)",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_ENVIRONMENT": "staging",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "1",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "True"

    def test_ir_flow_environment_demo_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import fluxoly_config; print(fluxoly_config.BACKGROUND_JOBS_ENABLED)",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_ENVIRONMENT": "DEMO",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "1",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "False"


class TestLogDeBootQuandoDemo:
    def test_log_estruturado_confirma_jobs_desativados_por_demo(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import app",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_ENVIRONMENT": "demo",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "1",
                    "MERCADO_PHONE_SYNC_ENABLED": "0",
                    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                    "IR_FLOW_ADMIN_PASSWORD": "senha-admin-teste-nao-usar-em-producao",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        mensagens = {evento.get("message") for evento in _eventos_json(resultado.stdout)}
        assert "demo_background_jobs_desativados" in mensagens
        assert "preview_background_jobs_desativados" not in mensagens

    def test_log_de_preview_nao_aparece_junto_do_de_demo_e_vice_versa(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import app",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IS_PULL_REQUEST": "true",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "1",
                    "MERCADO_PHONE_SYNC_ENABLED": "0",
                    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                    "IR_FLOW_ADMIN_PASSWORD": "senha-admin-teste-nao-usar-em-producao",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        mensagens = {evento.get("message") for evento in _eventos_json(resultado.stdout)}
        assert "preview_background_jobs_desativados" in mensagens
        assert "demo_background_jobs_desativados" not in mensagens

    def test_log_nao_aparece_fora_de_demo(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import app",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
                    "MERCADO_PHONE_SYNC_ENABLED": "0",
                    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                    "IR_FLOW_ADMIN_PASSWORD": "senha-admin-teste-nao-usar-em-producao",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        mensagens = {evento.get("message") for evento in _eventos_json(resultado.stdout)}
        assert "demo_background_jobs_desativados" not in mensagens


class TestSentryEnvironmentDemo:
    """ADR-012: environment do Sentry precisa distinguir Demo de Preview e de
    produção -- Preview vence se, por engano, IS_PULL_REQUEST e
    IR_FLOW_ENVIRONMENT=demo estiverem setados juntos (ordem de precedência
    definida no Plano Técnico)."""

    def test_environment_demo_quando_ir_flow_environment_demo(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import app",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_ENVIRONMENT": "demo",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
                    "MERCADO_PHONE_SYNC_ENABLED": "0",
                    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                    "IR_FLOW_ADMIN_PASSWORD": "senha-admin-teste-nao-usar-em-producao",
                    "SENTRY_DSN": _DSN_FALSO,
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        eventos = [e for e in _eventos_json(resultado.stdout) if e.get("message") == "sentry_inicializado"]
        assert eventos, f"log sentry_inicializado não encontrado. stdout={resultado.stdout!r}"
        assert eventos[0]["environment"] == "demo"

    def test_environment_preview_vence_quando_is_pull_request_e_demo_setados_juntos(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import app",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IS_PULL_REQUEST": "true",
                    "IR_FLOW_ENVIRONMENT": "demo",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
                    "MERCADO_PHONE_SYNC_ENABLED": "0",
                    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                    "IR_FLOW_ADMIN_PASSWORD": "senha-admin-teste-nao-usar-em-producao",
                    "SENTRY_DSN": _DSN_FALSO,
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        eventos = [e for e in _eventos_json(resultado.stdout) if e.get("message") == "sentry_inicializado"]
        assert eventos, f"log sentry_inicializado não encontrado. stdout={resultado.stdout!r}"
        assert eventos[0]["environment"] == "preview"
