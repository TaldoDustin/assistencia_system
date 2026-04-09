from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for


def create_admin_blueprint(deps):
    bp = Blueprint("admin_views", __name__)

    conectar = deps["conectar"]
    listar_custos_operacionais = deps["listar_custos_operacionais"]
    categorias_custos_operacionais = deps["categorias_custos_operacionais"]
    carregar_tabelas_preco = deps["carregar_tabelas_preco"]
    salvar_tabelas_preco = deps["salvar_tabelas_preco"]
    iphone_models = deps["iphone_models"]

    @bp.route("/custos-operacionais", methods=["GET", "POST"])
    def cadastrar_custo_operacional():
        if request.method == "POST":
            descricao = (request.form.get("descricao") or "").strip()
            categoria = (request.form.get("categoria") or "").strip() or "Outros"
            valor_raw = (request.form.get("valor") or "").strip()
            data = (request.form.get("data") or "").strip() or datetime.now().strftime("%Y-%m-%d")
            observacoes = (request.form.get("observacoes") or "").strip()

            redirect_args = {
                "start_date": (request.form.get("start_date") or "").strip(),
                "end_date": (request.form.get("end_date") or "").strip(),
            }

            if not descricao:
                flash("Informe a descricao do custo operacional.", "error")
                return redirect(url_for("admin_views.cadastrar_custo_operacional", **redirect_args))

            try:
                valor = float(valor_raw)
            except ValueError:
                flash("Informe um valor numerico valido para o custo operacional.", "error")
                return redirect(url_for("admin_views.cadastrar_custo_operacional", **redirect_args))

            if valor <= 0:
                flash("O valor do custo operacional deve ser maior que zero.", "error")
                return redirect(url_for("admin_views.cadastrar_custo_operacional", **redirect_args))

            conn = conectar()
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO custos_operacionais (descricao, categoria, valor, data, observacoes)
                VALUES (?, ?, ?, ?, ?)
                """,
                (descricao, categoria, valor, data, observacoes),
            )
            conn.commit()
            conn.close()

            flash("Custo operacional registrado com sucesso.", "success")
            return redirect(url_for("admin_views.cadastrar_custo_operacional", **redirect_args))

        start_date = request.args.get("start_date", "")
        end_date = request.args.get("end_date", "")
        resumo_custos = listar_custos_operacionais(start_date, end_date)

        return render_template(
            "custos_operacionais.html",
            custos_operacionais=resumo_custos["itens"][:20],
            custos_operacionais_total=len(resumo_custos["itens"]),
            custos_operacionais_periodo=resumo_custos["total_periodo"],
            custos_por_categoria=resumo_custos["por_categoria"],
            categorias_custos_labels=resumo_custos["labels_categoria"],
            categorias_custos_values=resumo_custos["values_categoria"],
            categorias_custos_opcoes=categorias_custos_operacionais,
            start_date=start_date,
            end_date=end_date,
            today_str=datetime.now().strftime("%Y-%m-%d"),
        )

    @bp.route("/custos-operacionais/excluir/<int:custo_id>", methods=["POST"])
    def excluir_custo_operacional(custo_id):
        redirect_args = {
            "start_date": (request.form.get("start_date") or "").strip(),
            "end_date": (request.form.get("end_date") or "").strip(),
        }

        conn = conectar()
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM custos_operacionais WHERE id=?", (custo_id,))
            conn.commit()
        finally:
            conn.close()

        flash("Custo operacional removido.", "success")
        return redirect(url_for("admin_views.cadastrar_custo_operacional", **redirect_args))

    @bp.route("/reparos", methods=["GET", "POST"])
    def reparos():
        conn = conectar()
        cursor = conn.cursor()

        try:
            if request.method == "POST":
                nome = (request.form.get("nome") or "").strip()

                if not nome:
                    flash("Informe o nome do reparo.", "error")
                    return redirect(url_for("admin_views.reparos"))

                cursor.execute("SELECT id FROM reparos WHERE lower(nome)=lower(?)", (nome,))
                if cursor.fetchone():
                    flash("Esse tipo de reparo ja existe.", "error")
                    return redirect(url_for("admin_views.reparos"))

                cursor.execute("INSERT INTO reparos (nome) VALUES (?)", (nome,))
                conn.commit()
                flash("Tipo de reparo adicionado com sucesso.", "success")
                return redirect(url_for("admin_views.reparos"))

            cursor.execute("SELECT * FROM reparos ORDER BY nome")
            lista = cursor.fetchall()

            cursor.execute("SELECT COUNT(*) FROM os")
            total_os = cursor.fetchone()[0] or 0
        finally:
            conn.close()

        return render_template("reparos.html", reparos=lista, total_os=total_os)

    @bp.route("/reparos/deletar/<int:reparo_id>", methods=["POST"])
    def deletar_reparo(reparo_id):
        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT COUNT(*) FROM os_reparos WHERE reparo_id=?", (reparo_id,))
            usados = cursor.fetchone()[0] or 0
            if usados > 0:
                flash("Nao e possivel excluir: esse reparo ja esta vinculado a OS.", "error")
                return redirect(url_for("admin_views.reparos"))

            cursor.execute("DELETE FROM reparos WHERE id=?", (reparo_id,))
            conn.commit()
        finally:
            conn.close()

        flash("Tipo de reparo excluido com sucesso.", "success")
        return redirect(url_for("admin_views.reparos"))

    @bp.route("/reparos/editar/<int:reparo_id>", methods=["POST"])
    def editar_reparo(reparo_id):
        conn = conectar()
        cursor = conn.cursor()

        novo_nome = (request.form.get("nome") or "").strip()

        try:
            if not novo_nome:
                flash("Informe um nome valido para o reparo.", "error")
                return redirect(url_for("admin_views.reparos"))

            cursor.execute("SELECT id FROM reparos WHERE id=?", (reparo_id,))
            if not cursor.fetchone():
                flash("Tipo de reparo nao encontrado.", "error")
                return redirect(url_for("admin_views.reparos"))

            cursor.execute(
                "SELECT id FROM reparos WHERE lower(nome)=lower(?) AND id<>?",
                (novo_nome, reparo_id),
            )
            if cursor.fetchone():
                flash("Ja existe um tipo de reparo com esse nome.", "error")
                return redirect(url_for("admin_views.reparos"))

            cursor.execute("UPDATE reparos SET nome=? WHERE id=?", (novo_nome, reparo_id))
            conn.commit()
        finally:
            conn.close()

        flash("Tipo de reparo atualizado com sucesso.", "success")
        return redirect(url_for("admin_views.reparos"))

    @bp.route("/tabelas-preco", methods=["GET"])
    def tabelas_preco():
        tabelas = carregar_tabelas_preco()
        return render_template(
            "tabelas_preco.html",
            tabelas=tabelas,
            iphone_models=iphone_models,
        )

    @bp.route("/tabelas-preco/salvar", methods=["POST"])
    def salvar_entrada_tabela():
        tabela = (request.form.get("tabela") or "").strip()
        servico = (request.form.get("servico") or "").strip().upper()
        modelo = (request.form.get("modelo") or "").strip()
        valor_raw = (request.form.get("valor") or "").strip()

        if tabela not in ("ir_phones", "clientes"):
            flash("Tabela invalida.", "error")
            return redirect(url_for("admin_views.tabelas_preco"))

        if not servico or not modelo:
            flash("Servico e modelo sao obrigatorios.", "error")
            return redirect(url_for("admin_views.tabelas_preco"))

        try:
            valor = float(valor_raw)
        except ValueError:
            flash("Valor deve ser numerico.", "error")
            return redirect(url_for("admin_views.tabelas_preco"))

        if valor < 0:
            flash("Valor nao pode ser negativo.", "error")
            return redirect(url_for("admin_views.tabelas_preco"))

        tabelas = carregar_tabelas_preco()
        tabelas.setdefault(tabela, {}).setdefault(servico, {})[modelo] = valor
        salvar_tabelas_preco(tabelas)

        flash(f"Preco salvo: {servico} / {modelo} → R$ {valor:.2f} ({tabela}).", "success")
        return redirect(url_for("admin_views.tabelas_preco"))

    @bp.route("/tabelas-preco/excluir", methods=["POST"])
    def excluir_entrada_tabela():
        tabela = (request.form.get("tabela") or "").strip()
        servico = (request.form.get("servico") or "").strip()
        modelo = (request.form.get("modelo") or "").strip()

        if tabela not in ("ir_phones", "clientes"):
            flash("Tabela invalida.", "error")
            return redirect(url_for("admin_views.tabelas_preco"))

        tabelas = carregar_tabelas_preco()
        removido = False
        if tabela in tabelas and servico in tabelas[tabela] and modelo in tabelas[tabela][servico]:
            del tabelas[tabela][servico][modelo]
            if not tabelas[tabela][servico]:
                del tabelas[tabela][servico]
            salvar_tabelas_preco(tabelas)
            removido = True

        if removido:
            flash("Entrada removida com sucesso.", "success")
        else:
            flash("Entrada nao encontrada.", "error")
        return redirect(url_for("admin_views.tabelas_preco"))

    return bp
