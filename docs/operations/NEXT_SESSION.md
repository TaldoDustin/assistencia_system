# NEXT_SESSION — Onde retomar

**Última atualização:** 2026-08-11
**Estado do repositório:** `main` limpa, sincronizada com `origin/main` em `5497a72`, CI 6/6 verde.

> Este arquivo é o ponto de partida rápido da próxima sessão — não substitui `PROJECT_STATUS.md`
> (estado vivo completo), `KNOWN_ISSUES.md` (lista de bugs) nem `docs/operations/INCIDENTS/` (incidentes).
> Sempre releia os três antes de agir, conforme o protocolo deste `CLAUDE.md`.

---

## Estado do Git

```
main         5497a72680472ca346d76e63b239763639856aa1
origin/main  5497a72680472ca346d76e63b239763639856aa1
CI            6/6 verde
working tree  limpa
```

**Branches locais preservadas, não apagar sem decisão explícita:**
- `dry-run/rollback-f5fdb23` / `dry-run/rollback-872496e` — Dry-Run 1A/1B (Rollback Git, concluído)
- `test/render-preview-isolation` (base da PR #22, evidência do INC-003)
- `fix/preview-seguro-inc003-ki035` — já mergeada (PR #23), pode ser apagada quando quiser, sem urgência
- `dry-run/2b-infra-rollback-render` (local + `origin/dry-run/2b-infra-rollback-render`) — base da
  **PR #24**, Dry-Run 2B em andamento, **não apagar**

**PR #22** (`https://github.com/TaldoDustin/assistencia_system/pull/22`) — **aberta, não mergeada, não
fechada** — preserva evidência do INC-003. Não fechar/mergear sem decisão explícita.

**PR #23** — ✅ **MERGEADA** (`6bb2ede`, 2026-08-11). Implementou o Preview Seguro (INC-003 Frente B) +
correções KI-035/KI-036. Confirmado em produção: Render `irflow-backend` "Deploy live for 6bb2ede",
Vercel Production `6bb2ede` (via GitHub Deployments API).

**PR #24** (`https://github.com/TaldoDustin/assistencia_system/pull/24`, `[render preview]`) — **aberta,
em andamento** — Dry-Run 2B (rollback de infraestrutura Render). Ver seção própria abaixo.

**Render PR Preview da PR #22** (`srv-d9t2ms0u01pc73bmuaqg`) — **continua suspenso** desde 2026-08-10.
Não reativar — preserva evidência do INC-003. **Não é o mesmo preview da PR #24.**

**Render PR Preview da PR #24** — provisionado, ver "achado a confirmar" abaixo.

---

## O que foi concluído nesta sessão (2026-08-11)

### 1. Discovery + Plano Técnico de "Preview Seguro" (aprovado pelo CTO)
Consolidou INC-003 Frente B + KI-035 + KI-036 num único plano
(`docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md`). Restrição adicionada na aprovação: a
captura de `IntegrityError` em `migrations/runner.py` (KI-035) precisa ser específica à constraint
`schema_migrations.id`, nunca um `except` genérico — implementada assim.

### 2. Implementação + Testes + QA Manual + Revisão Arquitetural (ciclo `ADR-010` completo)
- `fluxoly_config.py`: `IS_PULL_REQUEST` novo; `BACKGROUND_JOBS_ENABLED` incorpora
  `and not IS_PULL_REQUEST`.
- `app.py`: log `preview_background_jobs_desativados` no boot; `environment` do Sentry distingue
  `preview`/`production`/`development`.
- `migrations/runner.py`: captura restrita de `IntegrityError` (só `schema_migrations.id`).
- 751 testes existentes + 10 novos, `ruff check .` limpo.
- QA manual: 2 cenários (reprodução do INC-003 + baseline sem regressão), backend real, banco/disco
  descartáveis, nunca `database.db`.
- Revisão Arquitetural (4 eixos `ADR-010`): 3 limpos, 1 achado real — endpoints manuais de
  `api_mercadophone.py` continuam alcançáveis por sessão `admin`/`tecnico` real num preview, sem
  checagem de `IS_PULL_REQUEST` → registrado como **KI-037**, decisão do CTO de não expandir o escopo.

### 3. Encerramento do ciclo — KI-035/KI-036 resolvidos, INC-003 resolvido
`KNOWN_ISSUES.md`, `PROJECT_STATUS.md`, `CHANGELOG.md`, relatório do INC-003 (nova seção 12) atualizados.

### 4. PR #23 aberta, auditada e mergeada
Auditoria final (commits, arquivos tocados, `api_mercadophone.py` confirmado intocado — KI-037 fora do
escopo, `mergeable: MERGEABLE`, `mergeStateStatus: CLEAN`) antes do merge. Duas correções de
consistência documental encontradas na auditoria e corrigidas num commit à parte (`f67774c`) antes do
merge: `GO_LIVE_PLAN.md` ainda justificava o bloqueio do Dry-Run 2B por QA/Revisão pendentes (já
concluídas); `PROJECT_STATUS.md` ainda dizia "PR não aberta ainda".

### 5. Checkpoint pós-merge — produção confirmada
`main`/`origin/main` = `6bb2ede`. CI pós-merge 6/6 (uma ressalva registrada: o job "Docker Build" ficou
com o registro individual preso em `in_progress`/`conclusion: null` na API do GitHub apesar de todos os
passos internos terem sucesso — artefato de sincronização conhecido da API de Actions, não uma falha
real; a conclusão da *run* já estava fechada como sucesso). Vercel Production confirmado via GitHub
Deployments API (`6bb2ede`, `vercel[bot]`, `state: success`). Render confirmado **pelo usuário no
painel** — "Deploy live for 6bb2ede" no serviço `irflow-backend` (não consigo confirmar isso por API
nesta sessão, não há `RENDER_API_KEY` disponível).

**Ambiguidade resolvida:** o que parecia uma discrepância (`dd960eb` + "Suspended by you" no painel)
era o **Preview da PR #22**, não produção — `dd960eb` só existe na branch `test/render-preview-isolation`
(base da PR #22), nunca esteve em `main`. Confirmado por fora: `irflow-backend-pr-22.onrender.com` → 503
"Service Suspended" (esperado); `irflow-backend.onrender.com/health` → 200 (produção saudável).

### 6. Decisão do CTO: critérios de autorização do Dry-Run 2B
Registrada em `docs/company/GO_LIVE_PLAN.md` (seção "Preview Seguro", subseção "Critérios de autorização
do Dry-Run 2B"):
- Preview **novo**, nunca reaproveitar o da PR #22.
- KI-037 aceito como risco residual **para este exercício específico**, mitigado operacionalmente:
  nenhuma sessão `admin`/`tecnico` real dentro do preview do teste; smoke test restrito a rotas
  públicas/leitura; camada de configuração (`MERCADO_PHONE_API_TOKEN` vazio/inválido,
  `MERCADO_PHONE_SYNC_ENABLED=0`, `IR_FLOW_ENABLE_BACKGROUND_JOBS=0`) reforçada manualmente nesse preview.

### 7. Dry-Run 2B iniciado — PR #24 aberta, EM ANDAMENTO, checkpoint aberto
Branch `dry-run/2b-infra-rollback-render` a partir de `main`/`6bb2ede`, commit `1347fe1`
(`RENDER_PREVIEW_TEST_MARKER_2B.md`). PR #24 aberta com `[render preview]` no título.

**Achado a confirmar antes de continuar** (checkpoint aberto, não resolvido nesta sessão): sondagem
externa (`curl`) mostrou `irflow-backend-pr-24.onrender.com/health` já respondendo `200 ok` — ou seja, o
preview **já subiu** antes de qualquer confirmação de que a camada de configuração manual (item da
seção 6 acima) foi aplicada. Isso sugere que o preview não está em modo Manual como o da PR #22 (ou já
foi disparado), e que o primeiro boot pode ter acontecido com credenciais herdadas do serviço-base, como
no INC-003 original — a diferença é que agora o guard de código (`IS_PULL_REQUEST`) deveria ter impedido
o job automático de rodar mesmo assim (validado por QA nesta mesma sessão), mas isso **não foi confirmado
por log real do Render** ainda, só inferido pelo comportamento esperado do código.

**Não têm confirmação nesta sessão (dependem do painel Render, sem `RENDER_API_KEY` disponível):**
1. Se o serviço da PR #24 é realmente distinto de `srv-d9t2ms0u01pc73bmuaqg`.
2. Se o commit ativo bate com `1347fe1`.
3. Se o preview está em modo Manual ou Automatic (explicaria por que já subiu sozinho).
4. Se `preview_background_jobs_desativados` aparece nos logs do boot.
5. Se há qualquer log de `mercadophone_sync_*` (não deveria haver).
6. Valores atuais de `MERCADO_PHONE_SYNC_ENABLED`/`IR_FLOW_ENABLE_BACKGROUND_JOBS`/`MERCADO_PHONE_API_TOKEN`
   nesse preview específico — herdados ou já sobrescritos.

---

## Decisões tomadas (CTO, 2026-08-11)

- Preview Seguro: correção aprovada, implementada, testada, revisada, mergeada, deployada.
- KI-037: aceito como risco residual — fora do escopo da PR #23, tratado só operacionalmente para o
  Dry-Run 2B (sem sessão admin real no preview do teste).
- Dry-Run 2B: autorizado a começar, com preview novo (nunca o da PR #22) e sequência rígida —
  **provisionar → confirmar configuração segura → confirmar logs de boot → só então smoke test/commit
  marcador/revert** — não pular etapas, exatamente porque o INC-003 mostrou que testar antes de confirmar
  a configuração pode gerar efeito externo real mesmo com disco/banco isolados.

## Decisões pendentes

1. As 6 confirmações do painel Render listadas acima (item 7).
2. Se a camada de configuração não foi aplicada antes do primeiro boot (bem provável, dado o achado),
   decidir se isso é aceitável (código já protegeu) ou se exige suspender e reprovisionar o preview da
   PR #24 do zero, desta vez com a configuração aplicada antes do primeiro boot.
3. Resto da sequência do Dry-Run 2B (commit marcador → auto-deploy → `git revert` → push → confirmação →
   suspender preview) — **não iniciado ainda**, aguardando as confirmações acima.
4. Correção de código do KI-037 (fora de escopo até agora) — sprint própria, não decidida.

---

## Próximo passo exato

**Não avançar para o commit marcador / `git revert` do Dry-Run 2B.** Primeiro, obter do usuário (painel
Render) as 6 confirmações listadas na seção 7 acima sobre o preview da PR #24. Com base nelas, decidir se
o preview atual serve para o resto do exercício ou se precisa ser suspenso e reprovisionado com a
configuração aplicada antes do boot.

## O que NÃO fazer ainda

- Não reativar/tocar o preview da PR #22 (`srv-d9t2ms0u01pc73bmuaqg`) — evidência do INC-003.
- Não fazer o commit marcador, `git revert` ou qualquer smoke test autenticado no preview da PR #24 antes
  das 6 confirmações.
- Não usar sessão `admin`/`tecnico` real dentro de nenhum preview (mitigação operacional do KI-037).
- Não mergear a PR #24 — é um exercício descartável, não uma feature.
- Não corrigir o KI-037 sem decisão explícita de abrir escopo/sprint própria.

## Issues abertos relevantes

`KI-037` (endpoints manuais do MercadoPhone alcançáveis por sessão real num preview, risco residual
aceito) é o único issue novo desta sessão. `KI-035`/`KI-036`/`INC-003` — resolvidos. Lista completa de
KIs abertos em `docs/operations/KNOWN_ISSUES.md`.
