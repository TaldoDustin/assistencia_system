"""
IR Flow - Sistema de Gestão de Assistência Técnica
Application main module - Flask app bootstrap, configuration, and core functionality
"""

# ============================================================================
# IMPORTS PADRÃO DA BIBLIOTECA
# ============================================================================
import contextlib
import functools
import hmac
import os
import re
import shutil
import sqlite3
import sys
import threading
import time
import traceback
import uuid
import webbrowser
import weakref
from datetime import UTC, datetime, timedelta

# ============================================================================
# IMPORTS FLASK
# ============================================================================
from flask import Flask, request, redirect, jsonify, flash, url_for, send_from_directory, abort, session, g
from werkzeug.security import check_password_hash, generate_password_hash

# ============================================================================
# IMPORTS DE OBSERVABILIDADE (Sprint Observabilidade)
# ============================================================================
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest, multiprocess

from irflow_logging import configurar_logging, get_logger

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - CORE
# ============================================================================
from irflow_core import (
    GARANTIA_REPARO_DIAS_PADRAO,
    OS_TIPOS_OPCOES,
    PERFIS_OPCOES,
    STATUS_AGUARDANDO_PECA,
    STATUS_CANCELADO,
    STATUS_EM_ANDAMENTO,
    STATUS_FINALIZADO,
    STATUS_OS_OPCOES,
    calcular_faturamento_os,
    calcular_lucro_os,
    coletar_status_opcoes,
    normalizar_busca_texto,
    normalizar_status_os,
    sessao_ainda_ativa,
    status_aberto,
    status_cancelado,
    status_finalizado,
    texto_limpo,
)

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - OS, STORAGE, MERCADOPHONE
# ============================================================================
from irflow_os import (
    adicionar_peca_os_sem_consumir,
    buscar_garantia_reparo,
    buscar_historico_garantia_reparo,
    buscar_linhas_com_garantia_da_os,
    buscar_reparo_ids_da_os,
    carregar_os_com_relacoes,
    consumir_peca_da_os,
    corrigir_garantia_reparo,
    devolver_pecas_da_os,
    extrair_reparo_ids,
    gravar_garantias_reparo,
    modelo_compativel,
    obter_ou_criar_reparo,
    obter_reparos_por_os,
    registrar_movimentacao,
    resolver_garantias_reparo,
    salvar_reparos_os,
    validar_reparo_ids,
    vendedor_valido,
    zerar_garantia_reparo,
)

from fluxoly_audit import registrar_log_auditoria
from fluxoly_tipos_garantia_service import obter_tipo_garantia

from fluxoly_mercadophone import (
    detalhar_os_mercado_phone,
    importar_os_mercado_phone,
    loop_sincronizacao_mercado_phone,
    reimportar_todas_os_mercado_phone,
    reprocessar_todas_os_mercado_phone,
    sincronizar_mercado_phone,
)

from irflow_storage import (
    carregar_configuracoes_integracoes,
    criar_backup,
    enviar_backup_email,
    garantir_pasta_backup_google_drive,
    iniciar_thread_backup_automatico,
    salvar_configuracoes_integracoes,
)

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - BLUEPRINTS E RELATÓRIOS
# ============================================================================
from irflow_blueprints_main import create_main_blueprint
from fluxoly_price_tables import (
    carregar_tabelas_preco as carregar_tabelas_preco_arquivo,
    salvar_tabelas_preco as salvar_tabelas_preco_arquivo,
)
from fluxoly_reference_data import (
    CATEGORIAS_CUSTOS_OPERACIONAIS,
    IPHONE_COLORS,
    IPHONE_MODELS,
    PRODUTOS_CATEGORIAS,
    PRODUTOS_CONDICOES,
    REPAROS_PADRAO,
    TECNICOS,
    VENDEDORES,
    canonicalizar_para_lista,
    extrair_cor_da_descricao_aparelho,
    extrair_modelo_da_descricao_aparelho,
    modelo_para_os,
    nome_reparo_importavel,
    normalizar_imei,
    normalizar_modelo_iphone,
)
from irflow_web import anexar_query_string

from irflow_reports import (
    agrupar_relatorio_custos_operacionais,
    agrupar_relatorio_ir_phones,
    agrupar_relatorio_tecnicos,
    formatar_periodo_relatorio,
    montar_linhas_relatorio_custos_operacionais,
    montar_linhas_relatorio_ir_phones,
    montar_linhas_relatorio_tecnicos,
    montar_pdf_texto,
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
    # Em produção (Fly/Render), usa diretório persistente quando configurado.
    # Em desenvolvimento local, usa o próprio diretório da app.
    SERVER_DATA_DIR = (
        os.environ.get("IR_FLOW_DATA_DIR")
        or os.environ.get("FLY_DATA_DIR")
        or os.environ.get("RENDER_DISK_PATH")
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
BACKGROUND_JOBS_ENABLED = (os.environ.get("IR_FLOW_ENABLE_BACKGROUND_JOBS", "1").strip().lower() not in {"0", "false", "nao", "off"})
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


PUBLIC_BASE_URL = _normalizar_url_publica(os.environ.get("IR_FLOW_PUBLIC_BASE_URL")) or _normalizar_url_publica(VERCEL_URL)
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


# ============================================================================
# BOOTSTRAP FLASK
# ============================================================================
# Configurado antes de qualquer outra coisa poder logar durante o boot.
configurar_logging()
logger = get_logger("app")

# Sentry (Sprint Observabilidade) -- só inicializa com SENTRY_DSN definida.
# Vazia por padrão: usuário ainda não tem conta Sentry, vai criar depois e
# só colar o DSN no Render (mesmo padrão de integração opcional já usado
# pelo Mercado Phone). send_default_pii=False é deliberado -- o sistema
# lida com dado real de cliente (nome, IMEI), não pode vazar em
# breadcrumb/payload de erro. traces_sample_rate=0 -- só captura de erro,
# sem tracing de performance (evita overhead/custo sem necessidade
# confirmada; pode ser revisto depois se fizer sentido). environment reaproveita
# IS_SERVER_RUNTIME (mesma variável usada no resto do arquivo para distinguir
# dev local de produção -- projeto não tem staging). release lê
# RENDER_GIT_COMMIT, injetada automaticamente pelo Render em todo deploy, sem
# exigir nenhuma configuração manual de versionamento.
_sentry_dsn = os.environ.get("SENTRY_DSN", "").strip()
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[FlaskIntegration()],
        send_default_pii=False,
        traces_sample_rate=0,
        environment="production" if IS_SERVER_RUNTIME else "development",
        release=os.environ.get("RENDER_GIT_COMMIT", "dev"),
    )
    logger.info("sentry_inicializado")

try:
    from flask_cors import CORS
except Exception:
    CORS = None
app = Flask(__name__, template_folder=os.path.join(RESOURCE_DIR, "templates"))

# SECURITY_AUDIT_2026-07.md item 3: antes, um deploy sem FLASK_SECRET_KEY configurada
# iniciava silenciosamente com um valor hardcoded e publico ("ir-flow-dev-key"),
# permitindo forjar cookies de sessao. Falha no boot fora de dev local em vez de
# usar esse fallback -- em dev local (sem IR_FLOW_DATA_DIR/RENDER/FLY), o fallback
# continua liberado por conveniencia, documentado em .env.example.
_flask_secret_key_env = os.environ.get("FLASK_SECRET_KEY")
if not _flask_secret_key_env and IS_SERVER_RUNTIME:
    raise RuntimeError(
        "FLASK_SECRET_KEY obrigatoria fora de desenvolvimento local. "
        'Gere uma com: python -c "import secrets; print(secrets.token_hex(32))"'
    )
app.secret_key = _flask_secret_key_env or "ir-flow-dev-key"

# Cookies de sessão: em produção cross-site (Vercel -> Render), o navegador
# exige SameSite=None + Secure para enviar cookie com credentials: include.
if IS_SERVER_RUNTIME:
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_PARTITIONED"] = True
else:
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SESSION_COOKIE_PARTITIONED"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True

# Configuração de CORS para aceitar requisições do frontend.
# Pode ser definido como lista separada por vírgula em IR_FLOW_CORS_ORIGINS.
cors_origins_env = (os.environ.get("IR_FLOW_CORS_ORIGINS") or "").strip()


def _normalizar_origem_cors(valor):
    texto = (valor or "").strip()
    if not texto:
        return ""
    if texto.startswith("http://") or texto.startswith("https://"):
        return texto
    # Em alguns ambientes o VERCEL_URL pode vir sem esquema.
    return f"https://{texto}"


if cors_origins_env:
    cors_origins = [_normalizar_origem_cors(item) for item in cors_origins_env.split(",") if item.strip()]
elif VERCEL_URL:
    cors_origins = [_normalizar_origem_cors(VERCEL_URL)]
else:
    cors_origins = [
        r"https://.*\.vercel\.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

if CORS is not None:
    CORS(
        app,
        resources={r"/api/*": {"origins": cors_origins}},
        supports_credentials=True,
    )


def _origem_permitida_cors(origem):
    if not origem:
        return False

    origem = origem.strip()
    if not origem:
        return False

    for permitido in cors_origins:
        permitido_txt = (permitido or "").strip()
        if not permitido_txt:
            continue

        if permitido_txt == origem:
            return True

        # Suporte simples ao padrao de preview do Vercel.
        if (
            "vercel" in permitido_txt
            and (".*" in permitido_txt or "\\." in permitido_txt)
            and origem.startswith("https://")
            and origem.endswith(".vercel.app")
        ):
            return True

    return False


@app.after_request
def _cors_fallback_headers(response):
    if not request.path.startswith("/api/"):
        return response

    origem = request.headers.get("Origin", "")
    if _origem_permitida_cors(origem):
        response.headers["Access-Control-Allow-Origin"] = origem
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Vary"] = "Origin"

        if request.method == "OPTIONS":
            request_headers = request.headers.get("Access-Control-Request-Headers", "Content-Type, Authorization")
            response.headers["Access-Control-Allow-Headers"] = request_headers
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS"
            response.headers["Access-Control-Max-Age"] = "86400"

    return response


# SECURITY_AUDIT_2026-07.md itens 10 (CSP ausente) e 11 (sem protecao contra
# clickjacking). O build do Vite (frontend/dist) nao usa inline script/style
# no documento -- confirmado em frontend/dist/index.html -- entao script-src
# 'self' nao quebra o /app servido localmente. frame-ancestors 'none' +
# X-Frame-Options: DENY sao redundantes de proposito (CSP para navegadores
# modernos, X-Frame-Options como fallback legado); nenhuma rota deste
# projeto precisa ser incorporada em iframe de terceiros.
_CSP_HEADER_VALUE = (
    "default-src 'self'; "
    "script-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "img-src 'self' data:; "
    "font-src 'self' data:; "
    "connect-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'"
)


@app.after_request
def _security_headers(response):
    response.headers.setdefault("Content-Security-Policy", _CSP_HEADER_VALUE)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


# ============================================================================
# CORRELATION ID + LOG DE ACESSO POR REQUEST (Sprint Observabilidade)
# ============================================================================
# Alfanumérico + hífen, até 64 chars — aceita o formato usual de UUID/ULID.
# Um X-Request-Id de cliente fora desse formato é descartado (gera um novo),
# nunca repassado como veio: evita que um valor hostil (ex. com quebra de
# linha) vaze para dentro da linha de log JSON.
_REQUEST_ID_VALIDO = re.compile(r"^[A-Za-z0-9-]{1,64}$")

# Labels usam request.url_rule.rule (ex. "/api/ordens/<int:os_id>"), nunca
# request.path -- caso contrário cada OS/id vira uma série temporal nova
# (cardinalidade sem limite). Em modo multiprocess (PROMETHEUS_MULTIPROC_DIR
# setada, só acontece dentro do container -- ver Dockerfile/gunicorn.conf.py)
# o prometheus_client detecta a env var por conta própria e faz cada Counter/
# Histogram gravar num arquivo mmap compartilhado por worker; a agregação
# entre workers só acontece na leitura, em /metrics (ver metrics_endpoint).
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total de requisições HTTP recebidas",
    ["method", "route", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Duração das requisições HTTP em segundos",
    ["method", "route"],
)


@app.before_request
def _iniciar_request_id():
    recebido = (request.headers.get("X-Request-Id") or "").strip()
    g.request_id = recebido if _REQUEST_ID_VALIDO.match(recebido) else str(uuid.uuid4())
    g._inicio_request = time.monotonic()


@app.after_request
def _logar_acesso(response):
    response.headers["X-Request-Id"] = getattr(g, "request_id", "") or str(uuid.uuid4())

    duracao_ms = None
    inicio = getattr(g, "_inicio_request", None)
    if inicio is not None:
        duracao_ms = round((time.monotonic() - inicio) * 1000, 2)

    rota = request.url_rule.rule if request.url_rule else request.path
    logger.info(
        "request",
        extra={
            "http_method": request.method,
            "http_route": rota,
            "http_status": response.status_code,
            "duration_ms": duracao_ms,
            "usuario_id": session.get("usuario_id"),
        },
    )

    HTTP_REQUESTS_TOTAL.labels(method=request.method, route=rota, status=response.status_code).inc()
    if duracao_ms is not None:
        HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, route=rota).observe(duracao_ms / 1000)

    return response


# FUNÇÕES AUXILIARES - CARREGAMENTO DE DADOS
# ============================================================================
carregar_tabelas_preco = functools.partial(carregar_tabelas_preco_arquivo, PRICE_TABLES_PATH)
salvar_tabelas_preco = functools.partial(salvar_tabelas_preco_arquivo, PRICE_TABLES_PATH)


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
# LOCKS E FLAGS DE INICIALIZAÇÃO
# ============================================================================
SCHEMA_LOCK = threading.Lock()
SCHEMA_READY = False
SQLITE_TIMEOUT_SECONDS = max(5, int(os.environ.get("IR_FLOW_SQLITE_TIMEOUT_SECONDS", "30")))
SQLITE_BUSY_TIMEOUT_MS = SQLITE_TIMEOUT_SECONDS * 1000


def _configurar_conexao_sqlite(conn, habilitar_wal=False):
    conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA synchronous = NORMAL")
    if habilitar_wal:
        try:
            conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise


# ============================================================================
# FUNÇÕES DE DATABASE
# ============================================================================

# INC-001 (docs/operations/INCIDENTS/INC-001-database-is-locked.md) — instrumentação
# temporária, estritamente observacional (ver critérios C-1 a C-9 no documento do
# incidente), para reproduzir "database is locked" com evidência de runtime, não só
# leitura de código. Desligada por padrão (IR_FLOW_DEBUG_CONN_TRACE=1 para ligar);
# desligada, conectar() se comporta exatamente como antes, sem overhead algum. Vive
# inteiramente dentro de conectar() (C-9) — nenhuma rota precisa saber que ela existe,
# e removê-la não exige tocar em nenhuma rota. Remover assim que a causa raiz for
# confirmada.
_CONN_TRACE_ATIVO = os.environ.get("IR_FLOW_DEBUG_CONN_TRACE") == "1"
_conn_trace_lock = threading.Lock()
_conn_trace_contador = 0


def _proximo_conn_trace_id():
    global _conn_trace_contador
    with _conn_trace_lock:
        _conn_trace_contador += 1
        return _conn_trace_contador


def _conn_trace_rota_atual():
    try:
        if request:
            return f"{request.method} {request.path}"
    except RuntimeError:
        pass
    return threading.current_thread().name


class _ConexaoRastreada:
    """Envolve uma sqlite3.Connection real e loga OPEN/COMMIT/ROLLBACK/CLOSE (INC-001)
    via o logger estruturado já existente (irflow_logging.py, extra={...} -- nunca
    print() nem um pipeline de log paralelo).

    Transparente por requisito (C-2/C-9): qualquer atributo ou método não
    explicitamente instrumentado aqui (cursor(), execute(), row_factory, etc.) é
    delegado à conexão real via __getattr__/__setattr__ -- este objeto deve se
    comportar de forma indistinguível de um sqlite3.Connection normal para quem o
    usa, inclusive para código futuro ainda não escrito hoje.
    """

    def __init__(self, conn_real):
        self._conn = conn_real
        self._id = _proximo_conn_trace_id()
        self._rota = _conn_trace_rota_atual()
        self._thread_name = threading.current_thread().name
        self._thread_ident = threading.get_ident()
        self._abertura_monotonic = time.monotonic()
        self._aberta_em = datetime.now(UTC).isoformat()

        # Últimos 5 frames antes desta chamada -- suficiente para identificar quem
        # abriu a conexão sem despejar a stack inteira do processo no log.
        stack_resumida = "".join(traceback.format_stack()[:-1][-5:])
        conn_id, rota, thread_name, thread_ident = self._id, self._rota, self._thread_name, self._thread_ident

        def _ao_coletar(_ref, conn_id=conn_id, rota=rota, thread_name=thread_name, thread_ident=thread_ident, stack=stack_resumida):
            logger.warning(
                "INC-001: conexão coletada pelo GC sem close() explícito",
                extra={
                    "inc001_connection_id": conn_id,
                    "inc001_route": rota,
                    "inc001_thread_name": thread_name,
                    "inc001_thread_ident": thread_ident,
                    "inc001_close_called": False,
                    "inc001_stack": stack,
                },
            )

        self._finalizer = weakref.finalize(self, _ao_coletar, None)

        logger.info(
            "INC-001: conexão aberta",
            extra={
                "inc001_connection_id": self._id,
                "inc001_route": self._rota,
                "inc001_thread_name": self._thread_name,
                "inc001_thread_ident": self._thread_ident,
                "inc001_opened_at": self._aberta_em,
            },
        )

    def commit(self):
        self._conn.commit()
        logger.info(
            "INC-001: conexão commit",
            extra={
                "inc001_connection_id": self._id,
                "inc001_route": self._rota,
                "inc001_thread_name": self._thread_name,
            },
        )

    def rollback(self):
        self._conn.rollback()
        logger.info(
            "INC-001: conexão rollback",
            extra={
                "inc001_connection_id": self._id,
                "inc001_route": self._rota,
                "inc001_thread_name": self._thread_name,
            },
        )

    def close(self):
        # Cancela o finalizer antes de fechar -- close() explícito não deve gerar o
        # aviso de vazamento reservado para a coleta pelo GC.
        self._finalizer.detach()
        self._conn.close()
        elapsed_ms = (time.monotonic() - self._abertura_monotonic) * 1000
        logger.info(
            "INC-001: conexão fechada",
            extra={
                "inc001_connection_id": self._id,
                "inc001_route": self._rota,
                "inc001_thread_name": self._thread_name,
                "inc001_thread_ident": self._thread_ident,
                "inc001_opened_at": self._aberta_em,
                "inc001_closed_at": datetime.now(UTC).isoformat(),
                "inc001_elapsed_ms": round(elapsed_ms, 3),
                "inc001_close_called": True,
            },
        )

    def __getattr__(self, nome):
        # Só chamado quando o atributo não existe nesta classe (isto é, não é um
        # dos métodos instrumentados acima) -- delega à conexão real.
        return getattr(self._conn, nome)

    def __setattr__(self, nome, valor):
        if nome in ("_conn", "_id", "_rota", "_thread_name", "_thread_ident", "_abertura_monotonic", "_aberta_em", "_finalizer"):
            object.__setattr__(self, nome, valor)
        else:
            setattr(self._conn, nome, valor)


def conectar():
    """Cria conexão com banco de dados e garante schema."""
    criar_tabelas()
    conn = sqlite3.connect(DB_PATH, timeout=SQLITE_TIMEOUT_SECONDS)
    _configurar_conexao_sqlite(conn)
    if _CONN_TRACE_ATIVO:
        return _ConexaoRastreada(conn)
    return conn


def criar_tabelas():
    """Cria tabelas do schema se não existirem."""
    global SCHEMA_READY

    if SCHEMA_READY:
        return

    with SCHEMA_LOCK:
        if SCHEMA_READY:
            return

        conn = sqlite3.connect(DB_PATH, timeout=SQLITE_TIMEOUT_SECONDS)
        _configurar_conexao_sqlite(conn, habilitar_wal=True)
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
                data_compra TEXT,
                sku TEXT,
                modelo TEXT,
                tipo TEXT,
                qualidade TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS estoque_lotes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estoque_id INTEGER NOT NULL,
                fornecedor TEXT,
                valor_compra REAL,
                quantidade INTEGER,
                quantidade_disponivel INTEGER,
                data_compra TEXT,
                observacoes TEXT,
                criado_em TEXT
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
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto TEXT NOT NULL,
                os_id INTEGER,
                quantidade INTEGER NOT NULL DEFAULT 1,
                status TEXT DEFAULT 'PENDENTE',
                criado_em TEXT DEFAULT '',
                atualizado_em TEXT DEFAULT ''
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

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS os_checklists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                os_id INTEGER NOT NULL UNIQUE,
                access_token TEXT UNIQUE,
                status_touch TEXT NOT NULL DEFAULT 'nao_testado',
                status_audio TEXT NOT NULL DEFAULT 'nao_testado',
                status_microfone TEXT NOT NULL DEFAULT 'nao_testado',
                status_camera TEXT NOT NULL DEFAULT 'nao_testado',
                status_botoes TEXT NOT NULL DEFAULT 'nao_testado',
                observacoes TEXT NOT NULL DEFAULT '',
                executado_por TEXT NOT NULL DEFAULT '',
                origem TEXT NOT NULL DEFAULT '',
                resultado_json TEXT NOT NULL DEFAULT '{}',
                criado_em TEXT NOT NULL DEFAULT '',
                atualizado_em TEXT NOT NULL DEFAULT ''
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identificador TEXT NOT NULL,
                sucesso INTEGER NOT NULL,
                criado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """)

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_login_attempts_identificador_criado_em
                ON login_attempts (identificador, criado_em)
                """
            )

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entidade TEXT NOT NULL,
                entidade_id INTEGER,
                usuario_id INTEGER,
                acao TEXT NOT NULL,
                valor_anterior TEXT,
                valor_novo TEXT,
                criado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """)

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_log_entidade
                ON audit_log (entidade, entidade_id)
                """
            )

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                criado_em TEXT NOT NULL DEFAULT (datetime('now')),
                expira_em TEXT NOT NULL,
                usado_em TEXT,
                criado_por INTEGER
            )
            """)

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_usuario_id
                ON password_reset_tokens (usuario_id)
                """
            )

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                telefone TEXT,
                email TEXT,
                cpf_cnpj TEXT,
                observacoes TEXT NOT NULL DEFAULT '',
                criado_em TEXT NOT NULL DEFAULT (datetime('now')),
                atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_telefone ON clientes (telefone)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_cpf_cnpj ON clientes (cpf_cnpj)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes (nome)")

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS unidades_serializadas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estoque_id INTEGER,
                produto_id INTEGER,
                lote_id INTEGER,
                imei TEXT UNIQUE,
                status TEXT NOT NULL DEFAULT 'disponivel',
                reservado_por INTEGER,
                reservado_ate TEXT,
                venda_id INTEGER,
                saude_bateria TEXT,
                localizacao TEXT,
                criado_em TEXT NOT NULL DEFAULT (datetime('now')),
                atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """)

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_estoque_id ON unidades_serializadas (estoque_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_produto_id ON unidades_serializadas (produto_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_status ON unidades_serializadas (status)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_imei ON unidades_serializadas (imei)"
            )

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                categoria TEXT NOT NULL,
                marca TEXT,
                modelo TEXT,
                cor TEXT,
                capacidade TEXT,
                condicao TEXT NOT NULL DEFAULT 'Novo',
                descricao TEXT,
                sku TEXT,
                fornecedor TEXT,
                preco_custo REAL,
                preco_venda REAL NOT NULL,
                quantidade INTEGER NOT NULL DEFAULT 0,
                requer_rastreio_unidade INTEGER NOT NULL DEFAULT 0,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL DEFAULT (datetime('now')),
                atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """)

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos (categoria)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_sku ON produtos (sku)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_ativo ON produtos (ativo)")

            # Vendas MVP (docs/product/features/VENDAS.md) — fluxo básico: cliente + aparelho
            # (unidade serializada) + pagamento simples, sem desconto/comissão/garantia/troca
            # (dependem de decisões de negócio ainda pendentes do Product Owner, ver VENDAS.md
            # "O que ainda está em aberto"). status='concluida' é deliberadamente distinto de um
            # futuro conceito de status de pagamento (pago/pendente/estornado) — venda e
            # pagamento são conceitos diferentes, não misturados aqui.
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                vendedor_id INTEGER NOT NULL,
                forma_pagamento TEXT NOT NULL,
                valor_total REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'concluida',
                observacoes TEXT NOT NULL DEFAULT '',
                criado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_cliente_id ON vendas (cliente_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_vendedor_id ON vendas (vendedor_id)")

            # produto_nome/produto_sku/valor_tabela são snapshot no momento da venda (não
            # FK viva) -- preserva o histórico mesmo se o cadastro de produto/estoque mudar
            # depois, mesmo padrão já usado em os_pecas.peca_descricao/peca_fornecedor/
            # peca_modelo. valor_tabela é o preço de catálogo no momento (nullable -- item
            # pode não ter preço cadastrado); valor_unitario é o preço efetivo da venda,
            # pode divergir de valor_tabela (negociação) -- nunca um sobrescreve o outro.
            # unidade_serializada_id é UNIQUE: nunca a mesma unidade em duas vendas -- o
            # verdadeiro guardião contra a corrida de duas vendas simultâneas do mesmo
            # aparelho, no nível do banco, não só na validação da aplicação.
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS vendas_itens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                venda_id INTEGER NOT NULL,
                unidade_serializada_id INTEGER NOT NULL,
                produto_id INTEGER,
                produto_nome TEXT NOT NULL,
                produto_sku TEXT,
                quantidade INTEGER NOT NULL DEFAULT 1,
                valor_tabela REAL,
                valor_unitario REAL NOT NULL,
                subtotal REAL NOT NULL,
                criado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vendas_itens_venda_id ON vendas_itens (venda_id)")

            # V1.2 -- Cancelamento (BR-031 a BR-036, VENDAS.md "V1.2 -- Cancelamento"): cancelar uma
            # venda é evento comercial, terminal, sem efeito financeiro (estornada fica para o Épico
            # Financeiro). motivo_cancelamento é lista fechada validada no service, nunca normalizada.
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas ADD COLUMN motivo_cancelamento TEXT")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas ADD COLUMN observacao_cancelamento TEXT")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas ADD COLUMN cancelado_por INTEGER")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas ADD COLUMN cancelado_em TEXT")

            # ativo distingue a venda vigente de uma unidade das suas vendas canceladas no
            # histórico -- permite revenda da mesma unidade_serializada_id sem violar o índice
            # único (BR-033). DEFAULT 1 já backfila as linhas existentes corretamente: toda
            # vendas_itens hoje é uma venda vigente.
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas_itens ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")

            # Substitui o UNIQUE incondicional por um parcial -- só uma linha "ativa" por unidade,
            # não uma por vida inteira. DROP+CREATE é seguro (índice, não dado) e idempotente.
            cursor.execute("DROP INDEX IF EXISTS idx_vendas_itens_unidade_serializada_id")
            cursor.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_vendas_itens_unidade_ativa "
                "ON vendas_itens (unidade_serializada_id) WHERE ativo = 1"
            )

            # V1.3 -- Descontos e Aprovação (BR-037 a BR-043, VENDAS.md "V1.3 -- Descontos e
            # Aprovação"). Três colunas aditivas, nenhuma tabela nova.
            #
            # limite_desconto_livre: DEPRECADA (2026-07-29, ver VENDAS.md "Revisão do modelo de
            # desconto"). Existiu para BR-037 (limite de desconto sem aprovação, individual por
            # usuário) -- revogada um dia depois de implementada por não refletir o fluxo real de
            # negociação da loja (a venda nunca deveria ter sido bloqueada). Mantida só por
            # compatibilidade histórica com usuários configurados durante a V1.3; nenhum fluxo a
            # partir de 2026-07-29 lê ou escreve esta coluna.
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE usuarios ADD COLUMN limite_desconto_livre REAL")

            # motivo_desconto: opcional, texto livre (BR-039) -- deliberadamente diferente do
            # motivo_cancelamento (lista fechada obrigatória, BR-032). Vive no item, não na
            # venda, porque valor_tabela/valor_unitario já vivem no item. Continua em uso --
            # não afetada pela revisão de 2026-07-29.
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas_itens ADD COLUMN motivo_desconto TEXT DEFAULT ''")

            # desconto_aprovado_em: DEPRECADA (2026-07-29, ver VENDAS.md "Revisão do modelo de
            # desconto"). Existiu para BR-038 (timestamp de aprovação de desconto acima do
            # limite) -- revogada junto de limite_desconto_livre pelo mesmo motivo. Mantida só
            # por compatibilidade histórica com vendas já feitas na V1.3; nenhum fluxo a partir de
            # 2026-07-29 escreve nesta coluna (permanece sempre NULL para vendas novas).
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas_itens ADD COLUMN desconto_aprovado_em TEXT")

            # V1.4 -- Comissão (BR-044 a BR-052, VENDAS.md "V1.4 -- Comissão"). Uma coluna
            # aditiva. `comissao_valor`: atribuído manualmente por admin/financeiro, em R$.
            # NULL = "ainda não atribuída" -- nunca confundir com atribuída como zero. Sem
            # campo de "tipo" (fixo/percentual, BR-048): o valor final é sempre o que é
            # gravado, independente de como financeiro chegou nele mentalmente -- é isso que
            # permite a mesma estrutura suportar qualquer política de comissão da loja.
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas_itens ADD COLUMN comissao_valor REAL")

            # V1.5 -- Garantia (BR-055 a BR-066, VENDAS.md "V1.5 -- Garantia"). Cadastro de
            # política (Tipo de Garantia) separado da instância concedida (Garantia) -- nunca
            # confundir os dois no código. `ativo` permite ao admin aposentar uma política sem
            # apagá-la; nunca afeta garantias já concedidas, que são snapshot (colunas abaixo).
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tipos_garantia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                duracao_meses INTEGER NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL DEFAULT (datetime('now')),
                atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """)

            # Garantia de Venda (BR-056/BR-057): atribuída manualmente por item, na criação da
            # venda -- sem default vindo do produto. Snapshot completo (id do tipo, nome,
            # duração, datas) para que uma edição futura em `tipos_garantia` nunca altere uma
            # garantia já concedida. Nullable no schema (compatibilidade com linhas já
            # existentes) -- a obrigatoriedade de BR-056 é imposta pelo service, nunca pelo
            # schema, mesmo padrão já usado no resto do domínio Vendas. Sem FOREIGN KEY real em
            # `tipo_garantia_id`, mesmo padrão do resto do schema (FK lógica).
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas_itens ADD COLUMN tipo_garantia_id INTEGER")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas_itens ADD COLUMN garantia_nome TEXT")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas_itens ADD COLUMN garantia_duracao_meses INTEGER")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas_itens ADD COLUMN garantia_data_inicio TEXT")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE vendas_itens ADD COLUMN garantia_data_fim TEXT")

            # Garantia de Reparo (BR-061 a BR-063): mesmo conjunto de colunas, mas por linha de
            # reparo (`os_reparos`), não por OS inteira -- uma OS com reparos diferentes pode ter
            # garantias diferentes, cada linha mantém a sua (BR-062). Atribuída na conclusão da
            # OS (`Finalizado`), não na criação -- substitui o prazo fixo de 90 dias hardcoded
            # (`GARANTIA_REPARO_DIAS_PADRAO`, mantida só como fallback para dados históricos sem
            # `tipo_garantia_id`, ver `listar_garantias`).
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os_reparos ADD COLUMN tipo_garantia_id INTEGER")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os_reparos ADD COLUMN garantia_nome TEXT")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os_reparos ADD COLUMN garantia_duracao_meses INTEGER")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os_reparos ADD COLUMN garantia_data_inicio TEXT")
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os_reparos ADD COLUMN garantia_data_fim TEXT")

            # Add valor column if it doesn't exist
            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os_pecas ADD COLUMN valor REAL")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os_pecas ADD COLUMN peca_descricao TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os_pecas ADD COLUMN peca_fornecedor TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os_pecas ADD COLUMN peca_modelo TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os ADD COLUMN data_finalizado TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os ADD COLUMN modelo TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os ADD COLUMN cor TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os ADD COLUMN imei TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os ADD COLUMN vendedor TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os ADD COLUMN observacoes TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os ADD COLUMN origem_integracao TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE os ADD COLUMN id_externo_integracao TEXT")

            # INC-002 (docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md): sem
            # essa restricao, duas OS podiam ser importadas com o mesmo id_externo_integracao
            # (achado: sync do Mercado Phone rodando em mais de um worker do Gunicorn ao mesmo
            # tempo, sem coordenacao). O lock cross-processo (fluxoly_mercadophone.py) corrige o
            # mecanismo mais provavel do bug; este indice e a garantia definitiva no banco,
            # valendo contra qualquer outro caminho futuro de escrita (bug humano, script,
            # nova integracao). SQLite trata cada NULL como distinto em indices UNIQUE, entao
            # OS nativas (origem_integracao/id_externo_integracao ambos NULL) nao sao afetadas.
            cursor.execute(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS idx_os_origem_id_externo
                ON os (origem_integracao, id_externo_integracao)
                """
            )

            with contextlib.suppress(sqlite3.OperationalError):
                # Aditiva, nullable, sem backfill (CLIENTES.md) -- OS existentes
                # continuam com `cliente` (texto) e nada mais.
                cursor.execute("ALTER TABLE os ADD COLUMN cliente_id INTEGER")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE estoque ADD COLUMN modelo TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE estoque ADD COLUMN sku TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE estoque ADD COLUMN tipo TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                cursor.execute("ALTER TABLE estoque ADD COLUMN qualidade TEXT")

            with contextlib.suppress(sqlite3.OperationalError):
                # Flag manual (admin) -- nem todo item de estoque precisa de
                # unidade individual por IMEI (peca de reparo continua agregada).
                cursor.execute("ALTER TABLE estoque ADD COLUMN requer_imei INTEGER NOT NULL DEFAULT 0")

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_estoque_sku
                ON estoque (sku)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_estoque_tripla
                ON estoque (modelo, tipo, qualidade)
                """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_lotes_estoque_id
                ON estoque_lotes (estoque_id)
                """
            )

            conn.commit()

            cursor.execute("SELECT id, modelo FROM estoque")
            for item_id, modelo_atual in cursor.fetchall():
                modelo_norm = normalizar_modelo_iphone(modelo_atual)
                if modelo_norm != (modelo_atual or ""):
                    cursor.execute("UPDATE estoque SET modelo=? WHERE id=?", (modelo_norm, item_id))

            cursor.execute("SELECT id, COALESCE(sku, '') FROM estoque")
            for item_id, sku_atual in cursor.fetchall():
                if not (sku_atual or "").strip():
                    cursor.execute("UPDATE estoque SET sku=? WHERE id=?", (f"ITEM-{item_id}", item_id))

            cursor.execute(
                """
                INSERT INTO estoque_lotes (
                    estoque_id, fornecedor, valor_compra, quantidade, quantidade_disponivel, data_compra, observacoes, criado_em
                )
                SELECT
                    e.id,
                    COALESCE(e.fornecedor, 'Nao informado'),
                    COALESCE(e.valor, 0),
                    COALESCE(e.quantidade, 0),
                    COALESCE(e.quantidade, 0),
                    COALESCE(e.data_compra, ''),
                    'lote inicial legado',
                    datetime('now')
                FROM estoque e
                WHERE NOT EXISTS (
                    SELECT 1 FROM estoque_lotes l WHERE l.estoque_id = e.id
                )
                AND COALESCE(e.quantidade, 0) > 0
                """
            )

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

            # Shopping list tables
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_list (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                os_id INTEGER,
                produto_id INTEGER,
                produto_nome TEXT,
                quantidade_solicitada INTEGER NOT NULL DEFAULT 1,
                quantidade_comprada INTEGER NOT NULL DEFAULT 0,
                quantidade_recebida INTEGER NOT NULL DEFAULT 0,
                prioridade TEXT DEFAULT 'NORMAL',
                status TEXT DEFAULT 'PENDENTE',
                responsavel_id INTEGER,
                observacao TEXT DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now')),
                purchased_at TEXT,
                received_at TEXT,
                cancelled_at TEXT
            )
            """)

            cursor.execute("""
            CREATE TABLE IF NOT EXISTS shopping_list_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shopping_list_id INTEGER NOT NULL,
                usuario_id INTEGER,
                acao TEXT NOT NULL,
                valor_anterior TEXT,
                valor_novo TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """)

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_shopping_list_os_produto
                ON shopping_list (os_id, produto_id, produto_nome)
                """
            )

            conn.commit()
            SCHEMA_READY = True
        except sqlite3.OperationalError as exc:
            if "locked" in str(exc).lower():
                # Outro worker pode estar aplicando o schema neste instante.
                return
            raise
        finally:
            conn.close()


def forcar_migracao_schema():
    """Reexecuta migrações de schema no banco atual (útil após restore de arquivo legado)."""
    global SCHEMA_READY
    SCHEMA_READY = False
    criar_tabelas()


criar_tabelas()
if BACKGROUND_JOBS_ENABLED:
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
    try:
        # Verifica se já existe um usuário com o nome 'admin'
        cursor.execute("SELECT 1 FROM usuarios WHERE usuario = ?", ("admin",))
        if cursor.fetchone() is None:
            cursor.execute(
                "INSERT INTO usuarios (nome, usuario, senha_hash, perfil) VALUES (?, ?, ?, ?)",
                ("Administrador", "admin", generate_password_hash("irflow@2024"), "admin"),
            )
            conn.commit()
    except Exception as exc:
        # Loga o erro mas não interrompe o boot
        logger.warning("criar_admin_padrao_falhou", extra={"erro": str(exc)})
    finally:
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
    "canonicalizar_para_lista": canonicalizar_para_lista,
    "tecnicos": TECNICOS,
    "vendedores": VENDEDORES,
}

# ============================================================================
# ENDPOINTS - INTEGRAÇÃO MERCADO PHONE
# ============================================================================


def autenticar_integracao_mercado_phone():
    """Valida token de autenticação do webhook Mercado Phone.

    Sem MERCADO_PHONE_WEBHOOK_TOKEN configurado, nenhum candidato pode
    corresponder — a rota fica bloqueada por padrão (fail secure) em vez de
    aberta sem autenticação.
    """

    def _mascarar_token(valor):
        texto = texto_limpo(valor)
        if not texto:
            return "<vazio>"
        if len(texto) <= 8:
            return "*" * len(texto)
        return f"{texto[:4]}...{texto[-4:]} (len={len(texto)})"

    auth_header = texto_limpo(request.headers.get("Authorization"))
    token_header = texto_limpo(request.headers.get("X-Webhook-Token"))
    payload = request.get_json(silent=True)

    candidatos = []

    if token_header:
        candidatos.append(token_header)

    # Alguns provedores enviam em headers alternativos.
    for header_name in ("X-Api-Key", "X-Auth-Token", "X-Token", "Mp-Auth-Code"):
        valor = texto_limpo(request.headers.get(header_name))
        if valor:
            candidatos.append(valor)

    if auth_header:
        if auth_header.lower().startswith("bearer "):
            candidatos.append(auth_header[7:].strip())
        else:
            candidatos.append(auth_header.strip())

    for query_name in ("token", "webhook_token", "security_token"):
        valor = texto_limpo(request.args.get(query_name))
        if valor:
            candidatos.append(valor)

    if isinstance(payload, dict):
        for body_key in ("token", "webhook_token", "security_token"):
            valor = texto_limpo(payload.get(body_key))
            if valor:
                candidatos.append(valor)

    for form_key in ("token", "webhook_token", "security_token"):
        valor = texto_limpo(request.form.get(form_key))
        if valor:
            candidatos.append(valor)

    autenticado = any(hmac.compare_digest(MERCADO_PHONE_WEBHOOK_TOKEN, candidato) for candidato in candidatos)
    if not autenticado:
        logger.warning(
            "mercadophone_webhook_token_invalido",
            extra={
                "esperado": _mascarar_token(MERCADO_PHONE_WEBHOOK_TOKEN),
                "candidatos": [_mascarar_token(c) for c in candidatos],
                "headers": sorted(request.headers.keys()),
                "query_keys": sorted(request.args.keys()),
            },
        )
        abort(401)


@app.route("/api/integracoes/mercadophone/os", methods=["POST"])
def receber_os_mercado_phone():
    """Recebe OS do Mercado Phone via webhook."""
    autenticar_integracao_mercado_phone()

    payload = request.get_json(silent=True) or {}
    payload_evento = payload if isinstance(payload, dict) else {}
    if isinstance(payload_evento, dict) and isinstance(payload_evento.get("ordem_servico"), dict):
        payload = payload_evento["ordem_servico"]

    external_id = ""
    if isinstance(payload, dict):
        external_id = texto_limpo(
            payload.get("codigo")
            or payload.get("id")
            or payload.get("id_externo")
            or payload.get("os_id")
            or payload.get("ordem_servico_id")
        )
    if not external_id and isinstance(payload_evento, dict):
        external_id = texto_limpo(
            payload_evento.get("codigo")
            or payload_evento.get("id")
            or payload_evento.get("id_externo")
            or payload_evento.get("os_id")
            or payload_evento.get("ordem_servico_id")
            or payload_evento.get("ordem_servico", {}).get("id")
            or payload_evento.get("ordem_servico", {}).get("codigo")
        )

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
        # Alguns webhooks de edição vêm com payload parcial (apenas id/status).
        # Nesses casos, busca o detalhe por ID para salvar corretamente no IR Flow.
        if (
            external_id
            and "dados suficientes" in str(exc).lower()
            and texto_limpo(MERCADO_PHONE_RUNTIME_CONFIG.get("api_token"))
        ):
            try:
                detalhes = detalhar_os_mercado_phone(external_id, MERCADO_PHONE_RUNTIME_CONFIG)
                payload_detalhado = detalhes.get("data") if isinstance(detalhes, dict) else None
                if isinstance(payload_detalhado, dict):
                    resultado = importar_os_mercado_phone(
                        cursor,
                        payload_detalhado,
                        MERCADO_PHONE_RUNTIME_CONFIG,
                        MERCADO_PHONE_HELPERS,
                        fallback_external_id=external_id,
                    )
                    conn.commit()
                    status_code = 200 if resultado["duplicada"] else 201
                    return jsonify(
                        {
                            "ok": True,
                            "duplicada": resultado["duplicada"],
                            "os_id": resultado["os_id"],
                            "fallback_por_id": True,
                        }
                    ), status_code
            except Exception:
                pass

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
    for _item_id, descricao, quantidade in cursor.fetchall():
        qtd = quantidade or 0
        status_txt = "sem estoque" if qtd == 0 else f"{qtd} unid."
        alerts.append(
            {
                "nivel": "critico" if qtd == 0 else "atencao",
                "titulo": "Estoque baixo",
                "mensagem": f"{descricao or 'Peca'} ({status_txt})",
                "link": "/app/estoque",
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
    for os_id, cliente, _modelo, status, data_os in cursor.fetchall():
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
                    "link": "/app/ordens",
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
    for os_id, cliente, _modelo, data_finalizado, data_os, status in cursor.fetchall():
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
        }
    )
)

# ============================================================================
# AUTENTICAÇÃO — PERMISSÕES E BEFORE_REQUEST
# ============================================================================

# Perfis disponíveis: admin, tecnico, vendedor
# None = qualquer perfil logado
# Sentinel usado só para distinguir "endpoint não cadastrado aqui" (nega por
# padrão) de "cadastrado com valor None" (qualquer perfil logado) — ver uso em
# verificar_autenticacao().
_ENDPOINT_SEM_ENTRADA = object()

ROUTE_PERMISSIONS: dict[str, list[str] | None] = {
    # Acesso livre (não requer login)
    "auth_views.login": [],
    "auth_views.logout": [],
    "static": [],
    # Qualquer usuário logado
    "main_views.index": None,
    "main_views.kanban": None,
    "main_views.garantias": None,
    # Somente admin
    "main_views.relatorios": ["admin"],
    "main_views.backup": ["admin"],
    "main_views.backup_download": ["admin"],
    "main_views.relatorio_pdf_ir_phones": ["admin"],
    "main_views.relatorio_pdf_tecnicos": ["admin"],
    # Webhook (autenticação própria por token)
    "receber_os_mercado_phone": [],
}


LEGACY_REACT_REDIRECTS = {
    "/": "/app",
    "/dashboard": "/app",
    "/dashboard/": "/app",
    "/dashboard.html": "/app",
    "/index": "/app",
    "/index.html": "/app",
    "/login": "/app/login",
    "/ordens": "/app/ordens",
    "/nova": "/app/ordens/nova",
    "/kanban": "/app/kanban",
    "/garantias": "/app/garantias",
    "/estoque": "/app/estoque",
    "/estoque/cadastro": "/app/estoque",
    "/reparos": "/app/reparos",
    "/tabelas-preco": "/app/precos",
    "/custos-operacionais": "/app/custos",
    "/relatorios": "/app/relatorios",
    "/backup": "/app/backup",
    "/usuarios": "/app/usuarios",
}


def destino_react_legado(path: str) -> str | None:
    if path in LEGACY_REACT_REDIRECTS:
        return LEGACY_REACT_REDIRECTS[path]

    if path.startswith("/editar/"):
        os_id = path.removeprefix("/editar/").strip("/")
        if os_id.isdigit():
            return f"/app/ordens/editar/{os_id}"

    return None


@app.before_request
def verificar_autenticacao():
    endpoint = request.endpoint
    if request.method in ("GET", "HEAD"):
        destino_react = destino_react_legado(request.path)
        if destino_react:
            return redirect(anexar_query_string(destino_react, request.query_string))

    if not endpoint:
        return

    # Rotas estáticas e API — autenticação gerenciada pela própria API
    # "health_check"/"ready_check"/"metrics_endpoint": probes de infraestrutura
    # (Render, Prometheus) não autenticam — Sprint Observabilidade.
    if endpoint in (
        "static",
        "serve_react",
        "serve_react_assets",
        "health_check",
        "ready_check",
        "metrics_endpoint",
    ):
        return

    # Expiração de sessão por inatividade — roda para TODA rota autenticada,
    # inclusive /api/*, já que este before_request dispara antes do bypass
    # abaixo. Limpar a sessão aqui é suficiente para /api/* também: o
    # usuario_logado() de irflow_blueprints_api.py checa session["usuario_id"],
    # que já estará vazio quando a view rodar.
    if session.get("usuario_id") and not sessao_ainda_ativa(session):
        session.clear()

    # Bypass por path (não só pelo blueprint "api.") — cobre também blueprints
    # de domínio novos sob /api/* (ex.: clientes_api, unidades_serializadas_api),
    # que autenticam via usuario_logado() dentro de si mesmos, igual à API
    # principal. Checar o path em vez do nome do blueprint evita ter que
    # atualizar esta lista a cada novo domínio adicionado sob /api/*.
    if endpoint and endpoint.startswith("api."):
        return
    if request.path.startswith("/api/"):
        return

    perms = ROUTE_PERMISSIONS.get(endpoint, _ENDPOINT_SEM_ENTRADA)
    if perms is _ENDPOINT_SEM_ENTRADA:
        # Endpoint legado sem entrada em ROUTE_PERMISSIONS — nega por padrão
        # (fail secure) em vez de liberar para qualquer usuário logado, que é
        # o que `None` (chave presente) significa nesta tabela.
        flash("Você não tem permissão para acessar esta página.", "danger")
        return redirect("/app")
    if perms == []:
        # Acesso livre
        return

    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return redirect("/app/login")

    perfil = session.get("usuario_perfil", "")
    if perms is not None and perfil not in perms:
        flash("Você não tem permissão para acessar esta página.", "danger")
        return redirect("/app")


# ============================================================================
# REGISTRO DO BLUEPRINT DE AUTENTICAÇÃO
# ============================================================================

from irflow_blueprints_auth import create_auth_blueprint  # noqa: E402
from irflow_blueprints_api import create_api_blueprint  # noqa: E402
from irflow_rate_limit import resolver_ip_cliente, limite_excedido, registrar_tentativa  # noqa: E402

app.register_blueprint(
    create_auth_blueprint(
        {
            "conectar": conectar,
            "generate_password_hash": generate_password_hash,
            "check_password_hash": check_password_hash,
            "resolver_ip_cliente": resolver_ip_cliente,
            "limite_excedido": limite_excedido,
            "registrar_tentativa": registrar_tentativa,
            "perfis_opcoes": PERFIS_OPCOES,
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
            "buscar_reparo_ids_da_os": buscar_reparo_ids_da_os,
            "resolver_garantias_reparo": resolver_garantias_reparo,
            "gravar_garantias_reparo": gravar_garantias_reparo,
            "buscar_linhas_com_garantia_da_os": buscar_linhas_com_garantia_da_os,
            "zerar_garantia_reparo": zerar_garantia_reparo,
            "buscar_garantia_reparo": buscar_garantia_reparo,
            "corrigir_garantia_reparo": corrigir_garantia_reparo,
            "buscar_historico_garantia_reparo": buscar_historico_garantia_reparo,
            "obter_tipo_garantia": obter_tipo_garantia,
            "registrar_log_auditoria": registrar_log_auditoria,
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
            "agrupar_relatorio_custos_operacionais": functools.partial(agrupar_relatorio_custos_operacionais, conectar=conectar),
            "agrupar_relatorio_ir_phones": functools.partial(agrupar_relatorio_ir_phones, conectar=conectar),
            "agrupar_relatorio_tecnicos": functools.partial(agrupar_relatorio_tecnicos, conectar=conectar),
            "montar_linhas_relatorio_custos_operacionais": functools.partial(montar_linhas_relatorio_custos_operacionais, conectar=conectar),
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
            "os_tipos_opcoes": OS_TIPOS_OPCOES,
            "garantia_reparo_dias_padrao": GARANTIA_REPARO_DIAS_PADRAO,
            "perfis_opcoes": PERFIS_OPCOES,
            "categorias_custos": CATEGORIAS_CUSTOS_OPERACIONAIS,
            "reparos_padrao": REPAROS_PADRAO,
            "produtos_categorias": PRODUTOS_CATEGORIAS,
            "produtos_condicoes": PRODUTOS_CONDICOES,
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
            "resolver_ip_cliente": resolver_ip_cliente,
            "limite_excedido": limite_excedido,
            "registrar_tentativa": registrar_tentativa,
            "sincronizar_mercado_phone": sincronizar_mercado_phone,
            "reimportar_todas_os_mercado_phone": reimportar_todas_os_mercado_phone,
            "reprocessar_todas_os_mercado_phone": reprocessar_todas_os_mercado_phone,
            "mercado_phone_runtime_config": MERCADO_PHONE_RUNTIME_CONFIG,
            "mercado_phone_helpers": MERCADO_PHONE_HELPERS,
            "public_base_url": PUBLIC_BASE_URL,
            "integrations_config_path": INTEGRATIONS_CONFIG_PATH,
            "carregar_configuracoes_integracoes": carregar_configuracoes_integracoes,
            "salvar_configuracoes_integracoes": salvar_configuracoes_integracoes,
            "db_path": DB_PATH,
            "forcar_migracao_schema": forcar_migracao_schema,
        }
    )
)

# ============================================================================
# REGISTRO DO BLUEPRINT DE CLIENTES (Sprint P0.1 — primeiro domínio a seguir
# a convenção controller/service/repository de ENGINEERING_GUIDE.md §3.1)
# ============================================================================

from fluxoly_clientes_controller import create_clientes_blueprint  # noqa: E402

app.register_blueprint(create_clientes_blueprint({"conectar": conectar}))

# ============================================================================
# REGISTRO DO BLUEPRINT DE UNIDADES_SERIALIZADAS (Sprint P0.1, evoluído na
# migração ADR-007 — rastreamento individual por IMEI/serial, fonte única de
# verdade para unidades originadas de Estoque OU de Produtos)
# ============================================================================

from fluxoly_unidades_serializadas_controller import create_unidades_serializadas_blueprint  # noqa: E402

app.register_blueprint(create_unidades_serializadas_blueprint({"conectar": conectar}))

# ============================================================================
# REGISTRO DO BLUEPRINT DE PRODUTOS (Sprint Comercial 0.1 — catálogo
# comercial de venda, domínio novo e separado de Estoque/peças de reparo)
# ============================================================================

from fluxoly_produtos_controller import create_produtos_blueprint  # noqa: E402

app.register_blueprint(create_produtos_blueprint({"conectar": conectar}))

# ============================================================================
# REGISTRO DO BLUEPRINT DE VENDAS (Vendas MVP, 2026-07-27 — primeiro módulo a
# nascer com o prefixo fluxoly_, ver docs/engineering/adr/ADR-008.md)
# ============================================================================

from fluxoly_vendas_controller import create_vendas_blueprint  # noqa: E402

app.register_blueprint(create_vendas_blueprint({"conectar": conectar}))

# ============================================================================
# REGISTRO DO BLUEPRINT DE TIPOS DE GARANTIA (V1.5 — Garantia, cadastro
# compartilhado entre Vendas e Assistência, ver docs/engineering/plans/
# PLAN-V1.5-Garantia.md)
# ============================================================================

from fluxoly_tipos_garantia_controller import create_tipos_garantia_blueprint  # noqa: E402

app.register_blueprint(create_tipos_garantia_blueprint({"conectar": conectar}))

# ============================================================================
# HEALTH CHECKS (Sprint Observabilidade) — sem autenticação, usados por
# probes de infraestrutura (Render, load balancer). Não usam a convenção
# ok()/err() das blueprints de domínio de propósito — são infraestrutura,
# não API de negócio.
# ============================================================================


@app.route("/health")
def health_check():
    """Liveness — processo está de pé. Não checa nenhuma dependência externa."""
    return jsonify({"status": "ok"}), 200


@app.route("/ready")
def ready_check():
    """Readiness — banco de dados está acessível."""
    try:
        conn = conectar()
        try:
            conn.execute("SELECT 1")
        finally:
            conn.close()
    except Exception as exc:
        logger.error("readiness_check_failed", extra={"erro": str(exc)})
        return jsonify({"status": "unavailable"}), 503
    return jsonify({"status": "ok"}), 200


def _metrics_autorizado():
    # Fora de IS_SERVER_RUNTIME (dev local, testes) libera sem token, pra
    # facilitar curl local. Em produção, exige METRICS_TOKEN configurada e
    # correspondente -- se a variável não estiver setada, nega por padrão
    # (mais seguro do que deixar aberto por omissão de configuração).
    if not IS_SERVER_RUNTIME:
        return True
    token_esperado = os.environ.get("METRICS_TOKEN", "")
    if not token_esperado:
        return False
    return request.headers.get("X-Metrics-Token", "") == token_esperado


@app.route("/metrics")
def metrics_endpoint():
    """Métricas Prometheus. Em modo multiprocess (container com --workers 2,
    ver Dockerfile/gunicorn.conf.py), agrega os dados de todos os workers a
    partir dos arquivos em PROMETHEUS_MULTIPROC_DIR -- sem isso, cada worker
    reportaria só a própria fatia do tráfego."""
    if not _metrics_autorizado():
        return jsonify({"erro": "Não autorizado."}), 401

    multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if multiproc_dir:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        payload = generate_latest(registry)
    else:
        payload = generate_latest()

    return payload, 200, {"Content-Type": CONTENT_TYPE_LATEST}


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


_MERCADO_PHONE_SYNC_THREAD_STARTED = False


def iniciar_sync_mercadophone_se_habilitado():
    """Inicia thread de sincronização automática no processo atual, quando configurado."""
    global _MERCADO_PHONE_SYNC_THREAD_STARTED

    if _MERCADO_PHONE_SYNC_THREAD_STARTED:
        return

    if not BACKGROUND_JOBS_ENABLED:
        return

    if not (MERCADO_PHONE_SYNC_ENABLED and MERCADO_PHONE_API_TOKEN):
        return

    sync_thread = threading.Thread(
        target=loop_sincronizacao_mercado_phone,
        args=(conectar, MERCADO_PHONE_RUNTIME_CONFIG, MERCADO_PHONE_HELPERS),
        daemon=True,
        # INC-001: nome explícito (era "Thread-N" genérico) -- identifica esta
        # thread nos logs da instrumentação de conexões sem ambiguidade. Puramente
        # cosmético, não altera nenhum comportamento de sincronização.
        name="mercadophone-sync",
    )
    sync_thread.start()
    _MERCADO_PHONE_SYNC_THREAD_STARTED = True


# Em produção (Render/Gunicorn), o módulo é importado sem passar por __main__.
# Por isso iniciamos a sincronização aqui também.
iniciar_sync_mercadophone_se_habilitado()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    is_frozen = getattr(sys, "frozen", False)
    is_server = IS_SERVER_RUNTIME
    debug_mode = not is_frozen and not is_server

    # Inicia thread de sincronização Mercado Phone se habilitada
    iniciar_sync_mercadophone_se_habilitado()

    # Abre navegador automaticamente apenas no modo desktop (não no servidor)
    if not is_server and not os.environ.get("IR_FLOW_NO_BROWSER"):
        threading.Timer(1.2, lambda: webbrowser.open(f"http://{APP_HOST}:{APP_PORT}")).start()

    # Inicia servidor Flask
    app.run(host=APP_HOST, debug=debug_mode, use_reloader=False, port=APP_PORT)
