# Marcador de teste — Dry-Run 2B (rollback de infraestrutura)

Este arquivo existe só para disparar o provisionamento de um Render PR Preview novo, limpo, a partir de
`main`/`6bb2ede`, para o Dry-Run 2B da Operação Release 1.0 (Parte B).

**Não é o mesmo preview da PR #22** (`srv-d9t2ms0u01pc73bmuaqg`) — aquele permanece suspenso e intocado
como evidência do INC-003, conforme decisão do CTO registrada em
`docs/company/GO_LIVE_PLAN.md` (seção "Preview Seguro (pré-requisito do Dry-Run 2B)").

Este preview novo já nasce com a correção implementada em
`docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md` (guard `IS_PULL_REQUEST`, correção do
KI-035, `environment` do Sentry corrigido — KI-036).

Objetivo do exercício: validar o ciclo real de rollback contra infraestrutura Render (push → auto-deploy
→ revert → push → auto-deploy → confirmação), sem tocar produção.

Data: 2026-08-11.
