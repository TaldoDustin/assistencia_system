import os
import sys
import traceback

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app import app, conectar

LOGIN_DATA = {"usuario": "admin", "senha": "irflow@2024"}

print("TESTANDO SHOPPING LIST API")

with app.app_context():
    with app.test_client() as client:
        # autentica
        r = client.post("/login", data=LOGIN_DATA, follow_redirects=False)
        assert r.status_code in (302, 303), f"Login falhou: {r.status_code}"
        with client.session_transaction() as sess:
            assert sess.get("usuario_id"), "Sessão sem usuario_id"

        # cria item
        payload = {"os_id": 1, "produto_nome": "Peca Teste", "quantidade_solicitada": 2}
        res = client.post("/api/shopping-list", json=payload)
        assert res.status_code == 200
        data = res.get_json()
        assert data and data.get("ok"), f"Falha ao criar: {data}"
        item_id = data.get("id")
        print(" criado id=", item_id)

        # tenta duplicar
        res2 = client.post("/api/shopping-list", json=payload)
        data2 = res2.get_json()
        assert not data2.get("ok"), "Duplicidade nao foi bloqueada"

        # listar
        rlist = client.get("/api/shopping-list")
        assert rlist.status_code == 200
        ldata = rlist.get_json()
        assert ldata.get("total", 0) >= 1

        # grouped
        rg = client.get("/api/shopping-list/grouped")
        assert rg.status_code == 200
        gd = rg.get_json()
        assert gd.get("ok") and isinstance(gd.get("grouped"), list)

        # bloquear compra em andamento por outro usuario
        conn = conectar()
        cur = conn.cursor()
        # cria usuario comprador
        cur.execute("INSERT INTO usuarios (nome, usuario, senha_hash, perfil, ativo) VALUES (?,?,?,?,?)", ("Buyer Test", "buyer_test", "x", "comprador", 1))
        buyer_id = cur.lastrowid
        conn.commit()
        # atualiza item para EM_COMPRA por buyer
        cur.execute("UPDATE shopping_list SET status='EM_COMPRA', responsavel_id=? WHERE id=?", (buyer_id, item_id))
        conn.commit()
        conn.close()

        # agora admin tenta marcar EM_COMPRA -> deve retornar erro
        rp = client.patch(f"/api/shopping-list/{item_id}/status", json={"status": "EM_COMPRA"})
        assert rp.status_code == 400 or rp.status_code == 200
        pd = rp.get_json()
        assert not pd.get("ok"), f"Bloqueio falhou, resposta: {pd}"
        assert "Compra em andamento" in (pd.get("erro") or ""), f"Mensagem inesperada: {pd}"

print("TESTES SHOPPING LIST OK")
