"""
Regressão do hotfix `quantidade-zero-shopping-list`.

`POST /api/shopping-list` calculava `quantidade` com
`body.get("quantidade_solicitada") or body.get("quantidade")` — como `0` é falsy em Python,
enviar `quantidade_solicitada: 0` caía no operador `or` e virava `body.get("quantidade")`
(ausente), que por sua vez caía no `default=1` do `parse_int`. Resultado: o item era criado
silenciosamente com quantidade `1` em vez de ser rejeitado pela validação
`if quantidade is None or quantidade <= 0`, que nunca era alcançada com o valor real que o
chamador enviou (C-01 + C-04, `docs/engineering/ENGINEERING_GUIDE.md` §11).
"""

import app as _app


def _limpar_item(item_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM shopping_list_logs WHERE shopping_list_id=?", (item_id,))
        conn.execute("DELETE FROM shopping_list WHERE id=?", (item_id,))
        conn.commit()
    finally:
        conn.close()


class TestShoppingCreateQuantidadeZero:
    def test_quantidade_solicitada_zero_e_rejeitada_nao_normalizada_para_um(
        self, client, login_como, usuario_tecnico
    ):
        login_como(client, usuario_tecnico)

        resp = client.post(
            "/api/shopping-list", json={"produto_nome": "Peca Quantidade Zero", "quantidade_solicitada": 0}
        )

        assert resp.status_code == 400
        assert "Quantidade invalida" in resp.get_json()["erro"]

    def test_quantidade_ausente_ainda_usa_default_um(self, client, login_como, usuario_tecnico):
        # Garante que a correcao nao quebrou o comportamento existente: sem quantidade
        # informada, o default de 1 continua valendo.
        login_como(client, usuario_tecnico)

        resp = client.post("/api/shopping-list", json={"produto_nome": "Peca Sem Quantidade"})

        assert resp.status_code == 200
        item_id = resp.get_json()["id"]
        detalhe = client.get(f"/api/shopping-list/{item_id}").get_json()["item"]
        assert detalhe["quantidade_solicitada"] == 1
        _limpar_item(item_id)
