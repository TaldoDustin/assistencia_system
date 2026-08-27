# Fase 3.4 — Formulários/Detalhe (NewOrder + EditOrder + VendaDetalhe + ChecklistDevice) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended)
> or superpowers:executing-plans to implement cada fatia deste plano tarefa a tarefa.

**Goal:** Terceira fatia de composição visual real da Fase 3 (Visual Experience Redesign) — aplicar a
hierarquia de superfície (Panel/ListBlock/LooseMetric/DataTable, Foundation v2 da Fase 3.1) ao Tier 3
("Formulário/detalhe", `PLAN-design-system-fase3-visual-experience.md` §9): NewOrder, EditOrder,
VendaDetalhe, ChecklistDevice. Sequência imediata à Fase 3.3 (Operação — Tier 2), que fechou o Tier 2
inteiro.

**Status:** 🟢 Concluído — as 3 fatias (3.4.1 NewOrder/EditOrder, 3.4.2 VendaDetalhe, 3.4.3
ChecklistDevice) implementadas e revisadas. Revisão final whole-branch (2026-08-26) encontrou 0 Critical /
2 Important / 2 Minor — todos corrigidos antes do merge. `KI-048` fechado por completo (Tier 2 + Tier 3).
Branch `feat/design-system-fase3.4-newedit-order` pronta, aguardando merge.

---

## 0. Por que 3 fatias, não 1 PR único

Mesmo critério já usado nas Fases 2 e 3.3: telas com paths de composição distintos cabem melhor em PRs
menores e revisáveis. `NewOrder`/`EditOrder` têm estrutura quase idêntica (mesmo shape de mudança
repetido em 2 arquivos) — cabem no mesmo PR. `VendaDetalhe` tem um dominante real (Total da venda) e
migra uma tabela — path de composição diferente. `ChecklistDevice` é troca pura de recipiente
(`Card`→`Panel`), sem lógica nova — path mais simples dos três, mas arquivo isolado (única tela pública,
sem overlap com os outros dois PRs).

| Fatia | Escopo | Depende de |
|---|---|---|
| 3.4.1 | NewOrder + EditOrder (formulário, sem dominante) + KI-048 (2 pontos) | 3.2 |
| 3.4.2 | VendaDetalhe (Total da venda vira dominante, Itens vira `DataTable`) + KI-048 (1 ponto) | 3.4.1 |
| 3.4.3 | ChecklistDevice (`Card`→`Panel`, puro recipiente) | 3.4.1 |

---

## 1. Decisões de composição por tela (aprovadas pelo CTO, 2026-08-26)

| Tela | Dominante? | Detalhe |
|---|---|---|
| **NewOrder** | Não | Formulário — sem número/dado único (mesmo critério de Orders no Tier 2). As 6 seções (`Cliente`/`Aparelho`/`Serviço`/`Financeiro`/`Peças`/`Observações`), hoje `<section className="bg-card rounded-xl border border-border p-5">` manual, migram para `Panel`/`PanelContent`. As 2 métricas do bloco Financeiro ("Custo total de peças"/"Sugestão de serviço") viram `LooseMetric`. |
| **EditOrder** | Não | Mesma estrutura de NewOrder — mesmo tratamento. Diálogos (`AlertDialog`/`Dialog` de cancelar/checklist QR/garantia) não mudam — são elementos flutuantes, já cobertos pela Foundation (Radix). |
| **VendaDetalhe** | Sim | **Total da venda** — hoje só uma linha no rodapé de um card genérico — vira métrica hero dentro do `Panel` principal (mesmo tratamento de Faturamento/Saldo). Tabela de Itens migra para `DataTable`. Os 3 blocos condicionais (Ajuste Comercial/Comissão/Garantia) viram `Panel`s de peso secundário — são formulários de edição inline, não listas, então mantêm moldura própria (princípio 5 não força "sem moldura" para tudo que não é dominante). |
| **ChecklistDevice** | Não | Sequência de testes, sem dominante — mesmo critério já usado (golden standard da Fase 2, PR2). O wrapper local `Section` troca `Card`/`CardContent` (shadcn cru) por `Panel`/`PanelContent` (Foundation v2) — puramente o recipiente, zero mudança de lógica/fluxo de teste (touch/áudio/microfone/câmera/botões). |

**Bugs conhecidos, decisão do CTO: corrigir junto** (mesma tela já sendo tocada por composição, commit
separado do de composição — bug fix ≠ mudança visual):
- **KI-048** (promises sem `.catch`) — fecha por completo nesta fase. Os 3 pontos restantes:
  `NewOrder.jsx`/`EditOrder.jsx` (`Promise.all` de carga inicial) e `VendaDetalhe.jsx`
  (`tiposGarantiaApi.list().then()`, disparado só quando `podeCorrigirGarantia`).

Nenhum outro KI aberto (`KI-051`/`KI-052`/`KI-055`/`KI-056`) pertence a estas 4 telas.

---

## 2. Fatia 3.4.1 — NewOrder + EditOrder

### Task 1: NewOrder + EditOrder — Panel/LooseMetric + KI-048

**Contexto:** `frontend/src/pages/NewOrder.jsx` e `frontend/src/pages/EditOrder.jsx` têm estrutura quase
idêntica — 6 (NewOrder) / 6 (EditOrder, mais o bloco condicional de checklist) seções em
`<section className="bg-card rounded-xl border border-border p-5 space-y-4">` com um `<h2
className="text-sm font-semibold text-card-foreground">` de título. Nenhuma usa `Panel` (Foundation v2
não existia quando essas telas foram escritas). Componentes disponíveis: `Panel`/`PanelHeader`/
`PanelTitle`/`PanelContent` e `LooseMetric` em `frontend/src/components/ui/` (ver `Stock.jsx`/
`Financeiro.jsx` para exemplos de uso real pós-Fase-3.3).

**Escopo — composição (commit 1):**
- [ ] Em `NewOrder.jsx`: cada `<section>` (Cliente/Aparelho/Serviço/Financeiro/Peças/Observações) migra
      para `<Panel><PanelHeader><PanelTitle>...</PanelTitle></PanelHeader><PanelContent>...</PanelContent></Panel>`
      — título da seção (`<h2>`) vira `PanelTitle`, o resto do conteúdo interno de cada seção fica
      idêntico (mesmos campos, mesmo grid, mesma lógica).
- [ ] No bloco "Financeiro": as 2 caixas `<div className="bg-secondary rounded-xl p-4">` ("Custo total de
      peças" e "Sugestão de serviço") viram `LooseMetric` (número + rótulo, sem moldura própria) — o botão
      "Usar sugestão" permanece ao lado, fora do `LooseMetric`.
- [ ] Repetir exatamente a mesma migração em `EditOrder.jsx` (mesmas 6 seções + bloco Financeiro
      idêntico). O bloco condicional "Checklist do aparelho" (`checklistMeta &&`, hoje `<section
      className="rounded-xl border border-border bg-card p-4">`) também migra para `Panel` — é conteúdo
      informativo (não formulário), mas segue o mesmo recipiente por consistência com o resto da tela.
- [ ] Nenhuma mudança em: `handleSubmit`/`toggleReparo`/`adjustPeca`/`filteredEstoque`/`reparosDisponiveis`/
      `precosApi.sugerir` (NewOrder), `executarSubmit`/`handleFinalize`/`handleCancelOrder`/
      `confirmarGarantiaDialog`/`handleChecklistQr`/diálogos (`AlertDialog`/`Dialog`, EditOrder). Confirmar
      via diff isolado desses handlers contra `main` antes do commit.
- [ ] Nenhuma mudança nos `data-testid` existentes (`order-create-button`, `order-save-button`) nem nos
      `id`/`htmlFor` dos campos (usados por testes existentes).

**Escopo — KI-048 (commit 2, separado):**
- [ ] `NewOrder.jsx`: `useEffect` de carga inicial (`Promise.all([constApi.get(), reparosApi.list(),
      estoqueApi.list()]).then(([c, r, e]) => {...})`) ganha `.catch()` — mesmo padrão já usado em
      `Orders.jsx::fetchOrdens`/`Kanban.jsx::fetchOrdens` (`toast.error` + `setLoading(false)` no catch,
      já que não há `.finally()` aqui).
- [ ] `EditOrder.jsx`: mesmo `useEffect` (`Promise.all([ordensApi.get(id), constApi.get(),
      reparosApi.list(), estoqueApi.list(), tiposGarantiaApi.list()]).then(...)`) ganha `.catch()` — mesmo
      padrão. Atenção: o `.then()` atual já tem um branch de erro para `!osRes?.ok` (`toast.error("Ordem
      não encontrada"); navigate("/ordens")`) — isso cobre falha de negócio (`{ok:false}`), não rejeição de
      rede; o `.catch()` cobre exclusivamente a rejeição (rede/timeout), sem duplicar o toast existente.
- [ ] 2 testes novos (1 por arquivo): rejeição da promise de carga inicial dispara `toast.error` e não
      deixa a tela presa no spinner.
- [ ] Fechar **KI-048 por completo** em `KNOWN_ISSUES.md` (mover para Resolvidos) — este é o último ponto
      pendente do KI (Tier 2 já fechado na Fase 3.3).

**Validação:**
- [ ] Suíte completa passando, nenhuma regressão.
- [ ] `NewOrder.test.jsx`/`EditOrder.test.jsx` atualizados para os novos seletores se necessário
      (`LooseMetric` não usa `bg-secondary rounded-xl p-4` — ajustar asserções que dependiam da classe
      antiga, se houver).
- [ ] Lint 0 erros, build ok.

---

## 3. Fatia 3.4.2 — VendaDetalhe

### Task 2: VendaDetalhe — Panel hero + DataTable + KI-048

**Contexto:** `frontend/src/pages/VendaDetalhe.jsx` — card principal (`<div className="bg-card border
border-border rounded-xl p-6 space-y-5">`, linha ~366) contém cabeçalho (Venda #ID + badge de status),
grid de Cliente/Vendedor/Pagamento, Observações, tabela de Itens (HTML cru) e a linha de Total no rodapé
(`<span className="text-lg font-bold text-foreground">{formatCurrency(venda.valor_total)}</span>`, linha
454). 3 blocos condicionais abaixo (Ajuste Comercial `podeAjustar`, Comissão `podeVerComissao`, Garantia
sempre visível se `itemPrincipal`), cada um `<div className="bg-card border border-border rounded-xl p-4
space-y-3">`.

**Escopo — composição (commit 1):**
- [ ] Card principal migra para `Panel`/`PanelContent`. O Total da venda (linha 452-455) sai do rodapé
      simples e vira o número hero do `Panel` (mesmo tratamento de Faturamento/Saldo — `text-2xl`/`text-3xl`
      ou similar, avaliar contra o resto do conteúdo do painel para não competir com o cabeçalho Venda
      #ID). Cabeçalho (Venda #ID + badge), grid Cliente/Vendedor/Pagamento e Observações permanecem dentro
      do mesmo `Panel`, como conteúdo de apoio ao Total.
- [ ] Tabela de Itens (linhas 412-441, HTML cru com `<table>`/`<thead>`/`<tbody>` manual) migra para
      `DataTable` — colunas: Produto, IMEI, SKU, Valor de tabela, Valor vendido, Desconto, Total (mesmas 7
      colunas atuais, mesmo `render` por coluna). Sem `onRowClick` (tabela é só leitura aqui, diferente de
      Orders/Vendas-Histórico).
- [ ] Os 3 blocos condicionais (Ajuste/Comissão/Garantia) migram cada um para seu próprio `Panel` de peso
      secundário (mantêm moldura — são formulários de edição inline com estado próprio, não listas).
- [ ] Blocos de cancelamento (`cancelando &&`, linha 313) e "Venda cancelada" (linha 353) — avaliar durante
      a implementação se migram para `Panel` também (mesmo padrão de moldura) ou ficam como estão por serem
      estados transitórios/banners, não conteúdo permanente da tela; decisão fica com o implementador,
      documentar a escolha no relatório da task.
- [ ] Nenhuma mudança em `carregar`/`confirmarAjuste`/`confirmarComissao`/`confirmarGarantia`/
      `confirmarCancelamento`/nenhuma regra de permissão (`podeCancelar`/`podeAjustar`/`podeVerComissao`/
      `podeEditarComissao`/`podeCorrigirGarantia`) — 100% composição.

**Escopo — KI-048 (commit 2, separado):**
- [ ] `useEffect` que busca tipos de garantia (`if (podeCorrigirGarantia) { tiposGarantiaApi.list().then((res) => {...}) }`,
      linha ~155-159) ganha `.catch()`. Sem `.finally()` associado — adicionar tratamento de erro visível
      (mesmo critério do ponto `tiposGarantiaApi` de `NovaVenda` na Fase 3.3.2, que também não tinha
      `.finally`): `toast.error` explícito, já que sem isso a lista de tipos de garantia fica
      silenciosamente vazia numa falha de rede, sem qualquer sinal ao usuário.
- [ ] 1 teste novo: rejeição da busca de tipos de garantia dispara `toast.error`.
- [ ] Registrar em `KNOWN_ISSUES.md` que este era o 3º e último ponto do KI-048 (a fatia 3.4.1 já deve ter
      fechado o KI antes desta — se por algum motivo a ordem de execução inverter, fechar aqui).

**Validação:**
- [ ] Suíte completa passando, nenhuma regressão.
- [ ] `VendaDetalhe.test.jsx` atualizado para os novos seletores da tabela de Itens (`DataTable` não usa
      `<table>` cru — ajustar `getByRole`/`querySelector` que dependiam da estrutura antiga, se houver).
- [ ] Lint 0 erros, build ok.

---

## 4. Fatia 3.4.3 — ChecklistDevice

### Task 3: ChecklistDevice — Card → Panel

**Contexto:** `frontend/src/pages/ChecklistDevice.jsx` — wrapper local `Section` (linhas 62-68):

```jsx
function Section({ children }) {
  return (
    <Card>
      <CardContent className="p-5 space-y-4">{children}</CardContent>
    </Card>
  );
}
```

Usado 8 vezes na tela (Identificação, Touch, Alto-falante, Microfone, Câmera, Botões físicos,
Observações, mais o card de cabeçalho com o ícone do aparelho). Import atual: `import { Card, CardContent }
from "@/components/ui/card"`.

**Escopo (commit único — mudança puramente mecânica, sem lógica nova):**
- [ ] Trocar `Card`/`CardContent` por `Panel`/`PanelContent` no wrapper `Section` — `import { Panel,
      PanelContent } from "@/components/ui/panel"` (confirmar path exato do módulo antes, mesmo import
      usado em `Stock.jsx`/`NewOrder.jsx` após a Fatia 3.4.1).
- [ ] Nenhuma mudança em nenhum outro ponto do arquivo — nem nos testes de touch/áudio/microfone/câmera/
      botões, nem no fluxo de salvamento (`saveChecklist`), nem na estrutura de dados enviada à API. Se
      `Panel` tiver um espaçamento/padding padrão diferente de `CardContent className="p-5 space-y-4"`,
      preservar o `p-5 space-y-4` explícito dentro de `PanelContent` para não alterar o layout visual desta
      tela pública (sem QA visual ao vivo disponível nesta sessão, mesma limitação KI-027 — mudança mínima
      reduz risco).
- [ ] Confirmar que nenhum outro arquivo usa esse `Section` local (é definido e usado só dentro de
      `ChecklistDevice.jsx` — não é um componente compartilhado).

**Validação:**
- [ ] Suíte completa passando, nenhuma regressão (`ChecklistDevice.test.jsx` se existir).
- [ ] Lint 0 erros, build ok.

---

## 5. Fora de escopo desta fase, deliberadamente

- Qualquer mudança em endpoints/payloads/regras de negócio — 100% composição + o bug fix explicitado
  (KI-048).
- `KI-051`/`KI-052`/`KI-055`/`KI-056` — não pertencem a nenhuma destas 4 telas.
- Tier 4 (Administrativo) — Fase 3.5, fora desta fase.
- Impressão de recibo (comentário em `VendaDetalhe.jsx` menciona V1.8 do roadmap) — feature não
  solicitada, fora de escopo.

---

## Ver também

- `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` — direção geral e faseamento
  (§9 define os tiers, §12 a sequência de fases).
- `docs/engineering/plans/PLAN-design-system-fase3.3-operacao.md` — precedente imediato (Tier 2), mesmo
  padrão de execução (subagent-driven-development, revisão whole-branch antes do merge, KI-048 corrigido
  junto da composição em commit separado).
- `docs/engineering/ENGINEERING_GUIDE.md` §3.4/§3.5 — convenções vivas dos recipientes Foundation v2.
