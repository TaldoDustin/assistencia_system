#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Verificar OSs antigas do MercadoPhone
cursor.execute('SELECT id, cliente, status, origem_integracao, id_externo_integracao FROM os WHERE origem_integracao="mercado_phone" LIMIT 10')
rows = cursor.fetchall()

print("=== Primeiras 10 OSs do MercadoPhone ===")
for row in rows:
    print(row)

# Contar total
cursor.execute('SELECT COUNT(*) FROM os WHERE origem_integracao="mercado_phone"')
total = cursor.fetchone()[0]
print(f'\nTotal de OSs MercadoPhone: {total}')

# Verificar se há OSs sem id_externo_integracao
cursor.execute('SELECT COUNT(*) FROM os WHERE origem_integracao="mercado_phone" AND (id_externo_integracao IS NULL OR id_externo_integracao="")')
sem_id = cursor.fetchone()[0]
print(f'OSs sem id_externo_integracao: {sem_id}')

conn.close()
