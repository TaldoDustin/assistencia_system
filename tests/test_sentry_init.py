"""
Testes de inicialização condicional do Sentry (Sprint Observabilidade, 2026-07-25).

Mesmo padrão de tests/test_security_flask_secret_key_fallback.py: roda
`import app` num subprocesso isolado, já que a inicialização acontece uma
vez no nível do módulo -- não dá pra re-exercitar dentro da sessão de
testes normal (conftest.py importa `app` uma única vez).
"""

import os
import subprocess
import sys
import tempfile


def _rodar_import_app(env_extra):
    env = {"PATH": os.environ.get("PATH", "")}
    env.update(env_extra)
    resultado = subprocess.run(
        [sys.executable, "-c", "import app"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    return resultado


def _env_base(tmp_dir):
    return {
        "IR_FLOW_DATA_DIR": tmp_dir,
        "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
        "MERCADO_PHONE_SYNC_ENABLED": "0",
        "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
    }


def test_sem_sentry_dsn_nao_inicializa():
    with tempfile.TemporaryDirectory() as tmp_dir:
        resultado = _rodar_import_app(_env_base(tmp_dir))

    assert resultado.returncode == 0, resultado.stderr
    assert "sentry_inicializado" not in resultado.stdout


def test_com_sentry_dsn_valido_inicializa_sem_erro():
    with tempfile.TemporaryDirectory() as tmp_dir:
        env = _env_base(tmp_dir)
        env["SENTRY_DSN"] = "https://examplePublicKey@o0.ingest.sentry.io/0"
        resultado = _rodar_import_app(env)

    assert resultado.returncode == 0, resultado.stderr
    assert '"sentry_inicializado"' in resultado.stdout
