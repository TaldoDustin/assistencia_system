# SPRINT COMERCIAL 1.3.2 — Detalhes da Unidade Serializada

**Status:** CONCLUÍDA
**Período:** 2026-07-22 (dia único)
**Tipo:** Feature (frontend + endpoint de leitura novo)

---

## Objetivo

Ao clicar em uma unidade na listagem (C1.3.1), abrir um painel mostrando IMEI/serial, produto/origem,
status, saúde da bateria, localização, e o histórico completo de eventos (criação + mudanças de
status) — dando ao vendedor/técnico visibilidade total de uma unidade específica.

## Motivação

Sequência definida pelo usuário (CTO) como evolução natural após a listagem (C1.3.1): "clicar em uma
unidade e ver tudo sobre ela" é o próximo valor mais imediato antes de avançar para filtros avançados
(C1.3.3) ou edição (C1.3.4).

---

## Investigação (antes de codar)

- `GET /api/unidades-serializadas/<id>` (`obter_unidade`) já retornava IMEI, status, saúde da bateria,
  localização, `criado_em` — mas sem os campos de origem (produto/estoque) que a listagem (C1.3.1) já
  usa via `LEFT JOIN`. Corrigido: `obter_unidade` passou a usar a mesma query enriquecida.
- **Cliente atual, Data de venda, Garantia:** não existem em lugar nenhum do schema hoje — dependem do
  módulo de Vendas, que não foi implementado. Tratados como placeholder explícito na UI, mesmo padrão
  já usado em `Clientes.jsx` → "Compras".
- **Histórico de movimentações/status:** os dados já existem — toda criação e mudança de status já é
  gravada em `audit_log` (entidade `unidade_serializada`, via `registrar_log_auditoria`) desde a Sprint
  P0.1 — mas **não existia nenhum endpoint em todo o sistema que lesse `audit_log` de volta**. Reportado
  ao usuário antes de implementar (o pedido original era "só consumir API existente"); aprovada a adição
  de um endpoint de leitura novo, por ser estritamente `SELECT` sobre uma tabela já existente, zero
  schema, zero regra de negócio nova.

---

## Arquivos Envolvidos

| Arquivo | Mudança |
|---------|---------|
| `irflow_unidades_serializadas_repository.py` | `buscar_por_id_com_origem` (reaproveita o join de `buscar_paginado`); `buscar_historico` (nova query em `audit_log`, com `LEFT JOIN usuarios` só para exibir o nome de quem fez a mudança) |
| `irflow_unidades_serializadas_service.py` | `obter_unidade` passou a usar a query com origem; `obter_historico` (novo) |
| `irflow_unidades_serializadas_controller.py` | Nova rota `GET /<id>/historico` |
| `frontend/src/api/client.js` | `unidadesSerializadas.historico(id)` |
| `frontend/src/pages/UnidadesSerializadas.jsx` | Componente `DetalheUnidade` (modal), linha da tabela agora clicável |
| `tests/test_unidades_serializadas.py` | 5 novos casos (origem no detalhe + histórico) |

---

## Entregas

| Entrega | Tipo | Status |
|---------|------|--------|
| `GET /api/unidades-serializadas/<id>` inclui origem (produto/estoque) | feat | Concluído |
| `GET /api/unidades-serializadas/<id>/historico` (novo, só leitura) | feat | Concluído |
| Modal de detalhe: IMEI, origem, status, bateria, localização, cadastro | feat | Concluído |
| Placeholders explícitos para Cliente atual/Garantia (dependem de Vendas) | feat | Concluído |
| Timeline de histórico (criação + transições, com autor e data/hora) | feat | Concluído |
| Validação manual end-to-end | test | Concluído |

---

## Critérios de Aceitação

- [x] Clicar em uma linha da listagem abre o painel de detalhe
- [x] Painel mostra IMEI, produto/origem, status, saúde da bateria, localização — com fallback claro
      quando o dado não foi registrado (não erro, não campo vazio sem explicação)
- [x] Cliente atual/Garantia mostrados como placeholder explícito, não omitidos silenciosamente
- [x] Histórico mostra todos os eventos de auditoria já gravados, mais recente primeiro, com quem fez
      e quando
- [x] Nenhuma mudança de schema

---

## Testes Obrigatórios

| Teste | Arquivo | O que validou |
|-------|---------|----------------|
| Suíte completa do domínio | `tests/test_unidades_serializadas.py` | 29 → 34 casos, incluindo os 5 novos (origem no detalhe + histórico), sem regressão nos 29 existentes |
| Lint (`ruff check .`) | Automatizado | 0 erros no repositório inteiro |
| Lint frontend (`eslint .`) / Build (`vite build`) | Automatizado | Nenhum erro novo |
| Fluxo completo (login → listar → clicar → ver detalhe com histórico real) | Manual, Playwright dirigido via script + API | Produto/unidade/2 transições de status semeados via API; modal exibe tudo corretamente, timeline com 3 eventos na ordem certa |

---

## Riscos

Nenhum novo — endpoint de leitura estritamente aditivo, sem mudança de schema ou de regra de negócio
existente.

---

## Dependências

- Depende de: Sprint Comercial 1.3.1 (listagem) e ADR-007 (`unidades_serializadas`) — concluídas.
- Bloqueia: nada diretamente. C1.3.3 (filtros avançados) e C1.3.4 (edição) seguem o mesmo padrão de
  investigação antes de codar.

---

## Definition of Done

- [x] Todos os critérios de aceitação atingidos
- [x] Testes obrigatórios passando, sem regressão
- [x] `CHANGELOG.md` e `PROJECT_STATUS.md` atualizados
- [x] `KNOWN_ISSUES.md` — nenhum bug novo encontrado
- [x] Commits seguem Conventional Commits

---

## Retrospectiva

### O que funcionou bem

Reaproveitar `audit_log` (já gravado desde a Sprint P0.1) evitou qualquer necessidade de nova tabela ou
lógica de negócio — só uma query de leitura nova. O padrão de placeholder explícito (em vez de omitir
campos) já validado em `Clientes.jsx` se repetiu bem aqui.

### O que poderia ter sido melhor

Nada a registrar nesta sprint.

### Dívida técnica gerada

Nenhuma nova.
