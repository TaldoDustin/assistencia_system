#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar sincronização do MercadoPhone
"""
import sys
import os
import json
import sqlite3
from datetime import datetime

# Adicionar o diretório ao path
sys.path.insert(0, os.path.dirname(__file__))

from irflow_core import texto_limpo, normalizar_busca_texto, normalizar_status_os
from irflow_os import obter_ou_criar_reparo, salvar_reparos_os
from irflow_mercadophone import (
    listar_os_mercado_phone,
    detalhar_os_mercado_phone,
    importar_os_mercado_phone,
    valor_payload,
    extrair_ids_os_listagem_mercado_phone,
)

# Carregar config do integrations.json
try:
    with open("integrations.json", "r") as f:
        integrations = json.load(f)
        mp_config = integrations.get("mercado_phone", {})
        MERCADO_PHONE_API_TOKEN = mp_config.get("api_token", "").strip()
except:
    MERCADO_PHONE_API_TOKEN = os.environ.get("MERCADO_PHONE_API_TOKEN", "").strip()

MERCADO_PHONE_API_BASE = os.environ.get("MERCADO_PHONE_API_BASE", "https://api.mercadofone.com.br/v1/").strip()

if not MERCADO_PHONE_API_TOKEN:
    print("❌ MERCADO_PHONE_API_TOKEN não configurado!")
    sys.exit(1)

config = {
    "api_token": MERCADO_PHONE_API_TOKEN,
    "api_base": MERCADO_PHONE_API_BASE,
    "sync_timeout_seconds": 20,
    "sync_start_date": "2026-04-01",
}

def conectar():
    conn = sqlite3.connect("database.db")
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn

# Teste 1: Listar OSs do MercadoPhone
print("=" * 60)
print("TESTE 1: Buscando OSs do MercadoPhone (últimas 10)")
print("=" * 60)

try:
    listagem = listar_os_mercado_phone(config, page=1, limit=10)
    ids = extrair_ids_os_listagem_mercado_phone(listagem, texto_limpo)
    print(f"✓ IDs encontrados: {ids}\n")
except Exception as e:
    print(f"❌ Erro ao listar: {e}\n")
    sys.exit(1)

# Teste 2: Detalhar a primeira OS
if ids:
    print("=" * 60)
    print(f"TESTE 2: Detalhe da OS {ids[0]}")
    print("=" * 60)
    
    try:
        detalhes = detalhar_os_mercado_phone(ids[0], config)
        if isinstance(detalhes, dict) and "data" in detalhes:
            payload = detalhes["data"]
        else:
            payload = detalhes if isinstance(detalhes, dict) else {}
        
        # Extrair informações importantes
        codigo = texto_limpo(valor_payload(payload, ("codigo",), ("id",)))
        situacao = texto_limpo(valor_payload(payload, ("situacaoDescricao",), ("status",)))
        cliente = texto_limpo(valor_payload(payload, ("clienteNome",), ("cliente", "nome"), ("cliente",)))
        
        print(f"Código: {codigo}")
        print(f"Situação: {situacao}")
        print(f"Cliente: {cliente}")
        print()
        
        # Verificar se está no banco
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, status FROM os WHERE origem_integracao='mercado_phone' AND id_externo_integracao=?",
            (codigo,)
        )
        row = cursor.fetchone()
        
        if row:
            os_id, status_atual = row
            print(f"✓ OS existe no banco:")
            print(f"  - ID no banco: {os_id}")
            print(f"  - Status atual no banco: {status_atual}")
            print(f"  - Status no MercadoPhone: {situacao}")
            print(f"  - Status normalizado: {normalizar_status_os(situacao)}")
            
            if status_atual != situacao:
                print(f"  ⚠️  DIFERENÇA DETECTADA! Status não está sincronizado")
            else:
                print(f"  ✓ Status sincronizado")
        else:
            print(f"❌ OS não encontrada no banco com id_externo: {codigo}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao detalhar: {e}\n")
        import traceback
        traceback.print_exc()

print()
