"""
KI-038/KI-039 (docs/operations/KNOWN_ISSUES.md) -- antes, criar_admin_padrao()
(app.py) criava o admin inicial sempre com a senha fixa "irflow@2024",
incondicionalmente, em qualquer ambiente. Mesmo padrão de
test_security_flask_secret_key_fallback.py: roda `import app` num
subprocesso isolado para verificar o comportamento real de boot.
"""

import os
import sqlite3
import subprocess
import sys
import tempfile

from werkzeug.security import check_password_hash

_ENV_BASE = {
    "IR_FLOW_ENABLE_BACKGROUND_JOBS": "0",
    "MERCADO_PHONE_SYNC_ENABLED": "0",
    "FLASK_SECRET_KEY": "chave-de-teste-para-este-subprocesso",
}


def _rodar_import_app(tmp_dir, env_extra):
    env = {"PATH": os.environ.get("PATH", ""), "IR_FLOW_DATA_DIR": tmp_dir, **_ENV_BASE, **env_extra}
    return subprocess.run(
        [sys.executable, "-c", "import app"],
        cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _senha_hash_do_admin(tmp_dir):
    conn = sqlite3.connect(os.path.join(tmp_dir, "database.db"))
    try:
        row = conn.execute("SELECT senha_hash FROM usuarios WHERE usuario = ?", ("admin",)).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def test_falha_no_boot_sem_ir_flow_admin_password_em_server_runtime():
    with tempfile.TemporaryDirectory() as tmp_dir:
        resultado = _rodar_import_app(tmp_dir, {})
    assert resultado.returncode != 0
    assert "IR_FLOW_ADMIN_PASSWORD" in resultado.stderr


def test_admin_criado_com_senha_da_variavel_nao_com_fallback_antigo():
    with tempfile.TemporaryDirectory() as tmp_dir:
        resultado = _rodar_import_app(tmp_dir, {"IR_FLOW_ADMIN_PASSWORD": "senha-definida-pela-variavel"})
        assert resultado.returncode == 0, resultado.stderr
        senha_hash = _senha_hash_do_admin(tmp_dir)
    assert senha_hash is not None
    assert check_password_hash(senha_hash, "senha-definida-pela-variavel")
    assert not check_password_hash(senha_hash, "irflow@2024")


def test_admin_ja_existente_nao_exige_variavel():
    with tempfile.TemporaryDirectory() as tmp_dir:
        primeiro = _rodar_import_app(tmp_dir, {"IR_FLOW_ADMIN_PASSWORD": "senha-do-primeiro-boot"})
        assert primeiro.returncode == 0, primeiro.stderr

        segundo = _rodar_import_app(tmp_dir, {})
        assert segundo.returncode == 0, segundo.stderr

        senha_hash = _senha_hash_do_admin(tmp_dir)
    assert check_password_hash(senha_hash, "senha-do-primeiro-boot")


# Nota: o cenario "dev local sem IR_FLOW_DATA_DIR usa o fallback sem falhar" nao tem
# teste automatizado aqui de proposito -- mesma razao de
# test_security_flask_secret_key_fallback.py (violaria o isolamento de testes,
# tocaria o database.db real do projeto). Verificado manualmente.
