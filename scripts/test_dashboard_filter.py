#!/usr/bin/env python3
"""
Teste do filtro de data do dashboard
Simula diferentes cenários de filtragem
"""

import sqlite3
import os
from datetime import datetime, timedelta

# Detectar caminho do banco de dados
USER_BASE = os.path.join(os.path.expanduser("~"), "AppData", "Local")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(USER_BASE, "IR Flow")
DB_PATH = os.path.join(DATA_DIR, "database.db")

if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(APP_DIR, "database.db")

def test_filter(start_date="", end_date="", tecnico=""):
    """Simula o filtro do dashboard backend"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Carrega todas as ordens
    cursor.execute("""
        SELECT id, cliente, data, tecnico, status
        FROM os
        ORDER BY id DESC
    """)
    todas = cursor.fetchall()
    
    # Aplica os filtros (lógica do backend)
    filtradas = []
    for os_id, cliente, data, tecnico_db, status in todas:
        # Filtro de técnico
        if tecnico and tecnico_db != tecnico:
            continue
        
        # Filtro de data
        if (start_date or end_date) and not data:
            continue
        if start_date and data and data < start_date:
            continue
        if end_date and data and data > end_date:
            continue
        
        filtradas.append((os_id, cliente, data, tecnico_db, status))
    
    conn.close()
    return filtradas

# Testes
print("=" * 80)
print("TESTES DE FILTRAGEM DO DASHBOARD")
print("=" * 80)

tests = [
    {
        "nome": "SEM FILTRO (mostrar todas)",
        "start_date": "",
        "end_date": "",
        "tecnico": "",
    },
    {
        "nome": "FILTRO: Data entre 2026-05-03 e 2026-06-07",
        "start_date": "2026-05-03",
        "end_date": "2026-06-07",
        "tecnico": "",
    },
    {
        "nome": "FILTRO: Data entre 2026-05-01 e 2026-05-05",
        "start_date": "2026-05-01",
        "end_date": "2026-05-05",
        "tecnico": "",
    },
    {
        "nome": "FILTRO: Data >= 2026-05-03 (sem fim)",
        "start_date": "2026-05-03",
        "end_date": "",
        "tecnico": "",
    },
    {
        "nome": "FILTRO: Data <= 2026-06-07 (sem início)",
        "start_date": "",
        "end_date": "2026-06-07",
        "tecnico": "",
    },
]

for test in tests:
    print(f"\n🧪 {test['nome']}")
    print(f"   start_date: '{test['start_date']}'")
    print(f"   end_date: '{test['end_date']}'")
    
    resultado = test_filter(test['start_date'], test['end_date'], test['tecnico'])
    print(f"   ✓ Resultado: {len(resultado)} ordem(ns)")
    for os_id, cliente, data, tecnico, status in resultado:
        print(f"      - OS #{os_id}: {cliente} | {data} | {status}")

print("\n" + "=" * 80)

# Agora vamos testar enviando os parâmetros corretamente do Frontend
print("\nTESTANDO ENVIO DE PARÂMETROS DO FRONTEND:")
print("=" * 80)

import json
from urllib.parse import urlencode

test_params = {
    "startDate": "2026-05-03",
    "endDate": "2026-06-07",
    "tecnico": ""
}

# Simula o que o Dashboard.jsx faz
filtered_params = {k: v for k, v in test_params.items() if v}
print(f"\n1. Parâmetros do React (antes de filtrar vazios):")
print(f"   {json.dumps(test_params, indent=3)}")

print(f"\n2. Parâmetros filtrados (após remover vazios):")
print(f"   {json.dumps(filtered_params, indent=3)}")

# Simula o que client.js faz
query_string = urlencode(filtered_params)
print(f"\n3. Query string enviada à API:")
print(f"   /dashboard?{query_string}")

# O backend recebe start_date e end_date (não startDate e endDate!)
# Verificar se há mismatch de nomes
print(f"\n⚠️  POSSÍVEL PROBLEMA ENCONTRADO!")
print(f"   Frontend envia: startDate, endDate")
print(f"   Backend espera: start_date, end_date")
print(f"   Isso pode ser traduzido em client.js ou no backend!")
