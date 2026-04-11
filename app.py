"""
IR Flow - Sistema de Gestão de Assistência Técnica
Application main module - Flask app bootstrap, configuration, and core functionality
"""

# ============================================================================
# IMPORTS PADRÃO DA BIBLIOTECA
# ============================================================================
import functools
import json
import os
import re
import shutil
import sqlite3
import sys
import threading
import time
import unicodedata
import webbrowser
from collections import defaultdict
from datetime import datetime, timedelta

# ============================================================================
# IMPORTS FLASK
# ============================================================================
from flask import Flask, render_template, request, redirect, jsonify, flash, url_for, send_from_directory, Response, abort, session
from werkzeug.security import check_password_hash, generate_password_hash

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - CORE
# ============================================================================
from irflow_core import (
    STATUS_AGUARDANDO_PECA,
    STATUS_CANCELADO,
    STATUS_EM_ANDAMENTO,
    STATUS_FINALIZADO,
    STATUS_OS_OPCOES,
    STATUS_OS_VALIDOS,
    calcular_faturamento_os,
    calcular_lucro_os,
    coletar_status_opcoes,
    normalizar_busca_texto,
    normalizar_status_os,
    status_aberto,
    status_aguardando_peca,
    status_cancelado,
    status_finalizado,
    texto_limpo,
    to_float,
)

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - OS, STORAGE, MERCADOPHONE
# ============================================================================
from irflow_os import (
    adicionar_peca_os_sem_consumir,
    carregar_os_com_relacoes,
    consumir_peca_da_os,
    devolver_pecas_da_os,
    extrair_reparo_ids,
    ler_valores_financeiros_form,
    modelo_compativel,
    obter_ou_criar_reparo,
    obter_reparos_por_os,
    registrar_movimentacao,
    salvar_reparos_os,
    validar_reparo_ids,
    vendedor_valido,
)

from irflow_mercadophone import (
    corrigir_dados_importados_mercado_phone,
    importar_os_mercado_phone,
    loop_sincronizacao_mercado_phone,
    sincronizar_mercado_phone,
)

from irflow_storage import (
    aplicar_retencao_backups_automaticos,
    carregar_configuracoes_integracoes,
    criar_backup,
    diretorio_google_drive_disponivel,
    enviar_backup_email,
    executar_backup_diario_automatico,
    garantir_pasta_backup_google_drive,
    iniciar_thread_backup_automatico,
)

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - BLUEPRINTS E RELATÓRIOS
# ============================================================================
from irflow_blueprints_main import create_main_blueprint
from irflow_blueprints_orders import create_orders_blueprint
from irflow_blueprints_inventory import create_inventory_blueprint
from irflow_blueprints_admin import create_admin_blueprint

from irflow_reports import (
    agrupar_relatorio_ir_phones,
    agrupar_relatorio_tecnicos,
    buscar_dados_relatorios,
    formatar_mes_referencia,
    formatar_periodo_relatorio,
    linha_tabela,
    limitar_texto,
    moeda_pdf,
    montar_linhas_relatorio_ir_phones,
    montar_linhas_relatorio_tecnicos,
    montar_pdf_texto,
    normalizar_chave_preco,
    normalizar_texto_pdf,
    obter_data_referencia_os,
    texto_reparos_os,
)

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
    # FLY_DATA_DIR é definido no fly.toml e aponta para o volume persistente (/data)
    # Em desenvolvimento local, usa o próprio diretório da app
    DATA_DIR = os.environ.get("FLY_DATA_DIR") or APP_DIR

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
APP_HOST = os.environ.get("IR_FLOW_HOST", "0.0.0.0" if os.environ.get("FLY_DATA_DIR") else "127.0.0.1")
APP_PORT = int(os.environ.get("IR_FLOW_PORT", "5080"))
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
MERCADO_PHONE_SYNC_INTERVAL_SECONDS = int(os.environ.get("MERCADO_PHONE_SYNC_INTERVAL_SECONDS", "180"))
MERCADO_PHONE_SYNC_TIMEOUT_SECONDS = int(os.environ.get("MERCADO_PHONE_SYNC_TIMEOUT_SECONDS", "20"))
MERCADO_PHONE_SYNC_ONLY_AFTER_BOOT = os.environ.get("MERCADO_PHONE_SYNC_ONLY_AFTER_BOOT", "0") == "1"
MERCADO_PHONE_SYNC_START_DATE = os.environ.get("MERCADO_PHONE_SYNC_START_DATE", "2026-04-01")

# ============================================================================
# BOOTSTRAP FLASK
# ============================================================================
app = Flask(__name__, template_folder=os.path.join(RESOURCE_DIR, "templates"))
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ir-flow-dev-key")

# ============================================================================
# CONSTANTES - MODELOS DE IPHONE
# ============================================================================
IPHONE_MODELS = [
    "iPhone XR",
    "iPhone XS",
    "iPhone XS Max",
    "iPhone 11",
    "iPhone 11 Pro",
    "iPhone 11 Pro Max",
    "iPhone SE (2a geracao)",
    "iPhone 12 mini",
    "iPhone 12",
    "iPhone 12 Pro",
    "iPhone 12 Pro Max",
    "iPhone 13 mini",
    "iPhone 13",
    "iPhone 13 Pro",
    "iPhone 13 Pro Max",
    "iPhone SE (3a geracao)",
    "iPhone 14",
    "iPhone 14 Plus",
    "iPhone 14 Pro",
    "iPhone 14 Pro Max",
    "iPhone 15",
    "iPhone 15 Plus",
    "iPhone 15 Pro",
    "iPhone 15 Pro Max",
    "iPhone 16",
    "iPhone 16 Plus",
    "iPhone 16 Pro",
    "iPhone 16 Pro Max",
    "iPhone 16e",
]

IPHONE_MODEL_MAP = {m.lower(): m for m in IPHONE_MODELS}
IPHONE_ALIAS_MAP = {}
for _modelo in IPHONE_MODELS:
    _base = _modelo.lower().replace("iphone", "").strip()
    _base = _base.replace("(", " ").replace(")", " ").replace("-", " ")
    _base = " ".join(_base.split())
    if _base:
        IPHONE_ALIAS_MAP[_base] = _modelo
        IPHONE_ALIAS_MAP[_base.replace(" ", "")] = _modelo

# ============================================================================
# CONSTANTES - CORES DE IPHONE POR MODELO
# ============================================================================
IPHONE_COLORS = {
    "iPhone XR": ["Preto", "Branco", "Azul", "Amarelo", "Coral", "Vermelho"],
    "iPhone XS": ["Cinza-espacial", "Prata", "Dourado"],
    "iPhone XS Max": ["Cinza-espacial", "Prata", "Dourado"],
    "iPhone 11": ["Preto", "Branco", "Verde", "Amarelo", "Roxo", "Vermelho"],
    "iPhone 11 Pro": ["Cinza-espacial", "Prata", "Verde-meia-noite", "Dourado"],
    "iPhone 11 Pro Max": ["Cinza-espacial", "Prata", "Verde-meia-noite", "Dourado"],
    "iPhone SE (2a geracao)": ["Preto", "Branco", "Vermelho"],
    "iPhone 12 mini": ["Preto", "Branco", "Azul", "Verde", "Roxo", "Vermelho"],
    "iPhone 12": ["Preto", "Branco", "Azul", "Verde", "Roxo", "Vermelho"],
    "iPhone 12 Pro": ["Grafite", "Prata", "Dourado", "Azul-pacifico"],
    "iPhone 12 Pro Max": ["Grafite", "Prata", "Dourado", "Azul-pacifico"],
    "iPhone 13 mini": ["Meia-noite", "Estelar", "Azul", "Rosa", "Verde", "Vermelho"],
    "iPhone 13": ["Meia-noite", "Estelar", "Azul", "Rosa", "Verde", "Vermelho"],
    "iPhone 13 Pro": ["Grafite", "Prata", "Dourado", "Azul-sierra", "Verde-alpino"],
    "iPhone 13 Pro Max": ["Grafite", "Prata", "Dourado", "Azul-sierra", "Verde-alpino"],
    "iPhone SE (3a geracao)": ["Meia-noite", "Estelar", "Vermelho"],
    "iPhone 14": ["Meia-noite", "Estelar", "Azul", "Roxo", "Amarelo", "Vermelho"],
    "iPhone 14 Plus": ["Meia-noite", "Estelar", "Azul", "Roxo", "Amarelo", "Vermelho"],
    "iPhone 14 Pro": ["Preto-espacial", "Prata", "Dourado", "Roxo-profundo"],
    "iPhone 14 Pro Max": ["Preto-espacial", "Prata", "Dourado", "Roxo-profundo"],
    "iPhone 15": ["Preto", "Azul", "Verde", "Amarelo", "Rosa"],
    "iPhone 15 Plus": ["Preto", "Azul", "Verde", "Amarelo", "Rosa"],
    "iPhone 15 Pro": ["Titanio preto", "Titanio branco", "Titanio azul", "Titanio natural"],
    "iPhone 15 Pro Max": ["Titanio preto", "Titanio branco", "Titanio azul", "Titanio natural"],
    "iPhone 16": ["Preto", "Branco", "Rosa", "Verde-acinzentado", "Azul-ultramarino"],
    "iPhone 16 Plus": ["Preto", "Branco", "Rosa", "Verde-acinzentado", "Azul-ultramarino"],
    "iPhone 16 Pro": ["Titanio preto", "Titanio branco", "Titanio natural", "Titanio-deserto"],
    "iPhone 16 Pro Max": ["Titanio preto", "Titanio branco", "Titanio natural", "Titanio-deserto"],
    "iPhone 16e": ["Preto", "Branco"],
}

COLOR_ALIAS_MAP = {
    "preto": "Preto",
    "black": "Preto",
    "branco": "Branco",
    "white": "Branco",
    "azul": "Azul",
    "blue": "Azul",
    "vermelho": "Vermelho",
    "red": "Vermelho",
    "rosa": "Rosa",
    "pink": "Rosa",
    "roxo": "Roxo",
    "purple": "Roxo",
    "amarelo": "Amarelo",
    "yellow": "Amarelo",
    "verde": "Verde",
    "green": "Verde",
    "estelar": "Estelar",
    "starlight": "Estelar",
    "meia noite": "Meia-noite",
    "midnight": "Meia-noite",
    "grafite": "Grafite",
    "graphite": "Grafite",
    "prata": "Prata",
    "silver": "Prata",
    "dourado": "Dourado",
    "gold": "Dourado",
    "natural": "Titanio natural",
    "deserto": "Titanio-deserto",
    "titanio branco": "Titanio branco",
    "titanio preto": "Titanio preto",
    "titanio azul": "Titanio azul",
    "titanio natural": "Titanio natural",
    "titanio deserto": "Titanio-deserto",
}

# ============================================================================
# CONSTANTES - PESSOAL E CUSTOS
# ============================================================================
VENDEDORES = [
    "Camila",
    "Kauany",
    "Camily",
    "Taina",
    "Evellyn",
    "Marcelo",
    "Isabela",
]

TECNICOS = [
    "Aguardando definicao",
    "Isaque Souza",
    "Ruan Soares",
]

CATEGORIAS_CUSTOS_OPERACIONAIS = [
    "Limpeza e insumos",
    "Ferramentas",
    "Embalagem",
    "Transporte",
    "Terceiros",
    "Outros",
]

# ============================================================================
# CONSTANTES - REPAROS PADRÃO E MESES
# ============================================================================
REPAROS_PADRAO = [
    "TROCA DE TELA",
    "TROCA DE BATERIA",
    "TROCA DE DOCK DE CARGA",
    "TROCA DE VIDRO DA TELA",
    "TROCA DE LENTE DA CAMERA",
    "TROCA DE CAMERA TRASEIRA",
    "TROCA DE CAMERA FRONTAL",
    "TROCA DE FACE ID",
    "TROCA DE BOTOES",
    "TROCA DE AURICULAR",
    "TROCA DE TAMPA TRASEIRA",
    "TROCA DE VIDRO TRASEIRO",
    "TROCA DE CARCACA",
    "TROCA DE ALTO FALANTE",
    "REPARO DE TELA",
    "REPARO DE PLACA",
    "TROCA DE FLASH",
]

MESES_PT = {
    "01": "Janeiro",
    "02": "Fevereiro",
    "03": "Marco",
    "04": "Abril",
    "05": "Maio",
    "06": "Junho",
    "07": "Julho",
    "08": "Agosto",
    "09": "Setembro",
    "10": "Outubro",
    "11": "Novembro",
    "12": "Dezembro",
}

# ============================================================================
# LOCKS E FLAGS DE INICIALIZAÇÃO
# ============================================================================
SCHEMA_LOCK = threading.Lock()
SCHEMA_READY = False

# ============================================================================
# FUNÇÕES AUXILIARES - NORMALIZAÇÃO E CONVERSÃO
# ============================================================================


def normalizar_modelo_iphone(modelo):
    """Normaliza nome de modelo de iPhone para forma canônica."""
    valor = (modelo or "").strip()
    if not valor:
        return ""
    return IPHONE_MODEL_MAP.get(valor.lower(), "")


def obter_cores_modelo_iphone(modelo):
    """Retorna lista de cores disponíveis para um modelo de iPhone."""
    return IPHONE_COLORS.get(modelo or "", [])


def normalizar_imei(valor):
    """Extrai e valida IMEI (14-16 dígitos)."""
    digitos = "".join(ch for ch in str(valor or "") if ch.isdigit())
    if 14 <= len(digitos) <= 16:
        return digitos
    return ""


def modelo_para_os(valor):
    """Converte descrição de modelo para forma canônica ou fallback."""
    texto = texto_limpo(valor)
    if not texto:
        return ""
    return normalizar_modelo_iphone(texto) or texto


def extrair_modelo_da_descricao_aparelho(descricao):
    """Extrai modelo de iPhone de uma descrição de aparelho."""
    texto = normalizar_busca_texto(descricao)
    if not texto:
        return ""

    match = re.search(r"\b(?:iphone|ip)\s*(\d{1,2})(?:\s*(pro max|promax|pro|plus|mini|e))?\b", texto)
    if match:
        numero = match.group(1)
        sufixo = (match.group(2) or "").replace("promax", "pro max").strip()
        chave = f"{numero} {sufixo}".strip()
        modelo = IPHONE_ALIAS_MAP.get(chave) or IPHONE_ALIAS_MAP.get(chave.replace(" ", ""))
        if modelo:
            return modelo

    for alias, modelo in sorted(IPHONE_ALIAS_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if alias and alias in texto:
            return modelo
    return ""


def extrair_cor_da_descricao_aparelho(descricao, modelo=""):
    """Extrai cor de iPhone de uma descrição de aparelho."""
    texto = normalizar_busca_texto(descricao)
    if not texto:
        return ""

    cores_modelo = set(obter_cores_modelo_iphone(modelo))
    for alias, cor in COLOR_ALIAS_MAP.items():
        if alias in texto:
            if not cores_modelo or cor in cores_modelo:
                return cor
    return ""


def nome_reparo_importavel(nome):
    """Verifica se um nome de reparo é válido para importação."""
    texto = texto_limpo(nome)
    if not texto:
        return False

    texto_norm = normalizar_busca_texto(texto)
    if texto_norm in {"iphone", "ipad", "smartphone", "celular", "assistencia", "garantia", "reparo"}:
        return False
    if extrair_modelo_da_descricao_aparelho(texto):
        return False
    return True


def parse_data_ymd(valor):
    """Converte string de data YYYY-MM-DD para objeto datetime."""
    texto = texto_limpo(valor)
    if not texto:
        return None
    try:
        return datetime.strptime(texto[:10], "%Y-%m-%d")
    except ValueError:
        return None


# ============================================================================
# FUNÇÕES AUXILIARES - CARREGAMENTO DE DADOS
# ============================================================================


def carregar_tabelas_preco():
    """Carrega tabelas de preço do arquivo JSON."""
    if not os.path.exists(PRICE_TABLES_PATH):
        return {"ir_phones": {}, "clientes": {}}
    try:
        with open(PRICE_TABLES_PATH, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return {"ir_phones": {}, "clientes": {}}


def salvar_tabelas_preco(tabelas):
    """Salva tabelas de preço no arquivo JSON."""
    os.makedirs(os.path.dirname(PRICE_TABLES_PATH), exist_ok=True)
    with open(PRICE_TABLES_PATH, "w", encoding="utf-8") as arquivo:
        json.dump(tabelas, arquivo, ensure_ascii=False, indent=2)


# ============================================================================
# FUNÇÕES DE DATABASE
# ============================================================================


def conectar():
    """Cria conexão com banco de dados e garante schema."""
    criar_tabelas()
    return sqlite3.connect(DB_PATH)


def criar_tabelas():
    """Cria tabelas do schema se não existirem."""
    global SCHEMA_READY

    if SCHEMA_READY:
        return

    with SCHEMA_LOCK:
        if SCHEMA_READY:
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        try:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS reparos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS os (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT,
                cliente TEXT,
                aparelho TEXT,
                tecnico TEXT,
                reparo_id INTEGER,
                status TEXT,
                valor_cobrado REAL,
                valor_descontado REAL,
                custo_pecas REAL,
                data TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS estoque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT,
                valor REAL,
                fornecedor TEXT,
                quantidade INTEGER,
                data_compra TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS os_pecas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                os_id INTEGER,
                estoque_id INTEGER,
                quantidade INTEGER,
                valor REAL
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS os_reparos (
                os_id INTEGER NOT NULL,
                reparo_id INTEGER NOT NULL,
                PRIMARY KEY (os_id, reparo_id)
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estoque_id INTEGER,
                tipo TEXT,
                quantidade INTEGER,
                data TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS custos_operacionais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                categoria TEXT,
                valor REAL NOT NULL,
                data TEXT,
                observacoes TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS integracao_sync_estado (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS integracao_os_vistas (
                origem TEXT NOT NULL,
                id_externo TEXT NOT NULL,
                primeira_visualizacao TEXT,
                PRIMARY KEY (origem, id_externo)
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                usuario TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL DEFAULT 'tecnico',
                ativo INTEGER NOT NULL DEFAULT 1
            )
            """)

            # Add valor column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE os_pecas ADD COLUMN valor REAL")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE os_pecas ADD COLUMN peca_descricao TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE os_pecas ADD COLUMN peca_fornecedor TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE os ADD COLUMN data_finalizado TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE os ADD COLUMN modelo TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE os ADD COLUMN cor TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE os ADD COLUMN imei TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE os ADD COLUMN vendedor TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE os ADD COLUMN observacoes TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE os ADD COLUMN origem_integracao TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE os ADD COLUMN id_externo_integracao TEXT")
            except sqlite3.OperationalError:
                pass

            try:
                cursor.execute("ALTER TABLE estoque ADD COLUMN modelo TEXT")
            except sqlite3.OperationalError:
                pass

            conn.commit()

            cursor.execute("SELECT id, modelo FROM estoque")
            for item_id, modelo_atual in cursor.fetchall():
                modelo_norm = normalizar_modelo_iphone(modelo_atual)
                if modelo_norm != (modelo_atual or ""):
                    cursor.execute("UPDATE estoque SET modelo=? WHERE id=?", (modelo_norm, item_id))

            cursor.execute("SELECT id, modelo FROM os")
            for os_id, modelo_atual in cursor.fetchall():
                modelo_norm = normalizar_modelo_iphone(modelo_atual)
                if modelo_norm != (modelo_atual or ""):
                    cursor.execute("UPDATE os SET modelo=? WHERE id=?", (modelo_norm, os_id))

            cursor.execute(
                """
                INSERT OR IGNORE INTO os_reparos (os_id, reparo_id)
                SELECT id, reparo_id
                FROM os
                WHERE reparo_id IS NOT NULL
                """
            )

            conn.commit()
            SCHEMA_READY = True
        finally:
            conn.close()


criar_tabelas()
iniciar_thread_backup_automatico(
    BACKUP_DIR,
    GOOGLE_DRIVE_BACKUP_DIR,
    conectar,
    email_remetente=BACKUP_EMAIL_REMETENTE,
    email_senha_app=BACKUP_EMAIL_SENHA_APP,
    email_destino=BACKUP_EMAIL_DESTINO,
)


def criar_admin_padrao():
    """Cria usuário admin padrão se não existir nenhum usuário."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM usuarios")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO usuarios (nome, usuario, senha_hash, perfil) VALUES (?, ?, ?, ?)",
            ("Administrador", "admin", generate_password_hash("irflow@2024"), "admin"),
        )
        conn.commit()
    conn.close()


criar_admin_padrao()

# ============================================================================
# CONFIGURAÇÃO MERCADO PHONE
# ============================================================================

INTEGRATIONS_CONFIG = carregar_configuracoes_integracoes(INTEGRATIONS_CONFIG_PATH)
MERCADO_PHONE_CONFIG = INTEGRATIONS_CONFIG.get("mercado_phone", {}) if isinstance(INTEGRATIONS_CONFIG, dict) else {}
MERCADO_PHONE_API_TOKEN = os.environ.get("MERCADO_PHONE_API_TOKEN", "") or texto_limpo(MERCADO_PHONE_CONFIG.get("api_token"))
MERCADO_PHONE_SYNC_ENABLED = (texto_limpo(str(MERCADO_PHONE_CONFIG.get("sync_enabled", MERCADO_PHONE_SYNC_ENABLED))).lower() not in {"0", "false", "nao", "off"}) if MERCADO_PHONE_API_TOKEN else False
MERCADO_PHONE_SYNC_INTERVAL_SECONDS = int(MERCADO_PHONE_CONFIG.get("sync_interval_seconds", MERCADO_PHONE_SYNC_INTERVAL_SECONDS) or MERCADO_PHONE_SYNC_INTERVAL_SECONDS)
MERCADO_PHONE_SYNC_START_DATE = texto_limpo(MERCADO_PHONE_CONFIG.get("sync_start_date", MERCADO_PHONE_SYNC_START_DATE)) or "2026-04-01"

MERCADO_PHONE_RUNTIME_CONFIG = {
    "api_token": MERCADO_PHONE_API_TOKEN,
    "api_base": MERCADO_PHONE_API_BASE,
    "default_tecnico": MERCADO_PHONE_DEFAULT_TECNICO,
    "sync_enabled": MERCADO_PHONE_SYNC_ENABLED,
    "sync_interval_seconds": MERCADO_PHONE_SYNC_INTERVAL_SECONDS,
    "sync_timeout_seconds": MERCADO_PHONE_SYNC_TIMEOUT_SECONDS,
    "sync_only_after_boot": MERCADO_PHONE_SYNC_ONLY_AFTER_BOOT,
    "sync_start_date": MERCADO_PHONE_SYNC_START_DATE,
}

MERCADO_PHONE_HELPERS = {
    "texto_limpo": texto_limpo,
    "modelo_para_os": modelo_para_os,
    "extrair_modelo_da_descricao_aparelho": extrair_modelo_da_descricao_aparelho,
    "extrair_cor_da_descricao_aparelho": extrair_cor_da_descricao_aparelho,
    "normalizar_imei": normalizar_imei,
    "nome_reparo_importavel": nome_reparo_importavel,
    "obter_ou_criar_reparo": obter_ou_criar_reparo,
    "salvar_reparos_os": salvar_reparos_os,
    "normalizar_busca_texto": normalizar_busca_texto,
    "normalizar_status_os": normalizar_status_os,
}

# ============================================================================
# ENDPOINTS - INTEGRAÇÃO MERCADO PHONE
# ============================================================================


def autenticar_integracao_mercado_phone():
    """Valida token de autenticação do webhook Mercado Phone."""
    if not MERCADO_PHONE_WEBHOOK_TOKEN:
        return

    auth_header = texto_limpo(request.headers.get("Authorization"))
    token_header = texto_limpo(request.headers.get("X-Webhook-Token"))

    token_informado = token_header
    if auth_header.lower().startswith("bearer "):
        token_informado = auth_header[7:].strip()

    if token_informado != MERCADO_PHONE_WEBHOOK_TOKEN:
        abort(401)


@app.route("/api/integracoes/mercadophone/os", methods=["POST"])
def receber_os_mercado_phone():
    """Recebe OS do Mercado Phone via webhook."""
    autenticar_integracao_mercado_phone()

    payload = request.get_json(silent=True) or {}
    if isinstance(payload, dict) and isinstance(payload.get("ordem_servico"), dict):
        payload = payload["ordem_servico"]

    conn = conectar()
    cursor = conn.cursor()

    try:
        resultado = importar_os_mercado_phone(cursor, payload, MERCADO_PHONE_RUNTIME_CONFIG, MERCADO_PHONE_HELPERS)
        conn.commit()
        status_code = 200 if resultado["duplicada"] else 201
        return jsonify(
            {
                "ok": True,
                "duplicada": resultado["duplicada"],
                "os_id": resultado["os_id"],
            }
        ), status_code
    except ValueError as exc:
        conn.rollback()
        return jsonify({"ok": False, "erro": str(exc)}), 400
    finally:
        conn.close()


# ============================================================================
# FUNÇÕES DE NEGÓCIO
# ============================================================================


def sincronizar_reparos_padrao():
    """Sincroniza lista de reparos padrão para o banco."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT lower(nome) FROM reparos")
    existentes = {row[0] for row in cursor.fetchall() if row[0]}

    for reparo in REPAROS_PADRAO:
        if reparo.lower() in existentes:
            continue
        cursor.execute("INSERT INTO reparos (nome) VALUES (?)", (reparo,))

    conn.commit()
    conn.close()


def obter_alertas_sistema(limit=8):
    """
    Coleta alertas de sistema:
    - Estoque baixo
    - OS em aberto há muito tempo
    - Garantia perto de vencer
    """
    conn = conectar()
    cursor = conn.cursor()
    alerts = []
    hoje = datetime.now().date()

    # Alerta: Estoque Baixo
    cursor.execute(
        """
        SELECT id, descricao, quantidade
        FROM estoque
        WHERE COALESCE(quantidade, 0) <= 2
        ORDER BY quantidade ASC, descricao ASC
        LIMIT 10
        """
    )
    for item_id, descricao, quantidade in cursor.fetchall():
        qtd = quantidade or 0
        status_txt = "sem estoque" if qtd == 0 else f"{qtd} unid."
        alerts.append(
            {
                "nivel": "critico" if qtd == 0 else "atencao",
                "titulo": "Estoque baixo",
                "mensagem": f"{descricao or 'Peca'} ({status_txt})",
                "link": url_for("inventory_views.estoque"),
            }
        )

    # Alerta: OS em Aberto há Muito Tempo
    cursor.execute(
        """
        SELECT id, cliente, modelo, status, data
        FROM os
        WHERE status IN ('Em andamento', 'Aguardando peca', 'Aguardando peça')
        ORDER BY id DESC
        """
    )
    for os_id, cliente, modelo, status, data_os in cursor.fetchall():
        if normalizar_status_os(status) not in {STATUS_EM_ANDAMENTO, STATUS_AGUARDANDO_PECA}:
            continue
        dt = parse_data_ymd(data_os)
        if not dt:
            continue
        dias = (hoje - dt.date()).days
        if dias >= 10:
            alerts.append(
                {
                    "nivel": "info",
                    "titulo": "OS em aberto ha muito tempo",
                    "mensagem": f"OS #{os_id} - {cliente or 'Sem cliente'} ({dias} dias)",
                    "link": url_for("order_views.ordens"),
                }
            )

    # Alerta: Garantia Perto de Vencer
    cursor.execute(
        """
        SELECT id, cliente, modelo, data_finalizado, data, status
        FROM os
        WHERE status='Finalizado'
        ORDER BY id DESC
        """
    )
    for os_id, cliente, modelo, data_finalizado, data_os, status in cursor.fetchall():
        if normalizar_status_os(status) != STATUS_FINALIZADO:
            continue
        if (cliente or "").strip().lower() == "ir phones":
            continue
        inicio = parse_data_ymd(data_finalizado) or parse_data_ymd(data_os)
        if not inicio:
            continue
        fim = (inicio + timedelta(days=90)).date()
        dias_restantes = (fim - hoje).days
        if 0 <= dias_restantes <= 7:
            alerts.append(
                {
                    "nivel": "atencao",
                    "titulo": "Garantia perto do vencimento",
                    "mensagem": f"OS #{os_id} - {cliente or 'Sem cliente'} (vence em {dias_restantes} dia(s))",
                    "link": url_for("main_views.garantias"),
                }
            )

    conn.close()

    # Ordena por prioridade
    prioridade = {"critico": 0, "atencao": 1, "info": 2}
    alerts.sort(key=lambda a: prioridade.get(a["nivel"], 3))
    return alerts[:limit]


def listar_custos_operacionais(data_inicio="", data_fim=""):
    """Lista custos operacionais com filtros de período e agregação por categoria."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            COALESCE(descricao, ''),
            COALESCE(categoria, 'Outros'),
            COALESCE(valor, 0),
            COALESCE(data, ''),
            COALESCE(observacoes, '')
        FROM custos_operacionais
        ORDER BY data DESC, id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    itens = []
    total_periodo = 0
    por_categoria = {}

    for custo_id, descricao, categoria, valor, data, observacoes in rows:
        if (data_inicio or data_fim) and not data:
            continue
        if data_inicio and data and data < data_inicio:
            continue
        if data_fim and data and data > data_fim:
            continue

        item = {
            "id": custo_id,
            "descricao": descricao,
            "categoria": categoria or "Outros",
            "valor": round(valor or 0, 2),
            "data": data,
            "observacoes": observacoes,
        }
        itens.append(item)
        total_periodo += valor or 0
        por_categoria[item["categoria"]] = por_categoria.get(item["categoria"], 0) + (valor or 0)

    por_categoria_ordenado = sorted(por_categoria.items(), key=lambda item: item[1], reverse=True)
    return {
        "itens": itens,
        "total_periodo": round(total_periodo, 2),
        "por_categoria": por_categoria_ordenado,
        "labels_categoria": [item[0] for item in por_categoria_ordenado],
        "values_categoria": [round(item[1], 2) for item in por_categoria_ordenado],
    }


# ============================================================================
# CONTEXT PROCESSORS
# ============================================================================


@app.context_processor
def inject_system_alerts():
    """Injeta alertas de sistema em todos os templates."""
    try:
        alerts = obter_alertas_sistema(limit=10)
    except Exception:
        alerts = []
    return {
        "system_alerts": alerts,
        "system_alert_count": len(alerts),
    }


# ============================================================================
# REGISTRO DE BLUEPRINTS COM DEPENDÊNCIAS
# ============================================================================

sincronizar_reparos_padrao()

app.register_blueprint(
    create_main_blueprint(
        {
            "conectar": conectar,
            "carregar_os_com_relacoes": carregar_os_com_relacoes,
            "texto_reparos_os": texto_reparos_os,
            "normalizar_status_os": normalizar_status_os,
            "status_cancelado": status_cancelado,
            "status_finalizado": status_finalizado,
            "status_aberto": status_aberto,
            "coletar_status_opcoes": coletar_status_opcoes,
            "calcular_faturamento_os": calcular_faturamento_os,
            "calcular_lucro_os": calcular_lucro_os,
            "listar_custos_operacionais": listar_custos_operacionais,
            "categorias_custos_operacionais": CATEGORIAS_CUSTOS_OPERACIONAIS,
            "agrupar_relatorio_ir_phones": functools.partial(agrupar_relatorio_ir_phones, conectar=conectar),
            "agrupar_relatorio_tecnicos": functools.partial(agrupar_relatorio_tecnicos, conectar=conectar),
            "formatar_periodo_relatorio": formatar_periodo_relatorio,
            "montar_linhas_relatorio_ir_phones": functools.partial(montar_linhas_relatorio_ir_phones, conectar=conectar),
            "montar_linhas_relatorio_tecnicos": functools.partial(montar_linhas_relatorio_tecnicos, conectar=conectar),
            "montar_pdf_texto": montar_pdf_texto,
            "obter_reparos_por_os": obter_reparos_por_os,
            "status_em_andamento": STATUS_EM_ANDAMENTO,
            "status_aguardando_peca_const": STATUS_AGUARDANDO_PECA,
            "status_finalizado_const": STATUS_FINALIZADO,
            "status_cancelado_const": STATUS_CANCELADO,
            "parse_data_ymd": parse_data_ymd,
            "backup_dir": BACKUP_DIR,
            "google_drive_backup_dir": GOOGLE_DRIVE_BACKUP_DIR,
            "garantir_pasta_backup_google_drive": garantir_pasta_backup_google_drive,
            "criar_backup": criar_backup,
            "enviar_backup_email": enviar_backup_email,
            "backup_email_remetente": BACKUP_EMAIL_REMETENTE,
            "backup_email_senha_app": BACKUP_EMAIL_SENHA_APP,
            "backup_email_destino": BACKUP_EMAIL_DESTINO,
        }
    )
)

app.register_blueprint(
    create_orders_blueprint(
        {
            "conectar": conectar,
            "texto_reparos_os": texto_reparos_os,
            "normalizar_status_os": normalizar_status_os,
            "status_finalizado_const": STATUS_FINALIZADO,
            "status_cancelado_const": STATUS_CANCELADO,
            "status_em_andamento_const": STATUS_EM_ANDAMENTO,
            "status_os_validos": STATUS_OS_VALIDOS,
            "status_aberto": status_aberto,
            "coletar_status_opcoes": coletar_status_opcoes,
            "calcular_faturamento_os": calcular_faturamento_os,
            "calcular_lucro_os": calcular_lucro_os,
            "carregar_os_com_relacoes": carregar_os_com_relacoes,
            "extrair_reparo_ids": extrair_reparo_ids,
            "validar_reparo_ids": validar_reparo_ids,
            "vendedor_valido": vendedor_valido,
            "ler_valores_financeiros_form": ler_valores_financeiros_form,
            "salvar_reparos_os": salvar_reparos_os,
            "modelo_compativel": modelo_compativel,
            "consumir_peca_da_os": consumir_peca_da_os,
            "adicionar_peca_os_sem_consumir": adicionar_peca_os_sem_consumir,
            "devolver_pecas_da_os": devolver_pecas_da_os,
            "registrar_movimentacao": registrar_movimentacao,
            "obter_reparos_por_os": obter_reparos_por_os,
            "modelo_para_os": modelo_para_os,
            "normalizar_imei": normalizar_imei,
            "carregar_tabelas_preco": carregar_tabelas_preco,
            "iphone_models": IPHONE_MODELS,
            "iphone_colors": IPHONE_COLORS,
            "vendedores": VENDEDORES,
            "tecnicos": TECNICOS,
            "status_os_opcoes": STATUS_OS_OPCOES,
        }
    )
)

app.register_blueprint(
    create_inventory_blueprint(
        {
            "conectar": conectar,
            "normalizar_modelo_iphone": normalizar_modelo_iphone,
            "registrar_movimentacao": registrar_movimentacao,
            "iphone_models": IPHONE_MODELS,
        }
    )
)

app.register_blueprint(
    create_admin_blueprint(
        {
            "conectar": conectar,
            "listar_custos_operacionais": listar_custos_operacionais,
            "categorias_custos_operacionais": CATEGORIAS_CUSTOS_OPERACIONAIS,
            "carregar_tabelas_preco": carregar_tabelas_preco,
            "salvar_tabelas_preco": salvar_tabelas_preco,
            "iphone_models": IPHONE_MODELS,
        }
    )
)

# ============================================================================
# AUTENTICAÇÃO — PERMISSÕES E BEFORE_REQUEST
# ============================================================================

# Perfis disponíveis: admin, tecnico, vendedor
# None = qualquer perfil logado
ROUTE_PERMISSIONS: dict[str, list[str] | None] = {
    # Acesso livre (não requer login)
    "auth_views.login": [],
    "auth_views.logout": [],
    "static": [],
    # Qualquer usuário logado
    "main_views.dashboard": None,
    "main_views.index": None,
    "main_views.kanban": None,
    "main_views.garantias": None,
    "order_views.ordens": None,
    "order_views.nova": None,
    "order_views.editar": None,
    "order_views.atualizar_status": None,
    "order_views.deletar": None,
    "order_views.autocomplete_clientes": None,
    "order_views.api_buscar_pecas": None,
    "order_views.api_remover_peca": None,
    "order_views.api_adicionar_peca": None,
    "inventory_views.estoque": None,
    "inventory_views.cadastro_peca": ["admin", "tecnico"],
    "inventory_views.editar_item_estoque": ["admin", "tecnico"],
    "inventory_views.deletar_item_estoque": ["admin"],
    # Somente admin
    "main_views.relatorios": ["admin"],
    "main_views.backup": ["admin"],
    "main_views.backup_download": ["admin"],
    "admin_views.custos_operacionais": ["admin"],
    "admin_views.salvar_custo": ["admin"],
    "admin_views.deletar_custo": ["admin"],
    "admin_views.cadastrar_custo_operacional": ["admin"],
    "admin_views.excluir_custo_operacional": ["admin"],
    "admin_views.reparos": ["admin"],
    "admin_views.salvar_reparo": ["admin"],
    "admin_views.deletar_reparo": ["admin"],
    "admin_views.editar_reparo": ["admin"],
    "admin_views.tabelas_preco": ["admin"],
    "admin_views.salvar_tabelas_preco": ["admin"],
    "admin_views.excluir_tabelas_preco": ["admin"],
    "admin_views.salvar_entrada_tabela": ["admin"],
    "admin_views.excluir_entrada_tabela": ["admin"],
    "main_views.relatorio_pdf_ir_phones": ["admin"],
    "main_views.relatorio_pdf_tecnicos": ["admin"],
    "auth_views.usuarios": ["admin"],
    "auth_views.novo_usuario": ["admin"],
    "auth_views.editar_usuario": ["admin"],
    "auth_views.deletar_usuario": ["admin"],
    # Webhook (autenticação própria por token)
    "receber_os_mercado_phone": [],
    "sync_os_mercado_phone": [],
    "status_sync_mercado_phone": [],
}


@app.before_request
def verificar_autenticacao():
    endpoint = request.endpoint
    if not endpoint:
        return

    # Rotas estáticas e API — autenticação gerenciada pela própria API
    if endpoint in ("static", "serve_react", "serve_react_assets"):
        return
    if endpoint and endpoint.startswith("api."):
        return

    perms = ROUTE_PERMISSIONS.get(endpoint)
    if perms == []:
        # Acesso livre
        return

    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return redirect(url_for("auth_views.login", next=request.path))

    perfil = session.get("usuario_perfil", "")
    if perms is not None and perfil not in perms:
        flash("Você não tem permissão para acessar esta página.", "danger")
        return redirect(url_for("main_views.dashboard"))


# ============================================================================
# REGISTRO DO BLUEPRINT DE AUTENTICAÇÃO
# ============================================================================

from irflow_blueprints_auth import create_auth_blueprint  # noqa: E402
from irflow_blueprints_api import create_api_blueprint  # noqa: E402

app.register_blueprint(
    create_auth_blueprint(
        {
            "conectar": conectar,
            "generate_password_hash": generate_password_hash,
            "check_password_hash": check_password_hash,
        }
    )
)

# ============================================================================
# REGISTRO DO BLUEPRINT DE API (JSON — consumido pelo frontend React)
# ============================================================================

app.register_blueprint(
    create_api_blueprint(
        {
            "conectar": conectar,
            "normalizar_status_os": normalizar_status_os,
            "status_finalizado": status_finalizado,
            "status_cancelado": status_cancelado,
            "status_aberto": status_aberto,
            "status_em_andamento": STATUS_EM_ANDAMENTO,
            "status_aguardando_peca": STATUS_AGUARDANDO_PECA,
            "calcular_faturamento_os": calcular_faturamento_os,
            "calcular_lucro_os": calcular_lucro_os,
            "carregar_os_com_relacoes": carregar_os_com_relacoes,
            "extrair_reparo_ids": extrair_reparo_ids,
            "validar_reparo_ids": validar_reparo_ids,
            "vendedor_valido": vendedor_valido,
            "salvar_reparos_os": salvar_reparos_os,
            "modelo_compativel": modelo_compativel,
            "consumir_peca_da_os": consumir_peca_da_os,
            "adicionar_peca_os_sem_consumir": adicionar_peca_os_sem_consumir,
            "devolver_pecas_da_os": devolver_pecas_da_os,
            "registrar_movimentacao": registrar_movimentacao,
            "obter_reparos_por_os": obter_reparos_por_os,
            "modelo_para_os": modelo_para_os,
            "normalizar_imei": normalizar_imei,
            "normalizar_modelo_iphone": normalizar_modelo_iphone,
            "carregar_tabelas_preco": carregar_tabelas_preco,
            "salvar_tabelas_preco": salvar_tabelas_preco,
            "texto_reparos_os": texto_reparos_os,
            "listar_custos_operacionais": listar_custos_operacionais,
            "agrupar_relatorio_ir_phones": functools.partial(agrupar_relatorio_ir_phones, conectar=conectar),
            "agrupar_relatorio_tecnicos": functools.partial(agrupar_relatorio_tecnicos, conectar=conectar),
            "montar_linhas_relatorio_ir_phones": functools.partial(montar_linhas_relatorio_ir_phones, conectar=conectar),
            "montar_linhas_relatorio_tecnicos": functools.partial(montar_linhas_relatorio_tecnicos, conectar=conectar),
            "montar_pdf_texto": montar_pdf_texto,
            "formatar_periodo_relatorio": formatar_periodo_relatorio,
            "parse_data_ymd": parse_data_ymd,
            "obter_alertas_sistema": obter_alertas_sistema,
            "iphone_models": IPHONE_MODELS,
            "iphone_colors": IPHONE_COLORS,
            "vendedores": VENDEDORES,
            "tecnicos": TECNICOS,
            "status_os_opcoes": STATUS_OS_OPCOES,
            "categorias_custos": CATEGORIAS_CUSTOS_OPERACIONAIS,
            "reparos_padrao": REPAROS_PADRAO,
            "backup_dir": BACKUP_DIR,
            "criar_backup": criar_backup,
            "google_drive_backup_dir": GOOGLE_DRIVE_BACKUP_DIR,
            "garantir_pasta_backup_google_drive": garantir_pasta_backup_google_drive,
            "enviar_backup_email": enviar_backup_email,
            "backup_email_remetente": BACKUP_EMAIL_REMETENTE,
            "backup_email_senha_app": BACKUP_EMAIL_SENHA_APP,
            "backup_email_destino": BACKUP_EMAIL_DESTINO,
            "check_password_hash": check_password_hash,
            "generate_password_hash": generate_password_hash,
            "sincronizar_mercado_phone": sincronizar_mercado_phone,
            "mercado_phone_runtime_config": MERCADO_PHONE_RUNTIME_CONFIG,
            "mercado_phone_helpers": MERCADO_PHONE_HELPERS,
        }
    )
)

# ============================================================================
# SERVE REACT SPA — catch-all para todas as rotas não-API
# ============================================================================

REACT_DIST = os.path.join(RESOURCE_DIR, "frontend", "dist")


@app.route("/app", defaults={"path": ""})
@app.route("/app/<path:path>")
def serve_react(path):
    """Serve o frontend React. O React Router cuida da navegação interna."""
    if path and os.path.exists(os.path.join(REACT_DIST, path)):
        return send_from_directory(REACT_DIST, path)
    index_path = os.path.join(REACT_DIST, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(REACT_DIST, "index.html")
    return "Frontend não encontrado. Execute: cd frontend && npm run build", 404


@app.route("/app/assets/<path:filename>")
def serve_react_assets(filename):
    return send_from_directory(os.path.join(REACT_DIST, "assets"), filename)

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    is_frozen = getattr(sys, "frozen", False)
    is_server = bool(os.environ.get("FLY_DATA_DIR"))
    debug_mode = not is_frozen and not is_server

    # Inicia thread de sincronização Mercado Phone se habilitada
    if MERCADO_PHONE_SYNC_ENABLED and MERCADO_PHONE_API_TOKEN:
        sync_thread = threading.Thread(
            target=loop_sincronizacao_mercado_phone,
            args=(conectar, MERCADO_PHONE_RUNTIME_CONFIG, MERCADO_PHONE_HELPERS),
            daemon=True,
        )
        sync_thread.start()

    # Abre navegador automaticamente apenas no modo desktop (não no servidor)
    if not is_server:
        threading.Timer(1.2, lambda: webbrowser.open(f"http://{APP_HOST}:{APP_PORT}")).start()

    # Inicia servidor Flask
    app.run(host=APP_HOST, debug=debug_mode, use_reloader=False, port=APP_PORT)
