"""
INC-001 -- causa raiz confirmada em producao (2026-08-05,
docs/operations/INCIDENTS/INC-001-database-is-locked.md).

_sincronizar_mercado_phone_sem_lock() mantinha uma unica transacao de escrita aberta
durante todo o loop de sincronizacao (ate centenas de registros, cada um com uma
chamada HTTP externa para a API do Mercado Phone), so comitando no final -- qualquer
outro escritor (ex.: POST /api/auth/login) esperava o busy_timeout inteiro (30s) e
falhava com "database is locked" enquanto o ciclo estivesse em andamento. Corrigido
movendo o commit para dentro do loop (finally por registro), preservando a
atomicidade de cada registro (ja isolado pelo try/except existente).

Este teste prova o fix diretamente: verifica, a partir de uma conexao nova, que um
registro ja processado esta visivel (comitado) antes do proximo registro do loop
comecar a ser processado -- o que so e verdade se o commit acontece por registro,
nao so no final.
"""

import app as _app
import fluxoly_mercadophone


class TestINC001MercadoPhoneCommitPorRegistro:
    def test_commit_acontece_apos_cada_registro_nao_so_no_final_do_loop(self, monkeypatch):
        ids = ["90001", "90002", "90003"]
        visibilidade_observada = {}

        def fake_listar(config, page=1, limit=300):
            return {"data": [{"id": i} for i in ids]} if page == 1 else {"data": []}

        def fake_extrair_ids(payload, texto_limpo):
            return [item["id"] for item in payload.get("data", [])]

        def fake_detalhar(external_id, config):
            # No momento em que o loop pede os detalhes de um registro que nao o
            # primeiro, o registro anterior ja deveria estar commitado (visivel numa
            # conexao nova) se o commit acontece por registro -- prova direta do fix.
            # Antes da correcao, essa checagem falharia (False) porque a transacao
            # so era commitada apos o loop inteiro terminar.
            idx = ids.index(external_id)
            if idx > 0:
                anterior = ids[idx - 1]
                conn_verificacao = _app.conectar()
                try:
                    cursor_verificacao = conn_verificacao.cursor()
                    cursor_verificacao.execute(
                        "SELECT COUNT(1) FROM os WHERE origem_integracao='mercado_phone' AND id_externo_integracao=?",
                        (anterior,),
                    )
                    visibilidade_observada[anterior] = cursor_verificacao.fetchone()[0] > 0
                finally:
                    conn_verificacao.close()
            return {"id": external_id}

        def fake_importar(cursor, payload, config, helpers, fallback_external_id=""):
            ext_id = payload.get("id") or fallback_external_id
            cursor.execute(
                "INSERT INTO os (tipo, cliente, status, origem_integracao, id_externo_integracao, data) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                ("Assistencia", "Teste INC-001", "Em andamento", "mercado_phone", str(ext_id), "2026-08-05"),
            )
            return {"atualizada": False}

        monkeypatch.setattr(fluxoly_mercadophone, "listar_os_mercado_phone", fake_listar)
        monkeypatch.setattr(fluxoly_mercadophone, "extrair_ids_os_listagem_mercado_phone", fake_extrair_ids)
        monkeypatch.setattr(fluxoly_mercadophone, "detalhar_os_mercado_phone", fake_detalhar)
        monkeypatch.setattr(fluxoly_mercadophone, "importar_os_mercado_phone", fake_importar)

        config = {"sync_max_pages": 100, "sync_only_after_boot": False}
        helpers = {"texto_limpo": lambda s: s}

        resultado = fluxoly_mercadophone._sincronizar_mercado_phone_sem_lock(_app.conectar, config, helpers)

        assert resultado["importadas"] == 3
        assert resultado["ignoradas"] == 0
        # As duas verificacoes intermediarias (antes de processar 90002 e 90003)
        # confirmam que o registro anterior ja estava commitado -- se o commit so
        # acontecesse no final do loop inteiro (comportamento anterior ao fix), essas
        # entradas seriam False.
        assert visibilidade_observada == {"90001": True, "90002": True}
