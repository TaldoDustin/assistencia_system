from datetime import datetime

from flask import Blueprint, flash, jsonify, redirect, render_template, request

from irflow_web import redirecionar_com_query_string


def create_orders_blueprint(deps):
    bp = Blueprint("order_views", __name__)

    conectar = deps["conectar"]
    texto_reparos_os = deps["texto_reparos_os"]
    normalizar_status_os = deps["normalizar_status_os"]
    status_finalizado = deps["status_finalizado_const"]
    status_cancelado = deps["status_cancelado_const"]
    status_em_andamento = deps["status_em_andamento_const"]
    status_os_validos = deps["status_os_validos"]
    status_aberto = deps["status_aberto"]
    coletar_status_opcoes = deps["coletar_status_opcoes"]
    calcular_faturamento_os = deps["calcular_faturamento_os"]
    calcular_lucro_os = deps["calcular_lucro_os"]
    carregar_os_com_relacoes = deps["carregar_os_com_relacoes"]
    extrair_reparo_ids = deps["extrair_reparo_ids"]
    validar_reparo_ids = deps["validar_reparo_ids"]
    vendedor_valido = deps["vendedor_valido"]
    ler_valores_financeiros_form = deps["ler_valores_financeiros_form"]
    salvar_reparos_os = deps["salvar_reparos_os"]
    modelo_compativel = deps["modelo_compativel"]
    consumir_peca_da_os = deps["consumir_peca_da_os"]
    adicionar_peca_os_sem_consumir = deps["adicionar_peca_os_sem_consumir"]
    devolver_pecas_da_os = deps["devolver_pecas_da_os"]
    registrar_movimentacao = deps["registrar_movimentacao"]
    obter_reparos_por_os = deps["obter_reparos_por_os"]
    modelo_para_os = deps["modelo_para_os"]
    normalizar_imei = deps["normalizar_imei"]
    carregar_tabelas_preco = deps["carregar_tabelas_preco"]
    iphone_models = deps["iphone_models"]
    iphone_colors = deps["iphone_colors"]
    vendedores = deps["vendedores"]
    tecnicos = deps["tecnicos"]
    status_os_opcoes = deps["status_os_opcoes"]

    @bp.route("/ordens")
    def ordens():
        return redirecionar_com_query_string(request, "/app/ordens")

    @bp.route("/nova", methods=["GET", "POST"])
    def nova():
        if request.method == "GET":
            return redirecionar_com_query_string(request, "/app/ordens/nova")

        conn = conectar()
        cursor = conn.cursor()

        if request.method == "POST":
            tipo = (request.form.get("tipo") or "").strip()
            cliente = (request.form.get("cliente") or "").strip()
            modelo = modelo_para_os(request.form.get("modelo"))
            cor = (request.form.get("cor") or "").strip()
            imei = normalizar_imei(request.form.get("imei"))
            aparelho = modelo
            tecnico = (request.form.get("tecnico") or "").strip()
            vendedor = (request.form.get("vendedor") or "").strip()
            observacoes = (request.form.get("observacoes") or "").strip()
            interna_ir_phones = (request.form.get("interna_ir_phones") or "") == "1"

            if tipo.lower() == "upgrade":
                tipo = "Assistencia"
                cliente = "IR Phones"

            if interna_ir_phones:
                tipo = "Assistencia"
                cliente = "IR Phones"
                vendedor = ""

            try:
                reparo_ids = extrair_reparo_ids(request.form)
            except ValueError:
                conn.close()
                flash("Selecione apenas reparos validos.", "error")
                return redirect("/nova")

            if not tipo or not cliente or not modelo or not tecnico or not reparo_ids:
                conn.close()
                flash("Preencha os campos obrigatorios de cliente e servico.", "error")
                return redirect("/nova")

            if not validar_reparo_ids(cursor, reparo_ids):
                conn.close()
                flash("Um ou mais reparos selecionados nao existem mais.", "error")
                return redirect("/nova")

            if not vendedor_valido(vendedor, vendedores):
                conn.close()
                flash("Selecione um vendedor valido.", "error")
                return redirect("/nova")

            try:
                valor_cobrado, valor_descontado = ler_valores_financeiros_form(request.form)
            except ValueError as exc:
                conn.close()
                flash(str(exc) or "Campos financeiros invalidos.", "error")
                return redirect("/nova")

            data = (request.form.get("data_os") or "").strip() or datetime.now().strftime("%Y-%m-%d")
            pecas_ids = request.form.getlist("pecas_ids")
            status = normalizar_status_os(request.form.get("status"), status_padrao=status_em_andamento)

            cursor.execute(
                """
                INSERT INTO os (
                    tipo, cliente, aparelho, tecnico, reparo_id, status,
                    valor_cobrado, valor_descontado, custo_pecas, data, observacoes, modelo, vendedor, cor, imei
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tipo,
                    cliente,
                    aparelho,
                    tecnico,
                    reparo_ids[0],
                    status,
                    valor_cobrado,
                    valor_descontado,
                    0,
                    data,
                    observacoes,
                    modelo,
                    vendedor,
                    cor,
                    imei,
                ),
            )

            os_id = cursor.lastrowid
            salvar_reparos_os(cursor, os_id, reparo_ids)
            custo_total_pecas = 0.0

            for p_id in pecas_ids:
                try:
                    peca_id = int(p_id)
                except ValueError:
                    conn.rollback()
                    conn.close()
                    flash("Peca invalida selecionada.", "error")
                    return redirect("/nova")

                cursor.execute("SELECT valor, modelo FROM estoque WHERE id=?", (peca_id,))
                row = cursor.fetchone()
                valor_peca = float(row[0]) if row and row[0] is not None else 0.0
                modelo_peca = row[1] if row and len(row) > 1 else ""

                if not modelo_compativel(modelo_peca, modelo):
                    conn.rollback()
                    conn.close()
                    flash("Peca selecionada nao e compativel com o modelo informado.", "error")
                    return redirect("/nova")

                ok, erro = consumir_peca_da_os(cursor, os_id, peca_id)
                if not ok:
                    conn.rollback()
                    conn.close()
                    flash(erro, "error")
                    return redirect("/nova")

                custo_total_pecas += valor_peca

            cursor.execute(
                "UPDATE os SET custo_pecas=? WHERE id=?",
                (round(custo_total_pecas, 2), os_id),
            )

            conn.commit()
            conn.close()

            flash("Ordem de servico criada com sucesso.", "success")
            return redirect("/ordens")

        cursor.execute("SELECT * FROM reparos")
        reparos = cursor.fetchall()

        cursor.execute(
            """
            SELECT id, descricao, valor, fornecedor, quantidade, modelo
            FROM estoque
            ORDER BY descricao, valor
            """
        )
        pecas = cursor.fetchall()
        conn.close()

        return render_template(
            "nova_os.html",
            reparos=reparos,
            pecas=pecas,
            today_str=datetime.now().strftime("%Y-%m-%d"),
            iphone_models=iphone_models,
            iphone_colors=iphone_colors,
            vendedores=vendedores,
            tecnicos=tecnicos,
            price_tables=carregar_tabelas_preco(),
        )

    @bp.route("/deletar/<int:id>", methods=["POST"])
    def deletar(id):
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("SELECT status FROM os WHERE id=?", (id,))
        result = cursor.fetchone()

        if result:
            status = result[0]
            if normalizar_status_os(status) not in {status_finalizado, status_cancelado}:
                devolver_pecas_da_os(cursor, id, "devolucao")

        cursor.execute("DELETE FROM os_pecas WHERE os_id=?", (id,))
        cursor.execute("DELETE FROM os_reparos WHERE os_id=?", (id,))
        cursor.execute("DELETE FROM os WHERE id=?", (id,))

        conn.commit()
        conn.close()
        return redirect("/")

    @bp.route("/editar/<int:id>", methods=["GET", "POST"])
    def editar(id):
        if request.method == "GET":
            return redirecionar_com_query_string(request, f"/app/ordens/editar/{id}")

        conn = conectar()
        cursor = conn.cursor()

        if request.method == "POST":
            tipo = (request.form.get("tipo") or "").strip()
            cliente = (request.form.get("cliente") or "").strip()
            tecnico = (request.form.get("tecnico") or "").strip()
            vendedor = (request.form.get("vendedor") or "").strip()
            status = normalizar_status_os(request.form.get("status"))
            modelo = modelo_para_os(request.form.get("modelo"))
            cor = (request.form.get("cor") or "").strip()
            imei = normalizar_imei(request.form.get("imei"))
            data_os = (request.form.get("data_os") or "").strip()
            observacoes = (request.form.get("observacoes") or "").strip()
            try:
                valor_cobrado, valor_descontado = ler_valores_financeiros_form(request.form)
            except ValueError as exc:
                conn.close()
                flash(str(exc), "error")
                return redirect(f"/editar/{id}")

            try:
                reparo_ids = extrair_reparo_ids(request.form)
            except ValueError:
                conn.close()
                flash("Selecione apenas reparos validos.", "error")
                return redirect(f"/editar/{id}")

            if not tipo or not cliente or not tecnico or not reparo_ids or not status or not modelo:
                conn.close()
                flash("Preencha todos os campos obrigatorios.", "error")
                return redirect(f"/editar/{id}")

            if not validar_reparo_ids(cursor, reparo_ids):
                conn.close()
                flash("Um ou mais reparos selecionados nao existem mais.", "error")
                return redirect(f"/editar/{id}")

            if not vendedor_valido(vendedor, vendedores):
                conn.close()
                flash("Selecione um vendedor valido.", "error")
                return redirect(f"/editar/{id}")

            if not data_os:
                data_os = datetime.now().strftime("%Y-%m-%d")

            aparelho = modelo
            pecas_ids = request.form.getlist("pecas_ids")

            cursor.execute("SELECT status, COALESCE(data_finalizado, '') FROM os WHERE id=?", (id,))
            status_atual_row = cursor.fetchone()
            status_atual = status_atual_row[0] if status_atual_row else ""
            data_finalizado_atual = status_atual_row[1] if status_atual_row else ""

            data_finalizado_valor = None
            if status == status_finalizado:
                data_finalizado_valor = data_finalizado_atual or datetime.now().strftime("%Y-%m-%d")

            cursor.execute(
                """
                UPDATE os
                SET tipo=?, cliente=?, aparelho=?, tecnico=?, reparo_id=?, status=?,
                    valor_cobrado=?, valor_descontado=?, data=?, observacoes=?, modelo=?, vendedor=?, cor=?, imei=?, data_finalizado=?
                WHERE id=?
                """,
                (
                    tipo,
                    cliente,
                    aparelho,
                    tecnico,
                    reparo_ids[0],
                    status,
                    valor_cobrado,
                    valor_descontado,
                    data_os,
                    observacoes,
                    modelo,
                    vendedor,
                    cor,
                    imei,
                    data_finalizado_valor,
                    id,
                ),
            )
            salvar_reparos_os(cursor, id, reparo_ids)

            if normalizar_status_os(status_atual) != status_cancelado:
                devolver_pecas_da_os(cursor, id, "devolucao-edicao")
            cursor.execute("DELETE FROM os_pecas WHERE os_id=?", (id,))

            custo_total_pecas = 0.0
            for p_id in pecas_ids:
                try:
                    peca_id = int(p_id)
                except ValueError:
                    conn.rollback()
                    conn.close()
                    flash("Peca invalida selecionada.", "error")
                    return redirect(f"/editar/{id}")

                cursor.execute("SELECT valor, modelo FROM estoque WHERE id=?", (peca_id,))
                row = cursor.fetchone()
                valor_peca = float(row[0]) if row and row[0] is not None else 0.0
                modelo_peca = row[1] if row and len(row) > 1 else ""

                if not modelo_compativel(modelo_peca, modelo):
                    conn.rollback()
                    conn.close()
                    flash("Peca selecionada nao e compativel com o modelo informado.", "error")
                    return redirect(f"/editar/{id}")

                if status == status_cancelado:
                    ok, erro = adicionar_peca_os_sem_consumir(cursor, id, peca_id)
                else:
                    ok, erro = consumir_peca_da_os(cursor, id, peca_id)
                if not ok:
                    conn.rollback()
                    conn.close()
                    flash(erro, "error")
                    return redirect(f"/editar/{id}")

                custo_total_pecas += valor_peca

            cursor.execute(
                "UPDATE os SET custo_pecas=? WHERE id=?",
                (round(custo_total_pecas, 2), id),
            )

            conn.commit()
            conn.close()
            flash("OS atualizada com sucesso.", "success")
            return redirect("/ordens")

        cursor.execute(
            """
            SELECT
                id, tipo, cliente, aparelho, tecnico, reparo_id, status,
                COALESCE(valor_cobrado, 0), COALESCE(valor_descontado, 0),
                COALESCE(custo_pecas, 0), COALESCE(data, ''),
                COALESCE(data_finalizado, ''), COALESCE(modelo, ''),
                COALESCE(cor, ''), COALESCE(imei, ''),
                COALESCE(vendedor, ''), COALESCE(observacoes, ''),
                COALESCE(origem_integracao, '')
            FROM os
            WHERE id=?
            """,
            (id,),
        )
        os_item = cursor.fetchone()
        if not os_item:
            conn.close()
            flash("OS nao encontrada.", "error")
            return redirect("/ordens")

        cursor.execute("SELECT id, nome FROM reparos ORDER BY nome")
        reparos_lista = cursor.fetchall()
        reparos_por_os = obter_reparos_por_os(cursor)
        cursor.execute(
            """
            SELECT id, descricao, valor, fornecedor, quantidade, modelo
            FROM estoque
            ORDER BY descricao, valor
            """
        )
        pecas = cursor.fetchall()
        cursor.execute(
            """
            SELECT
                estoque_id,
                COALESCE(peca_descricao, ''),
                COALESCE(valor, 0),
                COALESCE(peca_fornecedor, ''),
                COALESCE(quantidade, 1),
                COALESCE(peca_modelo, '')
            FROM os_pecas
            WHERE os_id=?
            ORDER BY id
            """,
            (id,),
        )
        os_pecas = cursor.fetchall()
        conn.close()

        # índices alinhados ao SELECT explícito acima
        # [0]=id [1]=tipo [2]=cliente [3]=aparelho [4]=tecnico [5]=reparo_id
        # [6]=status [7]=valor_cobrado [8]=valor_descontado [9]=custo_pecas
        # [10]=data [11]=data_finalizado [12]=modelo [13]=cor [14]=imei
        # [15]=vendedor [16]=observacoes [17]=origem_integracao
        os_dict = {
            "id": os_item[0],
            "tipo": os_item[1] or "",
            "cliente": os_item[2] or "",
            "aparelho": os_item[3] or "",
            "tecnico": os_item[4] or "",
            "reparo_id": os_item[5] or "",
            "reparo_ids": reparos_por_os.get(id, {}).get("ids", []),
            "reparo": texto_reparos_os(reparos_por_os.get(id), ""),
            "status": os_item[6] or "",
            "valor_cobrado": os_item[7] or 0,
            "valor_descontado": os_item[8] or 0,
            "custo_pecas": os_item[9] or 0,
            "data": os_item[10] or "",
            "modelo": os_item[12] or "",
            "cor": os_item[13] or "",
            "imei": os_item[14] or "",
            "vendedor": os_item[15] or "",
            "observacoes": os_item[16] or "",
        }

        return render_template(
            "editar.html",
            os=os_dict,
            reparos=reparos_lista,
            pecas=pecas,
            os_pecas=os_pecas,
            iphone_models=iphone_models,
            iphone_colors=iphone_colors,
            price_tables=carregar_tabelas_preco(),
            status_opcoes=status_os_opcoes,
            tipos=["Assistencia", "Garantia"],
            tecnicos=tecnicos,
            vendedores=vendedores,
        )

    @bp.route("/atualizar_status", methods=["POST"])
    def atualizar_status():
        os_id = request.form.get("id", type=int)
        status = normalizar_status_os(request.form.get("status"), status_padrao="")

        if not os_id:
            return jsonify({"ok": False, "erro": "OS invalida."}), 400
        if status not in status_os_validos:
            return jsonify({"ok": False, "erro": "Status invalido."}), 400

        conn = conectar()
        cursor = conn.cursor()

        try:
            cursor.execute("SELECT status, COALESCE(data_finalizado, '') FROM os WHERE id=?", (os_id,))
            row = cursor.fetchone()
            if not row:
                return jsonify({"ok": False, "erro": "OS nao encontrada."}), 404

            status_atual = normalizar_status_os(row[0], status_padrao="")
            data_finalizado_atual = row[1] if row else ""

            if status == status_atual:
                return jsonify({"ok": True})

            data_finalizado_valor = None
            if status == status_finalizado:
                data_finalizado_valor = data_finalizado_atual or datetime.now().strftime("%Y-%m-%d")

            cursor.execute(
                "UPDATE os SET status=?, data_finalizado=? WHERE id=?",
                (status, data_finalizado_valor, os_id),
            )

            if status == status_cancelado and status_atual != status_cancelado:
                devolver_pecas_da_os(cursor, os_id, "devolucao")
            elif status_atual == status_cancelado and status != status_cancelado:
                cursor.execute(
                    """
                    SELECT id, estoque_id, quantidade
                    FROM os_pecas
                    WHERE os_id=?
                    """,
                    (os_id,),
                )
                pecas = cursor.fetchall()
                for os_peca_id, estoque_id, qtd in pecas:
                    cursor.execute("SELECT quantidade FROM estoque WHERE id=?", (estoque_id,))
                    item = cursor.fetchone()
                    if not item:
                        continue

                    if (item[0] or 0) < (qtd or 0):
                        conn.rollback()
                        return jsonify({"ok": False, "erro": "Estoque insuficiente para reativar OS."}), 400

                    cursor.execute(
                        "UPDATE estoque SET quantidade = quantidade - ? WHERE id = ?",
                        (qtd, estoque_id),
                    )
                    registrar_movimentacao(cursor, estoque_id, "saida", qtd)

            conn.commit()
            return jsonify({"ok": True})
        except Exception as exc:
            conn.rollback()
            return jsonify({"ok": False, "erro": f"Falha ao atualizar status: {exc}"}), 500
        finally:
            conn.close()

    return bp
