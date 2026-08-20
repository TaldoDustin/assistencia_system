# PLAN-design-system-fase2 — Fluxoly Design System (Fase 2: Foundation + Expansão às 24 telas)

**Data:** 2026-08-19
**Feature:** iniciativa de produto/UX, sem regra de negócio nova — decisão do CTO em conversa (mesmo gate
da Fase 1: "apresentar plano e aguardar aprovação" do `CLAUDE.md`, por envolver mais de 3 arquivos; não é
o ciclo `ADR-010` completo, que é obrigatório só para feature com regra de negócio nova, `ENGINEERING_GUIDE.md`
§12)
**Status:** 🟡 Em andamento — PRs 1 (Foundation), 2 (`ChecklistDevice.jsx`), 3
(Orders/Kanban/NewOrder/EditOrder) e 4 (Estoque/Unidades Serializadas/Produtos) mergeados, PR 5 (Vendas +
VendaDetalhe + Financeiro + Clientes) ainda não iniciado

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
| 1 | **Foundation Fase 2** — `Badge` semântico, `EmptyState`/`ErrorState`/`LoadingState`, padrão visual de filtros, convenção de Motion discreta, documentação. Nenhuma tela redesenhada. | ✅ Mergeado (PR #54) |
| 2 | `ChecklistDevice.jsx` — golden standard, primeira aplicação real da Foundation | ✅ Mergeado (PR #55) |
| 3 | Orders + Kanban + NewOrder + EditOrder (corrige divergência de cor de status do Kanban) | ✅ Mergeado (PR #56) |
| 4 | Stock + Unidades Serializadas + Produtos | ✅ Mergeado (PR #57) |
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

## PR 2 — ChecklistDevice.jsx (golden standard, escopo detalhado)

Redesenho puramente visual — nenhuma linha de lógica de negócio, estado, handler de API de dispositivo
(áudio/microfone/câmera) ou payload de `saveChecklist` foi alterada. Mudanças:

- Paleta própria (gradiente slate/azul, `bg-white/8`, `backdrop-blur`) substituída pelos tokens Fluxoly
  (`bg-background`/`bg-card`/`border-border`/`bg-muted`/`text-foreground`/`text-muted-foreground`).
- `rounded-3xl`/`rounded-2xl` (fora da escala) substituídos por `rounded-xl` (containers) via componente
  `Card`/`CardContent` da Foundation.
- Ícones `lucide-react` → Phosphor (`CircleNotch`, `Microphone`, `QrCode`, `DeviceMobile`, `SpeakerHigh`,
  `Camera`, `CheckCircle`), cor decorativa `cyan-300` (fora da paleta) → `text-primary`.
- Estado de "checklist indisponível" migrado para o `ErrorState` da Foundation.
- `Badge` semântico aplicado aos indicadores de status sugerido (cobertura de touch, sugestão de botões).
- `Checkbox` do design system substitui `<input type="checkbox">` cru nos botões físicos.
- Header com ícone + wordmark Fluxoly (mesmo padrão já em produção em `Login.jsx`), `Reveal` envolvendo o
  conteúdo carregado.
- 5 testes novos (Vitest) cobrindo loading/erro/sucesso/interação da grade de touch/salvar.

**QA visual:** estado de erro confirmado no navegador real (Vite dev server, sem backend — falha de rede
cai no mesmo caminho de `!ordem`); padrão de ícone+wordmark confirmado visualmente em `/login` (mesmo
código reaproveitado). Estado carregado (com OS real) validado via Vitest com asserção sobre o DOM
renderizado, não via captura de tela — reproduzir o estado ao vivo exigiria backend + token de checklist
reais, fora do custo-benefício desta verificação.

---

## PR 3 — Orders + Kanban + NewOrder + EditOrder (escopo detalhado)

Redesenho visual das 4 telas do pilar Serviços (fluxo central de OS) + 3 componentes de apoio
(`OrderStatusBadge`, `OrderTable`, `OrderFilters`). Nenhuma lógica de negócio alterada — confirmado por
busca no diff completo por toda função de regra de negócio (`handleSubmit`, `executarSubmit`,
`executarFinalize`, `handleDrop`, `toggleReparo`, `adjustPeca`, chamadas `.create`/`.update`/`.delete`/
`.patchStatus`, etc.): nenhuma aparece em nenhuma linha alterada.

**Unificação de cor de status (objetivo principal do PR, achado da auditoria):** `getStatusColor`
(`lib/constants.js`, retornava classes Tailwind cruas, usado só por `OrderStatusBadge`) substituído por
`getStatusVariant`, que retorna a variante semântica do `Badge` (`info`/`warning`/`success`/`error`/
`neutral`). `OrderStatusBadge` passa a renderizar `<Badge variant={getStatusVariant(status)}>`.
`Kanban.jsx` — que antes redefinia cor por coluna sozinho (`COLUMNS` hardcoded, hues iguais a Orders mas
mecanismo duplicado/divergente) — passa a derivar a cor de cada coluna da mesma `getStatusVariant`, via um
mapa `TONE` local. O card do Kanban ganhou `<OrderStatusBadge status={os.status} />` (import já existia,
nunca tinha sido usado — código morto silencioso porque o nome em PascalCase escapa do
`no-unused-vars`/`varsIgnorePattern` do ESLint).

**Demais mudanças, por arquivo:**
- `OrderFilters.jsx`: reescrito com `FilterBar`/`FilterSelect`/`FilterInput` da Foundation (primeira
  aplicação real desses componentes desde o PR 1) — puramente visual, nenhum parâmetro/comportamento de
  filtragem mudou.
- `OrderTable.jsx`: `EmptyState` no lugar do texto solto; `interactiveRowClassName` (`lib/interaction.js`)
  no hover da linha; ícones lucide → Phosphor.
- `Orders.jsx`: `ListSkeleton` no loading; estado `loadError` novo (só para a carga não-silenciosa) +
  `ErrorState` com retry quando a carga inicial falha e a lista fica vazia — mesmo padrão do Dashboard/
  ChecklistDevice. O polling silencioso a cada 30s continua exatamente como antes (sem toast, sem banner).
  Cores do stats bar (`amber-400`/`emerald-400`) → tokens (`text-warning`/`text-success`).
- `Kanban.jsx`: mesmo padrão de `loadError`/`ErrorState`; `hover:shadow-md` removido do card (violava a
  regra "sem shadow em superfície estática") e `rounded-lg` → `rounded-xl`; ícones → Phosphor.
- `NewOrder.jsx`/`EditOrder.jsx`: ícones → Phosphor; `rose-500` (fora da paleta) → `text-primary`/
  `border-primary` nos destaques de reparo selecionado e sugestão de preço; `rounded-2xl` → `rounded-xl`
  no container do QR do checklist (`EditOrder.jsx`); conteúdo carregado envolvido em `Reveal` (form
  continua um `<form>` real — `Reveal` só o envolve, não o substitui, para não quebrar submit via Enter).

**Testes:** 13 novos (`OrderStatusBadge.test.jsx`, `Orders.test.jsx`, `Kanban.test.jsx`) — as 4 páginas
nunca tinham teste antes deste PR. `NewOrder.jsx`/`EditOrder.jsx` não ganharam teste novo (mudança
puramente de ícone/cor/radius, sem lógica nova a cobrir; escrever teste de formulário completo para essas
duas telas ficaria desproporcional ao escopo visual desta fatia).

**Achados registrados, não corrigidos (fora de escopo):** `KI-048` — `NewOrder.jsx`/`EditOrder.jsx`/
`Kanban.jsx` não tratam rejeição de promise na carga inicial (`.then()` sem `.catch()`), pré-existente.

---

## PR 4 — Estoque + Unidades Serializadas + Produtos (escopo detalhado)

Checkpoint arquitetural somente-leitura do CTO antes de autorizar o início (git/PRs mergeados/docs/escopo/
dependências/riscos/KIs — sem alterar código), como já registrado em `PROJECT_STATUS.md`.

**Achado do checkpoint, resolvido antes de implementar:** `Produtos.jsx` (`CATEGORIA_BADGE`, 4 categorias)
e `UnidadesSerializadas.jsx`/`Vendas.jsx` (`ORIGEM_BADGE`, 2 valores, **duplicado literalmente entre os
dois arquivos**) usam badges categóricos — respondem "que tipo de coisa é isso", não "como está indo
isso". As cores usadas (`zinc`/`fuchsia`/`purple`) não têm variante de severidade correspondente no
`Badge` da Foundation. Apresentei 3 opções ao CTO (forçar nos 5 variants existentes / criar variante nova
não-semântica / não tocar agora) — decisão: **não tocar neste PR**, decisão de Design System sobre badge
de categoria/tag fica pendente, candidata a resolver antes do PR 5 (que repete o `ORIGEM_BADGE`).

**Unificação de status genuíno (onde havia, migrado normalmente):**
- `Stock.jsx`: `estoqueStatusVariant` local (disponível=`success`, esgotado ativo=`error`, esgotado=
  `warning`, inativo=`neutral`) + prioridade de reposição sugerida (`alta`=`error`/`media`=`warning`/
  `baixa`=`neutral`).
- `Produtos.jsx`: disponibilidade (`statusVariant`/`statusLabel`, calculada de `ativo`+`quantidade`) e
  condição (`condicaoVariant` — Novo/Seminovo/Vitrine mapeiam 1:1 em `success`/`warning`/`info`, as 3
  cores já usadas — `emerald`/`amber`/`sky` — cabiam sem forçar nada, diferente do `CATEGORIA_BADGE`).
- `UnidadesSerializadas.jsx`: `statusVariant`/`STATUS_LABEL` (5 estados — `disponivel`=`success`,
  `em_reparo`=`warning`, `devolvido`=`info`, `vendido`=`neutral`, `reservado`=`warning` reaproveitado —
  `reservado` não é produzido por nenhum fluxo real ainda, aguarda Vendas).

Cada domínio manteve sua própria função de mapeamento (local ao arquivo, não centralizada em
`lib/constants.js` como `getStatusVariant` de OS) — usado só naquele arquivo, sem necessidade real de
compartilhar entre páginas, mesmo critério já aplicado ao `TONE` do `Kanban.jsx` no PR 3.

**Demais mudanças:** ícones lucide → Phosphor nos 3 arquivos; `FilterBar`/`FilterSelect`/`FilterInput` nas
3 barras de filtro; `EmptyState`/`ErrorState`/`ListSkeleton` nos 3 fluxos de carga (preservando o texto
exato das mensagens de vazio originais); `Checkbox` do design system substitui `<input type="checkbox">`
cru (`Stock.jsx`/`Produtos.jsx`); `interactiveRowClassName` nas linhas de tabela; `rounded-lg`→`rounded-xl`
nos 3 painéis internos do modal de detalhe de `UnidadesSerializadas.jsx` (mesma classe de ajuste do PR 3).

**Bug introduzido e corrigido durante a própria implementação:** o primeiro `onRetry` do `ErrorState` em
`UnidadesSerializadas.jsx` chamava `setPage((p) => p)` — não muda o estado (`Object.is` no mesmo valor),
então o retry nunca disparava nova busca. Corrigido com um `reloadToken` dedicado no array de dependências
do efeito, antes de rodar os testes.

**Nenhuma lógica de negócio alterada** — confirmado por busca no diff completo por toda função de handler
(`handleSubmit`, `handleDelete`, `carregar`, `salvar`, `abrirEdicao`, chamadas `create`/`update`/`delete`/
`updateStatus`) e por diff isolado byte-a-byte de `handleSubmit`/`handleDelete` (Stock/Produtos) e
`carregar`/`salvar` (UnidadesSerializadas) contra `main` — idênticos. `buscar()` (UnidadesSerializadas) e
`fetchItems` (Stock/Produtos) só ganharam as chamadas `setLoadError` aditivas.

**Testes:** 12 novos (`Stock`/`Produtos`/`UnidadesSerializadas`, nenhuma das 3 tinha teste antes). Suíte
completa 70/70, lint 0 erros, build ok.

**Achado registrado, não corrigido:** `KI-048` estendido — `Stock.jsx::fetchItems` também não trata
rejeição de promise na carga inicial (mesmo padrão já registrado para NewOrder/EditOrder/Kanban no PR 3).

---

## Ver também

- `docs/engineering/plans/PLAN-design-system-fase1.md` — Fase 1 (fundação + Shell + Dashboard).
- `docs/engineering/ENGINEERING_GUIDE.md` §3.2/§3.3 — convenções vivas do Design System.
- `docs/company/BRAND_IDENTITY.md` — autoridade da marca.
