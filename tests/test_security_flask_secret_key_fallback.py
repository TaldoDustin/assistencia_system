"""
SECURITY_AUDIT_2026-07.md item 3 — antes, um deploy sem FLASK_SECRET_KEY configurada
iniciava silenciosamente com um valor hardcoded e público ("ir-flow-dev-key"),
permitindo forjar cookies de sessão sem que ninguém percebesse.

Esses testes rodam `import app` num subprocesso isolado (não através de conftest.py,
que já importa `app` uma vez por sessão com FLASK_SECRET_KEY sempre setada) para
verificar o comportamento real de boot em cada cenário.
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


def test_falha_no_boot_sem_flask_secret_key_em_server_runtime():
    with tempfile.TemporaryDirectory() as tmp_dir:
        resultado = _rodar_import_app(
            {
                "IR_FLOW_DATA_DIR": tmp_dir,
                "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
                "MERCADO_PHONE_SYNC_ENABLED": "0",
            }
        )
    assert resultado.returncode != 0
    assert "FLASK_SECRET_KEY" in resultado.stderr


def test_inicia_normalmente_com_flask_secret_key_definida():
    with tempfile.TemporaryDirectory() as tmp_dir:
        resultado = _rodar_import_app(
            {
                "IR_FLOW_DATA_DIR": tmp_dir,
                "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
                "MERCADO_PHONE_SYNC_ENABLED": "0",
                "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
                "IR_FLOW_ADMIN_PASSWORD": "senha-admin-teste-nao-usar-em-producao",
            }
        )
    assert resultado.returncode == 0, resultado.stderr


# Nota: o cenario "dev local sem IR_FLOW_DATA_DIR usa o fallback sem falhar" nao tem
# teste automatizado aqui de proposito -- rodar `import app` sem IR_FLOW_DATA_DIR faz
# APP_DIR (logo DATA_DIR/database.db) resolver para o diretorio real do projeto,
# violando a regra de isolamento de testes ("nenhum teste pode tocar database.db").
# Verificado manualmente durante o desenvolvimento desta mudanca.
