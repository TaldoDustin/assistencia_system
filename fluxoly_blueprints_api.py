"""
Fluxoly - API Blueprint (JSON endpoints)
All routes under /api/* — consumed by the React SPA frontend.
Authentication: Flask session cookies (same-origin, credentials: 'include').
"""

import re

from flask import Blueprint


def create_api_blueprint(deps):
    api = Blueprint("api", __name__, url_prefix="/api")

    def _slug_estoque(valor):
        base = (valor or "").strip().upper()
        base = re.sub(r"[^A-Z0-9]+", "-", base)
        base = re.sub(r"-+", "-", base).strip("-")
        return base

    def _gerar_sku_estoque(modelo, tipo, qualidade, descricao):
        partes = [
            _slug_estoque(modelo)[:10],
            _slug_estoque(tipo)[:8],
            _slug_estoque(qualidade)[:8],
            _slug_estoque(descricao)[:10],
        ]
        partes = [p for p in partes if p]
        if not partes:
            return "ITEM"
        return "-".join(partes)

    return api
