import os
import tempfile

# Must be set before importing app — DB_PATH is resolved at module load time
_tmp_dir = tempfile.mkdtemp()
os.environ["IR_FLOW_DATA_DIR"] = _tmp_dir
os.environ["IR_FLOW_ENABLE_BACKGROUND_JOBS"] = "0"
os.environ["MERCADO_PHONE_SYNC_ENABLED"] = "0"

import pytest  # noqa: E402

import app as _app  # noqa: E402


@pytest.fixture(scope="session")
def app():
    _app.app.config["TESTING"] = True
    _app.app.config["WTF_CSRF_ENABLED"] = False
    _app.criar_tabelas()
    yield _app.app


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def auth_client(app):
    client = app.test_client()
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        from werkzeug.security import generate_password_hash

        cursor.execute(
            "INSERT OR IGNORE INTO usuarios (nome, usuario, senha_hash, perfil) VALUES (?, ?, ?, ?)",
            ("Admin Teste", "admin_test", generate_password_hash("test_senha_123"), "admin"),
        )
        conn.commit()
    finally:
        conn.close()

    client.post("/login", data={"usuario": "admin_test", "senha": "test_senha_123"}, follow_redirects=True)
    return client
