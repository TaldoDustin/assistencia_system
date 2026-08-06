"""
Fluxoly - API Blueprint (MercadoPhone)
Rotas /api/integracoes/mercadophone/* -- consumidas pelo frontend React
(Integracoes.jsx). Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2 --
9º domínio extraído).
"""

import threading
from datetime import datetime

from flask import Blueprint, request, session

from fluxoly_api_helpers import _texto_limpo_local, err, ok, usuario_admin, usuario_logado
from fluxoly_mercadophone import atualizar_runtime_mercadophone, carregar_config_mercadophone
from fluxoly_validation import parse_int, safe_json


def create_api_mercadophone_blueprint(deps):
    api_mercadophone = Blueprint("api_mercadophone", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    sincronizar_mercado_phone = deps["sincronizar_mercado_phone"]
    reimportar_todas_os_mercado_phone = deps["reimportar_todas_os_mercado_phone"]
    reprocessar_todas_os_mercado_phone = deps["reprocessar_todas_os_mercado_phone"]
    mercado_phone_runtime_config = deps["mercado_phone_runtime_config"]
    mercado_phone_helpers = deps["mercado_phone_helpers"]
    integrations_config_path = deps["integrations_config_path"]
    carregar_configuracoes_integracoes = deps["carregar_configuracoes_integracoes"]
    salvar_configuracoes_integracoes = deps["salvar_configuracoes_integracoes"]

    def _to_bool(valor, padrao=False):
        if valor is None:
            return padrao
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() not in {"", "0", "false", "nao", "off"}

    reprocessamento_mp_lock = threading.Lock()
    reprocessamento_mp_estado = {
        "rodando": False,
        "iniciado_em": None,
        "finalizado_em": None,
        "atualizadas": 0,
        "erros": 0,
        "total": 0,
        "erro": "",
    }

    def _snapshot_reprocessamento_mp():
        with reprocessamento_mp_lock:
            return dict(reprocessamento_mp_estado)

    def _executar_reprocessamento_mp_async():
        try:
            resultado = reprocessar_todas_os_mercado_phone(
                conectar, mercado_phone_runtime_config, mercado_phone_helpers
            )
            with reprocessamento_mp_lock:
                reprocessamento_mp_estado["rodando"] = False
                reprocessamento_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reprocessamento_mp_estado["total"] = int(resultado.get("total") or 0)
                reprocessamento_mp_estado["atualizadas"] = int(resultado.get("atualizadas") or 0)
                reprocessamento_mp_estado["erros"] = int(resultado.get("erros") or 0)
                reprocessamento_mp_estado["erro"] = ""
        except Exception as exc:
            with reprocessamento_mp_lock:
                reprocessamento_mp_estado["rodando"] = False
                reprocessamento_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reprocessamento_mp_estado["erro"] = str(exc)

    reimportacao_mp_lock = threading.Lock()
    reimportacao_mp_estado = {
        "rodando": False,
        "iniciado_em": None,
        "finalizado_em": None,
        "removidas": 0,
        "importadas": 0,
        "atualizadas": 0,
        "erro": "",
    }

    def _snapshot_reimportacao_mp():
        with reimportacao_mp_lock:
            return dict(reimportacao_mp_estado)

    def _executar_reimportacao_mp_async():
        try:
            resultado = reimportar_todas_os_mercado_phone(conectar, mercado_phone_runtime_config, mercado_phone_helpers)
            with reimportacao_mp_lock:
                reimportacao_mp_estado["rodando"] = False
                reimportacao_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reimportacao_mp_estado["removidas"] = int(resultado.get("removidas") or 0)
                reimportacao_mp_estado["importadas"] = int(resultado.get("importadas") or 0)
                reimportacao_mp_estado["atualizadas"] = int(resultado.get("atualizadas") or 0)
                reimportacao_mp_estado["erro"] = ""
        except Exception as exc:
            with reimportacao_mp_lock:
                reimportacao_mp_estado["rodando"] = False
                reimportacao_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reimportacao_mp_estado["erro"] = str(exc)

    @api_mercadophone.route("/integracoes/mercadophone/sincronizar", methods=["POST"])
    def sincronizar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)
        try:
            _, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)
            status_cfg = atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)
            if not status_cfg["configurado"]:
                return err("Mercado Phone não configurado. Informe o token da API.", 400)

            resultado = sincronizar_mercado_phone(conectar, mercado_phone_runtime_config, mercado_phone_helpers)
            return ok(resultado=resultado)
        except Exception as exc:
            return err(str(exc))

    @api_mercadophone.route("/integracoes/mercadophone/reprocessar", methods=["POST", "OPTIONS"])
    def reprocessar_mercadophone():
        if request.method == "OPTIONS":
            return ("", 204)
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)
        try:
            _, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)
            status_cfg = atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)
            if not status_cfg["configurado"]:
                return err("Mercado Phone não configurado. Informe o token da API.", 400)

            with reprocessamento_mp_lock:
                if reprocessamento_mp_estado["rodando"]:
                    estado = dict(reprocessamento_mp_estado)
                    return ok(iniciado=False, reprocessamento=estado)

                reprocessamento_mp_estado["rodando"] = True
                reprocessamento_mp_estado["iniciado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reprocessamento_mp_estado["finalizado_em"] = None
                reprocessamento_mp_estado["atualizadas"] = 0
                reprocessamento_mp_estado["erros"] = 0
                reprocessamento_mp_estado["total"] = 0
                reprocessamento_mp_estado["erro"] = ""
                estado = dict(reprocessamento_mp_estado)

            threading.Thread(target=_executar_reprocessamento_mp_async, daemon=True).start()
            return ok(iniciado=True, reprocessamento=estado), 202
        except Exception as exc:
            return err(str(exc))

    @api_mercadophone.route("/integracoes/mercadophone/reprocessar/status")
    def status_reprocessar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        return ok(reprocessamento=_snapshot_reprocessamento_mp())

    @api_mercadophone.route("/integracoes/mercadophone/reimportar", methods=["POST", "OPTIONS"])
    def reimportar_mercadophone():
        if request.method == "OPTIONS":
            return ("", 204)
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)
        try:
            _, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)
            status_cfg = atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)
            if not status_cfg["configurado"]:
                return err("Mercado Phone não configurado. Informe o token da API.", 400)

            with reimportacao_mp_lock:
                if reimportacao_mp_estado["rodando"]:
                    estado = dict(reimportacao_mp_estado)
                    return ok(iniciado=False, reimportacao=estado)

                reimportacao_mp_estado["rodando"] = True
                reimportacao_mp_estado["iniciado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reimportacao_mp_estado["finalizado_em"] = None
                reimportacao_mp_estado["removidas"] = 0
                reimportacao_mp_estado["importadas"] = 0
                reimportacao_mp_estado["atualizadas"] = 0
                reimportacao_mp_estado["erro"] = ""
                estado = dict(reimportacao_mp_estado)

            threading.Thread(target=_executar_reimportacao_mp_async, daemon=True).start()
            return ok(iniciado=True, reimportacao=estado), 202
        except Exception as exc:
            return err(str(exc))

    @api_mercadophone.route("/integracoes/mercadophone/reimportar/status")
    def status_reimportar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        return ok(reimportacao=_snapshot_reimportacao_mp())

    @api_mercadophone.route("/integracoes/mercadophone/status")
    def status_mercadophone():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        _, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)
        status_cfg = atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)

        return ok(
            mercado_phone={
                **status_cfg,
                "tem_token": status_cfg["configurado"],
            }
        )

    @api_mercadophone.route("/integracoes/mercadophone/config", methods=["POST"])
    def salvar_config_mercadophone():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        dados, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)

        if "api_token" in body:
            mp_cfg["api_token"] = _texto_limpo_local(body.get("api_token"))

        if "sync_enabled" in body:
            mp_cfg["sync_enabled"] = _to_bool(body.get("sync_enabled"), padrao=True)

        if "sync_interval_seconds" in body:
            parsed_interval = parse_int(body.get("sync_interval_seconds"), default=180)
            if parsed_interval is None:
                return err("sync_interval_seconds inválido.", 400)
            mp_cfg["sync_interval_seconds"] = max(30, parsed_interval)

        if "sync_timeout_seconds" in body:
            parsed_timeout = parse_int(body.get("sync_timeout_seconds"), default=20)
            if parsed_timeout is None:
                return err("sync_timeout_seconds inválido.", 400)
            mp_cfg["sync_timeout_seconds"] = max(5, parsed_timeout)

        if "sync_start_date" in body:
            mp_cfg["sync_start_date"] = _texto_limpo_local(body.get("sync_start_date")) or "2026-04-01"

        dados["mercado_phone"] = mp_cfg
        salvar_configuracoes_integracoes(integrations_config_path, dados)

        status_cfg = atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)
        return ok(mercado_phone=status_cfg)

    return api_mercadophone
