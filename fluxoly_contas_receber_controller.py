"""
fluxoly_contas_receber_controller.py

Camada HTTP do domínio Contas a Receber (Blueprint Flask, prefixo
`/api/contas-receber`). Recebe request, valida forma do payload, chama o
service, formata resposta -- nunca contém regra de negócio nem acessa o
banco diretamente (ENGINEERING_GUIDE.md §3.1). Espelho de
`fluxoly_contas_pagar_controller.py`.

Todas as rotas exigem perfil `admin`/`financeiro` -- Financeiro Mínimo
(BR-067 a BR-069, docs/engineering/plans/PLAN-financeiro-minimo.md).
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_contas_receber_service as service
from fluxoly_validation import parse_float, parse_int, safe_json


def create_contas_receber_blueprint(deps: dict):
    conectar = deps["conectar"]

    contas_receber_api = Blueprint("contas_receber_api", __name__, url_prefix="/api/contas-receber")

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

    @contas_receber_api.route("")
    def listar_contas_receber():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        status = (request.args.get("status") or "").strip().lower() or None
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        resultado = service.listar_contas_receber(conectar, status, page, per_page)
        return ok(**resultado)

    @contas_receber_api.route("/<int:conta_id>")
    def obter_conta_receber(conta_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        conta = service.obter_conta_receber(conectar, conta_id)
        if not conta:
            return err("Conta a receber não encontrada.", 404)
        return ok(conta=conta)

    @contas_receber_api.route("", methods=["POST"])
    def criar_conta_receber():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        body = safe_json(request)
        valor = parse_float(body.get("valor"), default=None)
        conta_id, erro = service.criar_conta_receber(
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

    @contas_receber_api.route("/<int:conta_id>", methods=["PUT"])
    def atualizar_conta_receber(conta_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        body = safe_json(request)
        valor = parse_float(body.get("valor"), default=None)
        sucesso, erro = service.atualizar_conta_receber(
            conectar,
            session.get("usuario_id"),
            conta_id,
            body.get("descricao"),
            body.get("categoria"),
            valor,
            body.get("data_vencimento"),
        )
        if not sucesso:
            code = 404 if erro == "Conta a receber não encontrada." else 400
            return err(erro, code)
        return ok(id=conta_id)

    @contas_receber_api.route("/<int:conta_id>", methods=["DELETE"])
    def excluir_conta_receber(conta_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        sucesso, erro = service.excluir_conta_receber(conectar, session.get("usuario_id"), conta_id)
        if not sucesso:
            code = 404 if erro == "Conta a receber não encontrada." else 409
            return err(erro, code)
        return ok()

    @contas_receber_api.route("/<int:conta_id>/receber", methods=["POST"])
    def receber_conta(conta_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        sucesso, erro = service.receber_conta(conectar, session.get("usuario_id"), conta_id)
        if not sucesso:
            code = 404 if erro == "Conta a receber não encontrada." else 400
            return err(erro, code)
        return ok(id=conta_id, status="recebido")

    @contas_receber_api.route("/<int:conta_id>/cancelar", methods=["POST"])
    def cancelar_conta_receber(conta_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_financeiro():
            return err("Permissão negada.", 403)

        sucesso, erro = service.cancelar_conta_receber(conectar, session.get("usuario_id"), conta_id)
        if not sucesso:
            code = 404 if erro == "Conta a receber não encontrada." else 400
            return err(erro, code)
        return ok(id=conta_id, status="cancelado")

    return contas_receber_api
