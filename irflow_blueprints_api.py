"""
IR Flow - API Blueprint (JSON endpoints)
All routes under /api/* — consumed by the React SPA frontend.
Authentication: Flask session cookies (same-origin, credentials: 'include').
"""

from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request, session, send_from_directory
import os


def create_api_blueprint(deps):
    api = Blueprint("api", __name__, url_prefix="/api")

    # ── Inject dependencies ────────────────────────────────────────────────
    conectar = deps["conectar"]
    normalizar_status_os = deps["normalizar_status_os"]
    status_finalizado = deps["status_finalizado"]
    status_cancelado = deps["status_cancelado"]
    status_aberto = deps["status_aberto"]
    calcular_faturamento_os = deps["calcular_faturamento_os"]
    calcular_lucro_os = deps["calcular_lucro_os"]
    carregar_os_com_relacoes = deps["carregar_os_com_relacoes"]
    extrair_reparo_ids = deps["extrair_reparo_ids"]
    validar_reparo_ids = deps["validar_reparo_ids"]
    vendedor_valido = deps["vendedor_valido"]
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
    salvar_tabelas_preco = deps["salvar_tabelas_preco"]
    texto_reparos_os = deps["texto_reparos_os"]
    listar_custos_operacionais = deps["listar_custos_operacionais"]
    agrupar_relatorio_ir_phones = deps["agrupar_relatorio_ir_phones"]
    agrupar_relatorio_tecnicos = deps["agrupar_relatorio_tecnicos"]
    montar_linhas_relatorio_ir_phones = deps["montar_linhas_relatorio_ir_phones"]
    montar_linhas_relatorio_tecnicos = deps["montar_linhas_relatorio_tecnicos"]
    montar_pdf_texto = deps["montar_pdf_texto"]
    formatar_periodo_relatorio = deps["formatar_periodo_relatorio"]
    parse_data_ymd = deps["parse_data_ymd"]
    obter_alertas_sistema = deps["obter_alertas_sistema"]
    normalizar_modelo_iphone = deps["normalizar_modelo_iphone"]
    iphone_models = deps["iphone_models"]
    iphone_colors = deps["iphone_colors"]
    vendedores = deps["vendedores"]
    tecnicos = deps["tecnicos"]
    status_os_opcoes = deps["status_os_opcoes"]
    categorias_custos = deps["categorias_custos"]
    reparos_padrao = deps["reparos_padrao"]
    backup_dir = deps["backup_dir"]
    criar_backup = deps["criar_backup"]
    google_drive_backup_dir = deps["google_drive_backup_dir"]
    garantir_pasta_backup_google_drive = deps["garantir_pasta_backup_google_drive"]
    enviar_backup_email = deps["enviar_backup_email"]
    backup_email_remetente = deps["backup_email_remetente"]
    backup_email_senha_app = deps["backup_email_senha_app"]
    backup_email_destino = deps["backup_email_destino"]
    check_password_hash = deps["check_password_hash"]
    generate_password_hash = deps["generate_password_hash"]
    sincronizar_mercado_phone = deps["sincronizar_mercado_phone"]
    mercado_phone_runtime_config = deps["mercado_phone_runtime_config"]
    mercado_phone_helpers = deps["mercado_phone_helpers"]

    STATUS_FINALIZADO = status_finalizado
    STATUS_CANCELADO = status_cancelado
    STATUS_EM_ANDAMENTO = deps["status_em_andamento"]
    STATUS_AGUARDANDO_PECA = deps["status_aguardando_peca"]

    # ── Auth helpers ───────────────────────────────────────────────────────

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

    # ── AUTHENTICATION ─────────────────────────────────────────────────────

    @api.route("/auth/login", methods=["POST"])
    def auth_login():
        body = request.get_json(silent=True) or {}
        usuario_txt = (body.get("usuario") or "").strip()
        senha_txt = body.get("senha") or ""

        if not usuario_txt or not senha_txt:
            return err("Usuário e senha são obrigatórios.")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, senha_hash, perfil, ativo FROM usuarios WHERE usuario = ?",
            (usuario_txt,),
        )
        row = cursor.fetchone()
        conn.close()

        if row and row[4] == 1 and check_password_hash(row[2], senha_txt):
            session.permanent = True
            session["usuario_id"] = row[0]
            session["usuario_nome"] = row[1]
            session["usuario_perfil"] = row[3]
            return ok(usuario={"id": row[0], "nome": row[1], "perfil": row[3]})

        return err("Usuário ou senha inválidos.", 401)

    @api.route("/auth/logout", methods=["POST"])
    def auth_logout():
        session.clear()
        return ok()

    @api.route("/auth/me")
    def auth_me():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        return ok(usuario={
            "id": session["usuario_id"],
            "nome": session["usuario_nome"],
            "perfil": session["usuario_perfil"],
        })

    # ── CONSTANTS ──────────────────────────────────────────────────────────

    @api.route("/constantes")
    def constantes():
        return ok(
            iphone_models=iphone_models,
            iphone_colors=iphone_colors,
            vendedores=vendedores,
            tecnicos=tecnicos,
            status_opcoes=status_os_opcoes,
            os_tipos=["Assistencia", "Garantia", "Upgrade"],
            categorias_custos=categorias_custos,
            reparos_padrao=reparos_padrao,
            garantia_dias=90,
        )

    # ── ALERTS ─────────────────────────────────────────────────────────────

    @api.route("/alertas")
    def alertas():
        if not usuario_logado():
            return ok(alertas=[])
        try:
            alerts = obter_alertas_sistema(limit=20)
        except Exception:
            alerts = []
        return ok(alertas=alerts)

    # ── DASHBOARD ──────────────────────────────────────────────────────────

    @api.route("/dashboard")
    def dashboard():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        filtro_tecnico = (request.args.get("tecnico") or "").strip()

        conn = conectar()
        cursor = conn.cursor()
        dados, reparos_por_os, custos = carregar_os_com_relacoes(cursor, order_by="os.id DESC")

        lucro_total = faturamento_total = custo_consumido_periodo = 0.0
        ordens_finalizadas = ordens_abertas = 0
        lucro_por_tecnico = {}
        resumo_por_vendedor = {}
        servicos_mais_feitos = {}
        faturamento_por_dia = {}

        for os_item in dados:
            os_id = os_item[0]
            tipo = os_item[1]
            tecnico = os_item[4]
            status = normalizar_status_os(os_item[6])
            valor_cobrado = os_item[7]
            valor_descontado = os_item[8]
            data = os_item[10]
            vendedor = os_item[13]

            custo = custos.get(os_id, 0)
            lucro = calcular_lucro_os(tipo, valor_cobrado, valor_descontado, custo)
            faturamento_os = calcular_faturamento_os(valor_cobrado, valor_descontado)

            if filtro_tecnico and tecnico != filtro_tecnico:
                continue
            if (start_date or end_date) and not data:
                continue
            if start_date and data and data < start_date:
                continue
            if end_date and data and data > end_date:
                continue

            if not status_cancelado(status):
                custo_consumido_periodo += custo

            if status_finalizado(status):
                lucro_total += lucro
                faturamento_total += faturamento_os
                ordens_finalizadas += 1
                if data:
                    faturamento_por_dia[data] = faturamento_por_dia.get(data, 0) + faturamento_os
            elif status_aberto(status):
                ordens_abertas += 1

            for reparo_nome in (reparos_por_os.get(os_id, {}).get("nomes", []) or [tipo]):
                if reparo_nome:
                    servicos_mais_feitos[reparo_nome] = servicos_mais_feitos.get(reparo_nome, 0) + 1

            if tecnico and status_finalizado(status):
                lucro_por_tecnico[tecnico] = lucro_por_tecnico.get(tecnico, 0) + lucro

            if vendedor:
                if vendedor not in resumo_por_vendedor:
                    resumo_por_vendedor[vendedor] = {"os_total": 0, "faturamento": 0, "lucro": 0}
                resumo_por_vendedor[vendedor]["os_total"] += 1
                if status_finalizado(status):
                    resumo_por_vendedor[vendedor]["lucro"] += lucro
                    resumo_por_vendedor[vendedor]["faturamento"] += faturamento_os

        cursor.execute("SELECT COALESCE(SUM(valor * quantidade), 0) FROM estoque")
        gasto_total = cursor.fetchone()[0] or 0
        conn.close()

        resumo_custos = listar_custos_operacionais(start_date, end_date)
        custos_operacionais_periodo = resumo_custos["total_periodo"]
        resultado_liquido = lucro_total - custos_operacionais_periodo
        ticket_medio = round(faturamento_total / ordens_finalizadas, 2) if ordens_finalizadas else 0

        dias_ordenados = sorted(faturamento_por_dia.keys())
        servicos_sorted = sorted(servicos_mais_feitos.items(), key=lambda x: x[1], reverse=True)
        lucro_tecnicos_sorted = sorted(lucro_por_tecnico.items(), key=lambda x: x[1], reverse=True)

        return ok(
            faturamento_total=round(faturamento_total, 2),
            lucro_total=round(lucro_total, 2),
            custo_consumido_periodo=round(custo_consumido_periodo, 2),
            custos_operacionais_periodo=round(custos_operacionais_periodo, 2),
            resultado_liquido=round(resultado_liquido, 2),
            ticket_medio=ticket_medio,
            gasto_total_estoque=round(gasto_total, 2),
            ordens_finalizadas=ordens_finalizadas,
            ordens_abertas=ordens_abertas,
            faturamento_por_dia=[{"date": d, "value": round(faturamento_por_dia[d], 2)} for d in dias_ordenados],
            lucro_por_tecnico=[{"name": k, "value": round(v, 2)} for k, v in lucro_tecnicos_sorted],
            servicos_mais_feitos=[{"name": k, "value": v} for k, v in servicos_sorted[:10]],
            resumo_por_vendedor=[
                {"vendedor": k, **{kk: round(vv, 2) if isinstance(vv, float) else vv for kk, vv in v.items()}}
                for k, v in sorted(resumo_por_vendedor.items(), key=lambda x: x[1]["faturamento"], reverse=True)
            ],
            custos_por_categoria=resumo_custos["por_categoria"],
        )

    # ── SERVICE ORDERS ─────────────────────────────────────────────────────

    def _os_row_to_dict(row, reparos_por_os, custos):
        os_id = row[0]
        tipo = row[1]
        status = normalizar_status_os(row[6])
        valor_cobrado = row[7]
        valor_descontado = row[8]
        custo = custos.get(os_id, row[9] or 0)
        reparos_info = reparos_por_os.get(os_id, {"ids": [], "nomes": []})
        return {
            "id": os_id,
            "tipo": tipo or "",
            "cliente": row[2] or "",
            "aparelho": row[3] or "",
            "tecnico": row[4] or "",
            "status": status,
            "reparos": reparos_info.get("nomes", []),
            "reparo_ids": reparos_info.get("ids", []),
            "reparo": texto_reparos_os(reparos_info, tipo or "—"),
            "vendedor": row[13] or "",
            "cor": row[14] or "" if len(row) > 14 else "",
            "imei": row[15] or "" if len(row) > 15 else "",
            "modelo": row[12] or "" if len(row) > 12 else "",
            "valor_cobrado": round(valor_cobrado or 0, 2),
            "valor_descontado": round(valor_descontado or 0, 2),
            "custo_pecas": round(custo or 0, 2),
            "faturamento": round(calcular_faturamento_os(valor_cobrado, valor_descontado), 2),
            "lucro": round(calcular_lucro_os(tipo, valor_cobrado, valor_descontado, custo), 2),
            "data": row[10] or "",
            "observacoes": row[11] or "" if len(row) > 11 else "",
            "origem_integracao": row[16] or "" if len(row) > 16 else "",
        }

    @api.route("/ordens")
    def listar_ordens():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        q = (request.args.get("q") or "").strip().lower()
        filtro_status = (request.args.get("status") or "").strip()
        filtro_tipo = (request.args.get("tipo") or "").strip()
        filtro_tecnico = (request.args.get("tecnico") or "").strip()
        filtro_vendedor = (request.args.get("vendedor") or "").strip()
        filtro_modelo = (request.args.get("modelo") or "").strip()
        data_ini = (request.args.get("data_ini") or "").strip()
        data_fim = (request.args.get("data_fim") or "").strip()

        conn = conectar()
        cursor = conn.cursor()
        dados, reparos_por_os, custos = carregar_os_com_relacoes(cursor, order_by="os.id DESC")
        conn.close()

        result = []
        for row in dados:
            os_id = row[0]
            status = normalizar_status_os(row[6])
            tipo = row[1] or ""
            tecnico = row[4] or ""
            vendedor = row[13] or ""
            modelo = row[12] or ""
            data = row[10] or ""
            reparos_info = reparos_por_os.get(os_id, {"ids": [], "nomes": []})
            reparo_nome = texto_reparos_os(reparos_info, tipo)

            if q:
                haystack = f"{os_id} {row[2]} {row[3]} {tecnico} {status} {reparo_nome} {modelo} {vendedor} {row[14] or ''} {row[15] or ''} {row[16] or ''}".lower()
                if q not in haystack:
                    continue
            if filtro_status and status != filtro_status:
                continue
            if filtro_tipo and tipo != filtro_tipo:
                continue
            if filtro_tecnico and tecnico != filtro_tecnico:
                continue
            if filtro_vendedor and vendedor != filtro_vendedor:
                continue
            if filtro_modelo and modelo != filtro_modelo:
                continue
            if data_ini and (not data or data < data_ini):
                continue
            if data_fim and (not data or data > data_fim):
                continue

            result.append(_os_row_to_dict(row, reparos_por_os, custos))

        return ok(
            ordens=result,
            total=len(result),
            abertas=len([o for o in result if status_aberto(o["status"])]),
            finalizadas=len([o for o in result if o["status"] == STATUS_FINALIZADO]),
        )

    @api.route("/ordens/<int:os_id>")
    def obter_ordem(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id, tipo, cliente, aparelho, tecnico, reparo_id, status,
                COALESCE(valor_cobrado, 0), COALESCE(valor_descontado, 0),
                COALESCE(custo_pecas, 0), COALESCE(data, ''),
                COALESCE(observacoes, ''), COALESCE(modelo, ''),
                COALESCE(vendedor, ''), COALESCE(cor, ''),
                COALESCE(imei, ''), COALESCE(origem_integracao, ''),
                COALESCE(data_finalizado, '')
            FROM os
            WHERE id=?
            """,
            (os_id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return err("OS não encontrada.", 404)

        reparos_por_os = obter_reparos_por_os(cursor)
        cursor.execute(
            """
            SELECT estoque_id, COALESCE(peca_descricao,''), COALESCE(valor,0),
                   COALESCE(peca_fornecedor,''), COALESCE(quantidade,1), COALESCE(peca_modelo,'')
            FROM os_pecas WHERE os_id=? ORDER BY id
            """,
            (os_id,),
        )
        pecas_usadas = [
            {"estoque_id": p[0], "descricao": p[1], "valor": p[2], "fornecedor": p[3], "quantidade": p[4], "modelo": p[5]}
            for p in cursor.fetchall()
        ]
        conn.close()

        reparos_info = reparos_por_os.get(os_id, {"ids": [], "nomes": []})
        status = normalizar_status_os(row[6])
        tipo = row[1] or ""
        custo = row[9] or 0
        return ok(ordem={
            "id": row[0], "tipo": tipo, "cliente": row[2] or "",
            "aparelho": row[3] or "", "tecnico": row[4] or "",
            "status": status,
            "reparos": reparos_info.get("nomes", []),
            "reparo_ids": reparos_info.get("ids", []),
            "vendedor": row[13] or "", "cor": row[14] or "", "imei": row[15] or "",
            "modelo": row[12] or "",
            "valor_cobrado": row[7] or 0, "valor_descontado": row[8] or 0,
            "custo_pecas": custo,
            "faturamento": round(calcular_faturamento_os(row[7], row[8]), 2),
            "lucro": round(calcular_lucro_os(tipo, row[7], row[8], custo), 2),
            "data": row[10] or "", "observacoes": row[11] or "",
            "origem_integracao": row[16] or "", "data_finalizado": row[17] or "",
            "pecas_usadas": pecas_usadas,
        })

    @api.route("/ordens", methods=["POST"])
    def criar_ordem():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}

        tipo = (body.get("tipo") or "").strip()
        cliente = (body.get("cliente") or "").strip()
        modelo_raw = body.get("modelo") or ""
        modelo = modelo_para_os(modelo_raw)
        cor = (body.get("cor") or "").strip()
        imei = normalizar_imei(body.get("imei"))
        aparelho = modelo
        tecnico = (body.get("tecnico") or "").strip()
        vendedor = (body.get("vendedor") or "").strip()
        observacoes = (body.get("observacoes") or "").strip()
        reparo_ids = [int(x) for x in (body.get("reparo_ids") or []) if str(x).isdigit()]
        pecas_ids = [int(x) for x in (body.get("pecas_ids") or []) if str(x).isdigit()]
        valor_cobrado = float(body.get("valor_cobrado") or 0)
        valor_descontado = float(body.get("valor_descontado") or 0)
        data = (body.get("data_os") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        status_raw = (body.get("status") or "Em andamento").strip()

        # Upgrade → internal
        if tipo.lower() == "upgrade":
            tipo = "Assistencia"
            cliente = "IR Phones"
        if body.get("interna_ir_phones"):
            tipo = "Assistencia"
            cliente = "IR Phones"
            vendedor = ""

        status = normalizar_status_os(status_raw)

        if not tipo or not cliente or not modelo or not tecnico:
            return err("Preencha tipo, cliente, modelo e técnico.")
        if not reparo_ids:
            return err("Selecione ao menos um reparo.")
        if not vendedor_valido(vendedor, vendedores) and cliente != "IR Phones":
            return err("Vendedor inválido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            if not validar_reparo_ids(cursor, reparo_ids):
                return err("Um ou mais reparos não existem.")

            cursor.execute(
                """
                INSERT INTO os (tipo, cliente, aparelho, tecnico, reparo_id, status,
                    valor_cobrado, valor_descontado, custo_pecas, data, observacoes, modelo, vendedor, cor, imei)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (tipo, cliente, aparelho, tecnico, reparo_ids[0], status,
                 valor_cobrado, valor_descontado, 0, data, observacoes, modelo, vendedor, cor, imei),
            )
            novo_id = cursor.lastrowid
            salvar_reparos_os(cursor, novo_id, reparo_ids)

            custo_total = 0.0
            for peca_id in pecas_ids:
                cursor.execute("SELECT valor, modelo FROM estoque WHERE id=?", (peca_id,))
                row = cursor.fetchone()
                valor_peca = float(row[0]) if row and row[0] is not None else 0.0
                modelo_peca = row[1] if row else ""
                if not modelo_compativel(modelo_peca, modelo):
                    conn.rollback()
                    return err("Peça incompatível com o modelo da OS.")
                ok_peca, erro_peca = consumir_peca_da_os(cursor, novo_id, peca_id)
                if not ok_peca:
                    conn.rollback()
                    return err(erro_peca)
                custo_total += valor_peca

            cursor.execute("UPDATE os SET custo_pecas=? WHERE id=?", (round(custo_total, 2), novo_id))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(os_id=novo_id), 201

    @api.route("/ordens/<int:os_id>", methods=["PUT"])
    def atualizar_ordem(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}

        tipo = (body.get("tipo") or "").strip()
        cliente = (body.get("cliente") or "").strip()
        modelo_raw = body.get("modelo") or ""
        modelo = modelo_para_os(modelo_raw)
        cor = (body.get("cor") or "").strip()
        imei = normalizar_imei(body.get("imei"))
        tecnico = (body.get("tecnico") or "").strip()
        vendedor = (body.get("vendedor") or "").strip()
        observacoes = (body.get("observacoes") or "").strip()
        reparo_ids = [int(x) for x in (body.get("reparo_ids") or []) if str(x).isdigit()]
        pecas_ids = [int(x) for x in (body.get("pecas_ids") or []) if str(x).isdigit()]
        valor_cobrado = float(body.get("valor_cobrado") or 0)
        valor_descontado = float(body.get("valor_descontado") or 0)
        data_os = (body.get("data_os") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        status = normalizar_status_os(body.get("status") or "")
        aparelho = modelo

        if not tipo or not cliente or not modelo or not tecnico or not status:
            return err("Preencha todos os campos obrigatórios.")
        if not reparo_ids:
            return err("Selecione ao menos um reparo.")
        if not vendedor_valido(vendedor, vendedores) and cliente != "IR Phones":
            return err("Vendedor inválido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            if not validar_reparo_ids(cursor, reparo_ids):
                return err("Um ou mais reparos não existem.")

            cursor.execute("SELECT status, COALESCE(data_finalizado,'') FROM os WHERE id=?", (os_id,))
            row_atual = cursor.fetchone()
            if not row_atual:
                return err("OS não encontrada.", 404)

            status_atual = normalizar_status_os(row_atual[0])
            data_finalizado_atual = row_atual[1]

            data_finalizado_valor = None
            if status == STATUS_FINALIZADO:
                data_finalizado_valor = data_finalizado_atual or datetime.now().strftime("%Y-%m-%d")

            cursor.execute(
                """
                UPDATE os SET tipo=?,cliente=?,aparelho=?,tecnico=?,reparo_id=?,status=?,
                    valor_cobrado=?,valor_descontado=?,data=?,observacoes=?,modelo=?,vendedor=?,
                    cor=?,imei=?,data_finalizado=?
                WHERE id=?
                """,
                (tipo, cliente, aparelho, tecnico, reparo_ids[0], status,
                 valor_cobrado, valor_descontado, data_os, observacoes, modelo, vendedor,
                 cor, imei, data_finalizado_valor, os_id),
            )
            salvar_reparos_os(cursor, os_id, reparo_ids)

            if status_atual != STATUS_CANCELADO:
                devolver_pecas_da_os(cursor, os_id, "devolucao-edicao")
            cursor.execute("DELETE FROM os_pecas WHERE os_id=?", (os_id,))

            custo_total = 0.0
            for peca_id in pecas_ids:
                cursor.execute("SELECT valor, modelo FROM estoque WHERE id=?", (peca_id,))
                row = cursor.fetchone()
                valor_peca = float(row[0]) if row and row[0] is not None else 0.0
                modelo_peca = row[1] if row else ""
                if not modelo_compativel(modelo_peca, modelo):
                    conn.rollback()
                    return err("Peça incompatível com o modelo da OS.")
                if status == STATUS_CANCELADO:
                    ok_peca, erro_peca = adicionar_peca_os_sem_consumir(cursor, os_id, peca_id)
                else:
                    ok_peca, erro_peca = consumir_peca_da_os(cursor, os_id, peca_id)
                if not ok_peca:
                    conn.rollback()
                    return err(erro_peca)
                custo_total += valor_peca

            cursor.execute("UPDATE os SET custo_pecas=? WHERE id=?", (round(custo_total, 2), os_id))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/ordens/<int:os_id>", methods=["DELETE"])
    def deletar_ordem(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT status FROM os WHERE id=?", (os_id,))
            row = cursor.fetchone()
            if row:
                s = normalizar_status_os(row[0])
                if s not in {STATUS_FINALIZADO, STATUS_CANCELADO}:
                    devolver_pecas_da_os(cursor, os_id, "devolucao")
            cursor.execute("DELETE FROM os_pecas WHERE os_id=?", (os_id,))
            cursor.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
            cursor.execute("DELETE FROM os WHERE id=?", (os_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/ordens/<int:os_id>/status", methods=["PATCH"])
    def atualizar_status_os(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}
        status = normalizar_status_os(body.get("status") or "")
        if not status:
            return err("Status inválido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT status, COALESCE(data_finalizado,'') FROM os WHERE id=?", (os_id,))
            row = cursor.fetchone()
            if not row:
                return err("OS não encontrada.", 404)
            status_atual = normalizar_status_os(row[0])
            data_finalizado_atual = row[1]

            data_finalizado_valor = None
            if status == STATUS_FINALIZADO:
                data_finalizado_valor = data_finalizado_atual or datetime.now().strftime("%Y-%m-%d")

            cursor.execute(
                "UPDATE os SET status=?, data_finalizado=? WHERE id=?",
                (status, data_finalizado_valor, os_id),
            )

            if status == STATUS_CANCELADO and status_atual != STATUS_CANCELADO:
                devolver_pecas_da_os(cursor, os_id, "devolucao")

            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/ordens/historico-cliente")
    def historico_cliente():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        cliente = (request.args.get("cliente") or "").strip()
        excluir_id = request.args.get("excluir_id", type=int)
        if not cliente:
            return ok(ordens=[])

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, tipo, modelo, data, status
            FROM os
            WHERE lower(cliente) = lower(?) AND id != ?
            ORDER BY id DESC LIMIT 10
            """,
            (cliente, excluir_id or -1),
        )
        rows = cursor.fetchall()
        reparos_por_os = obter_reparos_por_os(cursor)
        conn.close()

        ordens = []
        for r in rows:
            rinfo = reparos_por_os.get(r[0], {"nomes": []})
            ordens.append({
                "id": r[0], "tipo": r[1] or "", "modelo": r[2] or "",
                "data": r[3] or "", "status": normalizar_status_os(r[4]),
                "reparos": rinfo.get("nomes", []),
            })
        return ok(ordens=ordens)

    # ── STOCK ──────────────────────────────────────────────────────────────

    @api.route("/estoque")
    def listar_estoque():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        filtro_modelo = (request.args.get("modelo") or "").strip()
        q = (request.args.get("q") or "").strip().lower()

        conn = conectar()
        cursor = conn.cursor()

        params = []
        where = []
        if filtro_modelo == "Universal":
            where.append("COALESCE(modelo,'') = ''")
        elif filtro_modelo:
            where.append("COALESCE(modelo,'') = ?")
            params.append(normalizar_modelo_iphone(filtro_modelo) or filtro_modelo)

        clause = f"WHERE {' AND '.join(where)}" if where else ""
        cursor.execute(
            f"SELECT id, descricao, valor, fornecedor, quantidade, data_compra, COALESCE(modelo,'') FROM estoque {clause} ORDER BY id DESC",
            params,
        )
        itens = [
            {"id": r[0], "descricao": r[1] or "", "valor": round(r[2] or 0, 2),
             "fornecedor": r[3] or "", "quantidade": r[4] or 0,
             "data_compra": r[5] or "", "modelo": r[6] or ""}
            for r in cursor.fetchall()
        ]

        if q:
            itens = [i for i in itens if q in f"{i['descricao']} {i['modelo']} {i['fornecedor']}".lower()]

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

    @api.route("/estoque", methods=["POST"])
    def criar_estoque():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}
        descricao = (body.get("descricao") or "").strip()
        modelo = normalizar_modelo_iphone(body.get("modelo") or "") or (body.get("modelo") or "").strip()
        valor = float(body.get("valor") or 0)
        fornecedor = (body.get("fornecedor") or "Nao informado").strip()
        quantidade = int(body.get("quantidade") or 0)
        data_compra = (body.get("data_compra") or "").strip() or datetime.now().strftime("%Y-%m-%d")

        if not descricao or valor <= 0 or quantidade < 0:
            return err("Preencha descrição, valor e quantidade.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO estoque (descricao, modelo, valor, fornecedor, quantidade, data_compra) VALUES (?,?,?,?,?,?)",
                (descricao, modelo, valor, fornecedor, quantidade, data_compra),
            )
            novo_id = cursor.lastrowid
            registrar_movimentacao(cursor, novo_id, "entrada", quantidade)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api.route("/estoque/<int:item_id>", methods=["PUT"])
    def atualizar_estoque(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = request.get_json(silent=True) or {}
        descricao = (body.get("descricao") or "").strip()
        modelo = normalizar_modelo_iphone(body.get("modelo") or "") or (body.get("modelo") or "").strip()
        valor = float(body.get("valor") or 0)
        fornecedor = (body.get("fornecedor") or "Nao informado").strip()
        quantidade_nova = int(body.get("quantidade") or 0)
        data_compra = (body.get("data_compra") or "").strip() or datetime.now().strftime("%Y-%m-%d")

        if not descricao or valor <= 0:
            return err("Preencha descrição e valor.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT quantidade, descricao FROM estoque WHERE id=?", (item_id,))
            row = cursor.fetchone()
            if not row:
                return err("Item não encontrado.", 404)
            qtd_antiga = row[0] or 0
            cursor.execute(
                "UPDATE estoque SET descricao=?,modelo=?,valor=?,fornecedor=?,quantidade=?,data_compra=? WHERE id=?",
                (descricao, modelo, valor, fornecedor, quantidade_nova, data_compra, item_id),
            )
            diff = quantidade_nova - qtd_antiga
            if diff != 0:
                tipo_mov = "entrada" if diff > 0 else "saida"
                registrar_movimentacao(cursor, item_id, tipo_mov, abs(diff))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/estoque/<int:item_id>", methods=["DELETE"])
    def deletar_estoque(item_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

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
            cursor.execute("DELETE FROM estoque WHERE id=?", (item_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/estoque/movimentacoes")
    def movimentacoes():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT m.id, m.estoque_id, m.tipo, m.quantidade, m.data,
                   COALESCE(e.descricao, m.descricao_peca, '')
            FROM movimentacoes m
            LEFT JOIN estoque e ON e.id = m.estoque_id
            ORDER BY m.id DESC LIMIT 30
            """
        )
        rows = cursor.fetchall()
        conn.close()
        return ok(movimentacoes=[
            {"id": r[0], "estoque_id": r[1], "tipo": r[2], "quantidade": r[3], "data": r[4], "descricao": r[5]}
            for r in rows
        ])

    # ── REPAIR TYPES ───────────────────────────────────────────────────────

    @api.route("/reparos")
    def listar_reparos():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM reparos ORDER BY nome")
        rows = cursor.fetchall()
        conn.close()
        return ok(reparos=[{"id": r[0], "nome": r[1]} for r in rows])

    @api.route("/reparos", methods=["POST"])
    def criar_reparo():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        nome = (body.get("nome") or "").strip()
        if not nome:
            return err("Informe o nome do reparo.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM reparos WHERE lower(nome)=lower(?)", (nome,))
            if cursor.fetchone():
                return err("Esse tipo de reparo já existe.")
            cursor.execute("INSERT INTO reparos (nome) VALUES (?)", (nome,))
            novo_id = cursor.lastrowid
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api.route("/reparos/<int:reparo_id>", methods=["PUT"])
    def atualizar_reparo(reparo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        nome = (body.get("nome") or "").strip()
        if not nome:
            return err("Informe um nome válido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM reparos WHERE lower(nome)=lower(?) AND id<>?", (nome, reparo_id))
            if cursor.fetchone():
                return err("Já existe um reparo com esse nome.")
            cursor.execute("UPDATE reparos SET nome=? WHERE id=?", (nome, reparo_id))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/reparos/<int:reparo_id>", methods=["DELETE"])
    def deletar_reparo(reparo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM os_reparos WHERE reparo_id=?", (reparo_id,))
            if (cursor.fetchone()[0] or 0) > 0:
                return err("Não é possível excluir: reparo vinculado a OS.")
            cursor.execute("DELETE FROM reparos WHERE id=?", (reparo_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    # ── OPERATIONAL COSTS ──────────────────────────────────────────────────

    @api.route("/custos")
    def listar_custos():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        resumo = listar_custos_operacionais(start_date, end_date)
        return ok(**resumo)

    @api.route("/custos", methods=["POST"])
    def criar_custo():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        descricao = (body.get("descricao") or "").strip()
        categoria = (body.get("categoria") or "Outros").strip()
        valor = float(body.get("valor") or 0)
        data = (body.get("data") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        observacoes = (body.get("observacoes") or "").strip()

        if not descricao or valor <= 0:
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

    @api.route("/custos/<int:custo_id>", methods=["PUT"])
    def atualizar_custo(custo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        descricao = (body.get("descricao") or "").strip()
        categoria = (body.get("categoria") or "Outros").strip()
        valor = float(body.get("valor") or 0)
        data = (body.get("data") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        observacoes = (body.get("observacoes") or "").strip()

        if not descricao or valor <= 0:
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

    @api.route("/custos/<int:custo_id>", methods=["DELETE"])
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

    # ── PRICE TABLES ───────────────────────────────────────────────────────

    @api.route("/precos")
    def listar_precos():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        return ok(tabelas=carregar_tabelas_preco())

    @api.route("/precos", methods=["POST"])
    def salvar_preco():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        tabela = (body.get("tabela") or "").strip()
        servico = (body.get("servico") or "").strip().upper()
        modelo = (body.get("modelo") or "").strip()
        valor = float(body.get("valor") or -1)

        if tabela not in ("ir_phones", "clientes"):
            return err("Tabela inválida.")
        if not servico or not modelo or valor < 0:
            return err("Preencha serviço, modelo e valor.")

        tabelas = carregar_tabelas_preco()
        tabelas.setdefault(tabela, {}).setdefault(servico, {})[modelo] = valor
        salvar_tabelas_preco(tabelas)
        return ok()

    @api.route("/precos/excluir", methods=["POST"])
    def excluir_preco():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        tabela = (body.get("tabela") or "").strip()
        servico = (body.get("servico") or "").strip()
        modelo = (body.get("modelo") or "").strip()

        if tabela not in ("ir_phones", "clientes"):
            return err("Tabela inválida.")

        tabelas = carregar_tabelas_preco()
        if tabela in tabelas and servico in tabelas[tabela] and modelo in tabelas[tabela][servico]:
            del tabelas[tabela][servico][modelo]
            if not tabelas[tabela][servico]:
                del tabelas[tabela][servico]
            salvar_tabelas_preco(tabelas)
            return ok()

        return err("Entrada não encontrada.", 404)

    # ── WARRANTIES ─────────────────────────────────────────────────────────

    @api.route("/garantias")
    def listar_garantias():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        q = (request.args.get("q") or "").strip().lower()
        hoje = datetime.now().date()
        garantia_dias = 90

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, cliente, modelo, tecnico,
                   COALESCE(data_finalizado,''), COALESCE(data,''), COALESCE(imei,'')
            FROM os
            WHERE status='Finalizado'
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()
        reparos_por_os = obter_reparos_por_os(cursor)
        conn.close()

        result = []
        for r in rows:
            os_id, cliente, modelo, tecnico, data_fin, data_os, imei = r
            if (cliente or "").strip().lower() == "ir phones":
                continue
            if q and q not in f"{cliente} {modelo} {imei}".lower():
                continue

            base = parse_data_ymd(data_fin) or parse_data_ymd(data_os)
            dias_restantes = None
            label = "Sem data"
            color = "gray"
            if base:
                fim = (base + timedelta(days=garantia_dias)).date()
                dias_restantes = (fim - hoje).days
                if dias_restantes < 0:
                    label = "Vencida"
                    color = "red"
                elif dias_restantes <= 7:
                    label = f"Vence em {dias_restantes}d"
                    color = "amber"
                else:
                    label = f"{dias_restantes} dias"
                    color = "green"

            rinfo = reparos_por_os.get(os_id, {"nomes": []})
            result.append({
                "id": os_id, "cliente": cliente or "", "modelo": modelo or "",
                "tecnico": tecnico or "", "imei": imei or "",
                "data_finalizado": data_fin or data_os,
                "reparos": rinfo.get("nomes", []),
                "garantia": {"dias_restantes": dias_restantes, "label": label, "color": color},
            })

        total = len(result)
        ativas = len([r for r in result if r["garantia"]["color"] == "green"])
        vencendo = len([r for r in result if r["garantia"]["color"] == "amber"])
        vencidas = len([r for r in result if r["garantia"]["color"] == "red"])

        return ok(
            ordens=result, total=total,
            ativas=ativas, vencendo=vencendo, vencidas=vencidas,
        )

    # ── REPORTS ────────────────────────────────────────────────────────────

    @api.route("/relatorios/ir-phones")
    def relatorio_ir_phones():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        resumo = agrupar_relatorio_ir_phones(start_date, end_date)
        total_os = sum(v["total_os"] for v in resumo.values())
        total_lucro = sum(v["lucro"] for v in resumo.values())
        return ok(meses=resumo, total_os=total_os, total_lucro=round(total_lucro, 2))

    @api.route("/relatorios/tecnicos")
    def relatorio_tecnicos():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        resumo = agrupar_relatorio_tecnicos(start_date, end_date)
        return ok(meses=resumo)

    @api.route("/relatorios/pdf/ir-phones")
    def pdf_ir_phones():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        data_inicio = (request.args.get("start_date") or "").strip()
        data_fim = (request.args.get("end_date") or "").strip()
        linhas = montar_linhas_relatorio_ir_phones(data_inicio, data_fim)
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)
        return montar_pdf_texto(
            "Relatorio Mensal - IR Phones",
            f"Servicos finalizados, gastos com pecas e lucro. Periodo: {periodo}",
            linhas,
            "relatorio-ir-phones.pdf",
        )

    @api.route("/relatorios/pdf/tecnicos")
    def pdf_tecnicos():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        data_inicio = (request.args.get("start_date") or "").strip()
        data_fim = (request.args.get("end_date") or "").strip()
        linhas = montar_linhas_relatorio_tecnicos(data_inicio, data_fim)
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)
        return montar_pdf_texto(
            "Relatorio Mensal - Tecnicos",
            f"Servicos finalizados por tecnico com gastos e lucro. Periodo: {periodo}",
            linhas,
            "relatorio-tecnicos.pdf",
        )

    # ── USERS ──────────────────────────────────────────────────────────────

    @api.route("/usuarios")
    def listar_usuarios():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, usuario, perfil, ativo FROM usuarios ORDER BY nome")
        rows = cursor.fetchall()
        conn.close()
        return ok(usuarios=[
            {"id": r[0], "nome": r[1], "usuario": r[2], "perfil": r[3], "ativo": bool(r[4])}
            for r in rows
        ])

    @api.route("/usuarios", methods=["POST"])
    def criar_usuario():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        nome = (body.get("nome") or "").strip()
        usuario_txt = (body.get("usuario") or "").strip()
        senha_txt = (body.get("senha") or "").strip()
        perfil = body.get("perfil") or "tecnico"

        if not nome or not usuario_txt or not senha_txt:
            return err("Preencha nome, usuário e senha.")
        if perfil not in ("admin", "tecnico", "vendedor"):
            perfil = "tecnico"

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (nome, usuario, senha_hash, perfil) VALUES (?,?,?,?)",
                (nome, usuario_txt, generate_password_hash(senha_txt), perfil),
            )
            novo_id = cursor.lastrowid
            conn.commit()
        except Exception:
            conn.rollback()
            return err("Usuário já existe.")
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api.route("/usuarios/<int:uid>", methods=["PUT"])
    def atualizar_usuario(uid):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = request.get_json(silent=True) or {}
        nome = (body.get("nome") or "").strip()
        perfil = body.get("perfil") or "tecnico"
        senha_nova = (body.get("senha_nova") or "").strip()
        ativo = bool(body.get("ativo", True))

        if perfil not in ("admin", "tecnico", "vendedor"):
            perfil = "tecnico"
        if uid == session.get("usuario_id") and not ativo:
            return err("Você não pode desativar sua própria conta.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            if senha_nova:
                cursor.execute(
                    "UPDATE usuarios SET nome=?,perfil=?,senha_hash=?,ativo=? WHERE id=?",
                    (nome, perfil, generate_password_hash(senha_nova), 1 if ativo else 0, uid),
                )
            else:
                cursor.execute(
                    "UPDATE usuarios SET nome=?,perfil=?,ativo=? WHERE id=?",
                    (nome, perfil, 1 if ativo else 0, uid),
                )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api.route("/usuarios/<int:uid>", methods=["DELETE"])
    def deletar_usuario(uid):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        if uid == session.get("usuario_id"):
            return err("Você não pode excluir sua própria conta.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE id=?", (uid,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    # ── BACKUP ─────────────────────────────────────────────────────────────

    @api.route("/backup/criar", methods=["POST"])
    def criar_backup_api():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        try:
            os.makedirs(backup_dir, exist_ok=True)
            info = criar_backup(
                backup_dir, google_drive_backup_dir,
                conectar,
            )
            if backup_email_senha_app:
                enviar_backup_email(
                    info["destino_local"], backup_email_remetente,
                    backup_email_senha_app, backup_email_destino,
                )
            return ok(
                arquivo=info["nome"],
                destino_drive=bool(info.get("destino_drive")),
                erro_drive=info.get("erro_drive", ""),
            )
        except Exception as exc:
            return err(str(exc))

    @api.route("/backup/listar")
    def listar_backups():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        backups = []
        if os.path.isdir(backup_dir):
            for f in os.listdir(backup_dir):
                if f.endswith(".db"):
                    full = os.path.join(backup_dir, f)
                    backups.append({
                        "nome": f,
                        "tamanho": os.path.getsize(full),
                        "data": datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M"),
                        "modificado_em": os.path.getmtime(full),
                    })

        backups.sort(key=lambda item: item["modificado_em"], reverse=True)
        for item in backups:
            item.pop("modificado_em", None)

        return ok(backups=backups[:30])

    @api.route("/backup/download/<path:filename>")
    def download_backup(filename):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        return send_from_directory(backup_dir, filename, as_attachment=True)

    # ── MERCADOPHONE SYNC ──────────────────────────────────────────────────

    @api.route("/integracoes/mercadophone/sincronizar", methods=["POST"])
    def sincronizar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        try:
            resultado = sincronizar_mercado_phone(
                conectar, mercado_phone_runtime_config, mercado_phone_helpers
            )
            return ok(resultado=resultado)
        except Exception as exc:
            return err(str(exc))

    return api
