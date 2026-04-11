"""
IR Flow - Blueprint de Autenticação
Login, logout e gestão de usuários.
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    request,
    session,
    url_for,
)
from urllib.parse import quote


def create_auth_blueprint(deps: dict):
    conectar = deps["conectar"]
    generate_password_hash = deps["generate_password_hash"]
    check_password_hash = deps["check_password_hash"]

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

        erro = None
        usuario_txt = (request.form.get("usuario") or "").strip()
        senha_txt = request.form.get("senha") or ""

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, nome, senha_hash, perfil, ativo FROM usuarios WHERE usuario = ?",
            (usuario_txt,),
        )
        row = cursor.fetchone()
        conn.close()

        if row and row[4] == 1 and check_password_hash(row[2], senha_txt):
            session.permanent = True
            session["usuario_id"] = row[0]
            session["usuario_nome"] = row[1]
            session["usuario_perfil"] = row[3]
            destino = request.form.get("next") or "/app"
            return redirect(destino)

        erro = quote("Usuário ou senha inválidos.")
        return redirect(f"/app/login?erro={erro}")

    @auth_views.route("/logout")
    def logout():
        session.clear()
        return redirect("/app/login")

    # ------------------------------------------------------------------
    # GESTÃO DE USUÁRIOS (admin)
    # ------------------------------------------------------------------

    @auth_views.route("/usuarios")
    def usuarios():
        return redirect("/app/usuarios")

    @auth_views.route("/usuarios/novo", methods=["POST"])
    def novo_usuario():
        nome = (request.form.get("nome") or "").strip()
        usuario_txt = (request.form.get("usuario") or "").strip()
        senha_txt = (request.form.get("senha") or "").strip()
        perfil = request.form.get("perfil") or "tecnico"

        if not nome or not usuario_txt or not senha_txt:
            flash("Preencha todos os campos.", "danger")
            return redirect(url_for("auth_views.usuarios"))

        if perfil not in ("admin", "tecnico", "vendedor"):
            perfil = "tecnico"

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (nome, usuario, senha_hash, perfil) VALUES (?, ?, ?, ?)",
                (nome, usuario_txt, generate_password_hash(senha_txt), perfil),
            )
            conn.commit()
            flash(f"Usuário '{usuario_txt}' criado com sucesso.", "success")
        except Exception:
            flash("Erro: usuário já existe.", "danger")
        finally:
            conn.close()

        return redirect(url_for("auth_views.usuarios"))

    @auth_views.route("/usuarios/editar/<int:uid>", methods=["POST"])
    def editar_usuario(uid):
        nome = (request.form.get("nome") or "").strip()
        perfil = request.form.get("perfil") or "tecnico"
        senha_nova = (request.form.get("senha_nova") or "").strip()
        ativo = 1 if request.form.get("ativo") else 0

        if perfil not in ("admin", "tecnico", "vendedor"):
            perfil = "tecnico"

        conn = conectar()
        cursor = conn.cursor()

        if senha_nova:
            cursor.execute(
                "UPDATE usuarios SET nome=?, perfil=?, senha_hash=?, ativo=? WHERE id=?",
                (nome, perfil, generate_password_hash(senha_nova), ativo, uid),
            )
        else:
            cursor.execute(
                "UPDATE usuarios SET nome=?, perfil=?, ativo=? WHERE id=?",
                (nome, perfil, ativo, uid),
            )

        # Não permite desativar o próprio admin logado
        if uid == session.get("usuario_id") and not ativo:
            conn.rollback()
            conn.close()
            flash("Você não pode desativar sua própria conta.", "danger")
            return redirect(url_for("auth_views.usuarios"))

        conn.commit()
        conn.close()
        flash("Usuário atualizado.", "success")
        return redirect(url_for("auth_views.usuarios"))

    @auth_views.route("/usuarios/deletar/<int:uid>", methods=["POST"])
    def deletar_usuario(uid):
        if uid == session.get("usuario_id"):
            flash("Você não pode excluir sua própria conta.", "danger")
            return redirect(url_for("auth_views.usuarios"))

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (uid,))
        conn.commit()
        conn.close()
        flash("Usuário removido.", "success")
        return redirect(url_for("auth_views.usuarios"))

    return auth_views
