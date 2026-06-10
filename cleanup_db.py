from app import conectar
conn = conectar()
cur = conn.cursor()
cur.execute("DELETE FROM shopping_list WHERE produto_nome LIKE 'Peca Teste%'")
cur.execute("DELETE FROM shopping_list_logs WHERE shopping_list_id NOT IN (SELECT id FROM shopping_list)")
cur.execute("DELETE FROM usuarios WHERE usuario='buyer_test'")
conn.commit()
conn.close()
print('Cleanup done')
