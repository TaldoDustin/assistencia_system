import sys
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app, conectar, BACKUP_DIR

ROUTES_GET = [
    "/",
    "/dashboard",
    "/ordens",
    "/nova",
    "/kanban",
    "/estoque",
    "/estoque/cadastro",
    "/reparos",
    "/garantias",
    "/backup",
]

failures = []
results = []

with app.app_context():
    with app.test_client() as client:
        for route in ROUTES_GET:
            r = client.get(route)
            results.append(("GET", route, r.status_code))
            if r.status_code != 200:
                failures.append(("GET", route, r.status_code, r.data[:200]))

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, COALESCE(status, 'Em andamento') FROM os ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()

        if row:
            os_id, status = row
            r = client.post("/atualizar_status", data={"id": str(os_id), "status": status})
            results.append(("POST", f"/atualizar_status (id={os_id})", r.status_code))
            if r.status_code != 200:
                failures.append(("POST", "/atualizar_status", r.status_code, r.data[:200]))

        r = client.post("/backup", follow_redirects=True)
        results.append(("POST", "/backup", r.status_code))
        if r.status_code != 200:
            failures.append(("POST", "/backup", r.status_code, r.data[:200]))

        if os.path.isdir(BACKUP_DIR):
            backups = [n for n in os.listdir(BACKUP_DIR) if n.lower().endswith('.db')]
            results.append(("CHECK", "backup files", 200 if backups else 500))
            if not backups:
                failures.append(("CHECK", "backup files", 500, b"Nenhum backup .db encontrado"))
        else:
            failures.append(("CHECK", "backup dir", 500, b"Pasta de backup nao existe"))

print("=" * 60)
print("SMOKE TEST - IR FLOW")
print("=" * 60)
for method, route, status in results:
    print(f"{method:5} {route:35} -> {status}")

if failures:
    print("\nFALHAS:")
    for method, route, status, body in failures:
        snippet = body.decode("utf-8", errors="ignore") if isinstance(body, (bytes, bytearray)) else str(body)
        print(f"- {method} {route} -> {status} | {snippet[:160]}")
    raise SystemExit(1)

print("\nRESULTADO: TODOS OS TESTES DE SMOKE PASSARAM")
print(f"Data/hora: {datetime.now().isoformat(timespec='seconds')}")
