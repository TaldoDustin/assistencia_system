"""
Sprint técnica de centralização de referências (2026-07-23).

Escopo: GET /api/constantes expõe os_tipos/garantia_dias a partir de
constantes nomeadas em irflow_core.py (OS_TIPOS_OPCOES,
GARANTIA_REPARO_DIAS_PADRAO) — antes eram literais soltos duplicados em
mais de um lugar do próprio irflow_blueprints_api.py.
"""

from irflow_core import GARANTIA_REPARO_DIAS_PADRAO, OS_TIPOS_OPCOES


class TestConstantesExpoeDadosDeOS:
    def test_constantes_inclui_os_tipos_e_garantia_dias(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/constantes")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["os_tipos"] == OS_TIPOS_OPCOES
        assert body["garantia_dias"] == GARANTIA_REPARO_DIAS_PADRAO

    def test_garantias_usa_o_mesmo_prazo_padrao(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Finalizado")

        resp = client.get("/api/garantias")

        assert resp.status_code == 200
        body = resp.get_json()
        garantia = next((g for g in body["ordens"] if g["id"] == os_id), None)
        assert garantia is not None
        assert garantia["garantia"]["dias_restantes"] <= GARANTIA_REPARO_DIAS_PADRAO
