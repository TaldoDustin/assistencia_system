"""
Testes de "Preview seguro" (INC-003 Frente B, KI-035, KI-036) --
docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md.

IS_PULL_REQUEST/BACKGROUND_JOBS_ENABLED/environment do Sentry são decididos
no momento do import do módulo -- por isso, mesmo padrão de
tests/test_security_flask_secret_key_fallback.py, cada cenário roda `import
fluxoly_config`/`import app` num subprocesso isolado (conftest.py já importa
`app` uma vez por sessão com env fixo, o que não reflete um boot com
IS_PULL_REQUEST setado).
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


class TestBackgroundJobsEnabledComPreview:
    def test_is_pull_request_desliga_mesmo_com_flag_manual_ligada(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import fluxoly_config; print(fluxoly_config.BACKGROUND_JOBS_ENABLED)",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IS_PULL_REQUEST": "true",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "1",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "False"

    def test_sem_is_pull_request_comportamento_identico_ao_de_hoje(self):
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

    def test_is_pull_request_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import fluxoly_config; print(fluxoly_config.BACKGROUND_JOBS_ENABLED)",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IS_PULL_REQUEST": "True",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "1",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "False"


class TestLogDeBootQuandoPreview:
    def test_log_estruturado_confirma_jobs_desativados_por_preview(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import app",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IS_PULL_REQUEST": "true",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "1",
                    "MERCADO_PHONE_SYNC_ENABLED": "0",
                    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        mensagens = {evento.get("message") for evento in _eventos_json(resultado.stdout)}
        assert "preview_background_jobs_desativados" in mensagens

    def test_log_nao_aparece_fora_de_preview(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import app",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
                    "MERCADO_PHONE_SYNC_ENABLED": "0",
                    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        mensagens = {evento.get("message") for evento in _eventos_json(resultado.stdout)}
        assert "preview_background_jobs_desativados" not in mensagens


class TestThreadMercadoPhoneNaoIniciaEmPreview:
    """Reproduz as condições exatas do INC-003: MERCADO_PHONE_SYNC_ENABLED e
    MERCADO_PHONE_API_TOKEN presentes (herdados do serviço-base) -- antes
    desta correção, isso era suficiente para a thread iniciar em qualquer
    ambiente, inclusive preview. Verifica o flag de módulo em vez de deixar
    a thread realmente rodar (evita chamada HTTP real à API do MercadoPhone
    num teste)."""

    def test_flag_de_thread_iniciada_permanece_falso_com_credenciais_herdadas(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import app; import time; time.sleep(0.2); print(app._MERCADO_PHONE_SYNC_THREAD_STARTED)",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IS_PULL_REQUEST": "true",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "1",
                    "MERCADO_PHONE_SYNC_ENABLED": "1",
                    "MERCADO_PHONE_API_TOKEN": "token-herdado-de-producao-fake",
                    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        assert resultado.stdout.strip().splitlines()[-1] == "False"


class TestSentryEnvironmentPreview:
    """KI-036: environment do Sentry precisa distinguir preview de produção --
    antes desta correção, IS_SERVER_RUNTIME sozinha reportava "production"
    para os dois, já que um Render PR Preview também seta RENDER/
    RENDER_SERVICE_ID."""

    def test_environment_preview_quando_is_pull_request(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import app",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IS_PULL_REQUEST": "true",
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
                    "MERCADO_PHONE_SYNC_ENABLED": "0",
                    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                    "SENTRY_DSN": _DSN_FALSO,
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        eventos = [e for e in _eventos_json(resultado.stdout) if e.get("message") == "sentry_inicializado"]
        assert eventos, f"log sentry_inicializado não encontrado. stdout={resultado.stdout!r}"
        assert eventos[0]["environment"] == "preview"

    def test_environment_production_quando_server_runtime_sem_preview(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            resultado = _rodar(
                "import app",
                {
                    "IR_FLOW_DATA_DIR": tmp_dir,
                    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
                    "MERCADO_PHONE_SYNC_ENABLED": "0",
                    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                    "SENTRY_DSN": _DSN_FALSO,
                },
            )
        assert resultado.returncode == 0, resultado.stderr
        eventos = [e for e in _eventos_json(resultado.stdout) if e.get("message") == "sentry_inicializado"]
        assert eventos, f"log sentry_inicializado não encontrado. stdout={resultado.stdout!r}"
        assert eventos[0]["environment"] == "production"
