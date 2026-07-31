"""
fluxoly_clientes_controller.py

Camada HTTP do domínio Clientes (Blueprint Flask, prefixo `/api/clientes`).
Recebe request, valida forma do payload, chama o service, formata resposta
— nunca contém regra de negócio nem acessa o banco diretamente
(`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Contrato de resposta segue o padrão real já usado no resto da API
(`{"ok": ...}` / `{"ok": false, "erro": ...}`, `irflow_blueprints_api.py`),
não o exemplo `{"data": ...}` do `ENGINEERING_GUIDE.md` — inconsistência
pré-existente entre a documentação e o código, fora de escopo corrigir
nesta sprint.
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_clientes_service as service
from irflow_validation import parse_int, safe_json


def create_clientes_blueprint(deps: dict):
    conectar = deps["conectar"]

    clientes_api = Blueprint("clientes_api", __name__, url_prefix="/api/clientes")

    def usuario_logado():
        return bool(session.get("usuario_id"))

    def usuario_admin():
        return session.get("usuario_perfil") == "admin"

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    def ok(data=None, **kwargs):
        payload = {"ok": True}
        if data is not None:
            payload.update(data if isinstance(data, dict) else {"data": data})
        payload.update(kwargs)
        return jsonify(payload)

    @clientes_api.route("")
    def listar_clientes():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        termo = (request.args.get("q") or "").strip()
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        resultado = service.listar_clientes(conectar, termo, page, per_page)
        return ok(**resultado)

    @clientes_api.route("/<int:cliente_id>")
    def obter_cliente(cliente_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        cliente = service.obter_cliente(conectar, cliente_id)
        if not cliente:
            return err("Cliente não encontrado.", 404)
        return ok(cliente=cliente)

    @clientes_api.route("", methods=["POST"])
    def criar_cliente():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = safe_json(request)
        cliente_id, erro = service.criar_cliente(
            conectar,
            session.get("usuario_id"),
            body.get("nome"),
            body.get("telefone"),
            body.get("email"),
            body.get("cpf_cnpj"),
            body.get("observacoes"),
        )
        if erro:
            return err(erro)
        return ok(id=cliente_id)

    @clientes_api.route("/<int:cliente_id>", methods=["PUT"])
    def atualizar_cliente(cliente_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = safe_json(request)
        sucesso, erro = service.atualizar_cliente(
            conectar,
            session.get("usuario_id"),
            cliente_id,
            body.get("nome"),
            body.get("telefone"),
            body.get("email"),
            body.get("cpf_cnpj"),
            body.get("observacoes"),
        )
        if not sucesso:
            code = 404 if erro == "Cliente não encontrado." else 400
            return err(erro, code)
        return ok(id=cliente_id)

    @clientes_api.route("/<int:cliente_id>", methods=["DELETE"])
    def deletar_cliente(cliente_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        sucesso, erro = service.excluir_cliente(conectar, session.get("usuario_id"), cliente_id)
        if not sucesso:
            code = 404 if erro == "Cliente não encontrado." else 409
            return err(erro, code)
        return ok()

    return clientes_api
