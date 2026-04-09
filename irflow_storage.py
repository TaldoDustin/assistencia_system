import json
import os
import shutil
import sqlite3
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
