from app import app, conectar

LOGIN_DATA = {"usuario": "admin", "senha": "irflow@2024"}

with app.app_context():
    with app.test_client() as client:
        r = client.post("/login", data=LOGIN_DATA, follow_redirects=False)
        print('login status', r.status_code)
        with client.session_transaction() as sess:
            print('session usuario_id=', sess.get('usuario_id'))

        payload = {"os_id": 1, "produto_nome": "Peca Teste Debug", "quantidade_solicitada": 2}
        res = client.post("/api/shopping-list", json=payload)
        print('create status', res.status_code)
        try:
            print('json:', res.get_json())
        except Exception as e:
            print('no json, data:', res.data)
