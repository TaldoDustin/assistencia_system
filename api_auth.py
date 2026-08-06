"""
Fluxoly - API Blueprint (Autenticação JSON)
Rotas /api/auth/* -- consumidas pelo frontend React (Login.jsx, contexto de auth).
Distinto de fluxoly_blueprints_auth.py (auth_views -- páginas renderizadas no
servidor, /login e /logout legados). Extraído de fluxoly_blueprints_api.py
(TD-01, Phase 2 -- 6º domínio extraído).
"""

from flask import Blueprint, request, session

from fluxoly_api_helpers import err, ok, usuario_logado
from fluxoly_validation import safe_json


def create_api_auth_blueprint(deps):
    api_auth = Blueprint("api_auth", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    check_password_hash = deps["check_password_hash"]
    resolver_ip_cliente = deps["resolver_ip_cliente"]
    limite_excedido = deps["limite_excedido"]
    registrar_tentativa = deps["registrar_tentativa"]

    @api_auth.route("/auth/login", methods=["POST"])
    def auth_login():
        body = safe_json(request)
        usuario_txt = (body.get("usuario") or "").strip()
        senha_txt = body.get("senha") or ""
        identificador = resolver_ip_cliente(request)

        # INC-001: conexão sem try/except/finally — qualquer exceção entre abrir
        # e fechar vazava a conexão com a transação de escrita ainda aberta,
        # bloqueando todo escritor seguinte em WAL até o processo coletar o
        # objeto via GC (não determinístico). Rota de maior frequência de
        # chamada do sistema, já é escrita (registrar_tentativa) — maior risco
        # identificado na investigação.
        conn = conectar()
        try:
            cursor = conn.cursor()

            if limite_excedido(cursor, identificador):
                return err("Muitas tentativas de login. Tente novamente em instantes.", 429)

            if not usuario_txt or not senha_txt:
                registrar_tentativa(cursor, identificador, False)
                conn.commit()
                return err("Usuário e senha são obrigatórios.")

            cursor.execute(
                "SELECT id, nome, senha_hash, perfil, ativo FROM usuarios WHERE usuario = ?",
                (usuario_txt,),
            )
            row = cursor.fetchone()

            sucesso = bool(row and row[4] == 1 and check_password_hash(row[2], senha_txt))
            registrar_tentativa(cursor, identificador, sucesso)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        if sucesso:
            session.permanent = True
            session["usuario_id"] = row[0]
            session["usuario_nome"] = row[1]
            session["usuario_perfil"] = row[3]
            return ok(usuario={"id": row[0], "nome": row[1], "perfil": row[3]})

        return err("Usuário ou senha inválidos.", 401)

    @api_auth.route("/auth/logout", methods=["POST"])
    def auth_logout():
        session.clear()
        return ok()

    @api_auth.route("/auth/me")
    def auth_me():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        return ok(
            usuario={
                "id": session["usuario_id"],
                "nome": session["usuario_nome"],
                "perfil": session["usuario_perfil"],
            }
        )

    return api_auth
