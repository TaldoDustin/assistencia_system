"""
Configuração de ambiente, paths e feature-flags do Fluxoly.

TD-02 Fatia 1 (docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md) -- extraído do bloco B de
app.py (linhas 158-256 antes desta extração). Só leitura de os.environ e derivação de constantes --
zero dependência de Flask, zero I/O além da criação/cópia de arquivos de dados que já existia no
bloco original (idempotente, mesmo comportamento de antes).
"""

import os
import shutil
import sys

# ============================================================================
# CONFIGURAÇÃO DE AMBIENTE E CAMINHOS
# ============================================================================
if getattr(sys, "frozen", False):
    # Executável PyInstaller (desktop)
    APP_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
    USER_BASE = os.environ.get("LOCALAPPDATA") or APP_DIR
    DATA_DIR = os.path.join(USER_BASE, "IR Flow")
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = APP_DIR
    # Em produção (Fly/Render), usa diretório persistente quando configurado.
    # Em desenvolvimento local, usa o próprio diretório da app.
    SERVER_DATA_DIR = (
        os.environ.get("IR_FLOW_DATA_DIR") or os.environ.get("FLY_DATA_DIR") or os.environ.get("RENDER_DISK_PATH")
    )
    if not SERVER_DATA_DIR and os.path.isdir("/data"):
        SERVER_DATA_DIR = "/data"
    DATA_DIR = SERVER_DATA_DIR or APP_DIR

os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================================
# CONFIGURAÇÃO DE BANCO DE DADOS
# ============================================================================
DB_PATH = os.path.join(DATA_DIR, "database.db")
SEED_DB_PATH = os.path.join(APP_DIR, "database.db")
INTEGRATIONS_CONFIG_PATH = os.path.join(DATA_DIR, "integrations.json")

if getattr(sys, "frozen", False) and not os.path.exists(DB_PATH) and os.path.exists(SEED_DB_PATH):
    shutil.copy2(SEED_DB_PATH, DB_PATH)

# ============================================================================
# CONFIGURAÇÃO DE BACKUP E ARMAZENAMENTO
# ============================================================================
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
IS_SERVER_RUNTIME = bool(
    os.environ.get("IR_FLOW_DATA_DIR")
    or os.environ.get("FLY_DATA_DIR")
    or os.environ.get("RENDER_DISK_PATH")
    or os.environ.get("RENDER")
    or os.environ.get("RENDER_SERVICE_ID")
)
BACKGROUND_JOBS_ENABLED = os.environ.get("IR_FLOW_ENABLE_BACKGROUND_JOBS", "1").strip().lower() not in {
    "0",
    "false",
    "nao",
    "off",
}
APP_HOST = os.environ.get("IR_FLOW_HOST", "0.0.0.0" if IS_SERVER_RUNTIME else "127.0.0.1")
APP_PORT = int(os.environ.get("IR_FLOW_PORT", "5080"))
VERCEL_URL = (os.environ.get("VERCEL_URL") or "").strip()  # Ex: https://assistencia-system.vercel.app


def _normalizar_url_publica(valor):
    texto = (valor or "").strip().rstrip("/")
    if not texto:
        return ""
    if texto.startswith("http://") or texto.startswith("https://"):
        return texto
    return f"https://{texto}"


PUBLIC_BASE_URL = _normalizar_url_publica(os.environ.get("IR_FLOW_PUBLIC_BASE_URL")) or _normalizar_url_publica(
    VERCEL_URL
)
GOOGLE_DRIVE_BACKUP_DIR = os.environ.get("IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR", "")

# Configuração de e-mail para envio automático de backup
BACKUP_EMAIL_REMETENTE = os.environ.get("IR_FLOW_BACKUP_EMAIL", "ir.phones.flow@gmail.com")
BACKUP_EMAIL_SENHA_APP = os.environ.get("IR_FLOW_BACKUP_EMAIL_SENHA", "")
BACKUP_EMAIL_DESTINO = os.environ.get("IR_FLOW_BACKUP_EMAIL_DESTINO", "ir.phones.flow@gmail.com")

# Tabelas de preço ficam no volume persistente; na primeira execução, copia o
# arquivo de referência embutido no código para o diretório de dados.
_PRICE_TABLES_SEED = os.path.join(RESOURCE_DIR, "data", "price_tables.json")
PRICE_TABLES_PATH = os.path.join(DATA_DIR, "data", "price_tables.json")
os.makedirs(os.path.dirname(PRICE_TABLES_PATH), exist_ok=True)
if not os.path.exists(PRICE_TABLES_PATH) and os.path.exists(_PRICE_TABLES_SEED):
    shutil.copy2(_PRICE_TABLES_SEED, PRICE_TABLES_PATH)

# ============================================================================
# CONFIGURAÇÃO MERCADOPHONE
# ============================================================================
MERCADO_PHONE_WEBHOOK_TOKEN = os.environ.get("MERCADO_PHONE_WEBHOOK_TOKEN", "")
MERCADO_PHONE_DEFAULT_TECNICO = os.environ.get("MERCADO_PHONE_DEFAULT_TECNICO", "Aguardando definicao")
MERCADO_PHONE_API_BASE = os.environ.get(
    "MERCADO_PHONE_API_BASE",
    "https://app.mercadophone.tech/api.php?class=OrdemServicoApiController&method=",
)
MERCADO_PHONE_SYNC_ENABLED = os.environ.get("MERCADO_PHONE_SYNC_ENABLED", "1") == "1"
MERCADO_PHONE_SYNC_INTERVAL_SECONDS = int(os.environ.get("MERCADO_PHONE_SYNC_INTERVAL_SECONDS", "30"))
MERCADO_PHONE_SYNC_TIMEOUT_SECONDS = int(os.environ.get("MERCADO_PHONE_SYNC_TIMEOUT_SECONDS", "20"))
MERCADO_PHONE_SYNC_ONLY_AFTER_BOOT = os.environ.get("MERCADO_PHONE_SYNC_ONLY_AFTER_BOOT", "0") == "1"
MERCADO_PHONE_SYNC_START_DATE = os.environ.get("MERCADO_PHONE_SYNC_START_DATE", "2026-04-01")
