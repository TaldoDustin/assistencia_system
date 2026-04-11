import os
import sqlite3
from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, send_from_directory, url_for

from irflow_web import redirecionar_com_query_string


def create_main_blueprint(deps):
    bp = Blueprint("main_views", __name__)
    conectar = deps["conectar"]
    formatar_periodo_relatorio = deps["formatar_periodo_relatorio"]
    montar_linhas_relatorio_ir_phones = deps["montar_linhas_relatorio_ir_phones"]
    montar_linhas_relatorio_tecnicos = deps["montar_linhas_relatorio_tecnicos"]
    montar_pdf_texto = deps["montar_pdf_texto"]
    backup_dir = deps["backup_dir"]
    google_drive_backup_dir = deps["google_drive_backup_dir"]
    garantir_pasta_backup_google_drive = deps["garantir_pasta_backup_google_drive"]
    criar_backup = deps["criar_backup"]
    enviar_backup_email = deps["enviar_backup_email"]
    backup_email_remetente = deps["backup_email_remetente"]
    backup_email_senha_app = deps["backup_email_senha_app"]
    backup_email_destino = deps["backup_email_destino"]

    @bp.route("/")
    @bp.route("/dashboard")
    @bp.route("/dashboard/")
    @bp.route("/dashboard.html")
    @bp.route("/index")
    @bp.route("/index.html")
    def index():
        return redirecionar_com_query_string(request, "/app")

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
        return redirecionar_com_query_string(request, "/app/relatorios")

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
        return redirecionar_com_query_string(request, "/app/kanban")

    @bp.route("/garantias")
    def garantias():
        return redirecionar_com_query_string(request, "/app/garantias")

    @bp.route("/backup", methods=["GET", "POST"])
    def backup():
        if request.method == "GET":
            return redirecionar_com_query_string(request, "/app/backup")

        os.makedirs(backup_dir, exist_ok=True)
        drive_dir = garantir_pasta_backup_google_drive(google_drive_backup_dir)
        email_configurado = bool(backup_email_remetente and backup_email_senha_app and backup_email_destino)

        if request.method == "POST":
            acao = request.form.get("acao", "criar")

            if acao == "enviar_email":
                # Envia o backup mais recente por e-mail
                arquivos_existentes = sorted(
                    [f for f in os.listdir(backup_dir) if f.lower().endswith(".db")],
                    reverse=True,
                )
                if not arquivos_existentes:
                    flash("Nenhum backup disponível para enviar. Crie um backup primeiro.", "error")
                    return redirect(url_for("main_views.backup"))
                caminho = os.path.join(backup_dir, arquivos_existentes[0])
                resultado = enviar_backup_email(
                    caminho, backup_email_remetente, backup_email_senha_app, backup_email_destino
                )
                if resultado["ok"]:
                    flash(f"Backup enviado para {backup_email_destino} com sucesso!", "success")
                else:
                    flash(f"Falha ao enviar e-mail: {resultado['erro']}", "error")
                return redirect(url_for("main_views.backup"))

            # acao == "criar"
            try:
                info = criar_backup(backup_dir, google_drive_backup_dir, conectar)
            except (OSError, sqlite3.Error) as exc:
                flash(f"Nao foi possivel gerar o backup: {exc}", "error")
                return redirect(url_for("main_views.backup"))

            msgs = []
            if info["destino_drive"]:
                msgs.append("copiado para o Google Drive")
            elif info.get("erro_drive"):
                flash(f"Backup criado localmente, mas o Google Drive recusou a copia: {info['nome']}", "error")

            if email_configurado:
                resultado = enviar_backup_email(
                    info["destino_local"], backup_email_remetente, backup_email_senha_app, backup_email_destino
                )
                if resultado["ok"]:
                    msgs.append(f"e-mail enviado para {backup_email_destino}")
                else:
                    flash(f"Backup criado, mas falha ao enviar e-mail: {resultado['erro']}", "error")

            descricao = " e ".join(msgs) if msgs else "localmente"
            flash(f"Backup criado ({descricao}): {info['nome']}", "success")
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
            email_configurado=email_configurado,
            email_destino=backup_email_destino,
        )

    @bp.route("/backup/download/<path:nome>")
    def backup_download(nome):
        return send_from_directory(backup_dir, nome, as_attachment=True)

    return bp
