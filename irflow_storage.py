import email.mime.application
import email.mime.multipart
import email.mime.text
import json
import os
import shutil
import smtplib
import sqlite3
import threading
import time
from datetime import datetime


def carregar_configuracoes_integracoes(integrations_config_path):
    padrao = {
        "mercado_phone": {
            "api_token": "",
            "sync_enabled": True,
            "sync_interval_seconds": 30,
            "sync_start_date": "2026-04-01",
        }
    }
    if not os.path.exists(integrations_config_path):
        try:
            with open(integrations_config_path, "w", encoding="utf-8") as arquivo:
                json.dump(padrao, arquivo, ensure_ascii=False, indent=2)
        except OSError:
            return padrao
        return padrao

    try:
        with open(integrations_config_path, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
            if isinstance(dados, dict):
                return dados
    except (OSError, json.JSONDecodeError):
        pass
    return padrao


def diretorio_google_drive_disponivel(google_drive_backup_dir):
    pasta = (google_drive_backup_dir or "").strip()
    if pasta and os.path.isdir(pasta):
        return pasta
    return ""


def garantir_pasta_backup_google_drive(google_drive_backup_dir):
    pasta = (google_drive_backup_dir or "").strip()
    if not pasta:
        return ""
    try:
        os.makedirs(pasta, exist_ok=True)
    except OSError:
        return ""
    return pasta


def criar_arquivo_backup(destino, conectar):
    origem = conectar()
    copia = sqlite3.connect(destino)
    try:
        origem.backup(copia)
    finally:
        copia.close()
        origem.close()


def criar_backup(backup_dir, google_drive_backup_dir, conectar, nome_arquivo=None):
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    nome = nome_arquivo or f"backup-{timestamp}.db"
    destino_local = os.path.join(backup_dir, nome)
    criar_arquivo_backup(destino_local, conectar)

    destino_drive = ""
    erro_drive = ""
    drive_dir = garantir_pasta_backup_google_drive(google_drive_backup_dir)
    if drive_dir:
        try:
            destino_drive = os.path.join(drive_dir, nome)
            shutil.copy2(destino_local, destino_drive)
        except (OSError, shutil.Error) as exc:
            destino_drive = ""
            erro_drive = str(exc)

    return {
        "nome": nome,
        "destino_local": destino_local,
        "destino_drive": destino_drive,
        "erro_drive": erro_drive,
    }


def aplicar_retencao_backups_automaticos(backup_dir, google_drive_backup_dir, limite=90):
    def coletar_backups_automaticos(diretorio):
        if not diretorio or not os.path.isdir(diretorio):
            return []
        arquivos = []
        for nome in os.listdir(diretorio):
            if not nome.lower().endswith(".db"):
                continue
            if not nome.startswith("backup-auto-"):
                continue
            caminho = os.path.join(diretorio, nome)
            if os.path.isfile(caminho):
                arquivos.append((nome, caminho))
        arquivos.sort(key=lambda item: item[0])
        return arquivos

    for diretorio in [backup_dir, diretorio_google_drive_disponivel(google_drive_backup_dir)]:
        arquivos = coletar_backups_automaticos(diretorio)
        excedentes = max(0, len(arquivos) - limite)
        for _, caminho in arquivos[:excedentes]:
            try:
                os.remove(caminho)
            except OSError as exc:
                print(f"Falha ao remover backup antigo {caminho}: {exc}")


def executar_backup_diario_automatico(backup_dir, google_drive_backup_dir, conectar):
    hoje = datetime.now().strftime("%Y%m%d")
    nome_arquivo = f"backup-auto-{hoje}.db"
    destino_local = os.path.join(backup_dir, nome_arquivo)
    if os.path.exists(destino_local):
        aplicar_retencao_backups_automaticos(backup_dir, google_drive_backup_dir, limite=90)
        return None
    try:
        info = criar_backup(backup_dir, google_drive_backup_dir, conectar, nome_arquivo=nome_arquivo)
        if info.get("erro_drive"):
            print(f"Backup diario criado localmente, mas sem copia no Drive: {info['erro_drive']}")
        aplicar_retencao_backups_automaticos(backup_dir, google_drive_backup_dir, limite=90)
        return info
    except Exception as exc:
        print(f"Falha ao gerar backup automatico diario: {exc}")
        return None


def enviar_backup_email(caminho_arquivo, email_remetente, email_senha_app, email_destino):
    """Envia o arquivo de backup como anexo por e-mail via Gmail SMTP."""
    if not all([email_remetente, email_senha_app, email_destino, caminho_arquivo]):
        return {"ok": False, "erro": "Configuração de e-mail incompleta."}
    if not os.path.isfile(caminho_arquivo):
        return {"ok": False, "erro": f"Arquivo não encontrado: {caminho_arquivo}"}

    nome_arquivo = os.path.basename(caminho_arquivo)
    data_str = datetime.now().strftime("%d/%m/%Y %H:%M")

    msg = email.mime.multipart.MIMEMultipart()
    msg["From"] = email_remetente
    msg["To"] = email_destino
    msg["Subject"] = f"[IR Flow] Backup automático — {data_str}"

    corpo = (
        f"Backup automático do IR Flow gerado em {data_str}.\n\n"
        f"Arquivo: {nome_arquivo}\n"
        f"Tamanho: {os.path.getsize(caminho_arquivo) / 1024:.1f} KB\n\n"
        "Este e-mail foi gerado automaticamente."
    )
    msg.attach(email.mime.text.MIMEText(corpo, "plain", "utf-8"))

    with open(caminho_arquivo, "rb") as f:
        anexo = email.mime.application.MIMEApplication(f.read(), Name=nome_arquivo)
    anexo["Content-Disposition"] = f'attachment; filename="{nome_arquivo}"'
    msg.attach(anexo)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as servidor:
            servidor.login(email_remetente, email_senha_app)
            servidor.sendmail(email_remetente, email_destino, msg.as_string())
        return {"ok": True, "erro": ""}
    except smtplib.SMTPAuthenticationError:
        return {"ok": False, "erro": "Autenticação falhou. Verifique o e-mail e a senha de app."}
    except Exception as exc:
        return {"ok": False, "erro": str(exc)}


def iniciar_thread_backup_automatico(
    backup_dir,
    google_drive_backup_dir,
    conectar,
    email_remetente="",
    email_senha_app="",
    email_destino="",
    intervalo_verificacao_segundos=3600,
):
    """
    Inicia thread daemon que verifica a cada hora se o backup do dia já existe.
    Se não existir, cria e opcionalmente envia por e-mail.
    """

    def _loop():
        # Aguarda 30s após o boot para não competir com a inicialização do app
        time.sleep(30)
        while True:
            try:
                info = executar_backup_diario_automatico(
                    backup_dir, google_drive_backup_dir, conectar
                )
                if info:
                    print(f"[Backup] Arquivo criado: {info['nome']}")
                    if email_remetente and email_senha_app and email_destino:
                        resultado = enviar_backup_email(
                            info["destino_local"],
                            email_remetente,
                            email_senha_app,
                            email_destino,
                        )
                        if resultado["ok"]:
                            print(f"[Backup] E-mail enviado para {email_destino}")
                        else:
                            print(f"[Backup] Falha ao enviar e-mail: {resultado['erro']}")
            except Exception as exc:
                print(f"[Backup] Erro inesperado na thread: {exc}")

            time.sleep(intervalo_verificacao_segundos)

    t = threading.Thread(target=_loop, daemon=True, name="backup-automatico")
    t.start()
    return t
