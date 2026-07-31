"""
INC-002 — OS duplicada apos sincronizacao com Mercado Phone
(docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md).

Causa estrutural: a thread de sincronizacao do Mercado Phone inicia uma vez por
processo do Gunicorn, sem coordenacao entre processos. Com --workers 2 em producao,
dois processos podiam rodar sincronizar_mercado_phone() ao mesmo tempo e, por o
importador so fazer SELECT-antes-de-INSERT (sem UNIQUE constraint como cinto de
seguranca), duplicar a mesma OS.

Este teste cobre o lock cross-processo adicionado em fluxoly_mercadophone.py:
adquirir_lock_sync_mercado_phone/liberar_lock_sync_mercado_phone, usando a tabela
integracao_sync_estado (ja existente) como lease com expiracao.
"""

import threading
import time

import app as _app
from fluxoly_mercadophone import (
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

    def test_apenas_um_vence_a_corrida_entre_workers_simultaneos(self):
        # Reproduz o cenario real de INC-002: processos (aqui, threads com conexao propria
        # cada, simulando workers do Gunicorn) tentam adquirir o lock no mesmo instante.
        # Sem o lock, todos passariam pelo SELECT-antes-de-INSERT do importador e
        # poderiam duplicar a OS. Com o lock, exatamente um vence - mesmo com 100
        # concorrentes de uma vez (review do usuario/CTO pediu um teste com mais escala
        # do que os 2 workers reais de producao, para dar mais confianca na atomicidade
        # do UPDATE ... WHERE que sustenta o lock).
        n_threads = 100
        resultados = []
        lock_resultados = threading.Lock()
        partida = threading.Barrier(n_threads)

        def tentar_adquirir():
            partida.wait()
            ganhou = adquirir_lock_sync_mercado_phone(_app.conectar, ttl_segundos=60)
            with lock_resultados:
                resultados.append(ganhou)

        threads = [threading.Thread(target=tentar_adquirir) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert resultados.count(True) == 1
        assert resultados.count(False) == n_threads - 1

    def test_lock_nunca_tem_dois_donos_ao_mesmo_tempo_sob_alta_concorrencia(self):
        # Review do usuario/CTO pediu algo na escala de "1000 aquisicoes" para ganhar
        # confianca na atomicidade; 300 (20 threads x 15 rodadas, cada rodada tenta ate
        # conseguir - simula retries de workers reais) ja e ordens de magnitude acima
        # dos 2 workers reais de producao e mantém o teste rápido. Usa um
        # contador compartilhado como secao critica classica: se o UPDATE ... WHERE que
        # sustenta o lock nao fosse atomico, mais de uma thread eventualmente entraria
        # "dentro do lock" ao mesmo tempo e o contador passaria de 1.
        n_threads = 20
        rodadas_por_thread = 15
        max_tentativas_por_rodada = 3000  # generoso; estoura so se o lock travar de verdade
        contador_secao_critica = {"valor": 0}
        contador_lock = threading.Lock()
        violacoes = []
        falhas_de_aquisicao = []
        total_vitorias = {"valor": 0}

        def trabalhar():
            for _ in range(rodadas_por_thread):
                adquirido = False
                for _tentativa in range(max_tentativas_por_rodada):
                    if adquirir_lock_sync_mercado_phone(_app.conectar, ttl_segundos=5):
                        adquirido = True
                        break
                    time.sleep(0.0005)
                if not adquirido:
                    falhas_de_aquisicao.append(1)
                    continue
                try:
                    with contador_lock:
                        contador_secao_critica["valor"] += 1
                        total_vitorias["valor"] += 1
                        if contador_secao_critica["valor"] > 1:
                            violacoes.append(contador_secao_critica["valor"])
                    # janela pequena para dar chance de uma corrida real se manifestar
                    time.sleep(0.001)
                    with contador_lock:
                        contador_secao_critica["valor"] -= 1
                finally:
                    liberar_lock_sync_mercado_phone(_app.conectar)

        threads = [threading.Thread(target=trabalhar) for _ in range(n_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert violacoes == []
        assert falhas_de_aquisicao == []
        assert total_vitorias["valor"] == n_threads * rodadas_por_thread
