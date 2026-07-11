"""
irflow_estoque_unidades_controller.py

Camada HTTP do domínio `estoque_unidades` (Blueprint Flask, prefixo
`/api/estoque-unidades`). Recebe request, valida forma do payload, chama o
service, formata resposta — nunca contém regra de negócio nem acessa o
banco diretamente (`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Mesmo contrato de resposta do resto da API (`{"ok": ...}` /
`{"ok": false, "erro": ...}`), mesma justificativa de
`irflow_clientes_controller.py`.
"""

from flask import Blueprint, jsonify, request, session

import irflow_estoque_unidades_service as service
from irflow_validation import parse_int, safe_json


def create_estoque_unidades_blueprint(deps: dict):
    conectar = deps["conectar"]

    estoque_unidades_api = Blueprint("estoque_unidades_api", __name__, url_prefix="/api/estoque-unidades")

    def usuario_logado():
        return bool(session.get("usuario_id"))

    def perfil_pode_escrever():
        return session.get("usuario_perfil") in ("admin", "tecnico")

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    def ok(data=None, **kwargs):
        payload = {"ok": True}
        if data is not None:
            payload.update(data if isinstance(data, dict) else {"data": data})
        payload.update(kwargs)
        return jsonify(payload)

    @estoque_unidades_api.route("")
    def listar_unidades():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        imei = (request.args.get("imei") or "").strip()
        estoque_id = parse_int(request.args.get("estoque_id"), default=None)
        status = (request.args.get("status") or "").strip()
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        resultado = service.listar_unidades(conectar, imei, estoque_id, status, page, per_page)
        return ok(**resultado)

    @estoque_unidades_api.route("/<int:unidade_id>")
    def obter_unidade(unidade_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        unidade = service.obter_unidade(conectar, unidade_id)
        if not unidade:
            return err("Unidade não encontrada.", 404)
        return ok(unidade=unidade)

    @estoque_unidades_api.route("", methods=["POST"])
    def criar_unidade():
        if not usuario_logado() or not perfil_pode_escrever():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        estoque_id = parse_int(body.get("estoque_id"), default=None)
        unidade_id, erro = service.criar_unidade(
            conectar, session.get("usuario_id"), estoque_id, body.get("imei"), body.get("lote_id")
        )
        if erro:
            code = 404 if erro == "Item de estoque não encontrado." else 400
            return err(erro, code)
        return ok(id=unidade_id)

    @estoque_unidades_api.route("/<int:unidade_id>/status", methods=["PATCH"])
    def atualizar_status(unidade_id):
        if not usuario_logado() or not perfil_pode_escrever():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        novo_status = (body.get("status") or "").strip()
        sucesso, erro = service.transicionar_status(conectar, session.get("usuario_id"), unidade_id, novo_status)
        if not sucesso:
            code = 404 if erro == "Unidade não encontrada." else 400
            return err(erro, code)
        return ok(id=unidade_id, status=novo_status)

    return estoque_unidades_api
