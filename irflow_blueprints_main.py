import os
import sqlite3
from datetime import datetime, timedelta

from flask import Blueprint, flash, redirect, render_template, request, send_from_directory, url_for


def create_main_blueprint(deps):
    bp = Blueprint("main_views", __name__)

    conectar = deps["conectar"]
    carregar_os_com_relacoes = deps["carregar_os_com_relacoes"]
    texto_reparos_os = deps["texto_reparos_os"]
    normalizar_status_os = deps["normalizar_status_os"]
    status_cancelado = deps["status_cancelado"]
    status_finalizado = deps["status_finalizado"]
    status_aberto = deps["status_aberto"]
    coletar_status_opcoes = deps["coletar_status_opcoes"]
    calcular_faturamento_os = deps["calcular_faturamento_os"]
    calcular_lucro_os = deps["calcular_lucro_os"]
    listar_custos_operacionais = deps["listar_custos_operacionais"]
    categorias_custos_operacionais = deps["categorias_custos_operacionais"]
    agrupar_relatorio_ir_phones = deps["agrupar_relatorio_ir_phones"]
    agrupar_relatorio_tecnicos = deps["agrupar_relatorio_tecnicos"]
    formatar_periodo_relatorio = deps["formatar_periodo_relatorio"]
    montar_linhas_relatorio_ir_phones = deps["montar_linhas_relatorio_ir_phones"]
    montar_linhas_relatorio_tecnicos = deps["montar_linhas_relatorio_tecnicos"]
    montar_pdf_texto = deps["montar_pdf_texto"]
    obter_reparos_por_os = deps["obter_reparos_por_os"]
    status_em_andamento = deps["status_em_andamento"]
    status_aguardando_peca = deps["status_aguardando_peca_const"]
    status_finalizado_const = deps["status_finalizado_const"]
    status_cancelado_const = deps["status_cancelado_const"]
    parse_data_ymd = deps["parse_data_ymd"]
    backup_dir = deps["backup_dir"]
    google_drive_backup_dir = deps["google_drive_backup_dir"]
    garantir_pasta_backup_google_drive = deps["garantir_pasta_backup_google_drive"]
    criar_backup = deps["criar_backup"]

    @bp.route("/")
    @bp.route("/dashboard")
    @bp.route("/dashboard/")
    @bp.route("/dashboard.html")
    @bp.route("/index")
    @bp.route("/index.html")
    def index():
        conn = conectar()
        cursor = conn.cursor()

        start_date = request.args.get("start_date", "")
        end_date = request.args.get("end_date", "")
        filtro_tecnico = request.args.get("tecnico", "")
        filtro_status = request.args.get("status", "")
        filtro_vendedor = request.args.get("vendedor", "")
        dashboard_tab = request.args.get("tab", "visao-geral")

        dados, reparos_por_os, custos = carregar_os_com_relacoes(cursor, order_by="os.id DESC")

        tecnicos = sorted({item[4] for item in dados if item[4]})
        status_opcoes = coletar_status_opcoes(dados, 6)
        vendedores_opcoes = sorted({item[13] for item in dados if item[13]})

        lucro_total = 0
        gasto_total = 0
        custo_consumido_periodo = 0
        faturamento_total = 0
        ordens_finalizadas = 0
        ordens_abertas = 0
        lucro_por_tecnico = {}
        resumo_por_vendedor = {}
        servicos_mais_feitos = {}
        faturamento_por_dia = {}
        dados_filtrados = []

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

            if filtro_tecnico and tecnico != filtro_tecnico:
                continue
            if filtro_status and status != filtro_status:
                continue
            if filtro_vendedor and vendedor != filtro_vendedor:
                continue
            if (start_date or end_date) and not data:
                continue
            if start_date and data and data < start_date:
                continue
            if end_date and data and data > end_date:
                continue

            dados_filtrados.append(os_item)
            if not status_cancelado(status):
                custo_consumido_periodo += custo
            faturamento_os = calcular_faturamento_os(valor_cobrado, valor_descontado)
            if status_finalizado(status):
                lucro_total += lucro
                faturamento_total += faturamento_os
                ordens_finalizadas += 1
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

            if status_finalizado(status) and data:
                faturamento_por_dia[data] = faturamento_por_dia.get(data, 0) + faturamento_os

        cursor.execute(
            """
            SELECT estoque.descricao, SUM(os_pecas.quantidade)
            FROM os_pecas
            JOIN estoque ON os_pecas.estoque_id = estoque.id
            GROUP BY os_pecas.estoque_id
            ORDER BY SUM(os_pecas.quantidade) DESC
            LIMIT 10
            """
        )
        pecas_mais_usadas = cursor.fetchall()

        cursor.execute("SELECT COALESCE(SUM(valor * quantidade), 0) FROM estoque")
        gasto_total = cursor.fetchone()[0] or 0
        conn.close()

        resumo_custos = listar_custos_operacionais(start_date, end_date)
        custos_operacionais = resumo_custos["itens"]
        custos_operacionais_periodo = resumo_custos["total_periodo"]
        custos_por_categoria_ordenado = resumo_custos["por_categoria"]

        lucro_por_tecnico_labels = list(lucro_por_tecnico.keys())
        lucro_por_tecnico_values = [round(v, 2) for v in lucro_por_tecnico.values()]
        servicos_labels = [s[0] for s in sorted(servicos_mais_feitos.items(), key=lambda x: x[1], reverse=True)]
        servicos_values = [s[1] for s in sorted(servicos_mais_feitos.items(), key=lambda x: x[1], reverse=True)]
        pecas_labels = [p[0] for p in pecas_mais_usadas]
        pecas_values = [p[1] for p in pecas_mais_usadas]
        dias_ordenados = sorted(faturamento_por_dia.keys())
        faturamento_labels = dias_ordenados
        faturamento_values = [round(faturamento_por_dia[d], 2) for d in dias_ordenados]

        resumo_por_vendedor_ordenado = sorted(
            resumo_por_vendedor.items(),
            key=lambda item: item[1]["faturamento"],
            reverse=True,
        )
        vendedor_labels = [item[0] for item in resumo_por_vendedor_ordenado]
        vendedor_faturamento_values = [round(item[1]["faturamento"], 2) for item in resumo_por_vendedor_ordenado]
        categorias_custos_labels = [item[0] for item in custos_por_categoria_ordenado]
        categorias_custos_values = [round(item[1], 2) for item in custos_por_categoria_ordenado]
        ticket_medio = round(faturamento_total / ordens_finalizadas, 2) if ordens_finalizadas else 0
        resultado_liquido = lucro_total - custos_operacionais_periodo

        return render_template(
            "index.html",
            lucro=lucro_total,
            gastos=gasto_total,
            custo_consumido_periodo=custo_consumido_periodo,
            faturamento_total=faturamento_total,
            ordens_finalizadas=ordens_finalizadas,
            ordens_abertas=ordens_abertas,
            ticket_medio=ticket_medio,
            custos_operacionais_periodo=custos_operacionais_periodo,
            resultado_liquido=resultado_liquido,
            dados=dados_filtrados,
            lucro_por_tecnico=lucro_por_tecnico,
            servicos_mais_feitos=sorted(servicos_mais_feitos.items(), key=lambda x: x[1], reverse=True),
            pecas_mais_usadas=pecas_mais_usadas,
            faturamento_por_dia=faturamento_por_dia,
            lucro_por_tecnico_labels=lucro_por_tecnico_labels,
            lucro_por_tecnico_values=lucro_por_tecnico_values,
            servicos_labels=servicos_labels,
            servicos_values=servicos_values,
            pecas_labels=pecas_labels,
            pecas_values=pecas_values,
            faturamento_labels=faturamento_labels,
            faturamento_values=faturamento_values,
            resumo_por_vendedor=resumo_por_vendedor_ordenado,
            vendedor_labels=vendedor_labels,
            vendedor_faturamento_values=vendedor_faturamento_values,
            custos_operacionais_total=len(custos_operacionais),
            custos_operacionais=custos_operacionais[:12],
            custos_por_categoria=custos_por_categoria_ordenado,
            categorias_custos_labels=categorias_custos_labels,
            categorias_custos_values=categorias_custos_values,
            categorias_custos_opcoes=categorias_custos_operacionais,
            tecnicos=tecnicos,
            status_opcoes=status_opcoes,
            vendedores_opcoes=vendedores_opcoes,
            start_date=start_date,
            end_date=end_date,
            filtro_tecnico=filtro_tecnico,
            filtro_status=filtro_status,
            filtro_vendedor=filtro_vendedor,
            dashboard_tab=dashboard_tab,
            today_str=datetime.now().strftime("%Y-%m-%d"),
        )

    @bp.route("/relatorios/pdf/ir-phones")
    def relatorio_pdf_ir_phones():
        data_inicio = (request.args.get("start_date") or request.args.get("data_ini") or "").strip()
        data_fim = (request.args.get("end_date") or request.args.get("data_fim") or "").strip()
        linhas = montar_linhas_relatorio_ir_phones(data_inicio, data_fim)
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)
        return montar_pdf_texto(
            "Relatorio Mensal - IR Phones",
            f"Servicos finalizados, gastos com pecas e lucro. Periodo: {periodo}",
            linhas,
            "relatorio-ir-phones.pdf",
        )

    @bp.route("/relatorios")
    def relatorios():
        data_inicio = (request.args.get("start_date") or "").strip()
        data_fim = (request.args.get("end_date") or "").strip()
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)

        resumo_ir = agrupar_relatorio_ir_phones(data_inicio, data_fim)
        resumo_tecnicos = agrupar_relatorio_tecnicos(data_inicio, data_fim)

        total_os_ir = sum(item["total_os"] for item in resumo_ir.values())
        total_lucro_ir = sum(item["lucro"] for item in resumo_ir.values())
        total_tecnicos = len({tecnico for tecnicos in resumo_tecnicos.values() for tecnico in tecnicos.keys()})

        return render_template(
            "relatorios.html",
            start_date=data_inicio,
            end_date=data_fim,
            periodo=periodo,
            total_os_ir=total_os_ir,
            total_lucro_ir=total_lucro_ir,
            total_tecnicos=total_tecnicos,
            meses_ir=len(resumo_ir),
            meses_tecnicos=len(resumo_tecnicos),
        )

    @bp.route("/relatorios/pdf/tecnicos")
    def relatorio_pdf_tecnicos():
        data_inicio = (request.args.get("start_date") or request.args.get("data_ini") or "").strip()
        data_fim = (request.args.get("end_date") or request.args.get("data_fim") or "").strip()
        linhas = montar_linhas_relatorio_tecnicos(data_inicio, data_fim)
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)
        return montar_pdf_texto(
            "Relatorio Mensal - Tecnicos",
            f"Servicos finalizados por tecnico com gastos e lucro. Periodo: {periodo}",
            linhas,
            "relatorio-tecnicos.pdf",
        )

    @bp.route("/kanban")
    def kanban():
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                os.id,
                os.tipo,
                os.cliente,
                os.aparelho,
                COALESCE(os.cor, ''),
                os.tecnico,
                os.status
            FROM os
            """
        )
        dados = cursor.fetchall()
        reparos_por_os = obter_reparos_por_os(cursor)
        conn.close()

        em_andamento = []
        aguardando = []
        finalizado = []
        cancelado = []

        for os_item in dados:
            item = {
                "id": os_item[0],
                "cliente": os_item[2],
                "aparelho": os_item[3],
                "cor": os_item[4],
                "tecnico": os_item[5],
                "reparo": texto_reparos_os(reparos_por_os.get(os_item[0]), "—"),
                "status": os_item[6],
            }

            status_normalizado = normalizar_status_os(os_item[6])
            item["status"] = status_normalizado

            if status_normalizado == status_finalizado_const:
                finalizado.append(item)
            elif status_normalizado == status_aguardando_peca:
                aguardando.append(item)
            elif status_normalizado == status_em_andamento:
                em_andamento.append(item)
            elif status_normalizado == status_cancelado_const:
                cancelado.append(item)

        return render_template(
            "kanban.html",
            em_andamento=em_andamento,
            aguardando=aguardando,
            finalizado=finalizado,
            cancelado=cancelado,
        )

    @bp.route("/garantias")
    def garantias():
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                id,
                cliente,
                modelo,
                tecnico,
                COALESCE(data_finalizado, ''),
                COALESCE(data, ''),
                COALESCE(status, '')
            FROM os
            WHERE status='Finalizado'
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        hoje = datetime.now().date()
        itens = []
        ativos = 0
        vencendo = 0
        vencidos = 0

        for os_id, cliente, modelo, tecnico, data_finalizado, data_os, status in rows:
            if (cliente or "").strip().lower() == "ir phones":
                continue

            inicio_dt = parse_data_ymd(data_finalizado) or parse_data_ymd(data_os)
            if not inicio_dt:
                continue

            inicio = inicio_dt.date()
            fim = inicio + timedelta(days=90)
            dias_restantes = (fim - hoje).days

            if dias_restantes < 0:
                status_garantia = "Vencida"
                status_class = "text-red-600 bg-red-50"
                vencidos += 1
            elif dias_restantes <= 7:
                status_garantia = "Vencendo"
                status_class = "text-yellow-700 bg-yellow-50"
                vencendo += 1
                ativos += 1
            else:
                status_garantia = "Ativa"
                status_class = "text-green-700 bg-green-50"
                ativos += 1

            itens.append(
                {
                    "id": os_id,
                    "cliente": cliente or "-",
                    "modelo": modelo or "-",
                    "tecnico": tecnico or "-",
                    "inicio": inicio.strftime("%Y-%m-%d"),
                    "fim": fim.strftime("%Y-%m-%d"),
                    "dias_restantes": dias_restantes,
                    "status": status_garantia,
                    "status_class": status_class,
                }
            )

        return render_template(
            "garantias.html",
            garantias=itens,
            total=len(itens),
            ativos=ativos,
            vencendo=vencendo,
            vencidos=vencidos,
        )

    @bp.route("/backup", methods=["GET", "POST"])
    def backup():
        os.makedirs(backup_dir, exist_ok=True)
        drive_dir = garantir_pasta_backup_google_drive(google_drive_backup_dir)

        if request.method == "POST":
            try:
                info = criar_backup(backup_dir, google_drive_backup_dir, conectar)
            except (OSError, sqlite3.Error) as exc:
                flash(f"Nao foi possivel gerar o backup: {exc}", "error")
                return redirect(url_for("main_views.backup"))
            if info["destino_drive"]:
                flash(f"Backup criado e copiado para o Google Drive: {info['nome']}", "success")
            elif info.get("erro_drive"):
                flash(f"Backup criado localmente, mas o Google Drive recusou a copia: {info['nome']}", "error")
            else:
                flash(f"Backup criado localmente: {info['nome']}", "success")
            return redirect(url_for("main_views.backup"))

        arquivos = []
        for nome in os.listdir(backup_dir):
            if not nome.lower().endswith(".db"):
                continue
            caminho = os.path.join(backup_dir, nome)
            if not os.path.isfile(caminho):
                continue
            stat = os.stat(caminho)
            arquivos.append(
                {
                    "nome": nome,
                    "tamanho_kb": round(stat.st_size / 1024, 1),
                    "modificado_em": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "sincronizado_drive": bool(drive_dir and os.path.exists(os.path.join(drive_dir, nome))),
                }
            )

        arquivos.sort(key=lambda x: x["modificado_em"], reverse=True)
        return render_template(
            "backup.html",
            backups=arquivos,
            google_drive_disponivel=bool(drive_dir),
            google_drive_pasta=drive_dir,
        )

    @bp.route("/backup/download/<path:nome>")
    def backup_download(nome):
        return send_from_directory(backup_dir, nome, as_attachment=True)

    return bp
