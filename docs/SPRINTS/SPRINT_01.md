# SPRINT 01 — Correções Críticas e Shopping List

**Status:** CONCLUÍDA  
**Período:** 01/06/2026 – 21/06/2026  
**Tipo:** Bug fixes + Feature

---

## Objetivo

Resolver 4 bugs críticos identificados em auditoria pós-deploy e entregar o módulo de lista de compras.

## Motivação

A auditoria de abril/2026 identificou bugs bloqueantes no fluxo central de OS.
O módulo de Shopping List era a próxima prioridade de negócio: rastrear necessidade de peças sem planilhas externas.

---

## Arquivos Envolvidos

| Arquivo | Mudança |
|---------|---------|
| `irflow_blueprints_api.py` | Novo endpoint `GET /api/precos/sugerir`; CRUD shopping_list |
| `frontend/src/pages/NewOrder.jsx` | Auto-fill `valor_cobrado` via `useEffect` |
| `frontend/src/pages/EditOrder.jsx` | Auto-fill com flag `initialized.current`; fix campo `cor` |
| `frontend/src/api/client.js` | Fix URL PDF IR Phones; fix `historico-cliente`; client `shoppingList` |
| `frontend/src/pages/Compras.jsx` | Nova página de lista de compras |
| `frontend/src/pages/ShoppingList.jsx` | Nova página |
| `frontend/src/components/ui/EditShoppingItemModal.jsx` | Modal de edição |
| `frontend/src/components/shopping/ShoppingModal.jsx` | Modal de adição |
| `.gitignore` | Remoção do `.env` do repositório (commit `832945c`) |

---

## Entregas

| Entrega | Tipo | Status |
|---------|------|--------|
| `GET /api/precos/sugerir` | Feature (bug fix) | Entregue |
| Auto-fill `valor_cobrado` em NewOrder | Feature (bug fix) | Entregue |
| Auto-fill seguro em EditOrder (flag `initialized`) | Fix | Entregue |
| Fix URL PDF IR Phones | Fix | Entregue |
| Fix rota `historico-cliente` | Fix | Entregue |
| Fix campo `cor` limpo ao trocar modelo | Fix | Entregue |
| CRUD Shopping List (backend) | Feature | Entregue |
| Página Compras (frontend) | Feature | Entregue |
| EditShoppingItemModal | Feature | Entregue |
| Remoção do `.env` do repositório | Segurança | Entregue |
| Correção do build/dist pipeline | Chore | Entregue |

---

## Critérios de Aceitação

- [x] `valor_cobrado` auto-preenchido ao selecionar modelo + reparo em OS nova
- [x] `valor_cobrado` não sobrescrito ao abrir OS existente para edição
- [x] PDF IR Phones exportado corretamente (sem 404)
- [x] Histórico de cliente sem erro 404
- [x] Campo `cor` limpo ao trocar modelo em EditOrder
- [x] CRUD da lista de compras com workflow de status
- [x] Modal de edição de item de compra funcional
- [x] `.env` removido do histórico de push

---

## Testes na Entrega

| Tipo | Ferramenta | Status |
|------|-----------|--------|
| Teste shopping list | `test_shopping_list.py` | Ad-hoc, banco real |
| Smoke test geral | `smoke_test_full.py` | Ad-hoc, banco real |
| E2E | Playwright | Não executado formalmente |
| Testes unitários | — | Ausentes |

---

## Bugs Resolvidos (de KNOWN_ISSUES.md)

| Issue | Severidade | Commit |
|-------|-----------|--------|
| KI-008 — Auto-fill `valor_cobrado` ausente | Crítico | fix: auto-preencher valor_cobrado |
| KI-009 — URL PDF IR Phones incorreta | Alto | fix: auto-preencher valor_cobrado... |
| KI-010 — `historico-cliente` 404 | Médio | fix: auto-preencher valor_cobrado... |
| KI-011 — Campo `cor` não limpo | Médio | fix: auto-preencher valor_cobrado... |

---

## Dívida Técnica Adicionada

Nenhuma nova dívida estrutural. Os commits sem padrão ("att 09/06 5", "S") agravam TD-07 (mensagens de commit).

---

## Lições Aprendidas

1. **O bug de `valor_cobrado` estava em produção desde o deploy.** Usuários preenchiam manualmente sem saber que havia tabela de preços. Testes de aceitação no deploy teriam detectado isso.
2. **Flag `initialized.current`** foi necessária para evitar sobrescrita no EditOrder — edge case que não seria óbvio sem teste específico.
3. **Commits sem padrão** dificultaram a rastreabilidade — qual commit corrigiu qual bug não estava claro sem leitura do `.TESTING_REPORT.md`.

---

## Definition of Done — Verificação

- [x] Todos os 4 bugs do `.TESTING_REPORT.md` com status ✅
- [x] Shopping List acessível e funcional em produção
- [x] Nenhuma regressão nas funcionalidades da Sprint 0
- [ ] Testes automatizados para as features entregues — **não atingido**
- [ ] Commits com padrão Conventional Commits — **não atingido**
