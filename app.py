"""
Fluxoly - Sistema de Gestão de Assistência Técnica
Application main module - Flask app bootstrap, configuration, and core functionality
"""

# ============================================================================
# IMPORTS PADRÃO DA BIBLIOTECA
# ============================================================================
import contextlib
import functools
import os
import re
import sqlite3
import sys
import threading
import time
import traceback
import uuid
import weakref
import webbrowser
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv

# Carrega .env em dev local antes de qualquer leitura de os.environ abaixo.
# Não sobrescreve variáveis já definidas no processo. Pulado quando os mesmos
# sinais de IS_SERVER_RUNTIME (definida adiante) já estão presentes: produção
# nunca tem .env de qualquer forma (Dockerfile não copia, .gitignore exclui),
# mas testes que simulam runtime de servidor num subprocesso isolado, rodando
# com cwd na raiz do repo, encontrariam o .env real do desenvolvedor e
# mascarariam a checagem obrigatória de FLASK_SECRET_KEY (ver
# tests/test_security_flask_secret_key_fallback.py).
if not any(
    os.environ.get(var)
    for var in ("IR_FLOW_DATA_DIR", "FLY_DATA_DIR", "RENDER_DISK_PATH", "RENDER", "RENDER_SERVICE_ID")
):
    load_dotenv()

# ============================================================================
# IMPORTS FLASK
# ============================================================================
from flask import Flask, flash, g, jsonify, redirect, request, send_from_directory, session, url_for

# ============================================================================
# IMPORTS DE OBSERVABILIDADE (Sprint Observabilidade)
# ============================================================================
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest, multiprocess
from werkzeug.security import generate_password_hash

from fluxoly_app_security import configurar_seguranca

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - REGISTRY DE BLUEPRINTS (TD-02 Fatia 3)
# ============================================================================
from fluxoly_blueprint_registry import RuntimeDeps, registrar_blueprints

# ============================================================================
# CONFIGURAÇÃO DE AMBIENTE, PATHS E FEATURE-FLAGS
# ============================================================================
# TD-02 Fatia 1 (docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md) -- extraído para
# fluxoly_config.py. app.py só importa os nomes; MERCADO_PHONE_SYNC_ENABLED/
# _INTERVAL_SECONDS/_START_DATE continuam sendo reatribuídos mais abaixo (seção "CONFIGURAÇÃO
# MERCADO PHONE") ao mesclar com integrations.json -- mesmo comportamento de antes.
from fluxoly_config import (  # noqa: E402
    APP_HOST,
    APP_PORT,
    BACKGROUND_JOBS_ENABLED,
    BACKUP_DIR,
    BACKUP_EMAIL_DESTINO,
    BACKUP_EMAIL_REMETENTE,
    BACKUP_EMAIL_SENHA_APP,
    DB_PATH,
    GOOGLE_DRIVE_BACKUP_DIR,
    INTEGRATIONS_CONFIG_PATH,
    IS_SERVER_RUNTIME,
    MERCADO_PHONE_API_BASE,
    MERCADO_PHONE_DEFAULT_TECNICO,
    MERCADO_PHONE_SYNC_ENABLED,
    MERCADO_PHONE_SYNC_INTERVAL_SECONDS,
    MERCADO_PHONE_SYNC_ONLY_AFTER_BOOT,
    MERCADO_PHONE_SYNC_START_DATE,
    MERCADO_PHONE_SYNC_TIMEOUT_SECONDS,
    PRICE_TABLES_PATH,
    RESOURCE_DIR,
    VERCEL_URL,
)

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - CORE
# ============================================================================
from fluxoly_core import (
    STATUS_AGUARDANDO_PECA,
    STATUS_EM_ANDAMENTO,
    STATUS_FINALIZADO,
    normalizar_busca_texto,
    normalizar_status_os,
    sessao_ainda_ativa,
    texto_limpo,
)
from fluxoly_logging import configurar_logging, get_logger
from fluxoly_mercadophone import loop_sincronizacao_mercado_phone

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - OS, STORAGE, MERCADOPHONE
# ============================================================================
from fluxoly_os import obter_ou_criar_reparo, salvar_reparos_os
from fluxoly_price_tables import carregar_tabelas_preco as carregar_tabelas_preco_arquivo
from fluxoly_price_tables import salvar_tabelas_preco as salvar_tabelas_preco_arquivo
from fluxoly_reference_data import (
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
from fluxoly_storage import carregar_configuracoes_integracoes, iniciar_thread_backup_automatico
from fluxoly_web import anexar_query_string

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

# TD-02 Fatia 2 (docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md) -- CORS, headers de
# segurança (CSP/X-Frame-Options/etc.) e os respectivos @app.after_request extraídos para
# fluxoly_app_security.py. cors_origins continua calculado aqui (fonte de verdade única).
configurar_seguranca(app, cors_origins)

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
    via o logger estruturado já existente (fluxoly_logging.py, extra={...} -- nunca
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

        def _ao_coletar(
            _ref, conn_id=conn_id, rota=rota, thread_name=thread_name, thread_ident=thread_ident, stack=stack_resumida
        ):
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
        if nome in (
            "_conn",
            "_id",
            "_rota",
            "_thread_name",
            "_thread_ident",
            "_abertura_monotonic",
            "_aberta_em",
            "_finalizer",
        ):
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
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS reparos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT
            )
            """
            )

            cursor.execute(
                """
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
            """
            )

            cursor.execute(
                """
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
            """
            )

            cursor.execute(
                """
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
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS os_pecas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                os_id INTEGER,
                estoque_id INTEGER,
                quantidade INTEGER,
                valor REAL
            )
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS os_reparos (
                os_id INTEGER NOT NULL,
                reparo_id INTEGER NOT NULL,
                PRIMARY KEY (os_id, reparo_id)
            )
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS movimentacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estoque_id INTEGER,
                tipo TEXT,
                quantidade INTEGER,
                data TEXT
            )
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS custos_operacionais (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT NOT NULL,
                categoria TEXT,
                valor REAL NOT NULL,
                data TEXT,
                observacoes TEXT
            )
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS integracao_sync_estado (
                chave TEXT PRIMARY KEY,
                valor TEXT
            )
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS integracao_os_vistas (
                origem TEXT NOT NULL,
                id_externo TEXT NOT NULL,
                primeira_visualizacao TEXT,
                PRIMARY KEY (origem, id_externo)
            )
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS compras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto TEXT NOT NULL,
                os_id INTEGER,
                quantidade INTEGER NOT NULL DEFAULT 1,
                status TEXT DEFAULT 'PENDENTE',
                criado_em TEXT DEFAULT '',
                atualizado_em TEXT DEFAULT ''
            )
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                usuario TEXT UNIQUE NOT NULL,
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL DEFAULT 'tecnico',
                ativo INTEGER NOT NULL DEFAULT 1
            )
            """
            )

            cursor.execute(
                """
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
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS login_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                identificador TEXT NOT NULL,
                sucesso INTEGER NOT NULL,
                criado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_login_attempts_identificador_criado_em
                ON login_attempts (identificador, criado_em)
                """
            )

            cursor.execute(
                """
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
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_audit_log_entidade
                ON audit_log (entidade, entidade_id)
                """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS password_reset_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                criado_em TEXT NOT NULL DEFAULT (datetime('now')),
                expira_em TEXT NOT NULL,
                usado_em TEXT,
                criado_por INTEGER
            )
            """
            )

            cursor.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_usuario_id
                ON password_reset_tokens (usuario_id)
                """
            )

            cursor.execute(
                """
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
            """
            )

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_telefone ON clientes (telefone)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_cpf_cnpj ON clientes (cpf_cnpj)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_clientes_nome ON clientes (nome)")

            cursor.execute(
                """
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
            """
            )

            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_estoque_id ON unidades_serializadas (estoque_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_produto_id ON unidades_serializadas (produto_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_status ON unidades_serializadas (status)"
            )
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_unidades_serializadas_imei ON unidades_serializadas (imei)")

            cursor.execute(
                """
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
            """
            )

            cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos (categoria)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_sku ON produtos (sku)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_produtos_ativo ON produtos (ativo)")

            # Vendas MVP (docs/product/features/VENDAS.md) — fluxo básico: cliente + aparelho
            # (unidade serializada) + pagamento simples, sem desconto/comissão/garantia/troca
            # (dependem de decisões de negócio ainda pendentes do Product Owner, ver VENDAS.md
            # "O que ainda está em aberto"). status='concluida' é deliberadamente distinto de um
            # futuro conceito de status de pagamento (pago/pendente/estornado) — venda e
            # pagamento são conceitos diferentes, não misturados aqui.
            cursor.execute(
                """
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
            """
            )
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
            cursor.execute(
                """
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
            """
            )
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
            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS tipos_garantia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                duracao_meses INTEGER NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT NOT NULL DEFAULT (datetime('now')),
                atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
            )

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
            cursor.execute(
                """
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
            """
            )

            cursor.execute(
                """
            CREATE TABLE IF NOT EXISTS shopping_list_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                shopping_list_id INTEGER NOT NULL,
                usuario_id INTEGER,
                acao TEXT NOT NULL,
                valor_anterior TEXT,
                valor_novo TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
            )

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
MERCADO_PHONE_API_TOKEN = os.environ.get("MERCADO_PHONE_API_TOKEN", "") or texto_limpo(
    MERCADO_PHONE_CONFIG.get("api_token")
)
MERCADO_PHONE_SYNC_ENABLED = (
    (
        texto_limpo(str(MERCADO_PHONE_CONFIG.get("sync_enabled", MERCADO_PHONE_SYNC_ENABLED))).lower()
        not in {"0", "false", "nao", "off"}
    )
    if MERCADO_PHONE_API_TOKEN
    else False
)
MERCADO_PHONE_SYNC_INTERVAL_SECONDS = int(
    MERCADO_PHONE_CONFIG.get("sync_interval_seconds", MERCADO_PHONE_SYNC_INTERVAL_SECONDS)
    or MERCADO_PHONE_SYNC_INTERVAL_SECONDS
)
MERCADO_PHONE_SYNC_START_DATE = (
    texto_limpo(MERCADO_PHONE_CONFIG.get("sync_start_date", MERCADO_PHONE_SYNC_START_DATE)) or "2026-04-01"
)

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
    # usuario_logado() de fluxoly_blueprints_api.py checa session["usuario_id"],
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
# REGISTRO DE BLUEPRINTS (TD-02 Fatia 3 — fluxoly_blueprint_registry.py)
# ============================================================================
# As 20 chamadas app.register_blueprint(...) que antes viviam inline aqui
# (auth + 12 domínios TD-01 + fluxoly_blueprints_api.py vazio + 5 domínios
# controller/service/repository) foram movidas para
# fluxoly_blueprint_registry.py::registrar_blueprints() -- mesma ordem, mesmos
# dicts de deps, nenhuma factory create_*_blueprint mudou. runtime carrega só
# os valores construídos em runtime dentro deste arquivo, que o registry não
# consegue importar direto sem criar import circular (ver docstring de
# RuntimeDeps em fluxoly_blueprint_registry.py).
runtime = RuntimeDeps(
    conectar=conectar,
    carregar_tabelas_preco=carregar_tabelas_preco,
    salvar_tabelas_preco=salvar_tabelas_preco,
    forcar_migracao_schema=forcar_migracao_schema,
    mercado_phone_runtime_config=MERCADO_PHONE_RUNTIME_CONFIG,
    mercado_phone_helpers=MERCADO_PHONE_HELPERS,
    listar_custos_operacionais=listar_custos_operacionais,
    obter_alertas_sistema=obter_alertas_sistema,
    parse_data_ymd=parse_data_ymd,
)
registrar_blueprints(app, runtime)

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
