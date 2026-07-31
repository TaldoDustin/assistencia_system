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


def _rodar_import_app_capturando_init(env_extra):
    """Substitui o pacote sentry_sdk inteiro por um fake em sys.modules antes
    de importar app -- evita depender de rede/DSN real e permite inspecionar
    exatamente os kwargs que app.py passaria para o SDK de verdade. Como
    bônus, não importa o pacote real (só o stub), então não é afetado pelo
    problema de ambiente Windows local do import transitivo de asyncio
    (ver tests/test_sentry_init.py::test_com_sentry_dsn_valido_inicializa_sem_erro)."""
    env = {"PATH": os.environ.get("PATH", "")}
    env.update(env_extra)
    codigo = (
        "import sys, types\n"
        "fake_sentry = types.ModuleType('sentry_sdk')\n"
        "def _fake_init(**kwargs):\n"
        "    print('SENTRY_INIT_KWARGS', kwargs.get('environment'), kwargs.get('release'))\n"
        "fake_sentry.init = _fake_init\n"
        "sys.modules['sentry_sdk'] = fake_sentry\n"
        "fake_integrations = types.ModuleType('sentry_sdk.integrations')\n"
        "fake_flask_mod = types.ModuleType('sentry_sdk.integrations.flask')\n"
        "class FlaskIntegration:\n"
        "    def __init__(self, *a, **kw): pass\n"
        "fake_flask_mod.FlaskIntegration = FlaskIntegration\n"
        "sys.modules['sentry_sdk.integrations'] = fake_integrations\n"
        "sys.modules['sentry_sdk.integrations.flask'] = fake_flask_mod\n"
        "import app\n"
    )
    return subprocess.run(
        [sys.executable, "-c", codigo],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_environment_production_e_release_do_render_git_commit():
    # IR_FLOW_DATA_DIR (exigido para isolar o teste de database.db) já torna
    # IS_SERVER_RUNTIME=True neste harness -- não dá pra exercitar o ramo
    # "development" do environment sem abrir mão do isolamento; a lógica do
    # ternário em si (IS_SERVER_RUNTIME -> "production"/"development") é
    # trivial o bastante para não precisar de um teste de processo separado
    # sem isolamento.
    with tempfile.TemporaryDirectory() as tmp_dir:
        env = _env_base(tmp_dir)
        env["SENTRY_DSN"] = "https://examplePublicKey@o0.ingest.sentry.io/0"
        env["RENDER_GIT_COMMIT"] = "abc1234"
        resultado = _rodar_import_app_capturando_init(env)

    assert resultado.returncode == 0, resultado.stderr
    assert "SENTRY_INIT_KWARGS production abc1234" in resultado.stdout


def test_release_cai_no_fallback_dev_sem_render_git_commit():
    with tempfile.TemporaryDirectory() as tmp_dir:
        env = _env_base(tmp_dir)
        env["SENTRY_DSN"] = "https://examplePublicKey@o0.ingest.sentry.io/0"
        resultado = _rodar_import_app_capturando_init(env)

    assert resultado.returncode == 0, resultado.stderr
    assert "SENTRY_INIT_KWARGS production dev" in resultado.stdout
