# Lista de Aparelhos Disponíveis — IR Phones

Ferramenta **interna** de consulta ao estoque de aparelhos da loja, alimentada pela API nova do
MercadoPhone. **Não faz parte do Fluxoly-plataforma** — app standalone, deploy próprio (ADR-013).

- Discovery: `docs/product/research/DISCOVERY_LISTA_PRECOS_PUBLICA.md`
- Arquitetura: `docs/engineering/adr/ADR-013.md`
- Plano Técnico: `docs/engineering/plans/PLAN-lista-aparelhos-disponiveis.md`

## Duas áreas, duas senhas

| Área | Vê |
|---|---|
| **Geral** (vendedores) | modelo, armazenamento, cor, estado, saúde de bateria, preço de venda, disponibilidade |
| **Estoque** (organizador) | + custo, margem, dias em estoque, e a ação de **reservar** (tira a unidade da Geral) |

Nenhum dado de cliente/fornecedor, nem IMEI completo, nem custo chegam à área Geral (allowlist em
`lib/snapshot.ts`, coberto por `test/snapshot.test.ts`).

## Como roda

```
MercadoPhone API ──(job a cada 20 min)──► 2 snapshots no Redis ──► /api/inventory (por papel) ──► página
                                              reservas no Redis ──► /api/reservar (só Estoque)
```

## Desenvolvimento

```bash
npm install
npm test          # vitest
npm run typecheck
```

Sem credenciais, o app usa um store em memória (`MemoryStore`) — bom para testes, não persiste.

## Deploy (resumo — ver Plano Técnico §"Estratégia de migração / deploy")

1. Projeto Vercel `estoque-fluxoly`, Root Directory = `apps/lista-aparelhos-disponiveis`.
2. Provisionar Redis (Upstash via Vercel Marketplace — sucessor do Vercel KV) e vincular ao projeto.
3. Env vars (ver `.env.example`): `MERCADOPHONE_API_KEY`, `SENHA_GERAL`, `SENHA_ESTOQUE`,
   `COOKIE_SIGNING_SECRET`, `SYNC_SECRET` (+ as do Redis, automáticas).
4. `vercel.json` já tem o cron `*/20 * * * *` para `/api/sync`. Se o plano não permitir cron sub-diário,
   usar um GitHub Actions `schedule` chamando `POST /api/sync` com `Authorization: Bearer $SYNC_SECRET`.
5. Rodar `/api/sync` uma vez, conferir `/api/health`.
6. Apontar `estoque.fluxoly.com` para o projeto.
7. **Rotacionar `MERCADOPHONE_API_KEY`** no MercadoPhone (foi exposto em texto puro no chat de Discovery).

## Endpoints

| Rota | Método | Auth |
|---|---|---|
| `/api/session` | POST `{senha}` / DELETE | — |
| `/api/inventory` | GET | cookie (geral/estoque) |
| `/api/reservar` | POST `{id, vendedor}` | cookie estoque |
| `/api/desreservar` | POST `{id}` | cookie estoque |
| `/api/sync` | POST/GET | `SYNC_SECRET` ou `CRON_SECRET` |
| `/api/health` | GET | — |
