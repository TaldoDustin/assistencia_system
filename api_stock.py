"""
Fluxoly - API Blueprint (Estoque)
Rotas /api/estoque* -- consumidas pelo frontend React (CRUD de itens de
estoque, reposição sugerida, movimentações). Extraído de
fluxoly_blueprints_api.py (TD-01, Phase 2 -- 11º domínio extraído).
"""

import math
from datetime import datetime, timedelta

from flask import Blueprint, request, session

from fluxoly_api_helpers import err, ok, usuario_logado
from fluxoly_validation import parse_float, parse_int, safe_json, validate_positive_number


def create_api_stock_blueprint(deps):
    api_stock = Blueprint("api_stock", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    normalizar_modelo_iphone = deps["normalizar_modelo_iphone"]
    registrar_movimentacao = deps["registrar_movimentacao"]
    ESTOQUE_TIPOS = deps["estoque_tipos"]
    ESTOQUE_QUALIDADES = deps["estoque_qualidades"]

    def _normalizar_tipo_estoque(valor):
        texto = (valor or "").strip().lower()
        for opcao in ESTOQUE_TIPOS:
            if texto == opcao.lower():
                return opcao
        return "Outros"

    def _normalizar_qualidade_estoque(valor):
        texto = (valor or "").strip().lower()
        for opcao in ESTOQUE_QUALIDADES:
            if texto == opcao.lower():
                return opcao
        return "Padrao"

    def _recalcular_custo_medio(cursor, estoque_id):
        cursor.execute(
            """
            SELECT
                COALESCE(SUM(COALESCE(valor_compra, 0) * COALESCE(quantidade_disponivel, 0)), 0),
                COALESCE(SUM(COALESCE(quantidade_disponivel, 0)), 0)
            FROM estoque_lotes
            WHERE estoque_id = ?
            """,
            (estoque_id,),
        )
        total_valor, total_qtd = cursor.fetchone() or (0, 0)
        total_qtd = int(total_qtd or 0)

        if total_qtd > 0:
            valor_medio = float(total_valor or 0) / total_qtd
            cursor.execute("UPDATE estoque SET valor=? WHERE id=?", (round(valor_medio, 2), estoque_id))

    def _status_item_estoque(quantidade, ultima_movimentacao, consumo_90d):
        qtd = int(quantidade or 0)
        consumo = int(consumo_90d or 0)
        if qtd > 0:
            return "disponivel"
        if consumo > 0:
            return "esgotado_ativo"
        if not (ultima_movimentacao or "").strip():
            return "inativo"
        return "esgotado"

    @api_stock.route("/estoque")
    def listar_estoque():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        filtro_modelo = (request.args.get("modelo") or "").strip()
        filtro_tipo = (request.args.get("tipo") or "").strip()
        filtro_qualidade = (request.args.get("qualidade") or "").strip()
        filtro_status = (request.args.get("status") or "").strip().lower()
        include_zerados = str(request.args.get("include_zerados") or "").strip().lower() in {"1", "true", "sim", "yes"}
        q = (request.args.get("q") or "").strip().lower()

        agora = datetime.now()
        corte_30 = (agora - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        corte_90 = (agora - timedelta(days=90)).strftime("%Y-%m-%d %H:%M:%S")

        conn = conectar()
        cursor = conn.cursor()

        params = []
        where = []
        if filtro_modelo == "Universal":
            where.append("COALESCE(modelo,'') = ''")
        elif filtro_modelo:
            where.append("COALESCE(modelo,'') = ?")
            params.append(normalizar_modelo_iphone(filtro_modelo) or filtro_modelo)

        if filtro_tipo:
            where.append("COALESCE(tipo,'Outros') = ?")
            params.append(_normalizar_tipo_estoque(filtro_tipo))

        if filtro_qualidade:
            where.append("COALESCE(qualidade,'Padrao') = ?")
            params.append(_normalizar_qualidade_estoque(filtro_qualidade))

        clause = f"WHERE {' AND '.join(where)}" if where else ""

        cursor.execute(
            f"""
            SELECT
                id,
                descricao,
                valor,
                fornecedor,
                quantidade,
                data_compra,
                COALESCE(modelo,''),
                COALESCE(tipo,'Outros'),
                COALESCE(qualidade,'Padrao'),
                (
                    SELECT COALESCE(MAX(m.data), '')
                    FROM movimentacoes m
                    WHERE m.estoque_id = estoque.id
                ) AS ultima_movimentacao,
                (
                    SELECT COALESCE(SUM(m.quantidade), 0)
                    FROM movimentacoes m
                    WHERE m.estoque_id = estoque.id
                      AND m.tipo = 'saida'
                      AND m.data >= ?
                ) AS consumo_30d,
                (
                    SELECT COALESCE(SUM(m.quantidade), 0)
                    FROM movimentacoes m
                    WHERE m.estoque_id = estoque.id
                      AND m.tipo = 'saida'
                      AND m.data >= ?
                ) AS consumo_90d,
                COALESCE(requer_imei, 0)
            FROM estoque {clause}
            ORDER BY id DESC
            """,
            [corte_30, corte_90, *params],
        )
        itens = []
        for r in cursor.fetchall():
            status_item = _status_item_estoque(r[4] or 0, r[9] or "", r[11] or 0)
            quantidade_item = int(r[4] or 0)
            if quantidade_item <= 0 and not include_zerados:
                continue
            item = {
                "id": r[0],
                "descricao": r[1] or "",
                "valor": round(r[2] or 0, 2),
                "fornecedor": r[3] or "",
                "quantidade": quantidade_item,
                "data_compra": r[5] or "",
                "modelo": r[6] or "",
                "tipo": r[7] or "Outros",
                "qualidade": r[8] or "Padrao",
                "ultima_movimentacao": r[9] or "",
                "consumo_30d": int(r[10] or 0),
                "consumo_90d": int(r[11] or 0),
                "status_estoque": status_item,
                # Rastreabilidade individual (IMEI/serial hoje; outros identificadores no
                # futuro -- ver KI-020/C1.3.5) do item, não apenas "IMEI" no sentido estrito.
                "requer_imei": bool(r[12]),
            }
            itens.append(item)

        if filtro_status:
            itens = [i for i in itens if (i.get("status_estoque") or "") == filtro_status]

        if q:
            itens = [
                i
                for i in itens
                if q in f"{i['descricao']} {i['modelo']} {i['fornecedor']} {i['tipo']} {i['qualidade']}".lower()
            ]

        # Summary stats
        cursor.execute("SELECT COALESCE(SUM(valor*quantidade),0) FROM estoque")
        valor_total = cursor.fetchone()[0] or 0
        conn.close()

        total_lotes = len(itens)
        total_unidades = sum(i["quantidade"] for i in itens)
        criticos = len([i for i in itens if i["quantidade"] <= 2])

        return ok(
            itens=itens,
            total_lotes=total_lotes,
            total_unidades=total_unidades,
            valor_total=round(valor_total, 2),
            criticos=criticos,
        )

    @api_stock.route("/estoque/reposicao-sugerida")
    def reposicao_sugerida_estoque():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        dias_base = parse_int(request.args.get("dias"), default=30)
        if dias_base is None:
            return err("Parâmetro dias inválido.")
        if dias_base < 7:
            dias_base = 7
        if dias_base > 120:
            dias_base = 120

        corte = (datetime.now() - timedelta(days=dias_base)).strftime("%Y-%m-%d %H:%M:%S")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                e.id,
                COALESCE(e.sku, ''),
                COALESCE(e.descricao, ''),
                COALESCE(e.modelo, ''),
                COALESCE(e.tipo, 'Outros'),
                COALESCE(e.qualidade, 'Padrao'),
                COALESCE(e.quantidade, 0),
                COALESCE(e.valor, 0),
                COALESCE(SUM(CASE WHEN m.tipo='saida' THEN m.quantidade ELSE 0 END), 0) AS consumo_periodo
            FROM estoque e
            LEFT JOIN movimentacoes m
                ON m.estoque_id = e.id
               AND m.data >= ?
            GROUP BY e.id
            ORDER BY consumo_periodo DESC, e.id DESC
            """,
            (corte,),
        )
        rows = cursor.fetchall()
        conn.close()

        itens = []
        for r in rows:
            quantidade = int(r[6] or 0)
            consumo_periodo = int(r[8] or 0)
            if consumo_periodo <= 0:
                continue
            if quantidade > 2:
                continue

            consumo_mensal = (consumo_periodo / max(dias_base, 1)) * 30.0
            estoque_alvo = max(1, int(math.ceil(consumo_mensal * 1.5)))
            sugestao = max(1, estoque_alvo - quantidade)

            if quantidade <= 0 and consumo_mensal >= 6:
                prioridade = "alta"
            elif quantidade <= 1 and consumo_mensal >= 3:
                prioridade = "media"
            else:
                prioridade = "baixa"

            itens.append(
                {
                    "id": r[0],
                    "sku": r[1],
                    "descricao": r[2],
                    "modelo": r[3],
                    "tipo": r[4],
                    "qualidade": r[5],
                    "quantidade_atual": quantidade,
                    "valor_medio": round(float(r[7] or 0), 2),
                    "consumo_periodo": consumo_periodo,
                    "consumo_mensal_estimado": round(consumo_mensal, 2),
                    "estoque_alvo": estoque_alvo,
                    "sugestao_reposicao": sugestao,
                    "prioridade": prioridade,
                }
            )

        return ok(itens=itens, dias_base=dias_base)

    @api_stock.route("/estoque", methods=["POST"])
    def criar_estoque():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "estoque"):
            return err("Permissão negada.", 403)

        body = safe_json(request)
        descricao = (body.get("descricao") or "").strip()
        modelo = normalizar_modelo_iphone(body.get("modelo") or "") or (body.get("modelo") or "").strip()
        tipo = _normalizar_tipo_estoque(body.get("tipo"))
        qualidade = _normalizar_qualidade_estoque(body.get("qualidade"))
        sku = (body.get("sku") or "").strip().upper()
        valor = parse_float(body.get("valor"), default=0.0)
        fornecedor = (body.get("fornecedor") or "Nao informado").strip()
        quantidade = parse_int(body.get("quantidade"), default=0)
        data_compra = (body.get("data_compra") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        # Rastreabilidade individual (IMEI/serial hoje -- ver KI-020/C1.3.5): flag manual
        # indicando se este item exige rastreamento por unidade via unidades_serializadas.
        requer_imei = 1 if body.get("requer_imei") else 0

        if not descricao or not validate_positive_number(valor) or quantidade is None or quantidade < 0:
            return err("Preencha descrição, valor e quantidade.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO estoque (descricao, modelo, valor, fornecedor, quantidade, data_compra, sku, tipo, qualidade, requer_imei)
                VALUES (?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    descricao,
                    modelo,
                    valor,
                    fornecedor,
                    max(0, quantidade),
                    data_compra,
                    sku,
                    tipo,
                    qualidade,
                    requer_imei,
                ),
            )
            novo_id = cursor.lastrowid
            if quantidade > 0:
                cursor.execute(
                    """
                    INSERT INTO estoque_lotes (
                        estoque_id, fornecedor, valor_compra, quantidade, quantidade_disponivel, data_compra, observacoes, criado_em
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        novo_id,
                        fornecedor,
                        valor,
                        quantidade,
                        quantidade,
                        data_compra,
                        "compra inicial",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    ),
                )
                registrar_movimentacao(cursor, novo_id, "entrada", quantidade)
            _recalcular_custo_medio(cursor, novo_id)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api_stock.route("/estoque/<int:item_id>", methods=["PUT"])
    def atualizar_estoque(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "estoque"):
            return err("Permissão negada.", 403)

        body = safe_json(request)
        descricao = (body.get("descricao") or "").strip()
        modelo = normalizar_modelo_iphone(body.get("modelo") or "") or (body.get("modelo") or "").strip()
        tipo = _normalizar_tipo_estoque(body.get("tipo"))
        qualidade = _normalizar_qualidade_estoque(body.get("qualidade"))
        sku = (body.get("sku") or "").strip().upper()
        valor = parse_float(body.get("valor"), default=0.0)
        fornecedor = (body.get("fornecedor") or "Nao informado").strip()
        quantidade_nova = parse_int(body.get("quantidade"), default=0)
        data_compra = (body.get("data_compra") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        # Rastreabilidade individual (IMEI/serial hoje -- ver KI-020/C1.3.5): flag manual
        # indicando se este item exige rastreamento por unidade via unidades_serializadas.
        requer_imei = 1 if body.get("requer_imei") else 0

        if not descricao or not validate_positive_number(valor) or quantidade_nova is None:
            return err("Preencha descrição, valor e quantidade válidos.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT quantidade, descricao, sku FROM estoque WHERE id=?", (item_id,))
            row = cursor.fetchone()
            if not row:
                return err("Item não encontrado.", 404)
            qtd_antiga = row[0] or 0
            sku_atual = (row[2] or "").strip().upper()
            if not sku:
                sku = sku_atual

            # Permitir sempre editar, mesmo se existir outro com modelo/tipo/qualidade igual

            cursor.execute(
                """
                UPDATE estoque
                SET descricao=?, modelo=?, valor=?, fornecedor=?, quantidade=?, data_compra=?, sku=?, tipo=?, qualidade=?, requer_imei=?
                WHERE id=?
                """,
                (
                    descricao,
                    modelo,
                    valor,
                    fornecedor,
                    max(0, quantidade_nova),
                    data_compra,
                    sku,
                    tipo,
                    qualidade,
                    requer_imei,
                    item_id,
                ),
            )
            diff = max(0, quantidade_nova) - qtd_antiga
            if diff != 0:
                tipo_mov = "entrada" if diff > 0 else "saida"
                registrar_movimentacao(cursor, item_id, tipo_mov, abs(diff))
                if diff > 0:
                    cursor.execute(
                        """
                        INSERT INTO estoque_lotes (
                            estoque_id, fornecedor, valor_compra, quantidade, quantidade_disponivel, data_compra, observacoes, criado_em
                        )
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            item_id,
                            fornecedor,
                            valor,
                            diff,
                            diff,
                            data_compra,
                            "ajuste manual",
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )
                else:
                    restante = abs(diff)
                    cursor.execute(
                        """
                        SELECT id, COALESCE(quantidade_disponivel, 0)
                        FROM estoque_lotes
                        WHERE estoque_id=? AND COALESCE(quantidade_disponivel, 0) > 0
                        ORDER BY COALESCE(data_compra, '') ASC, id ASC
                        """,
                        (item_id,),
                    )
                    for lote_id, disponivel in cursor.fetchall():
                        if restante <= 0:
                            break
                        usar = min(restante, int(disponivel or 0))
                        if usar <= 0:
                            continue
                        cursor.execute(
                            "UPDATE estoque_lotes SET quantidade_disponivel = MAX(0, quantidade_disponivel - ?) WHERE id=?",
                            (usar, lote_id),
                        )
                        restante -= usar
            _recalcular_custo_medio(cursor, item_id)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api_stock.route("/estoque/<int:item_id>", methods=["DELETE"])
    def deletar_estoque(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "estoque"):
            return err("Permissão negada.", 403)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT COUNT(*) FROM os_pecas p JOIN os o ON p.os_id=o.id WHERE p.estoque_id=? AND o.status NOT IN ('Finalizado','Cancelado')",
                (item_id,),
            )
            em_uso = cursor.fetchone()[0] or 0
            if em_uso > 0:
                return err("Não é possível excluir: peça está em uso em OS abertas.")
            cursor.execute("DELETE FROM estoque_lotes WHERE estoque_id=?", (item_id,))
            cursor.execute("DELETE FROM estoque WHERE id=?", (item_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api_stock.route("/estoque/movimentacoes")
    def movimentacoes():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.estoque_id, m.tipo, m.quantidade, m.data,
                   COALESCE(e.descricao, '')
            FROM movimentacoes m
            LEFT JOIN estoque e ON e.id = m.estoque_id
            ORDER BY m.id DESC LIMIT 30
            """
        )
        rows = cursor.fetchall()
        conn.close()
        return ok(
            movimentacoes=[
                {"id": r[0], "estoque_id": r[1], "tipo": r[2], "quantidade": r[3], "data": r[4], "descricao": r[5]}
                for r in rows
            ]
        )

    return api_stock
