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

ORDENACOES_VALIDAS = {"recente", "antigo"}


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

    @vendas_api.route("")
    def listar_vendas():
        """Histórico de vendas (Sprint Vendas 1.1) — só consulta, qualquer
        usuário autenticado (mesmo padrão de listagem de Clientes/Produtos;
        a restrição admin/vendedor vale para criar venda, não para ver o
        histórico)."""
        if not usuario_logado():
            return err("Não autenticado.", 401)

        termo = (request.args.get("q") or "").strip()
        cliente_id = parse_int(request.args.get("cliente_id"), default=None)
        vendedor_id = parse_int(request.args.get("vendedor_id"), default=None)
        forma_pagamento = (request.args.get("forma_pagamento") or "").strip().lower() or None
        status = (request.args.get("status") or "").strip() or None
        data_inicio = (request.args.get("data_inicio") or "").strip() or None
        data_fim = (request.args.get("data_fim") or "").strip() or None
        # criado_em é timestamp completo ("YYYY-MM-DD HH:MM:SS"); um data_fim
        # só com data (sem hora) precisa virar limite de fim de dia, senão a
        # comparação lexicográfica exclui as vendas feitas depois da meia-noite
        # do próprio dia (ex.: "2026-07-27" < "2026-07-27 14:32:10").
        if data_fim and len(data_fim) == 10:
            data_fim = f"{data_fim} 23:59:59"
        sort = (request.args.get("sort") or "recente").strip()
        if sort not in ORDENACOES_VALIDAS:
            sort = "recente"
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        resultado = service.listar_vendas(
            conectar, cliente_id, vendedor_id, forma_pagamento, status,
            data_inicio, data_fim, termo, sort, page, per_page,
        )
        return ok(**resultado)

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
            body.get("observacoes"),
            body.get("motivo_desconto"),  # BR-039 -- opcional, texto livre.
        )
        if erro:
            code = 404 if erro in ("Cliente não encontrado.", "Unidade não encontrada.") else 400
            return err(erro, code)
        return ok(id=venda_id), 201

    @vendas_api.route("/<int:venda_id>")
    def obter_venda(venda_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        venda, itens = service.obter_venda_com_itens(conectar, venda_id)
        if not venda:
            return err("Venda não encontrada.", 404)
        return ok(venda=venda, itens=itens)

    @vendas_api.route("/<int:venda_id>/cancelar", methods=["POST"])
    def cancelar_venda(venda_id):
        """V1.2 -- Cancelamento (BR-031 a BR-036). Gate grosso aqui (logado +
        perfil admin/vendedor); a checagem fina de "só a própria venda" para
        vendedor vive em service.cancelar_venda, não aqui."""
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "vendedor"):
            return err("Permissão negada.", 403)

        body = safe_json(request)
        sucesso, erro = service.cancelar_venda(
            conectar,
            venda_id,
            session.get("usuario_id"),
            session.get("usuario_perfil"),
            body.get("motivo"),
            body.get("observacao"),
        )
        if not sucesso:
            if erro == "Venda não encontrada.":
                code = 404
            elif erro.startswith("Permissão negada"):
                code = 403
            else:
                code = 400
            return err(erro, code)
        return ok(id=venda_id, status="cancelada")

    @vendas_api.route("/<int:venda_id>/itens/<int:item_id>/ajuste-desconto", methods=["PATCH"])
    def ajustar_desconto_item(venda_id, item_id):
        """Ajuste Comercial Autorizado (BR-043) -- só `admin`, checagem fina
        do perfil vive no service (mesmo padrão de `cancelar_venda`)."""
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") != "admin":
            return err("Permissão negada.", 403)

        body = safe_json(request)
        valor_unitario_novo = parse_float(body.get("valor_unitario"), default=None)
        sucesso, erro = service.ajustar_desconto_item(
            conectar,
            venda_id,
            item_id,
            session.get("usuario_id"),
            session.get("usuario_perfil"),
            valor_unitario_novo,
            body.get("motivo"),
        )
        if not sucesso:
            code = 404 if erro == "Item não encontrado." else 400
            return err(erro, code)
        return ok(id=item_id)

    @vendas_api.route("/<int:venda_id>/itens/<int:item_id>/historico-desconto")
    def historico_desconto_item(venda_id, item_id):
        """Histórico de Ajustes Comerciais do item (BR-043) -- só leitura,
        qualquer usuário autenticado (mesmo padrão de ver o Detalhe da
        venda)."""
        if not usuario_logado():
            return err("Não autenticado.", 401)

        return ok(historico=service.obter_historico_desconto_item(conectar, item_id))

    return vendas_api
