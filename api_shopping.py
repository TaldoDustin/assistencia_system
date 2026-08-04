"""
Fluxoly - API Blueprint (Shopping List)
Routes under /api/shopping-list/* -- consumed by the React SPA frontend.
Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2 -- 1º domínio extraído).
"""

import contextlib
import csv
import io
import json
from datetime import datetime

from flask import Blueprint, Response, request, session

from fluxoly_api_helpers import err, ok, usuario_logado
from fluxoly_validation import parse_int, safe_json


def create_api_shopping_blueprint(deps):
    api_shopping = Blueprint("api_shopping", __name__, url_prefix="/api")
    conectar = deps["conectar"]

    SHOPPING_STATUSES = {"PENDENTE", "EM_COTACAO", "EM_COMPRA", "COMPRADO", "RECEBIDO", "CANCELADO", "ARQUIVADO"}
    SHOPPING_PRIORITIES = {"URGENTE", "ALTA", "NORMAL", "BAIXA"}

    def _log_shopping(cursor, shopping_id, usuario_id, acao, antes=None, depois=None):
        # Armazena valores anteriores/novos como JSON quando possível
        try:
            va = antes if antes is None else (antes if isinstance(antes, str) else json.dumps(antes, default=str))
        except Exception:
            va = str(antes or "")
        try:
            vn = depois if depois is None else (depois if isinstance(depois, str) else json.dumps(depois, default=str))
        except Exception:
            vn = str(depois or "")

        cursor.execute(
            """
            INSERT INTO shopping_list_logs (shopping_list_id, usuario_id, acao, valor_anterior, valor_novo)
            VALUES (?, ?, ?, ?, ?)
            """,
            (shopping_id, usuario_id, acao, va or "", vn or ""),
        )

    @api_shopping.route("/shopping-list")
    def shopping_list():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        # filtros e paginação
        status = (request.args.get("status") or "").strip()
        prioridade = (request.args.get("prioridade") or "").strip()
        produto = (request.args.get("produto") or "").strip().lower()
        os_id = (request.args.get("os_id") or "").strip()
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        try:
            conn = conectar()
            cursor = conn.cursor()
            where = []
            params = []
            if status:
                where.append("status = ?")
                params.append(status)
            if prioridade:
                where.append("prioridade = ?")
                params.append(prioridade)
            if produto:
                where.append("lower(produto_nome) LIKE ?")
                params.append(f"%{produto}%")
            if os_id and os_id.isdigit():
                where.append("os_id = ?")
                params.append(int(os_id))

            where_sql = " AND ".join(where) if where else "1=1"
            cursor.execute(f"SELECT COUNT(1) FROM shopping_list WHERE {where_sql}", tuple(params))
            total = cursor.fetchone()[0] or 0

            offset = (max(1, page) - 1) * per_page
            # join with usuarios to get responsavel nome
            cursor.execute(
                f"SELECT s.id, s.os_id, s.produto_id, s.produto_nome, s.quantidade_solicitada, s.quantidade_comprada, s.quantidade_recebida, s.prioridade, s.status, s.responsavel_id, u.nome, s.observacao, s.created_at, s.updated_at, s.purchased_at, s.received_at, s.cancelled_at FROM shopping_list s LEFT JOIN usuarios u ON s.responsavel_id = u.id WHERE {where_sql} ORDER BY prioridade DESC, created_at DESC LIMIT ? OFFSET ?",
                tuple(params + [per_page, offset]),
            )
            rows = cursor.fetchall()
            items = []
            for r in rows:
                items.append(
                    {
                        "id": r[0],
                        "os_id": r[1],
                        "produto_id": r[2],
                        "produto_nome": r[3],
                        "quantidade_solicitada": int(r[4] or 0),
                        "quantidade_comprada": int(r[5] or 0),
                        "quantidade_recebida": int(r[6] or 0),
                        "prioridade": r[7],
                        "status": r[8],
                        "responsavel_id": r[9],
                        "responsavel_nome": r[10] or "",
                        "observacao": r[11] or "",
                        "created_at": r[12] or "",
                        "updated_at": r[13] or "",
                        "purchased_at": r[14] or "",
                        "received_at": r[15] or "",
                        "cancelled_at": r[16] or "",
                    }
                )
            conn.close()
            return ok(items=items, total=total, page=page, per_page=per_page)
        except Exception as exc:
            with contextlib.suppress(Exception):
                conn.close()
            return err(f"Erro ao listar shopping list: {exc}")

    @api_shopping.route("/shopping-list/<int:item_id>")
    def shopping_get(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT s.id, s.os_id, s.produto_id, s.produto_nome, s.quantidade_solicitada, s.quantidade_comprada, s.quantidade_recebida, s.prioridade, s.status, s.responsavel_id, u.nome, s.observacao, s.created_at, s.updated_at, s.purchased_at, s.received_at, s.cancelled_at FROM shopping_list s LEFT JOIN usuarios u ON s.responsavel_id = u.id WHERE s.id=?",
                (item_id,),
            )
            r = cursor.fetchone()
            conn.close()
            if not r:
                return err("Item não encontrado", 404)
            return ok(
                item={
                    "id": r[0],
                    "os_id": r[1],
                    "produto_id": r[2],
                    "produto_nome": r[3],
                    "quantidade_solicitada": int(r[4] or 0),
                    "quantidade_comprada": int(r[5] or 0),
                    "quantidade_recebida": int(r[6] or 0),
                    "prioridade": r[7],
                    "status": r[8],
                    "responsavel_id": r[9],
                    "responsavel_nome": r[10] or "",
                    "observacao": r[11] or "",
                    "created_at": r[12] or "",
                    "updated_at": r[13] or "",
                    "purchased_at": r[14] or "",
                    "received_at": r[15] or "",
                    "cancelled_at": r[16] or "",
                }
            )
        except Exception as exc:
            with contextlib.suppress(Exception):
                conn.close()
            return err(f"Erro ao obter item: {exc}")

    @api_shopping.route("/shopping-list", methods=["POST"])
    def shopping_create():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            body = safe_json(request)
            os_id = parse_int(body.get("os_id"), default=0)
            produto_id = body.get("produto_id")
            try:
                produto_id = int(produto_id) if produto_id else None
            except Exception:
                produto_id = None
            produto_nome = (body.get("produto_nome") or "").strip()
            quantidade = parse_int(body.get("quantidade_solicitada", body.get("quantidade")), default=1)
            prioridade = (body.get("prioridade") or "NORMAL").strip().upper()
            observacao = (body.get("observacao") or "").strip()

            if os_id is None:
                return err("os_id inválido.")
            if quantidade is None or quantidade <= 0:
                return err("Quantidade invalida")
            if prioridade not in SHOPPING_PRIORITIES:
                prioridade = "NORMAL"

            conn = conectar()
            cursor = conn.cursor()

            # Verifica duplicidade: mesmo produto (id ou nome) na mesma OS e status != CANCELADO
            if produto_id:
                cursor.execute(
                    "SELECT id FROM shopping_list WHERE os_id=? AND produto_id=? AND COALESCE(status, '') != 'CANCELADO'",
                    (os_id, produto_id),
                )
            else:
                cursor.execute(
                    "SELECT id FROM shopping_list WHERE os_id=? AND lower(produto_nome)=? AND COALESCE(status, '') != 'CANCELADO'",
                    (os_id, produto_nome.lower()),
                )
            if cursor.fetchone():
                conn.close()
                return err("Esta peça já está cadastrada nesta OS.")

            cursor.execute(
                """
                INSERT INTO shopping_list (os_id, produto_id, produto_nome, quantidade_solicitada, prioridade, observacao)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (os_id or None, produto_id, produto_nome, quantidade, prioridade, observacao),
            )
            new_id = cursor.lastrowid
            _log_shopping(
                cursor,
                new_id,
                session.get("usuario_id"),
                "create",
                antes=None,
                depois=str({"quantidade": quantidade, "prioridade": prioridade}),
            )
            conn.commit()
            conn.close()
            return ok(id=new_id)
        except Exception as exc:
            with contextlib.suppress(Exception):
                conn.close()
            return err(f"Erro ao criar item: {exc}")

    @api_shopping.route("/shopping-list/<int:item_id>", methods=["PUT"])
    def shopping_update(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            body = safe_json(request)
            quantidade = body.get("quantidade_solicitada")
            prioridade = (body.get("prioridade") or "").strip().upper()
            observacao = body.get("observacao")

            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT quantidade_solicitada, prioridade, observacao FROM shopping_list WHERE id=?", (item_id,)
            )
            row = cursor.fetchone()
            if not row:
                conn.close()
                return err("Item não encontrado", 404)
            antes = {"quantidade_solicitada": row[0], "prioridade": row[1], "observacao": row[2]}

            updates = []
            params = []
            if quantidade is not None:
                q = parse_int(quantidade, default=None)
                if q is None or q < 0:
                    conn.close()
                    return err("Quantidade invalida")
                updates.append("quantidade_solicitada = ?")
                params.append(q)
            if prioridade:
                if prioridade not in SHOPPING_PRIORITIES:
                    prioridade = "NORMAL"
                updates.append("prioridade = ?")
                params.append(prioridade)
            if observacao is not None:
                updates.append("observacao = ?")
                params.append(observacao)

            if updates:
                params.extend([datetime.now().isoformat(), item_id])
                cursor.execute(f"UPDATE shopping_list SET {', '.join(updates)}, updated_at=? WHERE id=?", tuple(params))
                _log_shopping(cursor, item_id, session.get("usuario_id"), "update", antes=str(antes), depois=str(body))
                conn.commit()

            conn.close()
            return ok(id=item_id)
        except Exception as exc:
            with contextlib.suppress(Exception):
                conn.close()
            return err(f"Erro ao atualizar item: {exc}")

    @api_shopping.route("/shopping-list/<int:item_id>/status", methods=["PATCH"])
    def shopping_patch_status(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        body = safe_json(request)
        novo = (body.get("status") or "").strip().upper()
        quantidade_recebida = body.get("quantidade_recebida")

        if novo not in SHOPPING_STATUSES:
            return err("Status invalido")

        usuario_id = session.get("usuario_id")
        perfil = session.get("usuario_perfil")

        # só perfis autorizados podem alterar status/cancel/arquivar
        if perfil not in ("admin", "tecnico", "comprador"):
            return err("Permissao negada", 403)

        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT status, responsavel_id FROM shopping_list WHERE id=?", (item_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return err("Item nao encontrado", 404)
            atual_status, atual_responsavel = row[0], row[1]

            # Bloqueio de compras simultâneas
            if (
                atual_status == "EM_COMPRA"
                and novo == "EM_COMPRA"
                and atual_responsavel
                and atual_responsavel != usuario_id
            ):
                # buscar nome do responsavel
                cursor.execute("SELECT nome FROM usuarios WHERE id=?", (atual_responsavel,))
                nome = cursor.fetchone()
                nome = nome[0] if nome else "Outro usuario"
                conn.close()
                return err(f"Compra em andamento por {nome}")

            # Valida transições simples (não permite saltos de RECEBIDO -> PENDENTE, por exemplo)
            valid_transitions = {
                "PENDENTE": {"EM_COTACAO", "EM_COMPRA", "CANCELADO", "ARQUIVADO"},
                "EM_COTACAO": {"EM_COMPRA", "CANCELADO", "ARQUIVADO"},
                "EM_COMPRA": {"COMPRADO", "CANCELADO", "ARQUIVADO"},
                "COMPRADO": {"RECEBIDO", "ARQUIVADO"},
                "RECEBIDO": {"ARQUIVADO"},
                "CANCELADO": set(),
                "ARQUIVADO": set(),
            }

            # Permite idempotência (novo == atual_status nunca é bloqueado)
            if (
                atual_status
                and atual_status in valid_transitions
                and novo not in valid_transitions.get(atual_status, set())
                and novo != atual_status
            ):
                conn.close()
                return err(f"Transição inválida de {atual_status} para {novo}")

            antes = atual_status
            updates = []
            params = []
            now = datetime.now().isoformat()

            if novo == "EM_COMPRA":
                updates.append("status = ?")
                updates.append("responsavel_id = ?")
                updates.append("updated_at = ?")
                params.extend([novo, usuario_id, now])
            elif novo == "COMPRADO":
                updates.append("status = ?")
                updates.append("quantidade_comprada = COALESCE(quantidade_comprada,0)")
                updates.append("purchased_at = ?")
                updates.append("updated_at = ?")
                params.extend([novo, now, now])
            elif novo == "RECEBIDO":
                # pode informar quantidade_recebida
                qrecv = parse_int(quantidade_recebida, default=None)
                if qrecv is not None:
                    updates.append("quantidade_recebida = ?")
                    params.append(qrecv)
                updates.append("status = ?")
                updates.append("received_at = ?")
                updates.append("updated_at = ?")
                params.extend([novo, now, now])
            elif novo == "CANCELADO":
                updates.append("status = ?")
                updates.append("cancelled_at = ?")
                updates.append("updated_at = ?")
                params.extend([novo, now, now])
            else:
                updates.append("status = ?")
                updates.append("updated_at = ?")
                params.extend([novo, now])

            params.append(item_id)
            cursor.execute(f"UPDATE shopping_list SET {', '.join(updates)} WHERE id=?", tuple(params))
            _log_shopping(cursor, item_id, usuario_id, "status_change", antes=str(antes), depois=novo)
            conn.commit()
            conn.close()
            return ok(id=item_id, status=novo)
        except Exception as exc:
            with contextlib.suppress(Exception):
                conn.close()
            return err(f"Erro ao alterar status: {exc}")

    @api_shopping.route("/shopping-list/<int:item_id>", methods=["DELETE"])
    def shopping_delete(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        perfil = session.get("usuario_perfil")
        if perfil not in ("admin", "tecnico", "comprador"):
            return err("Permissao negada", 403)
        usuario_id = session.get("usuario_id")
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute("SELECT status FROM shopping_list WHERE id=?", (item_id,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return err("Item nao encontrado", 404)
            antes = row[0]
            now = datetime.now().isoformat()
            cursor.execute(
                "UPDATE shopping_list SET status='CANCELADO', cancelled_at=?, updated_at=? WHERE id=?",
                (now, now, item_id),
            )
            _log_shopping(cursor, item_id, usuario_id, "cancel", antes=antes, depois="CANCELADO")
            conn.commit()
            conn.close()
            return ok(id=item_id)
        except Exception as exc:
            with contextlib.suppress(Exception):
                conn.close()
            return err(f"Erro ao cancelar item: {exc}")

    @api_shopping.route("/shopping-list/grouped")
    def shopping_grouped():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT COALESCE(produto_id,0), produto_nome, SUM(quantidade_solicitada) as total_qtd, COUNT(DISTINCT os_id) as os_count FROM shopping_list WHERE COALESCE(status,'') != 'CANCELADO' GROUP BY COALESCE(produto_id,0), produto_nome ORDER BY total_qtd DESC"
            )
            rows = cursor.fetchall()
            conn.close()
            result = []
            for r in rows:
                result.append(
                    {
                        "produto_id": r[0],
                        "produto_nome": r[1] or "",
                        "quantidade_total": int(r[2] or 0),
                        "os_count": int(r[3] or 0),
                    }
                )
            return ok(grouped=result)
        except Exception as exc:
            with contextlib.suppress(Exception):
                conn.close()
            return err(f"Erro ao agrupar: {exc}")

    @api_shopping.route("/shopping-list/<int:item_id>/logs")
    def shopping_logs(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, usuario_id, acao, valor_anterior, valor_novo, created_at FROM shopping_list_logs WHERE shopping_list_id=? ORDER BY created_at DESC",
                (item_id,),
            )
            rows = cursor.fetchall()
            conn.close()
            logs = []
            for r in rows:
                va = r[3] or ""
                vn = r[4] or ""
                # tenta desserializar JSON quando aplicavel
                try:
                    va_parsed = json.loads(va) if va else va
                except Exception:
                    va_parsed = va
                try:
                    vn_parsed = json.loads(vn) if vn else vn
                except Exception:
                    vn_parsed = vn

                logs.append(
                    {
                        "id": r[0],
                        "usuario_id": r[1],
                        "acao": r[2],
                        "valor_anterior": va_parsed,
                        "valor_novo": vn_parsed,
                        "created_at": r[5],
                    }
                )
            return ok(logs=logs)
        except Exception as exc:
            with contextlib.suppress(Exception):
                conn.close()
            return err(f"Erro ao listar logs: {exc}")

    @api_shopping.route("/shopping-list/logs/export")
    def shopping_logs_export():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        fmt = (request.args.get("format") or "json").lower()
        try:
            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT l.id, l.shopping_list_id, l.usuario_id, u.nome, l.acao, l.valor_anterior, l.valor_novo, l.created_at FROM shopping_list_logs l LEFT JOIN usuarios u ON l.usuario_id = u.id ORDER BY l.created_at DESC"
            )
            rows = cursor.fetchall()
            conn.close()
            records = []
            for r in rows:
                va = r[5] or ""
                vn = r[6] or ""
                try:
                    va_parsed = json.loads(va) if va else va
                except Exception:
                    va_parsed = va
                try:
                    vn_parsed = json.loads(vn) if vn else vn
                except Exception:
                    vn_parsed = vn

                records.append(
                    {
                        "id": r[0],
                        "shopping_list_id": r[1],
                        "usuario_id": r[2],
                        "usuario_nome": r[3] or "",
                        "acao": r[4],
                        "valor_anterior": va_parsed,
                        "valor_novo": vn_parsed,
                        "created_at": r[7],
                    }
                )

            if fmt == "csv":
                # gerar CSV simples
                out = io.StringIO()
                writer = csv.writer(out)
                writer.writerow(
                    [
                        "id",
                        "shopping_list_id",
                        "usuario_id",
                        "usuario_nome",
                        "acao",
                        "valor_anterior",
                        "valor_novo",
                        "created_at",
                    ]
                )
                for rec in records:
                    writer.writerow(
                        [
                            rec["id"],
                            rec["shopping_list_id"],
                            rec["usuario_id"],
                            rec["usuario_nome"],
                            rec["acao"],
                            (
                                json.dumps(rec["valor_anterior"], ensure_ascii=False)
                                if not isinstance(rec["valor_anterior"], str)
                                else rec["valor_anterior"]
                            ),
                            (
                                json.dumps(rec["valor_novo"], ensure_ascii=False)
                                if not isinstance(rec["valor_novo"], str)
                                else rec["valor_novo"]
                            ),
                            rec["created_at"],
                        ]
                    )
                csv_text = out.getvalue()
                resp = Response(csv_text, mimetype="text/csv")
                resp.headers["Content-Disposition"] = 'attachment; filename="shopping_list_logs.csv"'
                return resp
            # default JSON
            return ok(records=records)
        except Exception as exc:
            with contextlib.suppress(Exception):
                conn.close()
            return err(f"Erro ao exportar logs: {exc}")

    return api_shopping
