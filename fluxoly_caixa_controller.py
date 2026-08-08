"""
fluxoly_caixa_controller.py

Camada HTTP do domínio Caixa (Blueprint Flask, prefixo `/api/caixa`).
Recebe request, valida forma do payload, chama o service, formata resposta
-- nunca contém regra de negócio nem acessa o banco diretamente
(ENGINEERING_GUIDE.md §3.1).

Todas as rotas exigem perfil `admin`/`financeiro` -- Financeiro Mínimo
(BR-067 a BR-069, docs/engineering/plans/PLAN-financeiro-minimo.md).
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_caixa_service as service
from fluxoly_validation import parse_float, parse_int, safe_json


def create_caixa_blueprint(deps: dict):
    conectar = deps["conectar"]

    caixa_api = Blueprint("caixa_api", __name__, url_prefix="/api/caixa")

    def usuario_logado():
        return bool(session.get("usuario_id"))

    def usuario_pode_financeiro():
        return session.get("usuario_perfil") in ("admin", "financeiro")

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    def ok(data=None, **kwargs):
        payload = {"ok": True}
        if data is not None:
            payload.update(data if isinstance(data, dict) else {"data": data})
        payload.update(kwargs)
        return jsonify(payload)

    @caixa_api.route("")
    def listar_movimentacoes():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        tipo = (request.args.get("tipo") or "").strip().lower() or None
        origem = (request.args.get("origem") or "").strip().lower() or None
        data_inicio = (request.args.get("data_inicio") or "").strip() or None
        data_fim = (request.args.get("data_fim") or "").strip() or None
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        resultado = service.listar_movimentacoes(conectar, tipo, origem, data_inicio, data_fim, page, per_page)
        return ok(**resultado)

    @caixa_api.route("/saldo")
    def obter_saldo():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        return ok(saldo=service.obter_saldo(conectar))

    @caixa_api.route("/relatorio")
    def obter_relatorio():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        data_inicio = (request.args.get("data_inicio") or "").strip() or None
        data_fim = (request.args.get("data_fim") or "").strip() or None
        return ok(itens=service.obter_relatorio_fluxo_caixa(conectar, data_inicio, data_fim))

    @caixa_api.route("", methods=["POST"])
    def criar_movimentacao():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        body = safe_json(request)
        valor = parse_float(body.get("valor"), default=None)
        movimentacao_id, erro = service.criar_movimentacao_manual(
            conectar, session.get("usuario_id"), body.get("tipo"), valor, body.get("descricao")
        )
        if erro:
            return err(erro)
        return ok(id=movimentacao_id), 201

    @caixa_api.route("/<int:movimentacao_id>/estornar", methods=["POST"])
    def estornar_movimentacao(movimentacao_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        sucesso, erro = service.estornar_movimentacao_manual(conectar, session.get("usuario_id"), movimentacao_id)
        if not sucesso:
            code = 404 if erro == "Movimentação não encontrada." else 400
            return err(erro, code)
        return ok(id=movimentacao_id)

    return caixa_api
