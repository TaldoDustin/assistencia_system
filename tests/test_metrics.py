"""
Testes de /metrics (Sprint Observabilidade, 2026-07-25).

Nota: tests/conftest.py define IR_FLOW_DATA_DIR, o que liga
IS_SERVER_RUNTIME=True durante toda a suíte (mesmo comportamento de
produção) -- diferente do que se poderia supor ("ambiente de teste = sem
token"), o endpoint exige METRICS_TOKEN por padrão nos testes também,
igual em produção. Isso é bom: exercita o caminho real de autorização.
"""

import os


class TestMetricsAutorizacao:
    def test_sem_metrics_token_configurado_retorna_401(self, client, monkeypatch):
        monkeypatch.delenv("METRICS_TOKEN", raising=False)

        resp = client.get("/metrics")

        assert resp.status_code == 401

    def test_com_token_configurado_mas_header_ausente_retorna_401(self, client, monkeypatch):
        monkeypatch.setenv("METRICS_TOKEN", "segredo-teste")

        resp = client.get("/metrics")

        assert resp.status_code == 401

    def test_com_token_configurado_e_header_errado_retorna_401(self, client, monkeypatch):
        monkeypatch.setenv("METRICS_TOKEN", "segredo-teste")

        resp = client.get("/metrics", headers={"X-Metrics-Token": "errado"})

        assert resp.status_code == 401

    def test_com_token_correto_retorna_200_formato_prometheus(self, client, monkeypatch):
        monkeypatch.setenv("METRICS_TOKEN", "segredo-teste")

        resp = client.get("/metrics", headers={"X-Metrics-Token": "segredo-teste"})

        assert resp.status_code == 200
        assert b"# HELP" in resp.data
        assert b"http_requests_total" in resp.data


class TestMetricsConteudo:
    def test_metrica_reflete_requests_anteriores(self, client, monkeypatch):
        monkeypatch.setenv("METRICS_TOKEN", "segredo-teste")
        headers = {"X-Metrics-Token": "segredo-teste"}

        client.get("/api/constantes")
        client.get("/api/constantes")

        resp = client.get("/metrics", headers=headers)

        corpo = resp.data.decode()
        assert 'route="/api/constantes"' in corpo

    def test_modo_single_process_sem_prometheus_multiproc_dir(self, client, monkeypatch):
        monkeypatch.delenv("PROMETHEUS_MULTIPROC_DIR", raising=False)
        monkeypatch.setenv("METRICS_TOKEN", "segredo-teste")

        resp = client.get("/metrics", headers={"X-Metrics-Token": "segredo-teste"})

        assert resp.status_code == 200
        assert os.environ.get("PROMETHEUS_MULTIPROC_DIR") is None
