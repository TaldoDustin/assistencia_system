import os
import tempfile
import uuid

# Must be set before importing app — DB_PATH is resolved at module load time
_tmp_dir = tempfile.mkdtemp()
os.environ["IR_FLOW_DATA_DIR"] = _tmp_dir
os.environ["IR_FLOW_ENABLE_BACKGROUND_JOBS"] = "0"
os.environ["MERCADO_PHONE_SYNC_ENABLED"] = "0"

import pytest  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

import app as _app  # noqa: E402

SENHA_PADRAO = "senha_teste_123"


@pytest.fixture(scope="session")
def app():
    _app.app.config["TESTING"] = True
    _app.app.config["WTF_CSRF_ENABLED"] = False
    _app.criar_tabelas()
    yield _app.app


@pytest.fixture
def client(app):
    """Cliente HTTP isolado por teste — nao reutiliza sessao de outros testes."""
    return app.test_client()


def _criar_usuario(nome, perfil="tecnico", ativo=1):
    login = f"user_{uuid.uuid4().hex[:10]}"
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, usuario, senha_hash, perfil, ativo) VALUES (?, ?, ?, ?, ?)",
            (nome, login, generate_password_hash(SENHA_PADRAO), perfil, ativo),
        )
        conn.commit()
        user_id = cursor.lastrowid
    finally:
        conn.close()
    return {"id": user_id, "nome": nome, "usuario": login, "senha": SENHA_PADRAO}


def _remover_usuario(user_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def usuario_tecnico():
    dados = _criar_usuario("Tecnico Teste", perfil="tecnico", ativo=1)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def usuario_admin():
    dados = _criar_usuario("Admin Teste", perfil="admin", ativo=1)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def usuario_vendedor():
    dados = _criar_usuario("Vendedor Teste", perfil="vendedor", ativo=1)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def usuario_inativo():
    dados = _criar_usuario("Usuario Inativo", perfil="tecnico", ativo=0)
    yield dados
    _remover_usuario(dados["id"])


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
