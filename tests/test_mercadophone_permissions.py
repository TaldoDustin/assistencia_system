"""
Testes de autorizacao para os endpoints de mutacao em massa da integracao
MercadoPhone (achado de auditoria de seguranca — ver KNOWN_ISSUES.md).

Antes desta correcao, POST /api/integracoes/mercadophone/{sincronizar,
reprocessar,reimportar} so checavam usuario_logado() — qualquer perfil
autenticado, inclusive vendedor, podia disparar reimportar_todas_os_
mercado_phone() (apaga TODAS as OS de origem mercado_phone e reimporta do
zero). Corrigido para exigir admin/tecnico, mesmo padrao ja usado em
criar_ordem/atualizar_ordem/deletar_ordem.

Sem mock da API externa: com MERCADO_PHONE_SYNC_ENABLED=0 e sem token
configurado no ambiente de teste, uma vez que a checagem de perfil passa,
a resposta esperada e 400 "nao configurado" — o que ja prova que a
checagem de permissao nao bloqueou.
"""

ENDPOINTS = [
    "/api/integracoes/mercadophone/sincronizar",
    "/api/integracoes/mercadophone/reprocessar",
    "/api/integracoes/mercadophone/reimportar",
]


def _login_legado(client, usuario):
    return client.post("/login", data={"usuario": usuario["usuario"], "senha": usuario["senha"]})


class TestPermissoesMutacaoMercadoPhone:
    def test_sem_sessao_retorna_401(self, client):
        for endpoint in ENDPOINTS:
            resp = client.post(endpoint)
            assert resp.status_code == 401, endpoint

    def test_vendedor_recebe_acesso_negado(self, client, usuario_vendedor):
        _login_legado(client, usuario_vendedor)

        for endpoint in ENDPOINTS:
            resp = client.post(endpoint)
            assert resp.status_code == 403, endpoint

    def test_tecnico_passa_da_checagem_de_permissao(self, client, usuario_tecnico):
        _login_legado(client, usuario_tecnico)

        for endpoint in ENDPOINTS:
            resp = client.post(endpoint)
            assert resp.status_code == 400, endpoint
            assert "não configurado" in resp.get_json()["erro"]

    def test_admin_passa_da_checagem_de_permissao(self, client, usuario_admin):
        _login_legado(client, usuario_admin)

        for endpoint in ENDPOINTS:
            resp = client.post(endpoint)
            assert resp.status_code == 400, endpoint
            assert "não configurado" in resp.get_json()["erro"]
