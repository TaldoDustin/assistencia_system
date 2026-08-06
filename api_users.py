"""
Fluxoly - API Blueprint (Usuários)
Rotas /api/usuarios* (CRUD + reset de senha) e /api/password-reset/<token> --
consumidas pelo frontend React (Usuarios.jsx, ResetSenha.jsx).
Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2 -- 5º domínio extraído).
"""

import os
import secrets
import sqlite3
from datetime import datetime, timedelta

from flask import Blueprint, request, session

from fluxoly_api_helpers import err, ok, usuario_admin, usuario_logado
from fluxoly_validation import safe_json


def create_api_users_blueprint(deps):
    api_users = Blueprint("api_users", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    generate_password_hash = deps["generate_password_hash"]
    perfis_opcoes = deps["perfis_opcoes"]

    def _password_reset_token_horas():
        try:
            return int(os.environ.get("IR_FLOW_PASSWORD_RESET_TOKEN_HOURS", "24"))
        except (TypeError, ValueError):
            return 24

    @api_users.route("/usuarios")
    def listar_usuarios():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome, usuario, perfil, ativo FROM usuarios ORDER BY nome")
        rows = cursor.fetchall()
        conn.close()
        return ok(
            usuarios=[{"id": r[0], "nome": r[1], "usuario": r[2], "perfil": r[3], "ativo": bool(r[4])} for r in rows]
        )

    @api_users.route("/usuarios", methods=["POST"])
    def criar_usuario():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        nome = (body.get("nome") or "").strip()
        usuario_txt = (body.get("usuario") or "").strip()
        senha_txt = (body.get("senha") or "").strip()
        perfil = body.get("perfil") or "tecnico"

        if not nome or not usuario_txt or not senha_txt:
            return err("Preencha nome, usuário e senha.")
        if perfil not in perfis_opcoes:
            perfil = "tecnico"

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (nome, usuario, senha_hash, perfil) VALUES (?,?,?,?)",
                (nome, usuario_txt, generate_password_hash(senha_txt), perfil),
            )
            novo_id = cursor.lastrowid
            conn.commit()
        except sqlite3.IntegrityError:
            conn.rollback()
            return err("Usuário já existe.")
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api_users.route("/usuarios/<int:uid>", methods=["PUT"])
    def atualizar_usuario(uid):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        nome = (body.get("nome") or "").strip()
        perfil = body.get("perfil") or "tecnico"
        senha_nova = (body.get("senha_nova") or "").strip()
        ativo = bool(body.get("ativo", True))

        if perfil not in perfis_opcoes:
            perfil = "tecnico"
        if uid == session.get("usuario_id") and not ativo:
            return err("Você não pode desativar sua própria conta.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            if senha_nova:
                cursor.execute(
                    "UPDATE usuarios SET nome=?,perfil=?,senha_hash=?,ativo=? WHERE id=?",
                    (nome, perfil, generate_password_hash(senha_nova), 1 if ativo else 0, uid),
                )
            else:
                cursor.execute(
                    "UPDATE usuarios SET nome=?,perfil=?,ativo=? WHERE id=?",
                    (nome, perfil, 1 if ativo else 0, uid),
                )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api_users.route("/usuarios/<int:uid>", methods=["DELETE"])
    def deletar_usuario(uid):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        if uid == session.get("usuario_id"):
            return err("Você não pode excluir sua própria conta.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM usuarios WHERE id=?", (uid,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api_users.route("/usuarios/<int:uid>/reset-token", methods=["POST"])
    def gerar_token_reset_senha(uid):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM usuarios WHERE id=?", (uid,))
            if not cursor.fetchone():
                return err("Usuário não encontrado.", 404)

            agora = datetime.now()
            expira_em = (agora + timedelta(hours=_password_reset_token_horas())).isoformat()
            token = secrets.token_urlsafe(24)

            # Invalida qualquer token anterior ainda não usado deste usuário —
            # nunca mais de um token válido por vez.
            cursor.execute(
                "UPDATE password_reset_tokens SET usado_em=? WHERE usuario_id=? AND usado_em IS NULL",
                (agora.isoformat(), uid),
            )
            cursor.execute(
                """
                INSERT INTO password_reset_tokens (usuario_id, token, expira_em, criado_por)
                VALUES (?, ?, ?, ?)
                """,
                (uid, token, expira_em, session.get("usuario_id")),
            )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(token=token, expira_em=expira_em)

    @api_users.route("/password-reset/<token>", methods=["POST"])
    def consumir_token_reset_senha(token):
        body = safe_json(request)
        senha_nova = (body.get("senha_nova") or "").strip()
        if not senha_nova:
            return err("Informe a nova senha.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id, usuario_id, expira_em, usado_em FROM password_reset_tokens WHERE token=?",
                (token,),
            )
            row = cursor.fetchone()
            if not row:
                return err("Token inválido.", 404)

            token_id, usuario_id, expira_em, usado_em = row
            if usado_em:
                return err("Este token já foi usado.", 410)
            if datetime.fromisoformat(expira_em) < datetime.now():
                return err("Este token expirou.", 410)

            agora_iso = datetime.now().isoformat()
            cursor.execute(
                "UPDATE usuarios SET senha_hash=? WHERE id=?",
                (generate_password_hash(senha_nova), usuario_id),
            )
            cursor.execute(
                "UPDATE password_reset_tokens SET usado_em=? WHERE id=?",
                (agora_iso, token_id),
            )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    return api_users
