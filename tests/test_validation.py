"""
Testes unitarios da camada compartilhada de parsing (fluxoly_validation.py).

Sem banco de dados, sem app Flask, sem chamadas HTTP — puramente funcional.
"""

from fluxoly_validation import parse_float, parse_int, safe_json, validate_positive_number


class _FakeRequest:
    """Simula o suficiente de flask.Request para testar safe_json isoladamente."""

    def __init__(self, payload, raises=False):
        self._payload = payload
        self._raises = raises

    def get_json(self, silent=False):
        if self._raises:
            if silent:
                return None
            raise ValueError("corpo nao e JSON valido")
        return self._payload


# ── parse_int ────────────────────────────────────────────────────────────


def test_parse_int_retorna_default_quando_valor_ausente():
    assert parse_int(None, default=1) == 1


def test_parse_int_retorna_default_quando_string_vazia():
    assert parse_int("", default=20) == 20


def test_parse_int_converte_string_numerica():
    assert parse_int("42") == 42


def test_parse_int_converte_int_literal():
    assert parse_int(7, default=0) == 7


def test_parse_int_retorna_none_quando_valor_invalido():
    assert parse_int("abc", default=0) is None


def test_parse_int_usa_default_zero_quando_omitido():
    assert parse_int(None) == 0


# ── parse_float ──────────────────────────────────────────────────────────


def test_parse_float_retorna_default_quando_valor_ausente():
    assert parse_float(None, default=1.5) == 1.5


def test_parse_float_retorna_default_quando_string_vazia():
    assert parse_float("", default=9.9) == 9.9


def test_parse_float_converte_string_numerica():
    assert parse_float("12.5") == 12.5


def test_parse_float_retorna_none_quando_valor_invalido():
    assert parse_float("abc", default=0.0) is None


# ── safe_json ────────────────────────────────────────────────────────────


def test_safe_json_retorna_dict_quando_corpo_valido():
    req = _FakeRequest({"nome": "Tela iPhone 14"})
    assert safe_json(req) == {"nome": "Tela iPhone 14"}


def test_safe_json_retorna_dict_vazio_quando_corpo_ausente():
    req = _FakeRequest(None)
    assert safe_json(req) == {}


def test_safe_json_retorna_dict_vazio_quando_corpo_invalido():
    req = _FakeRequest(None, raises=True)
    assert safe_json(req) == {}


# ── validate_positive_number ────────────────────────────────────────────


def test_validate_positive_number_true_para_valor_maior_que_zero():
    assert validate_positive_number(10) is True


def test_validate_positive_number_false_para_zero():
    assert validate_positive_number(0) is False


def test_validate_positive_number_false_para_negativo():
    assert validate_positive_number(-5) is False


def test_validate_positive_number_false_para_nao_numerico():
    assert validate_positive_number("abc") is False
