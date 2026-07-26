"""
Testes de fail-secure para verificar_autenticacao() (app.py).

Antes desta correcao, `ROUTE_PERMISSIONS.get(endpoint)` retornava `None` tanto
para "endpoint cadastrado com None" (qualquer perfil logado) quanto para
"endpoint ausente do dict" — um endpoint legado novo, adicionado sem entrada
correspondente em ROUTE_PERMISSIONS, ficava liberado para qualquer usuario
logado em vez de negado. Corrigido com um sentinel que distingue os dois
casos: endpoint ausente agora e negado por padrao (fail secure).
"""

import app as _app

_ENDPOINT_TESTE = "rota_teste_sem_entrada_route_permissions"
_PATH_TESTE = "/rota-teste-sem-entrada-route-permissions"

# Registrado na coleta do modulo (antes de qualquer teste rodar) porque Flask
# bloqueia add_url_rule() apos a primeira requisicao ser tratada — chamar
# isso de dentro de uma funcao de teste falha quando a suite completa roda
# (outros testes ja fizeram requisicoes antes deste modulo ser exercitado).
if _ENDPOINT_TESTE not in _app.app.view_functions:
    _app.app.add_url_rule(
        _PATH_TESTE,
        endpoint=_ENDPOINT_TESTE,
        view_func=lambda: "nao deveria ser alcancado",
    )


def _login_legado(client, usuario):
    return client.post("/login", data={"usuario": usuario["usuario"], "senha": usuario["senha"]})


def test_endpoint_legado_sem_entrada_e_negado_para_usuario_logado(client, usuario_tecnico):
    _login_legado(client, usuario_tecnico)

    resp = client.get(_PATH_TESTE, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/app")


def test_endpoint_legado_sem_entrada_e_negado_para_usuario_anonimo(client):
    resp = client.get(_PATH_TESTE, follow_redirects=False)

    assert resp.status_code == 302
    assert resp.headers["Location"].endswith("/app")


def test_endpoint_com_entrada_none_continua_liberado_para_qualquer_logado(client, usuario_vendedor):
    """Regressao: endpoint explicitamente None (ex.: order_views.ordens) continua
    acessivel a qualquer perfil logado, sem virar negado pelo sentinel."""
    _login_legado(client, usuario_vendedor)

    resp = client.get("/ordens", follow_redirects=False)

    assert resp.status_code == 302
    assert "/app/ordens" in resp.headers["Location"]
