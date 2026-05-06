#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de validação das mudanças de sincronização
"""
import sqlite3
import os
from datetime import datetime

print("=" * 70)
print("VALIDAÇÃO DAS MUDANÇAS DE SINCRONIZAÇÃO")
print("=" * 70)
print()

# 1. Verificar arquivo Orders.jsx
print("1️⃣  Verificando mudanças no frontend (Orders.jsx)...")
with open("frontend/src/pages/Orders.jsx", "r") as f:
    content = f.read()
    if "setInterval(fetchOrdens, 30000)" in content:
        print("   ✓ Polling automático adicionado (30 segundos)")
    else:
        print("   ❌ Polling automático NÃO encontrado")

print()

# 2. Verificar mudanças no irflow_mercadophone.py
print("2️⃣  Verificando mudanças no backend (irflow_mercadophone.py)...")
with open("irflow_mercadophone.py", "r") as f:
    content = f.read()
    
    if "status != status_anterior" in content:
        print("   ✓ Comparação de status antes de atualizar")
    else:
        print("   ❌ Comparação de status NÃO encontrada")
    
    if "Atualizado status da OS" in content:
        print("   ✓ Logs de atualização adicionados")
    else:
        print("   ❌ Logs de atualização NÃO encontrados")
    
    if "Sincronização: importadas=" in content:
        print("   ✓ Logs de sincronização adicionados")
    else:
        print("   ❌ Logs de sincronização NÃO encontrados")

print()

# 3. Verificar banco de dados
print("3️⃣  Verificando banco de dados...")
if os.path.exists("database.db"):
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Contar OSs do MercadoPhone
    cursor.execute("SELECT COUNT(*) FROM os WHERE origem_integracao='mercado_phone'")
    total = cursor.fetchone()[0]
    print(f"   ✓ Total de OSs do MercadoPhone: {total}")
    
    # Verificar integracao_sync_estado
    cursor.execute("SELECT COUNT(*) FROM integracao_sync_estado")
    estado_rows = cursor.fetchone()[0]
    print(f"   ✓ Registros de estado de sincronização: {estado_rows}")
    
    conn.close()
else:
    print("   ❌ database.db não encontrado")

print()
print("=" * 70)
print("PRÓXIMOS PASSOS:")
print("=" * 70)
print()
print("1. Reinicie a aplicação (app.py)")
print("2. Verifique os logs do console para:")
print("   - '[MercadoPhone] Sincronização: importadas=X, atualizadas=Y'")
print("   - '[MercadoPhone] Atualizado status da OS X (código Y):'")
print()
print("3. Edite uma OS no MercadoPhone")
print("4. Aguarde 30 segundos para o frontend fazer polling")
print("5. A ordem deve aparecer atualizada na tela")
print()
