"""
fluxoly_contas_pagar_controller.py

Camada HTTP do domínio Contas a Pagar (Blueprint Flask, prefixo
`/api/contas-pagar`). Recebe request, valida forma do payload, chama o
service, formata resposta -- nunca contém regra de negócio nem acessa o
banco diretamente (ENGINEERING_GUIDE.md §3.1).

Todas as rotas exigem perfil `admin`/`financeiro` -- Financeiro Mínimo
(BR-067 a BR-069, docs/engineering/plans/PLAN-financeiro-minimo.md).
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_contas_pagar_service as service
from fluxoly_validation import parse_float, parse_int, safe_json


def create_contas_pagar_blueprint(deps: dict):
    conectar = deps["conectar"]

    contas_pagar_api = Blueprint("contas_pagar_api", __name__, url_prefix="/api/contas-pagar")

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

    @contas_pagar_api.route("")
    def listar_contas_pagar():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        status = (request.args.get("status") or "").strip().lower() or None
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        resultado = service.listar_contas_pagar(conectar, status, page, per_page)
        return ok(**resultado)

    @contas_pagar_api.route("/<int:conta_id>")
    def obter_conta_pagar(conta_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        conta = service.obter_conta_pagar(conectar, conta_id)
        if not conta:
            return err("Conta a pagar não encontrada.", 404)
        return ok(conta=conta)

    @contas_pagar_api.route("", methods=["POST"])
    def criar_conta_pagar():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        body = safe_json(request)
        valor = parse_float(body.get("valor"), default=None)
        conta_id, erro = service.criar_conta_pagar(
            conectar,
            session.get("usuario_id"),
            body.get("descricao"),
            body.get("categoria"),
            valor,
            body.get("data_vencimento"),
        )
        if erro:
            return err(erro)
        return ok(id=conta_id), 201

    @contas_pagar_api.route("/<int:conta_id>", methods=["PUT"])
    def atualizar_conta_pagar(conta_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        body = safe_json(request)
        valor = parse_float(body.get("valor"), default=None)
        sucesso, erro = service.atualizar_conta_pagar(
            conectar,
            session.get("usuario_id"),
            conta_id,
            body.get("descricao"),
            body.get("categoria"),
            valor,
            body.get("data_vencimento"),
        )
        if not sucesso:
            code = 404 if erro == "Conta a pagar não encontrada." else 400
            return err(erro, code)
        return ok(id=conta_id)

    @contas_pagar_api.route("/<int:conta_id>", methods=["DELETE"])
    def excluir_conta_pagar(conta_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        sucesso, erro = service.excluir_conta_pagar(conectar, session.get("usuario_id"), conta_id)
        if not sucesso:
            code = 404 if erro == "Conta a pagar não encontrada." else 409
            return err(erro, code)
        return ok()

    @contas_pagar_api.route("/<int:conta_id>/pagar", methods=["POST"])
    def pagar_conta(conta_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        sucesso, erro = service.pagar_conta(conectar, session.get("usuario_id"), conta_id)
        if not sucesso:
            code = 404 if erro == "Conta a pagar não encontrada." else 400
            return err(erro, code)
        return ok(id=conta_id, status="pago")

    @contas_pagar_api.route("/<int:conta_id>/cancelar", methods=["POST"])
    def cancelar_conta_pagar(conta_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        sucesso, erro = service.cancelar_conta_pagar(conectar, session.get("usuario_id"), conta_id)
        if not sucesso:
            code = 404 if erro == "Conta a pagar não encontrada." else 400
            return err(erro, code)
        return ok(id=conta_id, status="cancelado")

    return contas_pagar_api
