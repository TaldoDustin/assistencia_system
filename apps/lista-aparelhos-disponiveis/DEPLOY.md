# Provisionamento — `estoque.fluxoly.com`

Runbook para colocar o app no ar (Vercel + Upstash Redis). Passos marcados **[você]** exigem o painel
da Vercel/MercadoPhone e não podem ser feitos por código.

Ordem: criar projeto → Redis → env vars → deploy → primeiro sync → QA → domínio → rotacionar token.

---

## 0. Segredos a gerar antes de começar

Num terminal:

```bash
openssl rand -base64 32   # COOKIE_SIGNING_SECRET
openssl rand -base64 24   # SYNC_SECRET
```

Escolha também as **duas senhas de acesso** (`SENHA_GERAL` e `SENHA_ESTOQUE`) — diferentes entre si.
Podem ser PINs numéricos (a tela de bloqueio tem `inputmode="numeric"`). Não reaproveite senha de
outro sistema.

---

## 1. Criar o projeto Vercel **[você]**

1. Vercel → **Add New → Project** → importar o repo `TaldoDustin/assistencia_system`.
2. **Root Directory:** `apps/lista-aparelhos-disponiveis` ← passo crítico, não esqueça.
3. **Framework Preset:** `Other`.
4. Build Command: deixar vazio. Output Directory: `public`. Install Command: `npm install` (padrão).
5. **Project Name:** `estoque-fluxoly`.
6. Antes de "Deploy", pule para o passo 2 (adicionar o Redis) — ou faça o deploy e ajuste depois.
7. Depois do primeiro deploy: **Settings → Git → Production Branch** = `feat/lista-aparelhos-disponiveis`
   (temporário, para o QA rodar com cron antes do merge). Troca para `main` no Encerramento.

> Por que projeto separado: ADR-013 — nenhuma env var ou binding compartilhado com os projetos
> `assistencia-system` / `assistencia-system-do1h` (Fluxoly + Demo).

---

## 2. Provisionar o Redis (Upstash) **[você]**

O "Vercel KV" foi descontinuado; agora é Upstash Redis pelo Marketplace.

1. No projeto `estoque-fluxoly` → aba **Storage** → **Create Database** → **Upstash** → **Redis**.
2. Região: `gru1` (São Paulo) se disponível, senão `iad1`.
3. **Connect to Project** → `estoque-fluxoly`, ambiente **Production** (e Preview, se for testar em preview).
4. Isso injeta automaticamente `KV_REST_API_URL` + `KV_REST_API_TOKEN` (ou `UPSTASH_REDIS_REST_URL` /
   `UPSTASH_REDIS_REST_TOKEN`) — o código aceita qualquer um dos dois pares.

---

## 3. Variáveis de ambiente **[você]**

**Settings → Environment Variables**, ambiente **Production** (marque Preview também se for testar lá):

| Nome | Valor |
|---|---|
| `MERCADOPHONE_API_KEY` | o token da API nova do MercadoPhone |
| `SENHA_GERAL` | senha da área Geral (vendedores) |
| `SENHA_ESTOQUE` | senha da área Estoque (organizador) — diferente da Geral |
| `COOKIE_SIGNING_SECRET` | saída do `openssl rand -base64 32` |
| `SYNC_SECRET` | saída do `openssl rand -base64 24` |
| `CRON_SECRET` | (opcional) outro `openssl rand` — usado pelo cron nativo da Vercel |

`KV_REST_API_*` já vêm do passo 2. Depois de salvar, **Deployments → Redeploy** o último.

---

## 4. Cron do sync **[você — decisão de plano]**

`vercel.json` já declara `crons: [{ path: "/api/sync", schedule: "*/20 * * * *" }]`.

- **Plano Pro:** funciona direto. Defina `CRON_SECRET` (passo 3) — a Vercel manda
  `Authorization: Bearer $CRON_SECRET` nas chamadas de cron.
- **Plano Hobby:** cron só roda 1×/dia. Opções: (a) subir para Pro; (b) usar um cron externo
  (GitHub Actions `schedule` ou cron-job.org) chamando
  `POST https://estoque.fluxoly.com/api/sync` com header `Authorization: Bearer <SYNC_SECRET>`.

---

## 5. Primeiro sync + verificação **[você]**

Depois do deploy com as env vars:

```bash
# dispara o job manualmente
curl "https://<url-do-deploy>/api/sync?secret=<SYNC_SECRET>"
# -> {"ok":true,"diagnostico":{"totalCru":583,"aposFiltro":~212,...}}

curl "https://<url-do-deploy>/api/health"
# -> {"ok":true,"idadeMinutos":0,"itensGeral":~212,...}
```

Se `ok:false` com `erro` sobre `MERCADOPHONE_API_KEY` → env var não aplicada / precisa redeploy.

---

## 6. QA Manual (gate ADR-010)

Roteiro em `docs/engineering/plans/PLAN-lista-aparelhos-disponiveis.md` §"Critérios de aceite". Resumo:

1. Abrir o site → tela de bloqueio aparece.
2. Senha **Geral** → lista agrupada por modelo+estado, **sem** coluna de custo, sem botão reservar.
   Conferir uma contagem (ex.: nº de iPhones) contra o painel do MercadoPhone.
3. Sair → senha **Estoque** → agora tem Custo / Margem / Dias e botão **reservar** por linha.
4. Reservar uma unidade → informar vendedor → ela some da aba "Disponíveis" e aparece em "Reservados".
5. Sair, entrar de novo como **Geral** → a unidade reservada **não** aparece.
6. Voltar como Estoque → "Reservados" → **liberar** → ela volta para Disponíveis.
7. Botão **Excel** nas duas áreas baixa `.xlsx` com as colunas visíveis do papel.
8. `curl .../api/inventory` sem cookie → 401. Com cookie Geral, `grep -i custo` na resposta → nada.

---

## 7. Domínio **[você]**

1. **Settings → Domains** → adicionar `estoque.fluxoly.com`.
2. A Vercel mostra um alvo CNAME → criar esse CNAME no DNS de `fluxoly.com`.
3. Aguardar propagação + certificado.

---

## 8. Pós-deploy — rotacionar o token **[você]** (QA-42 / ADR-013)

O `MERCADOPHONE_API_KEY` foi exposto em texto puro no chat da Discovery.

1. No MercadoPhone → gerar uma nova API key, revogar a antiga.
2. Atualizar `MERCADOPHONE_API_KEY` na Vercel → Redeploy.
3. Confirmar `/api/sync` + `/api/health` de novo.

---

## 9. Encerramento (depois do QA aprovado)

- Trocar **Production Branch** de volta para `main`.
- Mergear o PR #68 (squash).
- Formalizar BR-070..078 em `docs/product/BUSINESS_RULES.md`; atualizar `CHANGELOG.md` / `PROJECT_STATUS.md`.
