"""
fluxoly_vendas_controller.py

Camada HTTP do domínio Vendas MVP (Blueprint Flask, prefixo `/api/vendas`).
Recebe request, valida forma do payload, chama o service, formata resposta —
nunca contém regra de negócio nem acessa o banco diretamente
(ENGINEERING_GUIDE.md §3.1). Primeiro módulo a nascer com o prefixo
`fluxoly_` (ADR-008).

Perfis: `admin`/`vendedor` podem criar venda (mesma tabela de perfis de
`docs/product/features/VENDAS.md` "Quem usa"). `tecnico` não tem papel na
venda básica desta fatia (seu papel é avaliação de usado, fora de escopo do
MVP).
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_vendas_service as service
from irflow_validation import parse_float, parse_int, safe_json


def create_vendas_blueprint(deps: dict):
    conectar = deps["conectar"]

    vendas_api = Blueprint("vendas_api", __name__, url_prefix="/api/vendas")

    def usuario_logado():
        return bool(session.get("usuario_id"))

    def usuario_pode_vender():
        return session.get("usuario_perfil") in ("admin", "vendedor")

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    def ok(data=None, **kwargs):
        payload = {"ok": True}
        if data is not None:
            payload.update(data if isinstance(data, dict) else {"data": data})
        payload.update(kwargs)
        return jsonify(payload)

    @vendas_api.route("", methods=["POST"])
    def criar_venda():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_pode_vender():
            return err("Permissão negada.", 403)

        body = safe_json(request)
        cliente_id = parse_int(body.get("cliente_id"), default=None)
        unidade_serializada_id = parse_int(body.get("unidade_serializada_id"), default=None)
        valor_unitario = parse_float(body.get("valor_unitario"), default=None)

        if cliente_id is None or unidade_serializada_id is None:
            return err("cliente_id e unidade_serializada_id são obrigatórios.")

        venda_id, erro = service.iniciar_venda(
            conectar,
            session.get("usuario_id"),
            cliente_id,
            unidade_serializada_id,
            body.get("forma_pagamento"),
            valor_unitario,
        )
        if erro:
            code = 404 if erro in ("Cliente não encontrado.", "Unidade não encontrada.") else 400
            return err(erro, code)
        return ok(id=venda_id), 201

    @vendas_api.route("/<int:venda_id>")
    def obter_venda(venda_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        venda = service.obter_venda(conectar, venda_id)
        if not venda:
            return err("Venda não encontrada.", 404)
        return ok(venda=venda)

    return vendas_api
