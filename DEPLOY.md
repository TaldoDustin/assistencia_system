# Deploy IR Flow → Fly.io

## Pré-requisitos

1. Conta em https://fly.io (gratuita)
2. CLI do Fly.io instalada:
   ```
   # Windows (PowerShell como admin)
   powershell -Command "iwr https://fly.io/install.ps1 -useb | iex"
   ```
3. Login:
   ```
   fly auth login
   ```

---

## 1. Criar a aplicação

```bash
# Escolha um nome único (ex: meu-irflow)
fly apps create irflow
```

Se o nome já existir, edite `fly.toml` → campo `app = "..."`.

---

## 2. Criar o volume persistente (banco de dados + arquivos)

```bash
fly volumes create irflow_data --region gru --size 1
```

> ⚠️ O volume guarda o `database.db`, `price_tables.json` e backups.
> Sem ele, os dados são perdidos a cada redeploy.

---

## 3. Definir secrets (variáveis sensíveis)

```bash
# Obrigatório: chave secreta do Flask
fly secrets set FLASK_SECRET_KEY="troque-por-uma-chave-aleatoria-longa"

# Opcional: integração Mercado Phone
fly secrets set MERCADO_PHONE_WEBHOOK_TOKEN="seu-token"
fly secrets set MERCADO_PHONE_API_TOKEN="seu-token"
```

---

## 4. Deploy

```bash
fly deploy
```

O Fly.io vai:
- Construir a imagem Docker
- Subir a aplicação em São Paulo (região `gru`)
- Montar o volume em `/data`

---

## 5. Abrir no navegador

```bash
fly open
```

Ou acesse: `https://irflow.fly.dev` (substitua pelo nome da sua app)

---

## Comandos úteis no dia a dia

```bash
# Ver logs em tempo real
fly logs

# Status da aplicação
fly status

# Acessar o banco de dados via SSH
fly ssh console
sqlite3 /data/database.db

# Escalar para zero (pausar e não cobrar)
fly scale count 0

# Voltar a funcionar
fly scale count 1

# Fazer backup manual do banco
fly ssh console -C "cp /data/database.db /data/database.db.bak"
```

---

## Observações

- **Região `gru`**: São Paulo, BR. Mude em `fly.toml` se preferir outro local.
- **Free tier**: 3 VMs compartilhadas gratuitas + 3GB de volume grátis por conta.
- **Sleep automático**: a app NÃO dorme no Fly.io (diferente do Render free tier).
- **Scaling**: para produção com mais usuários, aumente os workers no `Dockerfile`.
