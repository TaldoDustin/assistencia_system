import re

from irflow_core import normalizar_busca_texto, texto_limpo


IPHONE_MODELS = [
    "iPhone XR",
    "iPhone XS",
    "iPhone XS Max",
    "iPhone 11",
    "iPhone 11 Pro",
    "iPhone 11 Pro Max",
    "iPhone SE (2a geracao)",
    "iPhone 12 mini",
    "iPhone 12",
    "iPhone 12 Pro",
    "iPhone 12 Pro Max",
    "iPhone 13 mini",
    "iPhone 13",
    "iPhone 13 Pro",
    "iPhone 13 Pro Max",
    "iPhone SE (3a geracao)",
    "iPhone 14",
    "iPhone 14 Plus",
    "iPhone 14 Pro",
    "iPhone 14 Pro Max",
    "iPhone 15",
    "iPhone 15 Plus",
    "iPhone 15 Pro",
    "iPhone 15 Pro Max",
    "iPhone 16",
    "iPhone 16 Plus",
    "iPhone 16 Pro",
    "iPhone 16 Pro Max",
    "iPhone 16e",
]

IPHONE_MODEL_MAP = {modelo.lower(): modelo for modelo in IPHONE_MODELS}
IPHONE_ALIAS_MAP = {}
for modelo in IPHONE_MODELS:
    base = modelo.lower().replace("iphone", "").strip()
    base = base.replace("(", " ").replace(")", " ").replace("-", " ")
    base = " ".join(base.split())
    if base:
        IPHONE_ALIAS_MAP[base] = modelo
        IPHONE_ALIAS_MAP[base.replace(" ", "")] = modelo

IPHONE_COLORS = {
    "iPhone XR": ["Preto", "Branco", "Azul", "Amarelo", "Coral", "Vermelho"],
    "iPhone XS": ["Cinza-espacial", "Prata", "Dourado"],
    "iPhone XS Max": ["Cinza-espacial", "Prata", "Dourado"],
    "iPhone 11": ["Preto", "Branco", "Verde", "Amarelo", "Roxo", "Vermelho"],
    "iPhone 11 Pro": ["Cinza-espacial", "Prata", "Verde-meia-noite", "Dourado"],
    "iPhone 11 Pro Max": ["Cinza-espacial", "Prata", "Verde-meia-noite", "Dourado"],
    "iPhone SE (2a geracao)": ["Preto", "Branco", "Vermelho"],
    "iPhone 12 mini": ["Preto", "Branco", "Azul", "Verde", "Roxo", "Vermelho"],
    "iPhone 12": ["Preto", "Branco", "Azul", "Verde", "Roxo", "Vermelho"],
    "iPhone 12 Pro": ["Grafite", "Prata", "Dourado", "Azul-pacifico"],
    "iPhone 12 Pro Max": ["Grafite", "Prata", "Dourado", "Azul-pacifico"],
    "iPhone 13 mini": ["Meia-noite", "Estelar", "Azul", "Rosa", "Verde", "Vermelho"],
    "iPhone 13": ["Meia-noite", "Estelar", "Azul", "Rosa", "Verde", "Vermelho"],
    "iPhone 13 Pro": ["Grafite", "Prata", "Dourado", "Azul-sierra", "Verde-alpino"],
    "iPhone 13 Pro Max": ["Grafite", "Prata", "Dourado", "Azul-sierra", "Verde-alpino"],
    "iPhone SE (3a geracao)": ["Meia-noite", "Estelar", "Vermelho"],
    "iPhone 14": ["Meia-noite", "Estelar", "Azul", "Roxo", "Amarelo", "Vermelho"],
    "iPhone 14 Plus": ["Meia-noite", "Estelar", "Azul", "Roxo", "Amarelo", "Vermelho"],
    "iPhone 14 Pro": ["Preto-espacial", "Prata", "Dourado", "Roxo-profundo"],
    "iPhone 14 Pro Max": ["Preto-espacial", "Prata", "Dourado", "Roxo-profundo"],
    "iPhone 15": ["Preto", "Azul", "Verde", "Amarelo", "Rosa"],
    "iPhone 15 Plus": ["Preto", "Azul", "Verde", "Amarelo", "Rosa"],
    "iPhone 15 Pro": ["Titanio preto", "Titanio branco", "Titanio azul", "Titanio natural"],
    "iPhone 15 Pro Max": ["Titanio preto", "Titanio branco", "Titanio azul", "Titanio natural"],
    "iPhone 16": ["Preto", "Branco", "Rosa", "Verde-acinzentado", "Azul-ultramarino"],
    "iPhone 16 Plus": ["Preto", "Branco", "Rosa", "Verde-acinzentado", "Azul-ultramarino"],
    "iPhone 16 Pro": ["Titanio preto", "Titanio branco", "Titanio natural", "Titanio-deserto"],
    "iPhone 16 Pro Max": ["Titanio preto", "Titanio branco", "Titanio natural", "Titanio-deserto"],
    "iPhone 16e": ["Preto", "Branco"],
}

COLOR_ALIAS_MAP = {
    "preto": "Preto",
    "black": "Preto",
    "branco": "Branco",
    "white": "Branco",
    "azul": "Azul",
    "blue": "Azul",
    "vermelho": "Vermelho",
    "red": "Vermelho",
    "rosa": "Rosa",
    "pink": "Rosa",
    "roxo": "Roxo",
    "purple": "Roxo",
    "amarelo": "Amarelo",
    "yellow": "Amarelo",
    "verde": "Verde",
    "green": "Verde",
    "estelar": "Estelar",
    "starlight": "Estelar",
    "meia noite": "Meia-noite",
    "midnight": "Meia-noite",
    "grafite": "Grafite",
    "graphite": "Grafite",
    "prata": "Prata",
    "silver": "Prata",
    "dourado": "Dourado",
    "gold": "Dourado",
    "natural": "Titanio natural",
    "deserto": "Titanio-deserto",
    "titanio branco": "Titanio branco",
    "titanio preto": "Titanio preto",
    "titanio azul": "Titanio azul",
    "titanio natural": "Titanio natural",
    "titanio deserto": "Titanio-deserto",
}

VENDEDORES = [
    "Camila",
    "Kauany",
    "Camily",
    "Taina",
    "Evellyn",
    "Marcelo",
    "Isabela",
]

TECNICOS = [
    "Aguardando definicao",
    "ISAQUE SOUZA",
    "RUAM SOARES",
]

CATEGORIAS_CUSTOS_OPERACIONAIS = [
    "Limpeza e insumos",
    "Ferramentas",
    "Embalagem",
    "Transporte",
    "Terceiros",
    "Outros",
]

REPAROS_PADRAO = [
    "TROCA DE TELA",
    "TROCA DE BATERIA",
    "TROCA DE DOCK DE CARGA",
    "TROCA DE VIDRO DA TELA",
    "TROCA DE LENTE DA CAMERA",
    "TROCA DE CAMERA TRASEIRA",
    "TROCA DE CAMERA FRONTAL",
    "TROCA DE FACE ID",
    "TROCA DE BOTOES",
    "TROCA DE AURICULAR",
    "TROCA DE TAMPA TRASEIRA",
    "TROCA DE VIDRO TRASEIRO",
    "TROCA DE CARCACA",
    "TROCA DE ALTO FALANTE",
    "REPARO DE TELA",
    "REPARO DE PLACA",
    "TROCA DE FLASH",
]


def normalizar_modelo_iphone(modelo):
    valor = texto_limpo(modelo)
    if not valor:
        return ""
    return IPHONE_MODEL_MAP.get(valor.lower(), "")


def obter_cores_modelo_iphone(modelo):
    return IPHONE_COLORS.get(modelo or "", [])


def normalizar_imei(valor):
    digitos = "".join(ch for ch in str(valor or "") if ch.isdigit())
    if 14 <= len(digitos) <= 16:
        return digitos
    return ""


def modelo_para_os(valor):
    texto = texto_limpo(valor)
    if not texto:
        return ""
    return normalizar_modelo_iphone(texto) or texto


def extrair_modelo_da_descricao_aparelho(descricao):
    texto = normalizar_busca_texto(descricao)
    if not texto:
        return ""

    match = re.search(r"\b(?:iphone|ip)\s*(\d{1,2})(?:\s*(pro max|promax|pro|plus|mini|e))?\b", texto)
    if match:
        numero = match.group(1)
        sufixo = (match.group(2) or "").replace("promax", "pro max").strip()
        chave = f"{numero} {sufixo}".strip()
        modelo = IPHONE_ALIAS_MAP.get(chave) or IPHONE_ALIAS_MAP.get(chave.replace(" ", ""))
        if modelo:
            return modelo

    for alias, modelo in sorted(IPHONE_ALIAS_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if alias and alias in texto:
            return modelo
    return ""


def extrair_cor_da_descricao_aparelho(descricao, modelo=""):
    texto = normalizar_busca_texto(descricao)
    if not texto:
        return ""

    cores_modelo = set(obter_cores_modelo_iphone(modelo))
    for alias, cor in COLOR_ALIAS_MAP.items():
        if alias in texto and (not cores_modelo or cor in cores_modelo):
            return cor
    return ""


def nome_reparo_importavel(nome):
    texto = texto_limpo(nome)
    if not texto:
        return False

    texto_norm = normalizar_busca_texto(texto)
    if texto_norm in {"iphone", "ipad", "smartphone", "celular", "assistencia", "garantia", "reparo"}:
        return False
    if extrair_modelo_da_descricao_aparelho(texto):
        return False
    return True
