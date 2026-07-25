"""
INC-002 — OS duplicada apos sincronizacao com Mercado Phone
(docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md).

Ultima camada de protecao: UNIQUE INDEX em os(origem_integracao, id_externo_integracao)
(app.py::criar_tabelas). O lock cross-processo (irflow_mercadophone.py) corrige o
mecanismo mais provavel do bug, mas este indice e a garantia definitiva no banco,
valendo contra qualquer outro caminho futuro de escrita.
"""

import sqlite3

import pytest

import app as _app


def _inserir_os(cursor, cliente, origem_integracao=None, id_externo_integracao=None):
    cursor.execute(
        "INSERT INTO os (tipo, cliente, origem_integracao, id_externo_integracao) VALUES (?, ?, ?, ?)",
        ("Assistencia", cliente, origem_integracao, id_externo_integracao),
    )


class TestUniqueIndexOsMercadoPhone:
    def test_bloqueia_id_externo_duplicado_na_mesma_origem(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            _inserir_os(cursor, "Cliente A", "mercado_phone", "UNIQTEST-1")
            conn.commit()

            with pytest.raises(sqlite3.IntegrityError):
                _inserir_os(cursor, "Cliente B", "mercado_phone", "UNIQTEST-1")
            conn.rollback()
        finally:
            conn.execute(
                "DELETE FROM os WHERE origem_integracao = 'mercado_phone' AND id_externo_integracao = 'UNIQTEST-1'"
            )
            conn.commit()
            conn.close()

    def test_permite_ids_externos_diferentes(self):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            _inserir_os(cursor, "Cliente A", "mercado_phone", "UNIQTEST-2")
            _inserir_os(cursor, "Cliente B", "mercado_phone", "UNIQTEST-3")
            conn.commit()  # nao deve levantar excecao
        finally:
            conn.execute(
                "DELETE FROM os WHERE origem_integracao = 'mercado_phone' AND id_externo_integracao IN ('UNIQTEST-2', 'UNIQTEST-3')"
            )
            conn.commit()
            conn.close()

    def test_os_nativas_sem_integracao_nao_conflitam_entre_si(self):
        # origem_integracao/id_externo_integracao NULL em ambas -- SQLite trata cada NULL
        # como distinto num indice UNIQUE, entao OS criadas direto no app (sem integracao)
        # nunca esbarram nesta restricao entre si.
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            ids_criados = []
            for i in range(5):
                _inserir_os(cursor, f"Cliente nativo {i}")
                ids_criados.append(cursor.lastrowid)
            conn.commit()  # nao deve levantar excecao
            assert len(ids_criados) == 5
        finally:
            conn.execute(
                "DELETE FROM os WHERE cliente LIKE 'Cliente nativo %'"
            )
            conn.commit()
            conn.close()
