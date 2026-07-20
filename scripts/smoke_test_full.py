import sys
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app, conectar, BACKUP_DIR

LOGIN_DATA = {"usuario": "admin", "senha": "irflow@2024"}
ROUTES_GET = [
    "/app",
    "/app/ordens",
    "/app/backup",
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
LEGACY_REDIRECTS = {
    "/dashboard": "/app",
    "/backup": "/app/backup",
    "/nova": "/app/ordens/nova",
}

failures = []
results = []


def autenticar(client):
    response = client.post("/login", data=LOGIN_DATA, follow_redirects=False)
    results.append(("POST", "/login", response.status_code))
    if response.status_code not in (302, 303):
        failures.append(("POST", "/login", response.status_code, response.data[:200]))
        return False

    with client.session_transaction() as sess:
        if not sess.get("usuario_id"):
            failures.append(("CHECK", "session login", 500, b"Sessao nao foi autenticada"))
            return False
    return True


def registrar_resultado(method, route, response, body=None):
    results.append((method, route, response.status_code))
    if response.status_code >= 400:
        failures.append((method, route, response.status_code, body or response.data[:200]))
        return None
    if response.is_json:
        return response.get_json()
    return None


def verificar_json_ok(method, route, response):
    payload = registrar_resultado(method, route, response)
    if payload is None:
        return None
    if not payload.get("ok"):
        failures.append((method, route, response.status_code, str(payload).encode("utf-8")))
        return None
    return payload


with app.app_context():
    with app.test_client() as client:
        autenticado = autenticar(client)

        for route, expected in LEGACY_REDIRECTS.items():
            r = client.get(route, follow_redirects=False)
            status = r.status_code
            location = r.headers.get("Location", "")
            results.append(("REDIR", route, status))
            if status not in (301, 302, 303, 307, 308) or not location.endswith(expected):
                failures.append(("REDIR", route, status, location.encode("utf-8")))

        for route in ROUTES_GET:
            r = client.get(route, follow_redirects=True)
            results.append(("GET", route, r.status_code))
            if r.status_code != 200:
                failures.append(("GET", route, r.status_code, r.data[:200]))

        if autenticado:
            payload = verificar_json_ok("GET", "/api/auth/me", client.get("/api/auth/me"))
            if payload and payload.get("usuario", {}).get("perfil") != "admin":
                failures.append(("CHECK", "/api/auth/me perfil", 500, str(payload).encode("utf-8")))

            verificar_json_ok("GET", "/api/constantes", client.get("/api/constantes"))
            dashboard_payload = verificar_json_ok("GET", "/api/dashboard", client.get("/api/dashboard"))
            ordens_payload = verificar_json_ok("GET", "/api/ordens", client.get("/api/ordens"))
            verificar_json_ok("GET", "/api/backup/listar", client.get("/api/backup/listar"))
            verificar_json_ok("GET", "/api/usuarios", client.get("/api/usuarios"))

            if dashboard_payload and "faturamento_total" not in dashboard_payload:
                failures.append(("CHECK", "/api/dashboard payload", 500, str(dashboard_payload).encode("utf-8")))

            if ordens_payload:
                ordens = ordens_payload.get("ordens") or []
                if ordens:
                    os_id = ordens[0].get("id")
                    if os_id:
                        detalhe_payload = verificar_json_ok(
                            "GET",
                            f"/api/ordens/{os_id}",
                            client.get(f"/api/ordens/{os_id}"),
                        )
                        if detalhe_payload and "ordem" not in detalhe_payload:
                            failures.append(("CHECK", f"/api/ordens/{os_id} payload", 500, str(detalhe_payload).encode("utf-8")))

        conn = conectar()
        cur = conn.cursor()
        cur.execute("SELECT id, COALESCE(status, 'Em andamento') FROM os ORDER BY id DESC LIMIT 1")
        row = cur.fetchone()
        conn.close()

        if autenticado and row:
            os_id, status = row
            r = client.post("/atualizar_status", data={"id": str(os_id), "status": status})
            results.append(("POST", f"/atualizar_status (id={os_id})", r.status_code))
            if r.status_code != 200:
                failures.append(("POST", "/atualizar_status", r.status_code, r.data[:200]))

        if autenticado:
            r = client.post("/backup", follow_redirects=True)
            results.append(("POST", "/backup", r.status_code))
            if r.status_code != 200:
                failures.append(("POST", "/backup", r.status_code, r.data[:200]))

            backup_api_payload = verificar_json_ok("POST", "/api/backup/criar", client.post("/api/backup/criar"))
            if backup_api_payload and not backup_api_payload.get("arquivo"):
                failures.append(("CHECK", "/api/backup/criar payload", 500, str(backup_api_payload).encode("utf-8")))

            custo_payload = verificar_json_ok(
                "POST",
                "/api/custos",
                client.post(
                    "/api/custos",
                    json={
                        "descricao": "Smoke Test Custo",
                        "categoria": "Outros",
                        "valor": 1.23,
                        "data": datetime.now().strftime("%Y-%m-%d"),
                        "observacoes": "registro temporario de validacao",
                    },
                ),
            )
            custo_id = custo_payload.get("id") if custo_payload else None
            if custo_id:
                verificar_json_ok(
                    "PUT",
                    f"/api/custos/{custo_id}",
                    client.put(
                        f"/api/custos/{custo_id}",
                        json={
                            "descricao": "Smoke Test Custo Atualizado",
                            "categoria": "Outros",
                            "valor": 2.34,
                            "data": datetime.now().strftime("%Y-%m-%d"),
                            "observacoes": "atualizado",
                        },
                    ),
                )
                verificar_json_ok("DELETE", f"/api/custos/{custo_id}", client.delete(f"/api/custos/{custo_id}"))

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
