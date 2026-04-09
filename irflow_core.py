import unicodedata


STATUS_EM_ANDAMENTO = "Em andamento"
STATUS_AGUARDANDO_PECA = "Aguardando peca"
STATUS_FINALIZADO = "Finalizado"
STATUS_CANCELADO = "Cancelado"
STATUS_OS_VALIDOS = {
    STATUS_EM_ANDAMENTO,
    STATUS_AGUARDANDO_PECA,
    STATUS_FINALIZADO,
    STATUS_CANCELADO,
}
STATUS_OS_OPCOES = [
    STATUS_EM_ANDAMENTO,
    STATUS_AGUARDANDO_PECA,
    STATUS_FINALIZADO,
    STATUS_CANCELADO,
]


def texto_limpo(valor):
    return str(valor or "").strip()


def normalizar_busca_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor or "")).encode("ascii", "ignore").decode("ascii")
    texto = texto.lower().replace("-", " ").replace("/", " ")
    return " ".join(texto.split())


def normalizar_status_os(valor, status_padrao=STATUS_EM_ANDAMENTO):
    texto = normalizar_busca_texto(valor)
    if not texto:
        return status_padrao
    if "cancel" in texto:
        return STATUS_CANCELADO
    if "final" in texto or "entreg" in texto or "conclu" in texto:
        return STATUS_FINALIZADO
    if "aguard" in texto:
        return STATUS_AGUARDANDO_PECA
    if "andamento" in texto or "andando" in texto:
        return STATUS_EM_ANDAMENTO
    return status_padrao


def status_aguardando_peca(valor):
    return normalizar_status_os(valor) == STATUS_AGUARDANDO_PECA


def status_finalizado(valor):
    return normalizar_status_os(valor) == STATUS_FINALIZADO


def status_cancelado(valor):
    return normalizar_status_os(valor) == STATUS_CANCELADO


def status_aberto(valor):
    status_norm = normalizar_status_os(valor)
    return status_norm not in {STATUS_FINALIZADO, STATUS_CANCELADO}


def coletar_status_opcoes(rows, status_index):
    return sorted({normalizar_status_os(row[status_index]) for row in rows if row[status_index]})


def calcular_faturamento_os(valor_cobrado, valor_descontado):
    valor_cobrado = valor_cobrado or 0
    valor_descontado = valor_descontado or 0
    return valor_cobrado if valor_cobrado > 0 else valor_descontado


def calcular_lucro_os(tipo, valor_cobrado, valor_descontado, custo):
    if tipo in {"Assistencia", "Assistência", "Upgrade"}:
        return calcular_faturamento_os(valor_cobrado, valor_descontado) - (custo or 0)
    return -(custo or 0)


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default
