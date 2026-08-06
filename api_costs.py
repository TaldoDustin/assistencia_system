"""
Fluxoly - API Blueprint (Custos Operacionais)
Rotas /api/custos* (CRUD) -- consumidas pelo frontend React (Custos.jsx).
Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2 -- 3º domínio extraído).
"""

from datetime import datetime

from flask import Blueprint, request

from fluxoly_api_helpers import err, ok, usuario_admin, usuario_logado
from fluxoly_validation import parse_float, safe_json, validate_positive_number


def create_api_costs_blueprint(deps):
    api_costs = Blueprint("api_costs", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    listar_custos_operacionais = deps["listar_custos_operacionais"]

    @api_costs.route("/custos")
    def listar_custos():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        resumo = listar_custos_operacionais(start_date, end_date)
        return ok(**resumo)

    @api_costs.route("/custos", methods=["POST"])
    def criar_custo():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        descricao = (body.get("descricao") or "").strip()
        categoria = (body.get("categoria") or "Outros").strip()
        valor = parse_float(body.get("valor"), default=0.0)
        data = (body.get("data") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        observacoes = (body.get("observacoes") or "").strip()

        if not descricao or not validate_positive_number(valor):
            return err("Informe descrição e valor maior que zero.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO custos_operacionais (descricao, categoria, valor, data, observacoes) VALUES (?,?,?,?,?)",
                (descricao, categoria, valor, data, observacoes),
            )
            novo_id = cursor.lastrowid
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api_costs.route("/custos/<int:custo_id>", methods=["PUT"])
    def atualizar_custo(custo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        descricao = (body.get("descricao") or "").strip()
        categoria = (body.get("categoria") or "Outros").strip()
        valor = parse_float(body.get("valor"), default=0.0)
        data = (body.get("data") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        observacoes = (body.get("observacoes") or "").strip()

        if not descricao or not validate_positive_number(valor):
            return err("Informe descrição e valor maior que zero.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM custos_operacionais WHERE id=?", (custo_id,))
            if not cursor.fetchone():
                return err("Custo não encontrado.", 404)

            cursor.execute(
                """
                UPDATE custos_operacionais
                SET descricao=?, categoria=?, valor=?, data=?, observacoes=?
                WHERE id=?
                """,
                (descricao, categoria, valor, data, observacoes, custo_id),
            )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api_costs.route("/custos/<int:custo_id>", methods=["DELETE"])
    def deletar_custo(custo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM custos_operacionais WHERE id=?", (custo_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    return api_costs
