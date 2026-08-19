# PLAN-design-system-fase2 — Fluxoly Design System (Fase 2: Foundation + Expansão às 24 telas)

**Data:** 2026-08-19
**Feature:** iniciativa de produto/UX, sem regra de negócio nova — decisão do CTO em conversa (mesmo gate
da Fase 1: "apresentar plano e aguardar aprovação" do `CLAUDE.md`, por envolver mais de 3 arquivos; não é
o ciclo `ADR-010` completo, que é obrigatório só para feature com regra de negócio nova, `ENGINEERING_GUIDE.md`
§12)
**Status:** 🟡 Em andamento — PR 1 (Foundation) em implementação

> Este documento é efêmero, mesmo princípio do `PLAN-design-system-fase1.md`. O que precisar continuar
> vivo — componentes, convenções — é promovido para `ENGINEERING_GUIDE.md` no Encerramento de cada PR.

---

## Objetivo

A Fase 1 (PRs #41-#49, ver `PLAN-design-system-fase1.md`) formalizou o Design System e o validou em 3
áreas: Shell, Dashboard e Landing Page. As outras 21 páginas do sistema operacional do dia a dia (Orders,
Stock, Vendas, Financeiro, Clientes, etc.) ficaram fora. A Fase 2 estende consistentemente o que já existe
às 24 telas do frontend — **sem** criar uma identidade visual nova.

**Regra de ouro (inegociável em toda a fase):** `docs/company/BRAND_IDENTITY.md` é autoridade máxima sobre
a marca. Nenhum PR desta fase pode alterar `#FF0125`, a fonte Onest, o wordmark, criar paleta nova,
gradiente novo, ou token de spacing/radius/shadow fora da escala já formalizada em `ENGINEERING_GUIDE.md`
§3.2. O trabalho é aplicar a identidade existente de forma consistente, não redefini-la.

---

## Contexto — Auditoria (2026-08-19)

Levantamento das 24 páginas (`frontend/src/pages/`) + componentes de domínio confirmou:

- Design System Fase 1 cobre só Shell, `Dashboard.jsx` e `Landing.jsx`/`components/landing/*` (9 arquivos).
- **Ícones:** 21 páginas legadas usam `lucide-react`; nenhum arquivo mistura as duas bibliotecas — a
  divergência é por página, não dentro do arquivo.
- **Badges de status reimplementados à mão** em ~13 arquivos (`Stock.jsx`, `Financeiro.jsx`,
  `UnidadesSerializadas.jsx`, `Produtos.jsx`, `Vendas.jsx`, entre outros), no padrão
  `bg-emerald-500/10 text-emerald-300 border-emerald-500/30` — já usam `<Badge variant="outline">` com
  `className` sobrescrita, não markup solto; falta só a variante semântica centralizada.
- **Só o `Dashboard.jsx` tem os 4 estados explícitos** (loading/success/empty/error, PR #46). As outras 22
  páginas usam um `Loader2`/spinner genérico sem estado de vazio nem de erro diferenciado.
- **`ChecklistDevice.jsx`** (única tela pública, sem login) roda uma paleta própria (gradiente slate/azul)
  sem relação com a paleta Fluxoly — maior divergência de marca do frontend hoje.
- 2 desvios pontuais de radius/shadow contra a regra "separação por `border`, não por elevação"
  (`Kanban.jsx` hover-shadow em card estático, `Login.jsx` shadow-xl em card de formulário).
- `Kanban.jsx` redefine cor de status sozinho, divergente de `Orders.jsx` para o mesmo domínio (OS).

---

## Escopo — Fora de toda a fase (confirmado pelo CTO)

- Paleta nova, tokens novos de spacing/radius/shadow.
- Mudança de backend/API/schema.
- Refatoração funcional (ex.: unificar lógica de filtros entre Orders/Vendas/Stock) — só a composição
  visual dos filtros é padronizada, parâmetros/comportamento de negócio não mudam.
- Migração mecânica de ícones em massa — ícones migram junto da tela quando ela for efetivamente tocada,
  nunca em PR isolado de find-and-replace.

Qualquer achado fora deste escopo durante a execução: registrar em `KNOWN_ISSUES.md` (ou backlog), não
corrigir automaticamente.

---

## Plano de execução — 8 PRs sequenciais

| PR | Escopo | Status |
|----|--------|--------|
| 1 | **Foundation Fase 2** — `Badge` semântico, `EmptyState`/`ErrorState`/`LoadingState`, padrão visual de filtros, convenção de Motion discreta, documentação. Nenhuma tela redesenhada. | 🟡 Em implementação |
| 2 | `ChecklistDevice.jsx` — golden standard, primeira aplicação real da Foundation | ⬜ |
| 3 | Orders + Kanban + NewOrder + EditOrder (corrige divergência de cor de status do Kanban) | ⬜ |
| 4 | Stock + Unidades Serializadas + Produtos | ⬜ |
| 5 | Vendas + VendaDetalhe + Financeiro + Clientes | ⬜ |
| 6 | Reports + Price Tables + Repair Types + Users | ⬜ |
| 7 | Garantias + Operational Costs + Backup + Shopping List + Compras | ⬜ |
| 8 | QA visual global + correção dos 2 desvios de radius/shadow + documentação final | ⬜ |

Gate por PR: implementação → testes locais → CI 6/6 → revisão → autorização explícita do CTO → merge.

---

## PR 1 — Foundation Fase 2 (escopo detalhado)

**Dentro:**

- `components/ui/badge.jsx`: variantes semânticas novas `success`/`warning`/`error`/`info`/`neutral`
  (estilo "soft" — `bg-X/10 text-X border-X/30`, mesmo peso visual já usado nas reimplementações manuais
  encontradas na auditoria), mapeadas aos tokens já existentes em `index.css`
  (`--color-success`/`warning`/`destructive`/`info`). Variantes existentes (`default`/`secondary`/
  `destructive`/`outline`) preservadas sem alteração de comportamento.
- `components/ui/empty-state.jsx`, `components/ui/error-state.jsx`: generalização do padrão já validado
  em `Dashboard.jsx` (PR #46) — `DashboardEmpty`/`DashboardError`/banner de erro inline — para uso em
  qualquer página.
- `components/ui/loading-state.jsx`: duas formas de skeleton reutilizáveis (lista/tabela, grid de cards),
  generalizadas do padrão já usado no Dashboard.
- `components/ui/filter-bar.jsx`: composição visual (`FilterBar`, `FilterSelect`, `FilterInput`,
  `DateRangeFilter`, `ClearFiltersButton`) — só padroniza a apresentação já usada no Dashboard/páginas
  legadas, sem tocar lógica de filtragem existente em nenhuma página.
- `components/ui/reveal.jsx`: primitivo de Motion para conteúdo que aparece após carregar (linhas, cards,
  estados vazio/erro), respeitando `useReducedMotion` — mesmo princípio já em uso em
  `components/landing/FadeInSection.jsx`, mas para montagem (não scroll), sem alterar a Landing.
- `lib/interaction.js`: classes utilitárias documentadas (CSS puro, `transition-colors` + `focus-visible`)
  para hover/foco de linha de tabela e card — convenção para as fatias seguintes, não uma mudança visual
  em nenhuma tela agora.
- Testes Vitest para os componentes novos.
- `ENGINEERING_GUIDE.md` §3.3 documentando os padrões acima como convenção oficial da Fase 2.

**Fora:** qualquer página em `pages/` ou `components/dashboard|orders|shopping/` — nenhuma tela é tocada
neste PR.

---

## Ver também

- `docs/engineering/plans/PLAN-design-system-fase1.md` — Fase 1 (fundação + Shell + Dashboard).
- `docs/engineering/ENGINEERING_GUIDE.md` §3.2/§3.3 — convenções vivas do Design System.
- `docs/company/BRAND_IDENTITY.md` — autoridade da marca.
