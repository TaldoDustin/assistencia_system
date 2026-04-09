from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for


def create_inventory_blueprint(deps):
    bp = Blueprint("inventory_views", __name__)

    conectar = deps["conectar"]
    normalizar_modelo_iphone = deps["normalizar_modelo_iphone"]
    registrar_movimentacao = deps["registrar_movimentacao"]
    iphone_models = deps["iphone_models"]

    @bp.route("/estoque")
    def estoque():
        conn = conectar()
        cursor = conn.cursor()

        filtro_modelo = (request.args.get("modelo") or "").strip()
        filtro_modelo_norm = ""
        if filtro_modelo and filtro_modelo != "Universal":
            filtro_modelo_norm = normalizar_modelo_iphone(filtro_modelo) or filtro_modelo

        cursor.execute(
            """
            SELECT
                COALESCE(NULLIF(modelo, ''), 'Universal') AS modelo_grupo,
                COUNT(*) AS lotes,
                COALESCE(SUM(quantidade), 0) AS total_unidades,
                COALESCE(SUM(valor * quantidade), 0) AS valor_total
            FROM estoque
            GROUP BY COALESCE(NULLIF(modelo, ''), 'Universal')
            ORDER BY CASE WHEN COALESCE(NULLIF(modelo, ''), 'Universal') = 'Universal' THEN 1 ELSE 0 END,
                     COALESCE(NULLIF(modelo, ''), 'Universal')
            """
        )
        grupos_modelo = [
            {
                "modelo": row[0],
                "lotes": row[1],
                "quantidade": row[2],
                "valor_total": round(row[3] or 0, 2),
            }
            for row in cursor.fetchall()
        ]

        filtros_sql = []
        filtros_params = []
        if filtro_modelo == "Universal":
            filtros_sql.append("COALESCE(modelo, '') = ''")
        elif filtro_modelo_norm:
            filtros_sql.append("COALESCE(modelo, '') = ?")
            filtros_params.append(filtro_modelo_norm)

        where_clause = f"WHERE {' AND '.join(filtros_sql)}" if filtros_sql else ""

        cursor.execute(
            f"""
            SELECT id, descricao, valor, fornecedor, quantidade, data_compra, COALESCE(modelo, '')
            FROM estoque
            {where_clause}
            ORDER BY id DESC
            """,
            filtros_params,
        )
        dados = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT COALESCE(SUM(valor * quantidade), 0)
            FROM estoque
            {where_clause}
            """,
            filtros_params,
        )
        total_estoque = cursor.fetchone()[0] or 0

        cursor.execute(
            f"""
            SELECT
                descricao,
                COALESCE(modelo, '') AS modelo,
                COUNT(*) AS lotes,
                COALESCE(SUM(quantidade), 0) AS total_unidades,
                MIN(valor) AS min_valor,
                MAX(valor) AS max_valor
            FROM estoque
            {where_clause}
            GROUP BY descricao, COALESCE(modelo, '')
            ORDER BY descricao, modelo
            """,
            filtros_params,
        )
        agrupado = cursor.fetchall()

        cursor.execute(
            f"""
            SELECT estoque_id, tipo, quantidade, data
            FROM movimentacoes
            {"WHERE estoque_id IN (SELECT id FROM estoque " + where_clause + ")" if where_clause else ""}
            ORDER BY id DESC
            LIMIT 20
            """,
            filtros_params,
        )
        movimentacoes = cursor.fetchall()

        total_lotes = len(dados)
        total_itens = sum((item[4] or 0) for item in dados)
        itens_criticos = sum(1 for item in dados if (item[4] or 0) <= 2)

        conn.close()

        return render_template(
            "estoque.html",
            estoque=dados,
            total_estoque=total_estoque,
            estoque_agrupado=agrupado,
            grupos_modelo=grupos_modelo,
            movimentacoes=movimentacoes,
            total_lotes=total_lotes,
            total_itens=total_itens,
            itens_criticos=itens_criticos,
            iphone_models=iphone_models,
            filtro_modelo=(filtro_modelo if filtro_modelo else ""),
        )

    @bp.route("/estoque/cadastro", methods=["GET", "POST"])
    def cadastro_peca():
        conn = conectar()
        cursor = conn.cursor()

        if request.method == "POST":
            descricao = (request.form.get("descricao") or "").strip()
            modelo_raw = (request.form.get("modelo") or "").strip()
            modelo = normalizar_modelo_iphone(modelo_raw)
            fornecedor = (request.form.get("fornecedor") or "").strip() or "Nao informado"
            valor_raw = (request.form.get("valor") or "").strip()
            quantidade_raw = (request.form.get("quantidade") or "").strip()
            data = (request.form.get("data") or "").strip() or datetime.now().strftime("%Y-%m-%d")

            if not descricao:
                conn.close()
                flash("Descricao da peca e obrigatoria.", "error")
                return redirect(url_for("inventory_views.cadastro_peca"))

            if modelo_raw and not modelo:
                conn.close()
                flash("Selecione um modelo de iPhone valido na lista.", "error")
                return redirect(url_for("inventory_views.cadastro_peca"))

            if valor_raw == "":
                conn.close()
                flash("Valor da peca e obrigatorio.", "error")
                return redirect(url_for("inventory_views.cadastro_peca"))

            try:
                valor = float(valor_raw)
                quantidade = int(quantidade_raw)
            except ValueError:
                conn.close()
                flash("Valor e quantidade devem ser numericos.", "error")
                return redirect(url_for("inventory_views.cadastro_peca"))

            if valor < 0 or quantidade < 0:
                conn.close()
                flash("Valor e quantidade nao podem ser negativos.", "error")
                return redirect(url_for("inventory_views.cadastro_peca"))

            cursor.execute(
                """
                INSERT INTO estoque (descricao, valor, fornecedor, quantidade, data_compra, modelo)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (descricao, valor, fornecedor, quantidade, data, modelo),
            )
            estoque_id = cursor.lastrowid
            registrar_movimentacao(cursor, estoque_id, "entrada", quantidade)
            conn.commit()
            conn.close()
            flash("Peca cadastrada com sucesso.", "success")
            return redirect(url_for("inventory_views.estoque"))

        conn.close()
        return render_template(
            "estoque_cadastro.html",
            today_str=datetime.now().strftime("%Y-%m-%d"),
            iphone_models=iphone_models,
        )

    @bp.route("/estoque/editar/<int:item_id>", methods=["POST"])
    def editar_item_estoque(item_id):
        conn = conectar()
        cursor = conn.cursor()

        descricao = (request.form.get("descricao") or "").strip()
        modelo_raw = (request.form.get("modelo") or "").strip()
        modelo = normalizar_modelo_iphone(modelo_raw)
        fornecedor = (request.form.get("fornecedor") or "").strip() or "Nao informado"
        valor_raw = (request.form.get("valor") or "").strip()
        quantidade_raw = (request.form.get("quantidade") or "").strip()
        data_compra = (request.form.get("data_compra") or "").strip()

        if not descricao:
            conn.close()
            flash("Descricao da peca e obrigatoria.", "error")
            return redirect(url_for("inventory_views.estoque"))

        if modelo_raw and not modelo:
            conn.close()
            flash("Modelo invalido. Use apenas modelos da lista oficial.", "error")
            return redirect(url_for("inventory_views.estoque"))

        if valor_raw == "":
            conn.close()
            flash("Valor da peca e obrigatorio.", "error")
            return redirect(url_for("inventory_views.estoque"))

        try:
            valor = float(valor_raw)
            nova_quantidade = int(quantidade_raw)
        except ValueError:
            conn.close()
            flash("Valor e quantidade devem ser numericos.", "error")
            return redirect(url_for("inventory_views.estoque"))

        if valor < 0 or nova_quantidade < 0:
            conn.close()
            flash("Valor/quantidade nao podem ser negativos.", "error")
            return redirect(url_for("inventory_views.estoque"))

        cursor.execute("SELECT quantidade FROM estoque WHERE id=?", (item_id,))
        atual = cursor.fetchone()
        if not atual:
            conn.close()
            flash("Item de estoque nao encontrado.", "error")
            return redirect(url_for("inventory_views.estoque"))

        if not data_compra:
            data_compra = datetime.now().strftime("%Y-%m-%d")

        quantidade_anterior = atual[0] or 0
        delta = nova_quantidade - quantidade_anterior

        cursor.execute(
            """
            UPDATE estoque
            SET descricao=?, modelo=?, valor=?, fornecedor=?, quantidade=?, data_compra=?
            WHERE id=?
            """,
            (descricao, modelo, valor, fornecedor, nova_quantidade, data_compra, item_id),
        )

        if delta > 0:
            registrar_movimentacao(cursor, item_id, "entrada", delta)
        elif delta < 0:
            registrar_movimentacao(cursor, item_id, "saida", abs(delta))

        conn.commit()
        conn.close()
        flash("Item atualizado com sucesso.", "success")
        return redirect(url_for("inventory_views.estoque"))

    @bp.route("/estoque/deletar/<int:item_id>", methods=["POST"])
    def deletar_item_estoque(item_id):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT 1
            FROM os_pecas op
            JOIN os ON os.id = op.os_id
            WHERE op.estoque_id = ?
            AND os.status NOT IN ('Finalizado', 'Cancelado')
            LIMIT 1
            """,
            (item_id,),
        )
        bloqueado = cursor.fetchone()

        if bloqueado:
            conn.close()
            flash("Nao e possivel excluir item usado em OS ativa.", "error")
            return redirect(url_for("inventory_views.estoque"))

        cursor.execute("DELETE FROM estoque WHERE id=?", (item_id,))
        conn.commit()
        conn.close()
        flash("Item excluido do estoque.", "success")
        return redirect(url_for("inventory_views.estoque"))

    return bp
