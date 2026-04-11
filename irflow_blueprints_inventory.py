from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for

from irflow_web import redirecionar_com_query_string


def create_inventory_blueprint(deps):
    bp = Blueprint("inventory_views", __name__)

    conectar = deps["conectar"]
    normalizar_modelo_iphone = deps["normalizar_modelo_iphone"]
    registrar_movimentacao = deps["registrar_movimentacao"]
    iphone_models = deps["iphone_models"]

    @bp.route("/estoque")
    def estoque():
        return redirecionar_com_query_string(request, "/app/estoque")

    @bp.route("/estoque/cadastro", methods=["GET", "POST"])
    def cadastro_peca():
        if request.method == "GET":
            return redirecionar_com_query_string(request, "/app/estoque")

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
