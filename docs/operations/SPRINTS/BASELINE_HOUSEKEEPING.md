# BASELINE — Sprint Housekeeping (Fase 0)

Snapshot gerado em 2026-07-31, antes de qualquer mudança da Sprint Housekeeping
(`docs/operations/SPRINTS/SPRINT_HOUSEKEEPING.md`).

## Commit atual

```
2500418d9db31b154f10dc9af38ee08ecf205794
Merge pull request #17 from TaldoDustin/chore/cicd-1.1-hardening
2026-07-31 10:20:27 -0300
```

`main` sincronizada com `origin/main`, working tree limpo.

## Tag mais recente

`v1.2-cicd-hardening` (série de marcos de engenharia/processo: `v1.0-engineering-foundation` →
`v1.1-hotfix-workflow` → `v1.2-cicd-hardening`). Nenhuma mudança desde a tag — não é necessário criar
uma nova tag nesta baseline.

## PRs abertos

Nenhum (`gh pr list --state open` vazio).

## Estado do CI (últimos runs em `main`)

| Run | Commit | Status | Duração |
|-----|--------|--------|---------|
| 30634059180 | Merge PR #17 (chore/cicd-1.1-hardening) | success | 4m37s |
| 30598143699 | Merge PR #16 (feat/observabilidade-sentry-frontend) | success | 4m42s |
| 30593953898 | docs(vendas): status BR-055–066 pós-merge V1.5 | success | 4m50s |

## Testes e cobertura (medido localmente, `pytest tests/ --cov`)

- **682 testes**, todos passando
- **Cobertura total: 65.22%** (threshold bloqueante: 60%, ver `pyproject.toml`)
- Módulos com cobertura mais baixa (candidatos a atenção futura, fora do escopo desta sprint):
  `irflow_reports.py` (9%), `irflow_mercadophone.py` (27%), `irflow_storage.py` (25%)

## Branches locais (37, antes de qualquer limpeza)

```
chore/centralizar-referencias
chore/centralizar-referencias-os
chore/cicd-1.1-hardening
chore/inc-001-instrumentacao-conexoes
chore/inc-001-instrumentacao-transparente
chore/remove-fly-legacy-references
chore/vendas-service-stub
demo/commercial-preview          ← preservar (ver regra na Fase 3 da sprint)
docs/adr-007-imei-consolidacao
docs/company-sales-materials
docs/engineering-guide-31-adendo
docs/env-example
docs/process-hotfix-workflow
feat/audit-log-central
feat/clientes-dominio
feat/clientes-tela
feat/comercial-1.3.2-detalhes-unidade
feat/comercial-1.3.3-filtros-avancados
feat/comercial-1.3.4-edicao-unidade
feat/estoque-requer-imei
feat/estoque-unidades-imei
feat/password-reset-admin-token
feat/produtos-catalogo
feat/rate-limiting-login
feat/session-inactivity-timeout
feat/tela-unidades-serializadas
feat/vendas-mvp
feat/vendas-preco-catalogo
feat/vendas-v1-4-comissao
fix/catalogo-iphone-17
fix/checklist-conexao-database-locked
hotfix/criar-usuario-erro-mascarado
hotfix/estoque-diff-quantidade-negativa
hotfix/estoque-ordem-parametros-filtro
hotfix/os-numero-mercadophone
hotfix/quantidade-zero-shopping-list
hotfix/rebrand-sidebar-login-fluxoly
hotfix/select-jsx-build-syntax
main
release/ux-001
test/sprint-2-3-usuarios-autorizacao
test/sprint-2-4-regras-negocio-os
test/sprint-2-5-regras-negocio-estoque
test/sprint-2-pricing-shopping
```

## Branches remotas (`origin/*`, sem equivalente local ou distintas)

```
ajuste-render-webhook
chore/fix-ruff-lint-ki-017
docs/customer-feedback-log
feat/vendas-historico-detalhe
feature/shopping-edit-os
feature/shopping-edit-os-pr
feature/shopping-list
fix/csrf-rotas-legadas-escrita
fix/dashboard-kpi-card-overflow
fix/mercadophone-mutacao-em-massa-permissao
fix/mercadophone-webhook-fail-secure
fix/prefer-internal-os
fix/select-fix
refactor/system-audit
worktree-quizzical-cuddling-stardust
```

Nenhuma branch foi analisada por conteúdo ainda — isso é trabalho da Fase 1 (`AUDIT_BRANCHES.md`), não
desta baseline. Esta lista é apenas o inventário bruto no momento zero.

## Conclusão da Fase 0

Baseline íntegra: `main` sincronizada, CI verde, testes passando, cobertura acima do threshold, nenhuma
tag pendente de criação. Liberado avançar para a Fase 1 — Auditoria.
