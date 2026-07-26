"""
IR Flow - Blueprint de Autenticação
Login e logout via formulário legado.

Gestão de usuários por formulário (`/usuarios/novo`, `/usuarios/editar`,
`/usuarios/deletar`) foi removida — sem proteção CSRF e sem uso pelo frontend
real (que usa `/api/usuarios`). Ver KNOWN_ISSUES.md.
"""

from flask import (
    Blueprint,
    redirect,
    request,
    session,
)
from urllib.parse import quote


def create_auth_blueprint(deps: dict):
    conectar = deps["conectar"]
    check_password_hash = deps["check_password_hash"]
    resolver_ip_cliente = deps["resolver_ip_cliente"]
    limite_excedido = deps["limite_excedido"]
    registrar_tentativa = deps["registrar_tentativa"]

    auth_views = Blueprint("auth_views", __name__)

    # ------------------------------------------------------------------
    # LOGIN / LOGOUT
    # ------------------------------------------------------------------

    @auth_views.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("usuario_id"):
            return redirect("/app")

        if request.method == "GET":
            return redirect("/app/login")

        usuario_txt = (request.form.get("usuario") or "").strip()
        senha_txt = request.form.get("senha") or ""
        identificador = resolver_ip_cliente(request)

        conn = conectar()
        cursor = conn.cursor()

        if limite_excedido(cursor, identificador):
            conn.close()
            erro = quote("Muitas tentativas de login. Tente novamente em instantes.")
            return redirect(f"/app/login?erro={erro}")

        cursor.execute(
            "SELECT id, nome, senha_hash, perfil, ativo FROM usuarios WHERE usuario = ?",
            (usuario_txt,),
        )
        row = cursor.fetchone()

        sucesso = bool(row and row[4] == 1 and check_password_hash(row[2], senha_txt))
        registrar_tentativa(cursor, identificador, sucesso)
        conn.commit()
        conn.close()

        if sucesso:
            session.permanent = True
            session["usuario_id"] = row[0]
            session["usuario_nome"] = row[1]
            session["usuario_perfil"] = row[3]
            return redirect("/app")

        erro = quote("Usuário ou senha inválidos.")
        return redirect(f"/app/login?erro={erro}")

    @auth_views.route("/logout")
    def logout():
        session.clear()
        return redirect("/app/login")

    return auth_views
