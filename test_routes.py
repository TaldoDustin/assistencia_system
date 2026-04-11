import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app

LOGIN_DATA = {"usuario": "admin", "senha": "irflow@2024"}
ROUTES = ["/", "/ordens", "/app", "/app/ordens", "/app/backup"]
LEGACY_REDIRECTS = {
    "/dashboard": "/app",
    "/backup": "/app/backup",
}
failures = []


def autenticar(client):
    response = client.post("/login", data=LOGIN_DATA, follow_redirects=False)
    if response.status_code not in (302, 303):
        raise RuntimeError(f"Falha no login: status {response.status_code}")

    with client.session_transaction() as sess:
        if not sess.get("usuario_id"):
            raise RuntimeError("Login não persistiu na sessão de teste.")


print("=" * 50)
print("TESTANDO ROTAS")
print("=" * 50)

with app.app_context():
    with app.test_client() as anonymous_client:
        for route, expected in LEGACY_REDIRECTS.items():
            response = anonymous_client.get(route, follow_redirects=False)
            location = response.headers.get("Location", "")
            if response.status_code not in (301, 302, 303, 307, 308) or not location.endswith(expected):
                failures.append((route, response.status_code, location))

    with app.test_client() as client:
        try:
            autenticar(client)
            print("\nLogin admin: OK")
        except Exception as e:
            print(f"\nLogin admin: FALHOU ({e})")
            traceback.print_exc()
            raise SystemExit(1)

        for idx, route in enumerate(ROUTES, start=1):
            print(f"\n{idx}. GET {route}")
            try:
                r = client.get(route, follow_redirects=True)
                print(f"   Status: {r.status_code}")
                if r.status_code != 200:
                    failures.append((route, r.status_code, r.data.decode(errors="ignore")[:200]))
                    print(f"   Erro: {failures[-1][2]}")
            except Exception as e:
                print(f"   Exception: {e}")
                traceback.print_exc()
                failures.append((route, "exception", str(e)))

if failures:
    raise SystemExit(1)

print("\nFIM SUCESSO")
