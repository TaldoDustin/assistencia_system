#!/usr/bin/env python3
"""
Diagnóstico completo da integração Mercado Phone no IR Flow.
Use: python scripts/diagnose_mercadophone.py
"""

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DB_PATH = BASE_DIR / "database.db"
INTEGRATIONS_CONFIG_PATH = BASE_DIR / "integrations.json"


def print_header(titulo):
    print(f"\n{'='*70}")
    print(f"  {titulo}")
    print(f"{'='*70}")


def print_ok(msg):
    print(f"✓ {msg}")


def print_err(msg):
    print(f"✗ {msg}")


def print_warn(msg):
    print(f"⚠ {msg}")


def print_info(msg):
    print(f"ℹ {msg}")


def diagnostico_banco_dados():
    print_header("1. BANCO DE DADOS")
    
    if not DB_PATH.exists():
        print_err(f"Banco n\u00e3o encontrado: {DB_PATH}")
        return False
    
    print_ok(f"Banco encontrado: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Verificar tabelas críticas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = {row[0] for row in cursor.fetchall()}
        
        esperadas = {
            'os',
            'reparos',
            'estoque',
            'integracao_sync_estado',
            'integracao_os_vistas',
        }
        
        encontradas = esperadas & tabelas
        faltantes = esperadas - tabelas
        
        if encontradas == esperadas:
            print_ok(f"Todas as tabelas de integra\u00e7\u00e3o exist\u00e3o ({len(esperadas)})")
        elif encontradas:
            print_warn(f"Tabelas encontradas: {len(encontradas)}/{len(esperadas)}")
            for tab in encontradas:
                print_info(f"  - {tab}")
            if faltantes:
                print_err(f"Tabelas faltantes: {', '.join(faltantes)}")
        else:
            print_err("Nenhuma tabela de integra\u00e7\u00e3o encontrada!")
            conn.close()
            return False
        
        # Verificar coluna origem_integracao em OS
        cursor.execute("PRAGMA table_info(os)")
        colunas_os = {row[1] for row in cursor.fetchall()}
        
        if 'origem_integracao' in colunas_os and 'id_externo_integracao' in colunas_os:
            print_ok("Colunas de rastreamento de origem em OS: OK")
        else:
            print_warn("Colunas de origem em OS podem estar faltando")
        
        # Contar OS importadas do Mercado Phone
        cursor.execute("SELECT COUNT(*) FROM os WHERE origem_integracao = 'mercado_phone'")
        count_mp = cursor.fetchone()[0]
        
        if count_mp > 0:
            print_ok(f"{count_mp} OS importadas do Mercado Phone")
        else:
            print_info("Nenhuma OS importada ainda (normal na primeira execu\u00e7\u00e3o)")
        
        conn.close()
        return True
        
    except Exception as e:
        print_err(f"Erro ao conectar: {e}")
        return False


def diagnostico_configuracoes():
    print_header("2. CONFIGURA\u00c7\u00d5ES DE INTEGRA\u00c7\u00c3O")
    
    if not INTEGRATIONS_CONFIG_PATH.exists():
        print_warn(f"Arquivo de integra\u00e7\u00f5es n\u00e3o encontrado: {INTEGRATIONS_CONFIG_PATH}")
        print_info("Ser\u00e1 criado com defaults na primeira execu\u00e7\u00e3o")
        return False
    
    print_ok(f"Arquivo encontrado: {INTEGRATIONS_CONFIG_PATH}")
    
    try:
        with open(INTEGRATIONS_CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        mp_config = config.get('mercado_phone', {})
        
        api_token = mp_config.get('api_token', '')
        if api_token and len(api_token) > 8:
            token_preview = api_token[:8] + '...' + api_token[-8:]
            print_ok(f"Token configurado: {token_preview}")
        elif api_token:
            print_warn("Token muito curto ou inválido")
        else:
            print_warn("Token não configurado (integração desabilitada)")
        
        sync_enabled = mp_config.get('sync_enabled', True)
        print_info(f"Sincronização automática: {'SIM' if sync_enabled else 'NÃO'}")
        
        sync_interval = mp_config.get('sync_interval_seconds', 30)
        print_info(f"Intervalo de sincronização: {sync_interval}s")
        
        sync_start_date = mp_config.get('sync_start_date', '2026-04-01')
        print_info(f"Data de início (filtro): {sync_start_date}")
        
        return bool(api_token)
        
    except json.JSONDecodeError as e:
        print_err(f"Arquivo de integra\u00e7\u00f5es inválido (JSON): {e}")
        return False
    except Exception as e:
        print_err(f"Erro ao ler configura\u00e7\u00f5es: {e}")
        return False


def diagnostico_ultimas_sincronizacoes():
    print_header("3. HISTÓRICO DE SINCRONIZAÇÕES")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT chave, valor 
            FROM integracao_sync_estado 
            WHERE chave LIKE 'mercado_phone_sync%'
            ORDER BY chave
        """)
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            print_warn("Nenhuma sincronização realizada ainda")
            return False
        
        estado_dict = {row[0]: row[1] for row in rows}
        
        ultima_exec = estado_dict.get('mercado_phone_sync_ultima_execucao', '')
        if ultima_exec:
            try:
                dt = datetime.strptime(ultima_exec, '%Y-%m-%d %H:%M:%S')
                agora = datetime.now()
                delta = agora - dt
                minutos_atras = int(delta.total_seconds() / 60)
                print_ok(f"Última sincronização: {ultima_exec} ({minutos_atras} minutos atrás)")
                
                if minutos_atras < 5:
                    print_ok("Sincronização recente - integração está ATIVA")
                    return True
                else:
                    print_warn(f"Última sincronização há {minutos_atras} minutos")
                    return None  # Inconcluso
            except ValueError:
                print_warn(f"Data em formato inválido: {ultima_exec}")
        else:
            print_warn("Nenhuma data de última execução registrada")
        
        inicializado = estado_dict.get('mercado_phone_sync_inicializado', '')
        print_info(f"Status inicialização: {inicializado or 'não registrado'}")
        
        return False
        
    except sqlite3.OperationalError as e:
        print_err(f"Erro ao acessar tabela de sincronização: {e}")
        return False
    except Exception as e:
        print_err(f"Erro inesperado: {e}")
        return False


def diagnostico_variaveis_ambiente():
    print_header("4. VARIÁVEIS DE AMBIENTE")
    
    var_esperadas = {
        'MERCADO_PHONE_API_TOKEN': 'Token da API Mercado Phone',
        'MERCADO_PHONE_SYNC_ENABLED': 'Habilitar sincronização',
        'MERCADO_PHONE_SYNC_INTERVAL_SECONDS': 'Intervalo em segundos',
        'FLASK_SECRET_KEY': 'Chave secreta Flask',
    }
    
    config_encontradas = {}
    for var, desc in var_esperadas.items():
        valor = os.environ.get(var, '')
        encontrada = bool(valor)
        config_encontradas[var] = encontrada
        
        if var == 'MERCADO_PHONE_API_TOKEN':
            if valor and len(valor) > 8:
                print_ok(f"{var}: configurado")
            elif valor:
                print_warn(f"{var}: configurado mas muito curto")
            else:
                print_warn(f"{var}: NÃO configurado (usar integrations.json)")
        elif var == 'FLASK_SECRET_KEY':
            if valor:
                print_ok(f"{var}: configurado")
            else:
                print_warn(f"{var}: não configurado (usando padrão dev)")
        else:
            print_info(f"{var}: {valor or 'não configurado'}")
    
    return any(config_encontradas.values())


def main():
    print("\n" + "="*70)
    print("  DIAGNÓSTICO DE INTEGRAÇÃO MERCADO PHONE - IR FLOW")
    print("  Versão: 1.0 | Data: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("="*70)
    
    resultados = {
        'banco': diagnostico_banco_dados(),
        'config': diagnostico_configuracoes(),
        'sincronizacao': diagnostico_ultimas_sincronizacoes(),
        'ambiente': diagnostico_variaveis_ambiente(),
    }
    
    print_header("RESUMO DO DIAGNÓSTICO")
    
    if resultados['banco'] and resultados['config']:
        print_ok("Configuração básica: OK")
    else:
        print_err("Problemas na configuração básica - corrigir primeiro")
    
    if resultados['sincronizacao'] is True:
        print_ok("Sincronização ativa e funcionando")
    elif resultados['sincronizacao'] is False:
        print_warn("Sincronização não iniciada ou desabilitada")
    else:
        print_warn("Status de sincronização inconcluso - monitorar próximas horas")
    
    print("\n" + "="*70)
    print("  FIM DO DIAGNÓSTICO")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
