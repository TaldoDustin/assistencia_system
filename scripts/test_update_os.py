#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para testar atualização manual de uma OS no banco
"""
import sqlite3
from datetime import datetime

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Buscar a primeira OS do MercadoPhone
cursor.execute(
    "SELECT id, status, cliente, id_externo_integracao FROM os WHERE origem_integracao='mercado_phone' LIMIT 1"
)
row = cursor.fetchone()

if row:
    os_id, status_atual, cliente, codigo = row
    print(f"OS ID: {os_id}")
    print(f"Código: {codigo}")
    print(f"Cliente: {cliente}")
    print(f"Status atual: {status_atual}")
    print()
    
    # Simular atualização de status
    novo_status = "Finalizado" if status_atual != "Finalizado" else "Em andamento"
    print(f"Alterando status para: {novo_status}")
    
    cursor.execute("UPDATE os SET status=? WHERE id=?", (novo_status, os_id))
    conn.commit()
    
    # Verificar atualização
    cursor.execute("SELECT status FROM os WHERE id=?", (os_id,))
    novo_row = cursor.fetchone()
    
    if novo_row:
        print(f"✓ Status atualizado no banco: {novo_row[0]}")
    else:
        print("❌ Erro ao verificar atualização")
else:
    print("❌ Nenhuma OS do MercadoPhone encontrada")

conn.close()
