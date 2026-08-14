"""
Testes do guard de KI-037 (docs/operations/KNOWN_ISSUES.md) --
docs/engineering/plans/PLAN-ambiente-demo-homologacao.md.

Antes desta correcao, os endpoints manuais de api_mercadophone.py
(sincronizar/reprocessar/reimportar/config) so checavam permissao de perfil
(KI-022) -- uma sessao admin/tecnico real dentro de um Preview ou do Demo
conseguia disparar a integracao real com o MERCADO_PHONE_API_TOKEN herdado.
`integracao_externa_bloqueada_neste_ambiente()` (fluxoly_config.py) fecha essa
lacuna para os 4 endpoints, sem alterar quem tem permissao de acesso e sem
tocar em status_mercadophone (so leitura).

IS_PULL_REQUEST/IS_DEMO_ENVIRONMENT sao lidos por
`integracao_externa_bloqueada_neste_ambiente()` diretamente do namespace do
modulo fluxoly_config a cada chamada -- monkeypatch nesses atributos altera o
comportamento do guard mesmo com o app ja importado uma vez por sessao
(conftest.py), sem precisar de subprocesso.
"""

import fluxoly_config

ENDPOINTS_ADMIN_OU_TECNICO = [
    "/api/integracoes/mercadophone/sincronizar",
    "/api/integracoes/mercadophone/reprocessar",
    "/api/integracoes/mercadophone/reimportar",
]
ENDPOINT_CONFIG = "/api/integracoes/mercadophone/config"
ENDPOINT_STATUS = "/api/integracoes/mercadophone/status"


def _login_legado(client, usuario):
    return client.post("/login", data={"usuario": usuario["usuario"], "senha": usuario["senha"]})


class TestGuardBloqueiaEmPreview:
    def test_admin_recebe_403_nos_4_endpoints_com_is_pull_request(self, client, usuario_admin, monkeypatch):
        monkeypatch.setattr(fluxoly_config, "IS_PULL_REQUEST", True)
        _login_legado(client, usuario_admin)

        for endpoint in ENDPOINTS_ADMIN_OU_TECNICO:
            resp = client.post(endpoint)
            assert resp.status_code == 403, endpoint
            assert "ambiente" in resp.get_json()["erro"].lower()

        resp = client.post(ENDPOINT_CONFIG, json={"api_token": "token-que-nao-pode-ser-salvo"})
        assert resp.status_code == 403
        assert "ambiente" in resp.get_json()["erro"].lower()

    def test_config_bloqueado_nao_grava_nada(self, client, usuario_admin, monkeypatch):
        monkeypatch.setattr(fluxoly_config, "IS_PULL_REQUEST", True)
        _login_legado(client, usuario_admin)

        resp = client.post(ENDPOINT_CONFIG, json={"api_token": "token-que-nao-pode-ser-salvo"})
        assert resp.status_code == 403

        status = client.get(ENDPOINT_STATUS).get_json()
        assert status["mercado_phone"]["tem_token"] is False


class TestGuardBloqueiaEmDemo:
    def test_admin_recebe_403_nos_4_endpoints_com_ir_flow_environment_demo(self, client, usuario_admin, monkeypatch):
        monkeypatch.setattr(fluxoly_config, "IS_DEMO_ENVIRONMENT", True)
        _login_legado(client, usuario_admin)

        for endpoint in ENDPOINTS_ADMIN_OU_TECNICO:
            resp = client.post(endpoint)
            assert resp.status_code == 403, endpoint
            assert "ambiente" in resp.get_json()["erro"].lower()

        resp = client.post(ENDPOINT_CONFIG, json={"api_token": "token-que-nao-pode-ser-salvo"})
        assert resp.status_code == 403
        assert "ambiente" in resp.get_json()["erro"].lower()

    def test_tecnico_recebe_403_nos_3_endpoints_com_ir_flow_environment_demo(self, client, usuario_tecnico, monkeypatch):
        monkeypatch.setattr(fluxoly_config, "IS_DEMO_ENVIRONMENT", True)
        _login_legado(client, usuario_tecnico)

        for endpoint in ENDPOINTS_ADMIN_OU_TECNICO:
            resp = client.post(endpoint)
            assert resp.status_code == 403, endpoint


class TestStatusMercadophoneContinuaAcessivelNosTresAmbientes:
    def test_leitura_de_status_nao_e_bloqueada_por_preview_nem_demo(self, client, usuario_admin, monkeypatch):
        _login_legado(client, usuario_admin)

        resp = client.get(ENDPOINT_STATUS)
        assert resp.status_code == 200

        monkeypatch.setattr(fluxoly_config, "IS_PULL_REQUEST", True)
        resp = client.get(ENDPOINT_STATUS)
        assert resp.status_code == 200

        monkeypatch.setattr(fluxoly_config, "IS_PULL_REQUEST", False)
        monkeypatch.setattr(fluxoly_config, "IS_DEMO_ENVIRONMENT", True)
        resp = client.get(ENDPOINT_STATUS)
        assert resp.status_code == 200


class TestSemRegressaoForaDePreviewEDemo:
    """Produção/dev: nenhuma das duas flags está setada -- comportamento dos
    4 endpoints precisa continuar idêntico ao de antes desta correção (só a
    checagem de permissão já existente, KI-022)."""

    def test_admin_passa_do_guard_e_chega_na_checagem_de_configuracao(self, client, usuario_admin):
        _login_legado(client, usuario_admin)

        for endpoint in ENDPOINTS_ADMIN_OU_TECNICO:
            resp = client.post(endpoint)
            assert resp.status_code == 400, endpoint
            assert "não configurado" in resp.get_json()["erro"]

    def test_tecnico_passa_do_guard_e_chega_na_checagem_de_configuracao(self, client, usuario_tecnico):
        _login_legado(client, usuario_tecnico)

        for endpoint in ENDPOINTS_ADMIN_OU_TECNICO:
            resp = client.post(endpoint)
            assert resp.status_code == 400, endpoint
            assert "não configurado" in resp.get_json()["erro"]


class TestOrdemDasChecagensPreservada:
    """Sessão sem perfil admin/tecnico continua barrada pela checagem de
    permissão já existente antes mesmo de chegar no novo guard -- mesmo em
    Demo, um vendedor nunca alcança o guard do KI-037."""

    def test_vendedor_recebe_403_de_permissao_mesmo_em_demo(self, client, usuario_vendedor, monkeypatch):
        monkeypatch.setattr(fluxoly_config, "IS_DEMO_ENVIRONMENT", True)
        _login_legado(client, usuario_vendedor)

        for endpoint in ENDPOINTS_ADMIN_OU_TECNICO:
            resp = client.post(endpoint)
            assert resp.status_code == 403, endpoint
            assert "permiss" in resp.get_json()["erro"].lower()

    def test_sem_sessao_recebe_401_mesmo_em_demo(self, client, monkeypatch):
        monkeypatch.setattr(fluxoly_config, "IS_DEMO_ENVIRONMENT", True)

        for endpoint in ENDPOINTS_ADMIN_OU_TECNICO:
            resp = client.post(endpoint)
            assert resp.status_code == 401, endpoint
