"""
Testes de auditoria central (Sprint 3 — Unidade 3).

Escopo: `irflow_audit.py::registrar_log_auditoria` e a tabela `audit_log`.
Testado no nível de service (sem HTTP) — nenhum endpoint real consome isso
ainda; Clientes e `estoque_unidades` (Unidades 5 e 6) serão os primeiros
consumidores.

`shopping_list_logs` não é tocado por esta unidade — continua com sua
própria tabela/helper (`_log_shopping`), sem migração.
"""

import app as _app
from irflow_audit import registrar_log_auditoria


def _buscar_logs(entidade, entidade_id=None):
    conn = _app.conectar()
    try:
        if entidade_id is not None:
            rows = conn.execute(
                "SELECT entidade, entidade_id, usuario_id, acao, valor_anterior, valor_novo "
                "FROM audit_log WHERE entidade=? AND entidade_id=? ORDER BY id",
                (entidade, entidade_id),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT entidade, entidade_id, usuario_id, acao, valor_anterior, valor_novo "
                "FROM audit_log WHERE entidade=? ORDER BY id",
                (entidade,),
            ).fetchall()
        return rows
    finally:
        conn.close()


def _limpar(entidade):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade=?", (entidade,))
        conn.commit()
    finally:
        conn.close()


class TestRegistrarLogAuditoria:
    def test_grava_linha_com_campos_corretos(self):
        entidade = "teste_simples"
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            registrar_log_auditoria(cursor, entidade, 42, 7, "create", antes=None, depois={"nome": "Teste"})
            conn.commit()
        finally:
            conn.close()

        linhas = _buscar_logs(entidade, 42)
        assert len(linhas) == 1
        assert linhas[0][0] == entidade
        assert linhas[0][1] == 42
        assert linhas[0][2] == 7
        assert linhas[0][3] == "create"
        assert linhas[0][4] is None
        assert '"nome": "Teste"' in linhas[0][5]
        _limpar(entidade)

    def test_serializa_dict_como_json_e_aceita_string_direta(self):
        entidade = "teste_serializacao"
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            registrar_log_auditoria(
                cursor, entidade, 1, 1, "update", antes={"status": "A"}, depois="ja-e-string"
            )
            conn.commit()
        finally:
            conn.close()

        linhas = _buscar_logs(entidade, 1)
        assert '"status": "A"' in linhas[0][4]
        assert linhas[0][5] == "ja-e-string"
        _limpar(entidade)

    def test_valor_nao_serializavel_cai_para_str_em_vez_de_lancar_excecao(self):
        entidade = "teste_fallback"

        class NaoSerializavel:
            def __repr__(self):
                return "<NaoSerializavel>"

        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            registrar_log_auditoria(cursor, entidade, 1, 1, "create", depois=NaoSerializavel())
            conn.commit()
        finally:
            conn.close()

        linhas = _buscar_logs(entidade, 1)
        assert "NaoSerializavel" in linhas[0][5]
        _limpar(entidade)

    def test_entidades_diferentes_nao_se_confundem(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            registrar_log_auditoria(cursor, "cliente", 1, 1, "create")
            registrar_log_auditoria(cursor, "estoque_unidade", 1, 1, "create")
            conn.commit()
        finally:
            conn.close()

        assert len(_buscar_logs("cliente")) == 1
        assert len(_buscar_logs("estoque_unidade")) == 1
        _limpar("cliente")
        _limpar("estoque_unidade")

    def test_usuario_id_none_e_aceito(self):
        entidade = "teste_sem_usuario"
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            registrar_log_auditoria(cursor, entidade, 1, None, "create")
            conn.commit()
        finally:
            conn.close()

        linhas = _buscar_logs(entidade, 1)
        assert linhas[0][2] is None
        _limpar(entidade)
