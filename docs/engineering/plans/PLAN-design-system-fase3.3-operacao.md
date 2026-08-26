# Fase 3.3 — Operação (Orders + Kanban + Vendas + Stock + Financeiro + Clientes) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement each fatia deste plano tarefa a tarefa. Steps usam checkbox
> (`- [ ]`) para tracking.

**Goal:** Segunda fatia de composição visual real da Fase 3 (Visual Experience Redesign) — aplicar a
hierarquia de superfície (Panel/ListBlock/LooseMetric/DataTable, Foundation v2 da Fase 3.1) ao Tier 2
("Operação diária", `PLAN-design-system-fase3-visual-experience.md` §9): Orders, Kanban, Vendas, Stock,
Financeiro, Clientes. Sequência imediata à Fase 3.2 (Vitrine), que provou a direção em Login/Shell/
Dashboard.

**Status:** 🟡 Planejado — decisões de composição por tela aprovadas pelo CTO em conversa (ver seção 1).
Nenhum código escrito ainda.

---

## 0. Por que 5 fatias, não 1 PR único

Mesmo critério já usado na Fase 2 (PR 3/4/5 para clusters de tamanho parecido): 6 telas com paths de
composição distintos (contador simples vs. métrica financeira dominante vs. formulário de checkout) cabem
melhor em PRs menores e revisáveis do que um diff único. Cada fatia é seu próprio branch/PR/CI/revisão,
checkpoint arquitetural somente-leitura antes de cada uma (mesmo ritual da Fase 2).

| Fatia | Escopo | Depende de |
|---|---|---|
| 3.3.1 | `DataTable` ganha `getRowProps` (infra) + Orders/Kanban/`OrderTable` (primeiro consumidor real) | 3.2 |
| 3.3.2 | Vendas (Historico + NovaVenda) | 3.3.1 |
| 3.3.3 | Stock | 3.3.1 |
| 3.3.4 | Financeiro | 3.3.1 |
| 3.3.5 | Clientes | 3.3.1 |

---

## 1. Decisões de composição por tela (aprovadas pelo CTO, 2026-08-26)

Nem toda tela tem 1 elemento dominante óbvio — a spec original (`PLAN-design-system-fase3-visual-
experience.md` §2, princípio 1) foi escrita pensando no Dashboard. Para telas de CRUD simples, forçar um
dominante artificial seria pior que não ter nenhum.

| Tela | Dominante? | Detalhe |
|---|---|---|
| **Orders** | Não | 3 contadores (Total/Em aberto/Finalizadas) viram `LooseMetric` lado a lado, sem `Panel`-hero. |
| **Kanban** | N/A | Board de 4 colunas já é uma composição própria (nem card, nem grid uniforme) — **auditoria apenas**, sem mudança de composição esperada. |
| **Vendas — Histórico** | Não | Lista + filtro, mesmo critério de Orders. |
| **Vendas — Nova Venda** | Sim | Resumo do carrinho/total da venda (não um contador — é o próprio objetivo da tela) vira `Panel`. |
| **Stock** | Sim | "Valor Total" do estoque vira `Panel` (número hero); Lotes/Unidades/Críticos viram `LooseMetric`. |
| **Financeiro** | Sim | "Saldo em caixa" (hoje badge pequeno no header) vira `Panel` (número hero), mesmo tratamento do Faturamento no Dashboard. |
| **Clientes** | Não | 3 contadores (Clientes/Com telefone/Com e-mail) viram `LooseMetric`, sem dominante. |

**Bugs conhecidos, decisão do CTO: corrigir junto** (mesma tela já sendo tocada por composição, commit
separado do de composição — bug fix ≠ mudança visual):
- **KI-048** (promises sem `.catch`) — o KI real cobre `Kanban.jsx`, `Stock.jsx::fetchItems`,
  `Vendas.jsx::NovaVenda` (3 pontos) e `Clientes.jsx::PerfilCliente`, além de `NewOrder.jsx`/
  `EditOrder.jsx`/`VendaDetalhe.jsx` (Tier 3, fora desta fase — ver `KNOWN_ISSUES.md`). As 4 telas/pontos
  dentro do escopo desta fase (Kanban, Stock, Vendas, Clientes) são corrigidos junto; o KI só fecha por
  completo quando o Tier 3 (Fase 3.4) também corrigir os 3 pontos restantes.
- **KI-049** (`Clientes.jsx::fetchItems` sem estado de erro dedicado).

`KI-052` (paleta de gráfico cíclica) e `KI-053` (acessibilidade do `DataTable`) **não** são bugs destas 6
telas especificamente — KI-052 é do `ServicesChartCard` (Dashboard, fora deste tier) e KI-053 é corrigido
na Fatia 3.3.1 como parte da extensão do `DataTable` (é a primeira migração real do componente, ver seção
2).

---

## 2. Fatia 3.3.1 — `DataTable` + Orders/Kanban

### 2.1 Extensão do `DataTable` (`components/ui/data-table.jsx`)

**Problema:** `OrderTable.jsx` usa `data-testid={\`order-row-${os.id}\`}` e `data-context-row={os.id}` em
cada `<tr>` — consumidos por `useListContext.js` (realce de "veio de onde" ao voltar de uma edição, UX-001).
O `DataTable` atual não tem como propagar atributos arbitrários por linha; migrar `OrderTable` para
`DataTable` sem resolver isso perderia o realce de navegação silenciosamente.

**Solução:** novo prop opcional `getRowProps?: (row) => object` — spread no `<tr>` junto dos atributos já
existentes (`onClick`/`tabIndex`/`onKeyDown`/`className`). Assinatura:

```jsx
<DataTable
  columns={columns}
  rows={orders}
  getRowKey={(o) => o.id}
  getRowProps={(o) => ({ "data-testid": `order-row-${o.id}`, "data-context-row": o.id })}
  onRowClick={...}
/>
```

- [ ] Adicionar `getRowProps` ao `DataTable`, spread antes das props já fixas (para que `className`/
      `onClick`/`tabIndex` do componente nunca sejam sobrescritos por um retorno de `getRowProps` — ordem de
      spread importa).
- [ ] Atualizar o JSDoc do componente.

### 2.2 KI-053 — acessibilidade da linha clicável

**Problema:** quando `onRowClick` está presente, a `<tr>` responde a clique e `Enter`, mas não a `Espaço`
(padrão comum de ativação), nem expõe `role="button"` — leitor de tela anuncia como `row` comum.

- [ ] `onKeyDown`: também tratar `e.key === " "` (com `e.preventDefault()`, já que Espaço por padrão rola a
      página).
- [ ] Quando `onRowClick` está presente, adicionar `role="button"` à `<tr>` (mantém `role="row"` implícito
      do `<tr>` quando não há `onRowClick` — não regride o caso sem linha clicável).
- [ ] Teste novo: `DataTable` com `onRowClick` responde a Espaço e expõe o role correto.
- [ ] Fechar KI-053 em `KNOWN_ISSUES.md` (mover para Resolvidos, referenciar este commit).

### 2.3 Orders — stats viram `LooseMetric`

`frontend/src/pages/Orders.jsx` (linhas 140-151 na versão atual): grid de 3 `<div className="bg-card
border border-border rounded-xl p-4 text-center">` vira `LooseMetric` (sem moldura), mesmo padrão já usado
no Dashboard (Fase 3.2). Sem `Panel`-hero (decisão da seção 1).

- [ ] Migrar a stats bar para `LooseMetric`.
- [ ] Nenhuma mudança em `applyFilters`/`extractMeta`/`fetchOrdens`/`handleDelete` — confirmar via diff
      isolado desses handlers contra `main` antes do commit.

### 2.4 `OrderTable.jsx` — migração para `DataTable`

`frontend/src/components/orders/OrderTable.jsx` — colunas atuais mapeiam 1:1 para o formato `columns` do
`DataTable`: `#ID` (`render` via `getOrderDisplayNumber`), Cliente, Modelo/Cor (`render` composto —
modelo + cor condicional), Técnico, Status (`render` → `<OrderStatusBadge>`), Data (`render` formatado),
Valor (`render` → `formatCurrency`), e uma coluna final sem header para as ações (editar/excluir, `render`
retorna os 2 `Button` já existentes).

- [ ] Reescrever `OrderTable.jsx` usando `DataTable`, `getRowProps` para `data-testid`/`data-context-row`
      (ver 2.1).
- [ ] `EmptyState` (linhas 10-17 atuais) permanece exatamente como está — `DataTable` não substitui esse
      caminho, só a tabela populada.
- [ ] Nenhuma mudança em `onDelete`/`onEditClick`/nas rotas dos links de edição.

### 2.5 Kanban — auditoria de composição + KI-048

- [ ] Conferir contra os 5 princípios da seção 2 do
      `PLAN-design-system-fase3-visual-experience.md` (hierarquia de superfície, vermelho como
      assinatura, 2 modos, respiro, nem tudo é card) — o board de 4 colunas já usa `TONE` semântico
      (`getStatusVariant`, sem vermelho fora dos badges/estado de erro) e já não é um card uniforme
      (colunas de largura variável por conteúdo, cards de OS com peso claramente secundário aos
      cabeçalhos de coluna). Expectativa: nenhum achado de composição, registrar no relatório da fatia
      se algo aparecer.
- [ ] **KI-048** — `fetchOrdens` usa `.then()` sem `.catch()`; adicionar o mesmo tratamento já usado em
      `Orders.jsx::fetchOrdens` (`toast.error` + `setLoadError(true)` + `setLoading(false)`). Commit
      separado do de composição.

### 2.6 Testes e validação (3.3.1)

- [ ] Suíte completa passando, nenhuma regressão.
- [ ] Novo teste do `DataTable` (Espaço/`role="button"`, 2.2).
- [ ] `Orders.test.jsx` atualizado para os novos seletores (`LooseMetric` não usa `text-center`, ajustar
      asserções que dependiam da classe antiga se houver).
- [ ] Lint 0 erros, build ok.
- [ ] QA visual: Orders (stats + tabela) e Kanban (auditoria) em Chrome real, Light + Dark.

---

## 3. Fatia 3.3.2 — Vendas (Histórico + Nova Venda)

`frontend/src/pages/Vendas.jsx` (667 linhas, 2 abas: `Historico()` linha 50, `NovaVenda()` linha 280).

### 3.1 Histórico — sem dominante

- [x] Tabela de histórico migra para `DataTable` (mesmo padrão da seção 2.4), `getRowProps` para o mesmo
      mecanismo de `nav-context-highlight` já usado aqui (`NAV_CONTEXT_KEY = "vendas-historico"`).
- [x] Nenhuma mudança em `applyFilters`/paginação/`useDebounced`.

### 3.2 Nova Venda — resumo do carrinho vira `Panel`

- [x] Bloco de resumo/total da venda (grid de 2 colunas) migra para `Panel`/`PanelContent`, mesmos campos,
      total em destaque (`text-lg` → `text-2xl`). Card de confirmação ("Venda concluída") também migrado
      para `Panel` — mesmo elemento conceitual (resumo dominante da ação), em estado diferente.
- [x] Nenhuma mudança em `FORMAS_PAGAMENTO`/validação/submissão do formulário.

### 3.3 KI-048 — 3 promises sem `.catch` em `NovaVenda`

- [x] Identificados e corrigidos os 3 pontos (`tiposGarantiaApi`/`clientesApi`/`unidadesApi`). O ponto de
      `tiposGarantiaApi` (sem `.finally` associado) ganhou `toast.error` explícito — era o único caso real
      de "tela presa" (nenhum estado de loading dependia dele, mas o catch evita a rejection não tratada).
      Os outros 2 (`clientesApi`/`unidadesApi`) já tinham `.finally()` restaurando o estado de loading —
      `catch` adicionado apenas para tratar a rejection de forma simétrica ao `res?.ok ? ... : []` já
      existente (mesmo resultado visual: resultados vazios, sem toast, mesmo padrão de busca silenciosa).
- [x] Commit separado do de composição (bug fix ≠ visual).
- [x] Teste novo: rejeição da busca de tipos de garantia dispara `toast.error`.

### 3.4 Validação (3.3.2)

- [x] Suíte completa, lint, build.
- [x] Fechar a fatia de KI-048 referente a `Vendas.jsx` (1 dos 4 pontos totais do KI — os outros 3 são de
      `Clientes.jsx`, seção 6).
- [ ] QA visual: Histórico (tabela) + Nova Venda (Panel do resumo), Light + Dark — não executado nesta
      fatia (mesma limitação de ambiente já registrada em KI-027, sessão não persiste no navegador de
      automação; validado via testes automatizados + revisão de código).

---

## 4. Fatia 3.3.3 — Stock

`frontend/src/pages/Stock.jsx` (515 linhas).

- [x] Stats: "Valor Total" sai do grid uniforme e vira `Panel` dominante (número hero);
      "Lotes"/"Unidades"/"Críticos (≤2)" viram `LooseMetric`.
- [x] "Reposição sugerida" — tabela interna migra para `DataTable`; o container ao redor (título + botão
      "Atualizar sugestões") permanece como está, só a tabela muda.
- [x] Lista principal de itens de estoque migra para `DataTable`.
- [x] **KI-048** — `fetchItems` não tinha `try/catch`; adicionado o mesmo padrão já usado em
      `fetchReposicao` no mesmo arquivo. Commit separado do de composição. 1 teste novo.
- [x] Nenhuma mudança na lógica de filtro/paginação/`fetchReposicao`.
- [x] Suíte completa (143/143), lint 0 erros, build ok. QA visual não executada ao vivo (mesma limitação
      de KI-027).

---

## 5. Fatia 3.3.4 — Financeiro

`frontend/src/pages/Financeiro.jsx` (730 linhas, 3 abas: Movimentações/Contas a Pagar/Contas a Receber).

- [ ] "Saldo em caixa" (linha ~694-706 atual, hoje um badge pequeno no header) vira `Panel` dominante,
      número hero (mesmo tratamento do Faturamento no Dashboard) — sai do header, ganha espaço próprio
      logo abaixo do título da página.
- [ ] As 3 tabelas (Movimentações, Contas a Pagar, Contas a Receber) migram para `DataTable`.
- [ ] Nenhuma mudança em `caixaApi`/`contasPagarApi`/`contasReceberApi`, cálculo de saldo, ou fluxo de
      estorno/cancelamento.
- [ ] Suíte completa, lint, build, QA visual (Light + Dark, incluindo as 3 abas).

---

## 6. Fatia 3.3.5 — Clientes

`frontend/src/pages/Clientes.jsx` (457 linhas).

- [ ] Stats (linha ~292-302 atual): "Clientes"/"Com telefone"/"Com e-mail" viram `LooseMetric`, sem
      dominante (decisão da seção 1).
- [ ] Tabela de clientes migra para `DataTable`.
- [ ] **KI-049** — `fetchItems` ganha estado de erro dedicado (`ErrorState`/`ErrorBanner`, mesmo padrão já
      usado em Orders/Stock), distinto do `loading`/vazio atuais.
- [ ] **KI-048** — os 3 pontos restantes (`PerfilCliente`, promises sem `.catch`) corrigidos, mesmo padrão
      da seção 3.3.
- [ ] Suíte completa, lint, build, QA visual (Light + Dark).
- [ ] Fechar KI-048 e KI-049 em `KNOWN_ISSUES.md` (mover para Resolvidos).

---

## 7. Fora de escopo desta fase, deliberadamente

- Qualquer mudança em endpoints/payloads/regras de negócio — 100% composição + os 2 bug fixes explicitados
  (KI-048/049), nada além disso.
- `KI-051` (token de cor para papel "financeiro" em `Users.jsx`) e `KI-052` (paleta cíclica do
  `ServicesChartCard`) — fora do tier/tela desta fase.
- Migração de `NewOrder.jsx`/`EditOrder.jsx`/`VendaDetalhe.jsx` — Tier 3 (Fase 3.4).
- Reescrever `FilterBar`/`FilterSelect`/paginação — já Foundation (Fase 2), sem mudança aqui.

---

## Ver também

- `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` — direção geral e faseamento
  (§9 define os tiers, §12 a sequência de fases).
- `docs/engineering/plans/PLAN-design-system-fase3.2-vitrine.md` — precedente imediato (Vitrine),
  mesmo padrão de execução (subagent-driven-development, revisão whole-branch antes do merge).
- `docs/engineering/ENGINEERING_GUIDE.md` §3.4/§3.5 — convenções vivas dos recipientes Foundation v2.
