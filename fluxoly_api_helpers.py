"""
Fluxoly - Helpers compartilhados entre blueprints de /api/*.

Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2) -- só funções comprovadamente
usadas por 2+ domínios entram aqui (ver regra de admissão em
docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md, Phase 1). Um helper usado
por um único domínio permanece nesse domínio, mesmo que pareça genérico pelo nome.
"""

from flask import jsonify, session


def usuario_logado():
    return bool(session.get("usuario_id"))


def usuario_admin():
    return session.get("usuario_perfil") == "admin"


def err(msg, code=400):
    return jsonify({"ok": False, "erro": msg}), code


def ok(data=None, **kwargs):
    payload = {"ok": True}
    if data is not None:
        payload.update(data if isinstance(data, dict) else {"data": data})
    payload.update(kwargs)
    return jsonify(payload)
