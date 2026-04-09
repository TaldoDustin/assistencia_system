import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app

print("=" * 50)
print("TESTANDO ROTAS")
print("=" * 50)

with app.app_context():
    with app.test_client() as client:
        print("\n1. GET /")
        try:
            r = client.get('/')
            print(f"   Status: {r.status_code}")
            if r.status_code != 200:
                print(f"   Erro: {r.data.decode()[:200]}")
        except Exception as e:
            print(f"   Exception: {e}")
            traceback.print_exc()
        
        print("\n2. GET /ordens")
        try:
            r = client.get('/ordens')
            print(f"   Status: {r.status_code}")
            if r.status_code != 200:
                print(f"   Erro: {r.data.decode()[:200]}")
        except Exception as e:
            print(f"   Exception: {e}")
            traceback.print_exc()

print("\nFIM SUCESSO")
