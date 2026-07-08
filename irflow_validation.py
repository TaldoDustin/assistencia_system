"""
Camada compartilhada de parsing e validação de entrada para rotas Flask.

Usada pelos endpoints JSON de `irflow_blueprints_api.py`. Os blueprints
HTML (admin/inventory/orders/auth) usam fluxo `flash()`/`redirect()` e não
consomem estes utilitários.
"""


def parse_int(value, default=0):
    """
    Converte `value` para int.

    Ausente ou string vazia -> `default`.
    Presente mas não conversível -> `None` (sinaliza entrada inválida;
    não mascara como `default`, para não transformar um erro de input em
    um valor de negócio silenciosamente aceito).
    """
    if value in (None, ""):
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def parse_float(value, default=0.0):
    """Mesmo contrato de `parse_int`, para valores de ponto flutuante."""
    if value in (None, ""):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_json(request_obj):
    """Corpo JSON da requisição como dict, nunca `None` e nunca levanta exceção."""
    return request_obj.get_json(silent=True) or {}


def require_fields(data, *field_names):
    """Retorna a lista dos nomes em `field_names` ausentes ou vazios em `data`."""
    return [name for name in field_names if not data.get(name)]


def validate_positive_number(value):
    """True se `value` é conversível para float e estritamente positivo."""
    try:
        return float(value) > 0
    except (TypeError, ValueError):
        return False
