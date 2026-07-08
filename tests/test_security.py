"""
Testes de resiliencia de entrada em /api/auth/login (Sprint 2.3): SQL
injection, campos obrigatorios ausentes, payload vazio, JSON invalido e
Content-Type incorreto.

O endpoint usa consultas parametrizadas (cursor.execute("... WHERE usuario
= ?", (usuario_txt,))) e request.get_json(silent=True) — estes testes
confirmam que entradas hostis ou malformadas resultam em 400/401
previsiveis, nunca em 500 ou em autenticacao indevida.
"""

import json

import app as _app


def _contar_usuarios():
    conn = _app.conectar()
    try:
        return conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
    finally:
        conn.close()


# ============================================================================
# SQL Injection
# ============================================================================


class TestSqlInjectionNoLogin:
    def test_tautologia_classica_no_usuario_e_senha_nao_autentica(self, client):
        resp = client.post(
            "/api/auth/login",
            json={"usuario": "' OR '1'='1", "senha": "' OR '1'='1"},
        )

        assert resp.status_code == 401
        assert resp.get_json()["ok"] is False

    def test_tentativa_de_drop_table_nao_autentica_e_preserva_tabela(self, client, usuario_tecnico):
        total_antes = _contar_usuarios()

        resp = client.post(
            "/api/auth/login",
            json={"usuario": "x'; DROP TABLE usuarios; --", "senha": "qualquer"},
        )

        assert resp.status_code == 401
        assert _contar_usuarios() == total_antes

    def test_comentario_sql_no_campo_usuario_nao_bypassa_senha(self, client, usuario_tecnico):
        resp = client.post(
            "/api/auth/login",
            json={"usuario": f"{usuario_tecnico['usuario']}' --", "senha": "senha_qualquer"},
        )

        assert resp.status_code == 401

    def test_uniao_maliciosa_no_campo_usuario_nao_autentica(self, client):
        resp = client.post(
            "/api/auth/login",
            json={
                "usuario": "' UNION SELECT id, nome, senha_hash, perfil, 1 FROM usuarios --",
                "senha": "x",
            },
        )

        assert resp.status_code == 401


# ============================================================================
# Campos obrigatorios ausentes / payload vazio
# ============================================================================


class TestCamposObrigatorios:
    def test_payload_vazio_retorna_400(self, client):
        resp = client.post("/api/auth/login", json={})

        assert resp.status_code == 400
        assert resp.get_json()["ok"] is False

    def test_sem_campo_senha_retorna_400(self, client):
        resp = client.post("/api/auth/login", json={"usuario": "alguem"})

        assert resp.status_code == 400

    def test_sem_campo_usuario_retorna_400(self, client):
        resp = client.post("/api/auth/login", json={"senha": "senha123"})

        assert resp.status_code == 400

    def test_campos_so_com_espacos_retorna_400(self, client):
        resp = client.post("/api/auth/login", json={"usuario": "   ", "senha": "   "})

        assert resp.status_code == 400

    def test_sem_corpo_nenhum_retorna_400_nao_500(self, client):
        resp = client.post("/api/auth/login")

        assert resp.status_code == 400


# ============================================================================
# JSON invalido
# ============================================================================


class TestJsonInvalido:
    def test_json_malformado_com_content_type_correto_retorna_400_nao_500(self, client):
        resp = client.post(
            "/api/auth/login",
            data="{usuario: 'sem aspas', senha:}",
            content_type="application/json",
        )

        assert resp.status_code == 400

    def test_corpo_binario_arbitrario_retorna_400_nao_500(self, client):
        resp = client.post(
            "/api/auth/login",
            data=b"\x00\x01\x02\xff\xfe",
            content_type="application/json",
        )

        assert resp.status_code == 400


# ============================================================================
# Content-Type incorreto
# ============================================================================


class TestContentTypeIncorreto:
    def test_form_urlencoded_com_credenciais_validas_nao_autentica_via_json(self, client, usuario_tecnico):
        """
        /api/auth/login so le request.get_json() — um corpo form-urlencoded,
        mesmo com credenciais validas, nao e interpretado como JSON.
        """
        resp = client.post(
            "/api/auth/login",
            data={"usuario": usuario_tecnico["usuario"], "senha": usuario_tecnico["senha"]},
        )

        assert resp.status_code == 400

    def test_json_valido_com_content_type_text_plain_retorna_400_nao_500(self, client, usuario_tecnico):
        resp = client.post(
            "/api/auth/login",
            data=json.dumps({"usuario": usuario_tecnico["usuario"], "senha": usuario_tecnico["senha"]}),
            content_type="text/plain",
        )

        assert resp.status_code == 400

    def test_content_type_ausente_retorna_400_nao_500(self, client, usuario_tecnico):
        resp = client.post(
            "/api/auth/login",
            data=f'{{"usuario": "{usuario_tecnico["usuario"]}", "senha": "{usuario_tecnico["senha"]}"}}',
            content_type=None,
        )

        assert resp.status_code == 400
