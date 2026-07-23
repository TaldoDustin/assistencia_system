"""
INC-002 — OS duplicada apos sincronizacao com Mercado Phone
(docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md).

Causa estrutural: a thread de sincronizacao do Mercado Phone inicia uma vez por
processo do Gunicorn, sem coordenacao entre processos. Com --workers 2 em producao,
dois processos podiam rodar sincronizar_mercado_phone() ao mesmo tempo e, por o
importador so fazer SELECT-antes-de-INSERT (sem UNIQUE constraint como cinto de
seguranca), duplicar a mesma OS.

Este teste cobre o lock cross-processo adicionado em irflow_mercadophone.py:
adquirir_lock_sync_mercado_phone/liberar_lock_sync_mercado_phone, usando a tabela
integracao_sync_estado (ja existente) como lease com expiracao.
"""

import threading

import app as _app
from irflow_mercadophone import (
    adquirir_lock_sync_mercado_phone,
    liberar_lock_sync_mercado_phone,
    sincronizar_mercado_phone,
)


class TestLockSyncMercadoPhone:
    def teardown_method(self):
        # Garante que um teste que falhe no meio nao deixe o lock preso para o proximo.
        liberar_lock_sync_mercado_phone(_app.conectar)

    def test_segunda_aquisicao_falha_enquanto_a_primeira_nao_libera(self):
        assert adquirir_lock_sync_mercado_phone(_app.conectar, ttl_segundos=60) is True

        # Simula o segundo worker do Gunicorn tentando sincronizar ao mesmo tempo.
        assert adquirir_lock_sync_mercado_phone(_app.conectar, ttl_segundos=60) is False

    def test_lock_liberado_pode_ser_adquirido_de_novo(self):
        assert adquirir_lock_sync_mercado_phone(_app.conectar, ttl_segundos=60) is True
        liberar_lock_sync_mercado_phone(_app.conectar)

        assert adquirir_lock_sync_mercado_phone(_app.conectar, ttl_segundos=60) is True

    def test_lock_expirado_pode_ser_readquirido_sem_liberacao_explicita(self):
        # Simula um worker que caiu no meio da sincronizacao e nunca liberou o lock -
        # o lease expira sozinho, o sistema nao fica travado para sempre. Em vez de
        # esperar o TTL real passar (precisao de segundo, lento e nao-deterministico
        # em teste), forca o valor armazenado para uma data no passado, exatamente
        # como um lease legitimamente expirado ficaria.
        assert adquirir_lock_sync_mercado_phone(_app.conectar, ttl_segundos=60) is True
        conn = _app.conectar()
        try:
            conn.execute(
                "UPDATE integracao_sync_estado SET valor=? WHERE chave='mercado_phone_sync_lock'",
                ("2000-01-01 00:00:00",),
            )
            conn.commit()
        finally:
            conn.close()

        assert adquirir_lock_sync_mercado_phone(_app.conectar, ttl_segundos=60) is True

    def test_sincronizar_mercado_phone_nao_compete_quando_lock_ocupado(self):
        assert adquirir_lock_sync_mercado_phone(_app.conectar, ttl_segundos=60) is True

        # Se sincronizar_mercado_phone tentasse sincronizar mesmo com o lock ocupado,
        # isso levantaria excecao de rede (sem token/API real configurados no teste) -
        # retornar lock_ocupado=True sem tentar prova que o curto-circuito aconteceu
        # antes de qualquer chamada externa.
        resultado = sincronizar_mercado_phone(_app.conectar, config=None, helpers=None)

        assert resultado == {
            "ok": True,
            "importadas": 0,
            "ignoradas": 0,
            "inicializada": True,
            "lock_ocupado": True,
        }

    def test_apenas_um_vence_a_corrida_entre_dois_workers_simultaneos(self):
        # Reproduz o cenario real de INC-002: dois processos (aqui, threads com conexao
        # propria cada, simulando os 2 workers do Gunicorn) tentam adquirir o lock no
        # mesmo instante. Sem o lock, ambos passariam pelo SELECT-antes-de-INSERT do
        # importador e duplicariam a OS. Com o lock, exatamente um vence.
        resultados = []
        lock_resultados = threading.Lock()
        partida = threading.Barrier(2)

        def tentar_adquirir():
            partida.wait()
            ganhou = adquirir_lock_sync_mercado_phone(_app.conectar, ttl_segundos=60)
            with lock_resultados:
                resultados.append(ganhou)

        threads = [threading.Thread(target=tentar_adquirir) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert sorted(resultados) == [False, True]
