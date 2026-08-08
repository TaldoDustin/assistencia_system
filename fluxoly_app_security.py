"""
Factory de configuração de segurança HTTP (CORS + headers) do Fluxoly.

TD-02 Fatia 2 (docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md) -- extrai de app.py só o
registro de CORS e os headers de segurança (CSP, X-Content-Type-Options, X-Frame-Options,
Referrer-Policy) e os respectivos @app.after_request. FLASK_SECRET_KEY, cookies de sessão,
observabilidade por request e middleware de autenticação permanecem em app.py -- não fazem parte
deste bloco (Phase 1, matriz de escopo aprovada).
"""

from flask import request

try:
    from flask_cors import CORS
except Exception:
    CORS = None


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


def configurar_seguranca(app, cors_origins):
    """Registra CORS e os headers de segurança HTTP em `app`.

    `cors_origins` já vem calculado por quem chama (depende de IR_FLOW_CORS_ORIGINS/VERCEL_URL,
    hoje em fluxoly_config.py) -- esta função não lê os.environ, para não duplicar a fonte de
    verdade de config.
    """
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

    @app.after_request
    def _security_headers(response):
        response.headers.setdefault("Content-Security-Policy", _CSP_HEADER_VALUE)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
        return response
