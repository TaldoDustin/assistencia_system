"""
irflow_produtos_controller.py

Camada HTTP do domínio Produtos (Blueprint Flask, prefixo `/api/produtos`).
Recebe request, valida forma do payload, chama o service, formata resposta
— nunca contém regra de negócio nem acessa o banco diretamente
(`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Contrato de resposta segue o padrão real já usado no resto da API
(`{"ok": ...}` / `{"ok": false, "erro": ...}`), mesmo padrão de
`fluxoly_clientes_controller.py`.

Permissão (V1, default conservador — decisão de negócio pendente de
validação com cliente real): listar/obter é qualquer usuário autenticado
(vendedor precisa consultar o catálogo durante uma venda); criar/editar/
excluir é `admin`, já que preço/margem é dado sensível.
"""

from flask import Blueprint, jsonify, request, session

import irflow_produtos_service as service
from irflow_validation import parse_float, parse_int, safe_json


def create_produtos_blueprint(deps: dict):
    conectar = deps["conectar"]

    produtos_api = Blueprint("produtos_api", __name__, url_prefix="/api/produtos")

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

    def _parse_ativo(valor):
        if valor is None or valor == "":
            return None
        return valor not in ("0", "false", "False")

    @produtos_api.route("")
    def listar_produtos():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        termo = (request.args.get("q") or "").strip()
        categoria = (request.args.get("categoria") or "").strip() or None
        marca = (request.args.get("marca") or "").strip() or None
        condicao = (request.args.get("condicao") or "").strip() or None
        ativo = _parse_ativo(request.args.get("ativo"))
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        resultado = service.listar_produtos(conectar, termo, categoria, marca, condicao, ativo, page, per_page)
        return ok(**resultado)

    @produtos_api.route("/<int:produto_id>")
    def obter_produto(produto_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        produto = service.obter_produto(conectar, produto_id)
        if not produto:
            return err("Produto não encontrado.", 404)
        return ok(produto=produto)

    @produtos_api.route("", methods=["POST"])
    def criar_produto():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        preco_custo = parse_float(body.get("preco_custo"), default=None)
        preco_venda = parse_float(body.get("preco_venda"), default=None)
        quantidade = parse_int(body.get("quantidade"), default=0)
        if preco_custo is None and body.get("preco_custo") not in (None, ""):
            return err("Preço de custo inválido.")
        if preco_venda is None:
            return err("Preço de venda é obrigatório e deve ser maior que zero.")
        if quantidade is None:
            return err("Quantidade inválida.")

        produto_id, erro = service.criar_produto(
            conectar,
            session.get("usuario_id"),
            body.get("categoria"),
            body.get("marca"),
            body.get("modelo"),
            body.get("cor"),
            body.get("capacidade"),
            body.get("condicao"),
            body.get("descricao"),
            body.get("sku"),
            body.get("fornecedor"),
            preco_custo,
            preco_venda,
            quantidade,
            bool(body.get("requer_rastreio_unidade")),
        )
        if erro:
            return err(erro)
        return ok(id=produto_id)

    @produtos_api.route("/<int:produto_id>", methods=["PUT"])
    def atualizar_produto(produto_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        preco_custo = parse_float(body.get("preco_custo"), default=None)
        preco_venda = parse_float(body.get("preco_venda"), default=None)
        quantidade = parse_int(body.get("quantidade"), default=0)
        if preco_custo is None and body.get("preco_custo") not in (None, ""):
            return err("Preço de custo inválido.")
        if preco_venda is None:
            return err("Preço de venda é obrigatório e deve ser maior que zero.")
        if quantidade is None:
            return err("Quantidade inválida.")

        sucesso, erro = service.atualizar_produto(
            conectar,
            session.get("usuario_id"),
            produto_id,
            body.get("categoria"),
            body.get("marca"),
            body.get("modelo"),
            body.get("cor"),
            body.get("capacidade"),
            body.get("condicao"),
            body.get("descricao"),
            body.get("sku"),
            body.get("fornecedor"),
            preco_custo,
            preco_venda,
            quantidade,
            bool(body.get("requer_rastreio_unidade")),
            body.get("ativo", True),
        )
        if not sucesso:
            code = 404 if erro == "Produto não encontrado." else 400
            return err(erro, code)
        return ok(id=produto_id)

    @produtos_api.route("/<int:produto_id>", methods=["DELETE"])
    def deletar_produto(produto_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        sucesso, erro = service.excluir_produto(conectar, session.get("usuario_id"), produto_id)
        if not sucesso:
            code = 404 if erro == "Produto não encontrado." else 400
            return err(erro, code)
        return ok()

    return produtos_api
