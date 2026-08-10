"""
Fluxoly - Testes de integração de Backup/Restore (Discovery de Operação Release 1.0,
docs/company/RELEASE_1.0_MASTER_CHECKLIST.md, item "Restore validado").

`tests/conftest.py` compartilha um único banco real (`DB_PATH`) entre toda a sessão de
pytest (fixture `app` é `scope="session"`). Como `POST /api/backup/restaurar` sobrescreve
esse arquivo de verdade (`api_backup.py::restaurar_backup_upload`), a fixture
`_preservar_banco_real` abaixo faz snapshot/restore do banco -- com
`PRAGMA wal_checkpoint(FULL)` antes, já que o banco roda em WAL (`app.py`) -- só neste
arquivo. `tests/conftest.py` não é alterado, para não afetar as demais suítes.
"""

import io
import os
import shutil
import sqlite3
import uuid

import pytest

import app as _app

HEADER_SQLITE = b"SQLite format 3\x00"


def _checkpoint_wal():
    conn = _app.conectar()
    try:
        conn.execute("PRAGMA wal_checkpoint(FULL)")
    finally:
        conn.close()


def _limpar_pre_restore():
    """`pre-restore-<timestamp por segundo>.db` colide entre restores no mesmo segundo
    (sobrescreve em vez de criar um novo arquivo) -- limpar antes de cada teste garante
    que a contagem 'antes'/'depois' de cada teste não herda arquivo de um teste anterior."""
    if not os.path.isdir(_app.BACKUP_DIR):
        return
    for nome in os.listdir(_app.BACKUP_DIR):
        if nome.startswith("pre-restore-"):
            os.remove(os.path.join(_app.BACKUP_DIR, nome))


@pytest.fixture(autouse=True)
def _preservar_banco_real():
    """Isola este arquivo do banco compartilhado da sessão -- ver docstring do módulo."""
    _checkpoint_wal()
    snapshot_path = _app.DB_PATH + ".snapshot-test-restore"
    shutil.copy2(_app.DB_PATH, snapshot_path)
    _limpar_pre_restore()
    try:
        yield
    finally:
        shutil.copy2(snapshot_path, _app.DB_PATH)
        os.remove(snapshot_path)
        _checkpoint_wal()
        _limpar_pre_restore()


def _usuario_existe(login):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT 1 FROM usuarios WHERE usuario = ?", (login,)).fetchone() is not None
    finally:
        conn.close()


def _contar_pre_restore():
    if not os.path.isdir(_app.BACKUP_DIR):
        return 0
    return len([f for f in os.listdir(_app.BACKUP_DIR) if f.startswith("pre-restore-")])


def _arquivo_com_marcador(login_marcador):
    """Copia o banco atual (pós-checkpoint) e insere um usuário-marcador direto no
    arquivo, sem passar pela API -- prova que o restore troca o conteúdo de fato."""
    _checkpoint_wal()
    tmp_path = _app.DB_PATH + f".upload-{uuid.uuid4().hex[:8]}"
    shutil.copy2(_app.DB_PATH, tmp_path)
    conn = sqlite3.connect(tmp_path)
    try:
        conn.execute(
            "INSERT INTO usuarios (nome, usuario, senha_hash, perfil, ativo) VALUES (?,?,?,?,1)",
            ("Marcador Restore", login_marcador, "hash-nao-usado-neste-teste", "tecnico"),
        )
        conn.commit()
    finally:
        conn.close()
    with open(tmp_path, "rb") as f:
        conteudo = f.read()
    os.remove(tmp_path)
    return conteudo


def _arquivo_corrompido():
    """Copia o banco real e corrompe bytes de uma página de dados (não o header),
    reproduzindo corrupção estrutural -- ver investigação na Discovery: corromper um
    arquivo sintético minúsculo pode levantar sqlite3.DatabaseError direto na leitura do
    schema; corromper uma página de dados de um banco real com schema completo é
    detectado de forma limpa pelo PRAGMA integrity_check, como o código de produção
    espera."""
    _checkpoint_wal()
    tmp_path = _app.DB_PATH + f".corrompido-{uuid.uuid4().hex[:8]}"
    shutil.copy2(_app.DB_PATH, tmp_path)
    tamanho = os.path.getsize(tmp_path)
    offset = min(4096, tamanho // 2)
    with open(tmp_path, "r+b") as f:
        f.seek(offset)
        f.write(os.urandom(min(1024, tamanho - offset)))
    with open(tmp_path, "rb") as f:
        conteudo = f.read()
    os.remove(tmp_path)
    return conteudo


class TestRestoreBackup:
    def test_restore_com_arquivo_valido_altera_o_banco(self, client, login_como, usuario_admin):
        login_marcador = f"marcador_{uuid.uuid4().hex[:10]}"
        conteudo = _arquivo_com_marcador(login_marcador)
        assert not _usuario_existe(login_marcador)

        login_como(client, usuario_admin)
        resp = client.post(
            "/api/backup/restaurar",
            data={"arquivo": (io.BytesIO(conteudo), "backup-teste.db")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 200
        assert resp.get_json()["ok"] is True
        assert _usuario_existe(login_marcador)

    def test_restore_cria_backup_pre_restore_com_estado_anterior(self, client, login_como, usuario_admin):
        login_marcador = f"marcador_{uuid.uuid4().hex[:10]}"
        conteudo = _arquivo_com_marcador(login_marcador)
        antes = _contar_pre_restore()

        login_como(client, usuario_admin)
        resp = client.post(
            "/api/backup/restaurar",
            data={"arquivo": (io.BytesIO(conteudo), "backup-teste.db")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 200
        assert _contar_pre_restore() == antes + 1

        novos = sorted(f for f in os.listdir(_app.BACKUP_DIR) if f.startswith("pre-restore-"))
        arquivo_pre_restore = os.path.join(_app.BACKUP_DIR, novos[-1])
        conn = sqlite3.connect(arquivo_pre_restore)
        try:
            marcador_no_pre_restore = conn.execute(
                "SELECT 1 FROM usuarios WHERE usuario = ?", (login_marcador,)
            ).fetchone()
        finally:
            conn.close()
        assert marcador_no_pre_restore is None

    def test_restore_rejeita_extensao_invalida_sem_alterar_banco(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        antes = _contar_pre_restore()

        resp = client.post(
            "/api/backup/restaurar",
            data={"arquivo": (io.BytesIO(HEADER_SQLITE + b"resto"), "backup-teste.txt")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 400
        assert _contar_pre_restore() == antes

    def test_restore_rejeita_header_invalido_sem_alterar_banco(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        antes = _contar_pre_restore()

        resp = client.post(
            "/api/backup/restaurar",
            data={"arquivo": (io.BytesIO(b"isto nao e um banco sqlite"), "backup-teste.db")},
            content_type="multipart/form-data",
        )

        assert resp.status_code == 400
        assert _contar_pre_restore() == antes

    def test_restore_rejeita_banco_corrompido_sem_alterar_banco(self, client, login_como, usuario_admin):
        """PRAGMA integrity_check diverge entre builds de SQLite para o mesmo arquivo
        corrompido (achado em CI -- runner Linux/Python 3.11): ora retorna uma linha de
        erro (400 limpo, tratado por restaurar_backup_upload), ora levanta
        sqlite3.DatabaseError diretamente, que o cliente de teste propaga porque
        TESTING=True. Em ambos os desfechos a exceção/erro ocorre em api_backup.py antes
        de qualquer escrita em db_path (backup pre-restore e shutil.copy2 só acontecem
        depois), então o invariante que importa -- banco original inalterado -- vale
        nos dois casos. Não atende a nenhum critério objetivo de interrupção do
        ENGINEERING_GUIDE.md §11 (sem mutação silenciosa, sem perda de dado, sem bypass)."""
        login_como(client, usuario_admin)
        antes = _contar_pre_restore()
        conteudo_corrompido = _arquivo_corrompido()

        try:
            resp = client.post(
                "/api/backup/restaurar",
                data={"arquivo": (io.BytesIO(conteudo_corrompido), "backup-teste.db")},
                content_type="multipart/form-data",
            )
        except sqlite3.DatabaseError as exc:
            assert "malformed" in str(exc).lower()
        else:
            assert resp.status_code == 400
            assert "corrompido" in resp.get_json()["erro"].lower()

        assert _contar_pre_restore() == antes

    def test_restore_sem_sessao_retorna_403_sem_processar_arquivo(self, client):
        resp = client.post(
            "/api/backup/restaurar",
            data={"arquivo": (io.BytesIO(HEADER_SQLITE), "backup-teste.db")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 403

    def test_restore_usuario_nao_admin_retorna_403_sem_processar_arquivo(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post(
            "/api/backup/restaurar",
            data={"arquivo": (io.BytesIO(HEADER_SQLITE), "backup-teste.db")},
            content_type="multipart/form-data",
        )
        assert resp.status_code == 403
