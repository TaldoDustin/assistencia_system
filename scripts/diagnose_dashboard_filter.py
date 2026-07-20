#!/usr/bin/env python3
"""
Diagnóstico do problema de filtro no dashboard.
Verifica se há ordens sem datas preenchidas que impedem o filtro de funcionar.
"""

import sqlite3
import os
from datetime import datetime, timedelta

# Detectar caminho do banco de dados
USER_BASE = os.path.join(os.path.expanduser("~"), "AppData", "Local")
APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(USER_BASE, "IR Flow")
DB_PATH = os.path.join(DATA_DIR, "database.db")

# Se não encontrar em DATA_DIR, tenta APP_DIR
if not os.path.exists(DB_PATH):
    DB_PATH = os.path.join(APP_DIR, "database.db")

def diagnose():
    if not os.path.exists(DB_PATH):
        print(f"❌ Banco de dados não encontrado")
        print(f"   Procurado em: {DB_PATH}")
        print(f"   DATA_DIR: {DATA_DIR}")
        print(f"   APP_DIR: {APP_DIR}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("DIAGNÓSTICO DO FILTRO DE DATA NO DASHBOARD")
    print("=" * 70)
    
    # 1. Total de ordens
    cursor.execute("SELECT COUNT(*) FROM os")
    total_os = cursor.fetchone()[0]
    print(f"\n📊 Total de Ordens: {total_os}")
    
    # 2. Ordens com data vazia/NULL
    cursor.execute("""
        SELECT COUNT(*) FROM os 
        WHERE data IS NULL OR data = '' OR LENGTH(TRIM(data)) = 0
    """)
    os_sem_data = cursor.fetchone()[0]
    print(f"   ⚠️  Ordens SEM data: {os_sem_data} ({100*os_sem_data/total_os:.1f}%)")
    
    # 3. Ordens com data preenchida
    cursor.execute("""
        SELECT COUNT(*) FROM os 
        WHERE data IS NOT NULL AND data != '' AND LENGTH(TRIM(data)) > 0
    """)
    os_com_data = cursor.fetchone()[0]
    print(f"   ✓ Ordens COM data: {os_com_data} ({100*os_com_data/total_os:.1f}%)")
    
    # 4. Range de datas
    if os_com_data > 0:
        cursor.execute("""
            SELECT MIN(data), MAX(data) FROM os 
            WHERE data IS NOT NULL AND data != '' AND LENGTH(TRIM(data)) > 0
        """)
        row = cursor.fetchone()
        min_data, max_data = row[0], row[1]
        print(f"\n📅 Range de datas:")
        print(f"   Data mais antiga: {min_data}")
        print(f"   Data mais recente: {max_data}")
    
    # 5. Distribuição de datas
    print(f"\n📈 Distribuição de ordens por data (últimas 10):")
    cursor.execute("""
        SELECT data, COUNT(*) as qtd 
        FROM os 
        WHERE data IS NOT NULL AND data != '' AND LENGTH(TRIM(data)) > 0
        GROUP BY data
        ORDER BY data DESC
        LIMIT 10
    """)
    rows = cursor.fetchall()
    if rows:
        for data, qtd in rows:
            print(f"   {data}: {qtd} ordem(ns)")
    else:
        print("   (Nenhuma ordem com data)")
    
    # 6. Testar filtragem
    print(f"\n🧪 TESTE DE FILTRAGEM:")
    
    # Test 1: Filtro com data válida (últimos 30 dias)
    today = datetime.now().strftime("%Y-%m-%d")
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT COUNT(*) FROM os
        WHERE data >= ? AND data <= ?
    """, (thirty_days_ago, today))
    count_30d = cursor.fetchone()[0]
    print(f"   Últimos 30 dias ({thirty_days_ago} a {today}): {count_30d} ordem(ns)")
    
    # Test 2: Verificar estrutura da tabela
    cursor.execute("PRAGMA table_info(os)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}
    print(f"\n📋 Coluna 'data' tipo: {columns.get('data', 'NÃO ENCONTRADA')}")
    
    # Test 3: Ver exemplo de ordens sem data
    if os_sem_data > 0:
        print(f"\n⚠️  Exemplo de {min(5, os_sem_data)} ordens SEM data:")
        cursor.execute("""
            SELECT id, cliente, tipo, status, data 
            FROM os 
            WHERE data IS NULL OR data = '' OR LENGTH(TRIM(data)) = 0
            LIMIT 5
        """)
        for os_id, cliente, tipo, status, data in cursor.fetchall():
            print(f"   OS #{os_id}: {cliente} | {tipo} | Status: {status} | Data: '{data}'")
    
    conn.close()
    print("\n" + "=" * 70)

if __name__ == "__main__":
    diagnose()
