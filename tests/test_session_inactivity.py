"""
Testes de expiração de sessão por inatividade (Sprint 3 — Unidade 2).

Escopo: `irflow_core.py::sessao_ainda_ativa`, aplicada em `verificar_autenticacao()`
(`app.py`, `before_request` global) — cobre tanto rotas `/api/*` quanto views
legadas, já que o `before_request` dispara para ambas antes de qualquer bypass.

Isolamento: `client.session_transaction()` manipula o conteúdo da sessão
diretamente (sem precisar forjar assinatura de cookie, diferente de
`tests/test_session.py`, que testa o timestamp da própria assinatura
itsdangerous — mecanismo distinto e mais antigo, não tocado por esta sprint).
"""

from datetime import datetime, timedelta


class TestInatividadeSessaoApi:
    def test_requisicao_dentro_da_janela_mantem_sessao_ativa(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)

        resp = client.get("/api/auth/me")

        assert resp.status_code == 200

    def test_requisicao_apos_janela_de_30min_expira_sessao(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        with client.session_transaction() as sess:
            sess["_ultima_atividade"] = (datetime.now() - timedelta(minutes=31)).isoformat()

        resp = client.get("/api/auth/me")

        assert resp.status_code == 401
        with client.session_transaction() as sess:
            assert "usuario_id" not in sess

    def test_requisicao_dentro_dos_30min_nao_expira(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        with client.session_transaction() as sess:
            sess["_ultima_atividade"] = (datetime.now() - timedelta(minutes=29)).isoformat()

        resp = client.get("/api/auth/me")

        assert resp.status_code == 200

    def test_janela_desliza_uso_recente_reseta_o_timer(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        with client.session_transaction() as sess:
            sess["_ultima_atividade"] = (datetime.now() - timedelta(minutes=25)).isoformat()

        assert client.get("/api/auth/me").status_code == 200

        with client.session_transaction() as sess:
            ultima_atividade = datetime.fromisoformat(sess["_ultima_atividade"])
        assert (datetime.now() - ultima_atividade) < timedelta(minutes=1)

    def test_sessao_sem_marca_de_atividade_nao_expira_de_imediato(self, client, login_como, usuario_tecnico):
        # Sessao "legada" (criada antes desta feature existir) nao deve derrubar
        # o usuario na primeira requisicao apos o deploy.
        login_como(client, usuario_tecnico)
        with client.session_transaction() as sess:
            sess.pop("_ultima_atividade", None)

        resp = client.get("/api/auth/me")

        assert resp.status_code == 200


class TestInatividadeSessaoViewLegada:
    # GET/HEAD para paths legados conhecidos (ex.: /kanban) são interceptados por
    # destino_react_legado() e redirecionam para /app/* ANTES de qualquer checagem
    # de autenticação — não servem para testar expiração. /atualizar_status é
    # POST-only (order_views, ROUTE_PERMISSIONS None = qualquer logado), então
    # passa pela checagem de inatividade normalmente.

    def test_view_legada_redireciona_para_login_apos_expirar(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        with client.session_transaction() as sess:
            sess["_ultima_atividade"] = (datetime.now() - timedelta(minutes=31)).isoformat()

        resp = client.post("/atualizar_status", data={})

        assert resp.status_code == 302
        assert "/app/login" in resp.headers["Location"]

    def test_view_legada_dentro_da_janela_nao_redireciona(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        with client.session_transaction() as sess:
            sess["_ultima_atividade"] = (datetime.now() - timedelta(minutes=5)).isoformat()

        resp = client.post("/atualizar_status", data={})

        # Passa pela autenticação e chega na view, que rejeita o payload vazio
        # (400) — o ponto do teste é que NÃO houve redirect para /app/login.
        assert resp.status_code == 400


class TestSessaoAindaAtivaUnitario:
    def test_primeira_chamada_sem_marca_define_e_retorna_true(self):
        from irflow_core import sessao_ainda_ativa

        sess = {}
        assert sessao_ainda_ativa(sess) is True
        assert "_ultima_atividade" in sess

    def test_dentro_do_limite_retorna_true_e_atualiza(self):
        from irflow_core import sessao_ainda_ativa

        agora = datetime.now()
        sess = {"_ultima_atividade": (agora - timedelta(minutes=10)).isoformat()}
        assert sessao_ainda_ativa(sess, agora=agora) is True
        assert sess["_ultima_atividade"] == agora.isoformat()

    def test_acima_do_limite_retorna_false_sem_atualizar(self):
        from irflow_core import sessao_ainda_ativa

        agora = datetime.now()
        marca_antiga = (agora - timedelta(minutes=31)).isoformat()
        sess = {"_ultima_atividade": marca_antiga}
        assert sessao_ainda_ativa(sess, agora=agora) is False
        assert sess["_ultima_atividade"] == marca_antiga

    def test_limite_configuravel_via_env_var(self, monkeypatch):
        from irflow_core import sessao_ainda_ativa

        monkeypatch.setenv("IR_FLOW_SESSION_INACTIVITY_MINUTES", "5")
        agora = datetime.now()
        sess = {"_ultima_atividade": (agora - timedelta(minutes=6)).isoformat()}
        assert sessao_ainda_ativa(sess, agora=agora) is False
