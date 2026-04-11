import json
import os


def tabelas_preco_vazias():
    return {"ir_phones": {}, "clientes": {}}


def carregar_tabelas_preco(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        return tabelas_preco_vazias()
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
            return json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return tabelas_preco_vazias()


def salvar_tabelas_preco(caminho_arquivo, tabelas):
    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(tabelas, arquivo, ensure_ascii=False, indent=2)
