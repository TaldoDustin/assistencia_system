import re

from irflow_core import normalizar_busca_texto, texto_limpo


# IMPORTANTE
# Sempre manter esta lista atualizada.
# Esta e a fonte unica utilizada por:
# - Nova OS
# - Editar OS
# - Estoque
# - Tabela de precos
# - API /api/constantes
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
    "iPhone 17",
    "iPhone 17 Air",
    "iPhone 17 Pro",
    "iPhone 17 Pro Max",
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
    # Cores da linha iPhone 17 (lancamento 2025): lista generica de proposito, nao
    # o catalogo oficial Apple — decisao deliberada (Hotfix H-002) para nao arriscar
    # nome de cor incorreto sem necessidade comercial ainda. Trocar pelos nomes
    # oficiais quando/se houver demanda real de precisao (ex.: Vendas/Produtos).
    "iPhone 17": ["Preto", "Branco", "Azul", "Verde", "Rosa"],
    "iPhone 17 Air": ["Preto", "Branco", "Azul", "Verde", "Rosa"],
    "iPhone 17 Pro": ["Preto", "Branco", "Azul", "Verde", "Rosa"],
    "iPhone 17 Pro Max": ["Preto", "Branco", "Azul", "Verde", "Rosa"],
}

COLOR_ALIAS_MAP = {
    # Titanio (iPhone 15 Pro+, 16 Pro+) — termos compostos primeiro
    "black titanium": "Titanio preto",
    "white titanium": "Titanio branco",
    "blue titanium": "Titanio azul",
    "natural titanium": "Titanio natural",
    "desert titanium": "Titanio-deserto",
    "titanio preto": "Titanio preto",
    "titanio negro": "Titanio preto",
    "titanium preto": "Titanio preto",
    "titanio branco": "Titanio branco",
    "titanium branco": "Titanio branco",
    "titanio azul": "Titanio azul",
    "titanium azul": "Titanio azul",
    "titanio natural": "Titanio natural",
    "titanium natural": "Titanio natural",
    "titanio deserto": "Titanio-deserto",
    "titanium deserto": "Titanio-deserto",
    # Cores compostas específicas — mais longos primeiro para evitar match parcial
    "verde meia noite": "Verde-meia-noite",
    "midnight green": "Verde-meia-noite",   # iPhone 11 Pro
    "verde alpino": "Verde-alpino",
    "alpine green": "Verde-alpino",         # iPhone 13 Pro
    "azul pacifico": "Azul-pacifico",
    "pacific blue": "Azul-pacifico",        # iPhone 12 Pro
    "azul sierra": "Azul-sierra",
    "sierra blue": "Azul-sierra",           # iPhone 13 Pro
    "azul ultramarino": "Azul-ultramarino",
    "ultramarine": "Azul-ultramarino",      # iPhone 16
    "ultramarino": "Azul-ultramarino",
    "verde acinzentado": "Verde-acinzentado",
    "teal": "Verde-acinzentado",            # iPhone 16
    "preto espacial": "Preto-espacial",
    "space black": "Preto-espacial",        # iPhone 14 Pro
    "cinza espacial": "Cinza-espacial",
    "space gray": "Cinza-espacial",
    "space grey": "Cinza-espacial",
    "spacegray": "Cinza-espacial",
    "spacegrey": "Cinza-espacial",
    "roxo profundo": "Roxo-profundo",
    "deep purple": "Roxo-profundo",         # iPhone 14 Pro
    "product red": "Vermelho",
    # Compostos simples
    "meia noite": "Meia-noite",
    # Simples — depois dos compostos para não cortar match longo
    "midnight": "Meia-noite",               # iPhone 13+
    "starlight": "Estelar",
    "estelar": "Estelar",
    "graphite": "Grafite",
    "grafite": "Grafite",
    "deserto": "Titanio-deserto",
    "natural": "Titanio natural",
    "coral": "Coral",
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
    "prata": "Prata",
    "silver": "Prata",
    "dourado": "Dourado",
    "gold": "Dourado",
    "laranja": "Laranja",
    "orange": "Laranja",
    "lilas": "Lilas",
    "lilac": "Lilas",
    "bege": "Bege",
    "beige": "Bege",
    "creme": "Creme",
    "cream": "Creme",
    "cinza": "Cinza",
    "gray": "Cinza",
    "grey": "Cinza",
    # Abreviações comuns em lojas/sistemas
    "mg": "Verde-meia-noite",   # Midnight Green — iPhone 11 Pro
    "sg": "Cinza-espacial",     # Space Gray
    "sb": "Preto-espacial",     # Space Black — iPhone 14 Pro
    "dp": "Roxo-profundo",      # Deep Purple — iPhone 14 Pro
    "nt": "Titanio natural",    # Natural Titanium
    "dt": "Titanio-deserto",    # Desert Titanium
    "bt": "Titanio preto",      # Black Titanium (contexto iPhone 15/16 Pro)
    "wt": "Titanio branco",     # White Titanium
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

PRODUTOS_CATEGORIAS = [
    "iPhone",
    "Apple Watch",
    "AirPods",
    "Acessorio",
]

PRODUTOS_CONDICOES = [
    "Novo",
    "Seminovo",
    "Vitrine",
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
    # 1º: busca exata no mapa canônico (ex: "iPhone 13" → "iPhone 13")
    # 2º: extrai de descrição livre (ex: "IPHONE 13 64GB" → "iPhone 13")
    # 3º: mantém o texto original como último recurso
    return normalizar_modelo_iphone(texto) or extrair_modelo_da_descricao_aparelho(texto) or texto


def extrair_modelo_da_descricao_aparelho(descricao):
    texto = normalizar_busca_texto(descricao)
    if not texto:
        return ""

    match = re.search(r"\b(?:iphone|ip)\s*(\d{1,2})(?:\s*(pro max|promax|pro|plus|mini|air|e))?\b", texto)
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
    # Aliases ordenados do mais longo ao mais curto para evitar match parcial
    # (ex: "midnight green" antes de "midnight", "space gray" antes de "gray")
    sorted_aliases = sorted(COLOR_ALIAS_MAP.items(), key=lambda x: len(x[0]), reverse=True)

    # 1ª passagem: cor preferida quando bate com a lista de cores do modelo
    for alias, cor in sorted_aliases:
        if alias in texto and (not cores_modelo or cor in cores_modelo):
            return cor

    # 2ª passagem: canonicaliza para o nome padrão mesmo fora da lista do modelo
    # (garante que "space gray" → "Cinza-espacial", "midnight" → "Meia-noite", etc.)
    for alias, cor in sorted_aliases:
        if alias in texto:
            return cor

    return ""


def canonicalizar_para_lista(valor, lista):
    """
    Tenta encontrar o valor canônico de `valor` dentro de `lista`.

    Estratégia (em ordem de prioridade):
    1. Match exato normalizado (sem acentos, minúsculo)
    2. Match parcial: o texto normalizado contém o nome canônico ou vice-versa
    3. Match por palavra: ao menos uma palavra em comum

    Retorna o item canônico da lista, ou "" se não há match.

    Exemplos:
        canonicalizar_para_lista("Isaque", ["ISAQUE SOUZA", "RUAM SOARES"])
            → "ISAQUE SOUZA"
        canonicalizar_para_lista("space gray", ["Cinza-espacial", "Prata"])
            → "" (use extrair_cor_da_descricao_aparelho para cores)
        canonicalizar_para_lista("camila santos", ["Camila", "Kauany"])
            → "Camila"
    """
    texto = normalizar_busca_texto(valor)
    if not texto:
        return ""

    # 1ª: match exato normalizado
    for opcao in lista:
        if normalizar_busca_texto(opcao) == texto:
            return opcao

    # 2ª: match parcial (contém ou está contido) — preferir opções mais longas
    for opcao in sorted(lista, key=lambda x: len(x), reverse=True):
        opcao_norm = normalizar_busca_texto(opcao)
        if opcao_norm and (opcao_norm in texto or texto in opcao_norm):
            return opcao

    # 3ª: ao menos uma palavra em comum (ex: "Isaque" → "ISAQUE SOUZA")
    palavras_entrada = set(texto.split())
    for opcao in lista:
        palavras_opcao = set(normalizar_busca_texto(opcao).split())
        if palavras_entrada & palavras_opcao:
            return opcao

    return ""


def nome_reparo_importavel(nome):
    texto = texto_limpo(nome)
    if not texto:
        return False

    texto_norm = normalizar_busca_texto(texto)
    if texto_norm in {"iphone", "ipad", "smartphone", "celular", "assistencia", "garantia", "reparo"}:
        return False
    return not extrair_modelo_da_descricao_aparelho(texto)
