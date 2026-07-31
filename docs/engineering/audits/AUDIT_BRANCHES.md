# AUDIT_BRANCHES — Investigação por Conteúdo (Sprint Housekeeping)

**Data:** 2026-07-31
**Fase:** Sprint Housekeeping — Fase 1 (Auditoria), item 5 de 6
**Método:** `git branch --merged`/`--no-merged` para status de merge (verificação de árvore de commits, não
de nome) + `git log`/`git diff --stat`/inspeção de conteúdo para cada branch não-mergeada. **Nenhuma
branch foi apagada, mergeada ou modificada nesta etapa** — regra da sprint: nunca apagar sem investigar
por conteúdo antes, e `demo/commercial-preview` preservada por padrão.

---

## Resumo

| Categoria | Quantidade | Ação nesta fase |
|-----------|:--:|------------------|
| Locais mergeadas em `main` | 38 | Nenhuma — candidatas seguras para a Fase 3, `git branch -d` (não `-D`) |
| Remotas mergeadas em `origin/main`, sem branch local | 21 | Nenhuma — mesma observação, via `git push origin --delete` |
| Locais **não** mergeadas | 3 | Investigadas individualmente abaixo |
| Remotas **não** mergeadas, sem branch local | 5 | Investigadas individualmente abaixo |

---

## Branches mergeadas (seguras, verificado por `git branch --merged main`)

Git confirma pela árvore de commits (não pelo nome) que todo commit destas branches já é alcançável a
partir de `main`. Baixo risco de remoção — mas ainda assim, remoção é trabalho da **Fase 3**, não desta
auditoria.

<details>
<summary>38 branches locais mergeadas (clique para expandir)</summary>

`chore/centralizar-referencias`, `chore/centralizar-referencias-os`, `chore/cicd-1.1-hardening`,
`chore/inc-001-instrumentacao-transparente`, `chore/remove-fly-legacy-references`,
`chore/vendas-service-stub`, `docs/adr-007-imei-consolidacao`, `docs/engineering-guide-31-adendo`,
`docs/env-example`, `docs/process-hotfix-workflow`, `feat/audit-log-central`, `feat/clientes-dominio`,
`feat/clientes-tela`, `feat/comercial-1.3.2-detalhes-unidade`, `feat/comercial-1.3.3-filtros-avancados`,
`feat/comercial-1.3.4-edicao-unidade`, `feat/estoque-requer-imei`, `feat/estoque-unidades-imei`,
`feat/password-reset-admin-token`, `feat/produtos-catalogo`, `feat/rate-limiting-login`,
`feat/session-inactivity-timeout`, `feat/tela-unidades-serializadas`, `feat/vendas-mvp`,
`feat/vendas-preco-catalogo`, `feat/vendas-v1-4-comissao`, `fix/catalogo-iphone-17`,
`fix/checklist-conexao-database-locked`, `hotfix/criar-usuario-erro-mascarado`,
`hotfix/estoque-diff-quantidade-negativa`, `hotfix/estoque-ordem-parametros-filtro`,
`hotfix/os-numero-mercadophone`, `hotfix/quantidade-zero-shopping-list`,
`hotfix/rebrand-sidebar-login-fluxoly`, `hotfix/select-jsx-build-syntax`, `release/ux-001`,
`test/sprint-2-3-usuarios-autorizacao`, `test/sprint-2-4-regras-negocio-os`,
`test/sprint-2-5-regras-negocio-estoque`, `test/sprint-2-pricing-shopping`

</details>

<details>
<summary>21 branches remotas mergeadas, sem branch local (clique para expandir)</summary>

`origin/chore/cicd-1.1-hardening`, `origin/chore/fix-ruff-lint-ki-017`,
`origin/chore/remove-fly-legacy-references`, `origin/docs/customer-feedback-log`,
`origin/docs/process-hotfix-workflow`, `origin/feat/produtos-catalogo`,
`origin/feat/tela-unidades-serializadas`, `origin/feat/unidades-serializadas`,
`origin/feat/vendas-historico-detalhe`, `origin/feature/shopping-edit-os`,
`origin/feature/shopping-edit-os-pr`, `origin/feature/shopping-list`,
`origin/fix/csrf-rotas-legadas-escrita`, `origin/fix/dashboard-kpi-card-overflow`,
`origin/fix/mercadophone-mutacao-em-massa-permissao`, `origin/fix/mercadophone-webhook-fail-secure`,
`origin/fix/prefer-internal-os`, `origin/fix/select-fix`, `origin/hotfix/criar-usuario-erro-mascarado`,
`origin/release/ux-001`, `origin/test/sprint-2-3-usuarios-autorizacao`

</details>

---

## Branches não mergeadas — análise individual

### `demo/commercial-preview` — **PRESERVAR** (regra explícita da sprint)

7 commits (2026-07-17), 17 arquivos, ~805 linhas — modo de demonstração comercial real (Clientes real +
preview de Vendas/Financeiro/Insights, `Financeiro.jsx`, `Insights.jsx`, nota de posicionamento na tela
de preview). Já documentado em `CHANGELOG.md`/`PROJECT_STATUS.md` como modo de demo intencional. **Não
apagar, não mergear integralmente** — decisão já tomada antes desta auditoria, apenas confirmada aqui.

### `chore/inc-001-instrumentacao-conexoes` — provável superada, candidata a remoção

Commit único (2026-07-23), 79 linhas em `app.py` — instrumentação temporária de conexões para
investigar INC-001. **Superada** por `chore/inc-001-instrumentacao-transparente` (2026-07-27, já
mergeada em `main`) — versão posterior, mais completa (68 arquivos vs. 1), do mesmo trabalho. Os
marcadores centrais (`_ConexaoRastreada`, `IR_FLOW_DEBUG_CONN_TRACE`) já existem em `main` via a branch
que substituiu esta. Recomendação: confirmar que nada além do já mergeado é único aqui (parece não
haver) e remover — mas por não estar tecnicamente mergeada, `git branch -d` vai recusar; precisaria de
`-D` (force), o que exige confirmação explícita antes de qualquer execução na Fase 3.

### `docs/company-sales-materials` — **conteúdo real não mergeado, não é lixo**

2 commits (2026-07-17): cria `docs/company/CUSTOMER_FEEDBACK.md`, `DEMO_SCRIPT.md`, `FAQ_COMERCIAL.md`,
`SALES_DECK.md`. Investigado arquivo a arquivo contra `main`:

| Arquivo | Já existe em `main`? |
|---------|:--:|
| `docs/company/CUSTOMER_FEEDBACK.md` | Sim — existe em `main` (provavelmente recriado/mergeado por outro caminho) |
| `docs/company/DEMO_SCRIPT.md` | **Não** |
| `docs/company/FAQ_COMERCIAL.md` | **Não** |
| `docs/company/SALES_DECK.md` | **Não** |

`SALES_DECK.md` não é rascunho — está marcado "Primeira versão, 2026-07-17", referencia
`BRAND_IDENTITY.md`/`VISION.md`/`PRODUCT_REQUIREMENTS.md`/`RELEASE_STRATEGY.md` (documentos que
continuam atuais), e é estruturado como material comercial completo (perguntas de comprador,
consistência entre canais). **Isto não é um achado de limpeza — é trabalho de negócio real, pronto,
nunca integrado.** Recomendação: **não tratar como parte da Fase 3 (Limpeza)**. Decisão é do usuário
(Product Owner): mergear como está, revisar antes de mergear, ou confirmar que ficou obsoleto por outro
motivo não visível no diff.

### `origin/ajuste-render-webhook` — provável já integrada por outro caminho, candidata a remoção

Commit único (2026-06-21, "att 21/06"), 13 linhas em `app.py` — introduz `_normalizar_url_publica()` e
fallback de `PUBLIC_BASE_URL` via `VERCEL_URL`. **Este exato mecanismo já existe em `main` hoje**
(`app.py:197-209`, idêntico em estrutura e nome de função). Recomendação: remover — conteúdo já
presente em `main`, aparentemente reimplementado/mergeado por outro commit em algum momento.

### `origin/refactor/system-audit` — obsoleta, anterior à arquitetura atual

Commit único (2026-07-06, "att", sem mensagem descritiva). Cria `claude.md` (minúsculo) e
`docs/ENGINEERING_GUIDE.md` num `docs/` "flat" — **antes** da reorganização por audiência de
`ADR-006` (2026-07-10). Remove `import sqlite3` e `from irflow_validation import ...` de
`irflow_blueprints_api.py`/`app.py` — **ambos presentes e necessários em `main` hoje** (o `import
sqlite3` inclusive foi adicionado deliberadamente no hotfix do bug de `criar_usuario`, sessão recente).
Mergear isso reverteria trabalho posterior. Recomendação: remover — branch de uma linha de
desenvolvimento divergente e já obsoleta, sem valor de conteúdo único que não tenha sido refeito melhor
depois.

### `origin/worktree-quizzical-cuddling-stardust` — obsoleta, conteúdo relevante já em `main`

Nome de branch com padrão de worktree auto-gerado (provável sessão de agente de IA). Commit único
(`ae7c575`, 2026-07-06, "Fix frontend build/dist pipeline") — **não é ancestral de `main`** (hash
diferente), mas o `PROJECT_STATUS.md` já credita esse mesmo fix ("Build/dist pipeline corrigido —
Commit `ae7c575`") na Sprint 1, então o conteúdo foi reaplicado a `main` sob outro commit. Confirmado
arquivo a arquivo: `frontend/src/components/ui/select.jsx` é **idêntico** ao de `main` (0 linhas de
diferença). `frontend/vite.config.js` difere só porque a branch é anterior à Sprint Observabilidade
(não tem a config de `VITE_SENTRY_RELEASE`) e tinha um bloco `preview.proxy` nunca carregado para
`main` — de baixo valor dado o tempo decorrido. Recomendação: remover.

---

## Observação sobre origem das divergências

Duas das branches remotas obsoletas (`refactor/system-audit`, `worktree-quizzical-cuddling-stardust`)
datam de 2026-07-06 — antes da reorganização de documentação (`ADR-006`, 2026-07-10) e antes de boa
parte do trabalho de domínio (Clientes, Produtos, Unidades Serializadas, Vendas). Não é um padrão
recorrente preocupante, é esperado em qualquer repositório ativo por meses — branches experimentais que
perderam a corrida para a versão que realmente foi mergeada.

---

## Resumo de recomendações para a Fase 3

| Branch | Recomendação | Observação |
|--------|--------------|------------|
| `demo/commercial-preview` | **Preservar** | Regra explícita, não é uma recomendação de limpeza |
| 38 locais + 21 remotas mergeadas | Remover (`git branch -d` local / `git push origin --delete` remota) | Seguro — git confirma merge pela árvore de commits |
| `chore/inc-001-instrumentacao-conexoes` | Remover (precisa `-D`, confirmar antes) | Superada por versão mergeada |
| `origin/ajuste-render-webhook` | Remover | Conteúdo já presente em `main` |
| `origin/refactor/system-audit` | Remover | Obsoleta, conflita com decisões posteriores |
| `origin/worktree-quizzical-cuddling-stardust` | Remover | Conteúdo relevante já em `main` |
| `docs/company-sales-materials` | **Não remover — decisão do usuário** | Contém trabalho de negócio real e completo nunca integrado (Sales Deck, Demo Script, FAQ) |

## Próximo passo

`AUDIT_INFRA.md` — Render, Vercel, variáveis de ambiente em produção, confirmação do comportamento de
build da Vercel levantado em `AUDIT_REPOSITORY.md` seção 5.
