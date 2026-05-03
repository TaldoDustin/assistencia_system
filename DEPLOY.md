
# Deploy IR Flow → Render (backend) & Vercel (frontend)

## Backend (Render.com)

### 1. Crie uma conta em https://render.com

### 2. Novo serviço web
- Clique em **New +** > **Web Service**
- Conecte seu repositório (GitHub/GitLab)
- Escolha o repositório do projeto

### 3. Configuração do serviço
- **Environment**: Docker
- **Docker Build Context**: `.`
- **Dockerfile Path**: `Dockerfile`
- **Start Command**: (deixe em branco, o Dockerfile já define)
- **Port**: 8080

### 4. Variáveis de ambiente
Adicione as variáveis necessárias em **Environment > Add Environment Variable**:
- `FLASK_SECRET_KEY` (obrigatório)
- `MERCADO_PHONE_WEBHOOK_TOKEN` (opcional)
- `MERCADO_PHONE_API_TOKEN` (opcional)
- `MERCADO_PHONE_SYNC_ENABLED=1` (opcional)
- `MERCADO_PHONE_SYNC_INTERVAL_SECONDS=180` (opcional)
- `MERCADO_PHONE_SYNC_TIMEOUT_SECONDS=20` (opcional)
- `MERCADO_PHONE_SYNC_START_DATE=2026-04-01` (opcional)
- `MERCADO_PHONE_DEFAULT_TECNICO=Aguardando definicao` (opcional)
- `IR_FLOW_HOST=0.0.0.0`
- `IR_FLOW_PORT=8080`
- `IR_FLOW_DATA_DIR=/data` (recomendado)
- `RENDER_DISK_PATH=/data` (alternativa)
- `IR_FLOW_CORS_ORIGINS=https://assistencia-system.vercel.app` (ou uma lista separada por vírgula)

> Dica: se usar preview URLs do Vercel, inclua também esses domínios em `IR_FLOW_CORS_ORIGINS`.

### 5. Volume persistente (Disks)
- Em **Disks**, clique em **Add Disk**
- Nome: `irflow_data`
- Mount Path: `/data`
- Size: 1GB (ou mais, conforme necessidade)

### 6. Deploy
- Clique em **Create Web Service**
- O Render irá buildar e subir o backend automaticamente

### 7. Acesso
- O Render fornecerá uma URL pública (ex: `https://irflow-backend.onrender.com`)

---

## Frontend (Vercel)

### 1. Crie uma conta em https://vercel.com

### 2. Novo projeto
- Clique em **Add New... > Project**
- Importe o repositório (ou apenas a pasta `frontend`)

### 3. Configuração
- **Framework Preset**: Vite
- **Root Directory**: `frontend`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`

### 4. Variáveis de ambiente (opcional)
Se precisar apontar para a API do backend Render, adicione:
- `VITE_API_URL=https://irflow-backend.onrender.com/api`

No código, use `import.meta.env.VITE_API_URL` para consumir a URL da API.

### 5. Deploy
- Clique em **Deploy**
- A Vercel irá buildar e publicar o frontend automaticamente

### 6. Acesso
- A Vercel fornecerá uma URL pública (ex: `https://irflow-frontend.vercel.app`)

---

## Observações

- O backend (Render) serve apenas a API e arquivos de dados.
- O frontend (Vercel) serve o app React estático e consome a API do backend.
- Ajuste o CORS no backend se necessário para aceitar requisições do domínio da Vercel.
- Para backups, acesse o disco `/data` no Render via SSH ou painel.
- Backups versionados podem ser criados via `POST /api/backup/criar` enviando `{ "versao": "v2" }`.
- Configuração persistente do Mercado Phone pode ser salva via `POST /api/integracoes/mercadophone/config`.

---

## Passo a passo resumido

1. Suba o backend no Render seguindo as instruções acima.
2. Suba o frontend na Vercel seguindo as instruções acima.
3. Teste o fluxo completo: frontend (Vercel) consumindo a API (Render).
4. Ajuste variáveis de ambiente e CORS conforme necessário.
5. (Opcional) Remova arquivos do Fly.io (`fly.toml`) se não for mais usar.
