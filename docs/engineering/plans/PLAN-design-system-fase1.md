# PLAN-design-system-fase1 — Fluxoly Design System & Experience (Fase 1: Fundação + Shell + Dashboard piloto)

**Data:** 2026-08-16
**Feature:** iniciativa de produto/UX, sem regra de negócio nova — decisão do CTO em conversa (ver "Contexto
atual" abaixo; não há Discovery formal em `docs/product/` porque não há BR envolvida, conforme
`ENGINEERING_GUIDE.md` §12: o ciclo `ADR-010` completo é obrigatório para feature com regra de negócio —
este plano segue o gate mais simples de "apresentar plano e aguardar aprovação" do `CLAUDE.md`, seção
"Critérios para Aprovar Alterações", por envolver dependências novas + >3 arquivos)
**Status:** Aprovado pelo CTO (2026-08-16) — com ajuste na estratégia de PRs (ver "Plano de Execução"); nenhuma
instalação de dependência ou código de produção antes da aprovação específica do amendment do ADR-001 (ver
abaixo)

> Este documento é efêmero (mesmo princípio do `ADR-010`/`CONTRIBUTING.md` §9). Depois que a fase encerra,
> permanece só como histórico da decisão de implementação. O que precisar continuar vivo — tokens, padrão
> de composição, convenções de teste de componente — é promovido para `ENGINEERING_GUIDE.md`/`ARCHITECTURE.md`
> no Encerramento.

**Estado**

- [x] Plano Técnico — aprovado pelo CTO (2026-08-16)
- [ ] Amendment do ADR-001 — aprovado
- [ ] Implementação
- [ ] Testes
- [ ] QA Manual
- [ ] Revisão Arquitetural (recomendada — toca >3 arquivos, ver `ADR-010`)
- [ ] Encerramento

---

## Objetivo

Estabelecer a fundação formal do Fluxoly Design System (tokens, padrão de composição de componentes,
ícones, motion) e validar esse padrão em dois pontos piloto — Shell da aplicação (Sidebar + Header) e
Dashboard — sem alterar nenhuma regra de negócio, endpoint, schema ou fluxo de autenticação/permissão.

---

## Contexto atual

Investigação do código (não hipótese) antes de propor qualquer mudança:

- **O projeto já usa, de fato, o padrão shadcn/ui — só não formalizado.** `frontend/src/components/ui/button.jsx`
  já é escrito no formato canônico shadcn (`cva` + `@radix-ui/react-slot` + `cn()`), e `frontend/src/lib/utils.js`
  já exporta exatamente o `cn(...) = twMerge(clsx(inputs))` que o CLI do shadcn gera. `class-variance-authority`,
  `clsx`, `tailwind-merge` e 9 pacotes `@radix-ui/react-*` já estão em `frontend/package.json`. Existem 11
  componentes em `frontend/src/components/ui/` (`button`, `input`, `label`, `select`, `dialog`, `alert-dialog`,
  `popover`, `checkbox`, `badge`, `textarea`, mais o `EditShoppingItemModal`, que é específico de domínio,
  não de design system). **Conclusão prática:** esta fase não é "adotar shadcn do zero" — é completar e
  padronizar formalmente o que já existe, usando o CLI oficial para os componentes que faltam e mantendo o
  padrão já em uso para os que já existem.
- **Design Tokens de cor já existem e são maduros.** `frontend/src/index.css` já define uma paleta completa
  via Tailwind v4 `@theme` (`--color-background`, `--color-primary` #FF0125, `--color-sidebar`, `--color-chart-1`
  a `5`, etc.) — a identidade visual (fundo escuro + vermelho de marca + sidebar quase preta) já está
  codificada, não é uma decisão nova desta fase. **O que não existe ainda:** escala formal de espaçamento,
  radius e shadow como tokens nomeados (hoje são valores Tailwind ad-hoc espalhados pelas classes).
- **Ícones hoje são 100% `lucide-react`** (`^1.8.0`, já em `package.json`), usados em `Layout.jsx` e em toda
  página existente. Adotar Phosphor Icons nesta fase é aditivo — coexiste com `lucide-react`, sem migração
  em massa dos ícones já em uso (isso violaria "Fora de Escopo" abaixo e o princípio de escopo cirúrgico do
  `CLAUDE.md`).
  Sonner (`sonner ^2.0.7`) já cobre toast — não é substituído.
- **Motion (`motion`/`motion/react`) não existe no projeto hoje** — dependência nova de fato, sem equivalente
  parcial já presente.
- **`Layout.jsx`** (`frontend/src/components/Layout.jsx`) é o Shell atual: `SidebarContent()` (nav filtrada
  por `perfis`/`adminOnly`) + wrapper `Layout()` (sidebar fixa desktop, drawer mobile controlado por
  `useState`, header mobile com `Menu`/`X` do `lucide-react`). Não há componente `Sidebar` do shadcn em uso —
  a implementação é feita à mão com `<aside>`/classes Tailwind diretas.
- **`Dashboard.jsx`** (`frontend/src/pages/Dashboard.jsx`) já segue boas práticas parciais (lazy loading dos
  3 gráficos via `lazy()`/`Suspense`, `ChartFallback` como estado de loading) — mas usa `Input`/`Select`/`Button`
  do design system atual (não shadcn formal) e não tem estado de erro nem de vazio desenhados explicitamente
  além do `toast.error`.
- **Cobertura de teste de componente frontend é 0% hoje** — confirmado em `docs/operations/PROJECT_STATUS.md`
  (Sprint Comercial 1.1: "Sem framework de teste de componente/unitário no frontend ainda"). Não há Vitest
  nem Testing Library em `package.json`. CI frontend hoje só roda `npm run lint` (G-03) e `npm run build`
  (G-06) — nenhum teste de componente é executado.

---

## Escopo

**Dentro da Fase 1:**

- Design Tokens: formalizar espaçamento/radius/shadow como tokens nomeados em `frontend/src/index.css`
  (`@theme`), documentados em `ENGINEERING_GUIDE.md`. Tokens de cor existentes são preservados, não
  redesenhados.
- shadcn/ui: instalar CLI, completar componentes faltantes usados pelo Shell/Dashboard piloto (`card`,
  `sheet`, `tooltip`, `skeleton`, `separator` já existe via Radix mas sem wrapper shadcn, `sidebar` — o
  componente dedicado do shadcn), alinhando os já existentes ao padrão oficial só quando necessário para
  interoperar com os novos.
- Phosphor Icons: dependência nova, usada **somente** em componentes novos/migrados desta fase (Shell,
  Dashboard). Ícones já em uso em outras páginas continuam `lucide-react`.
- Motion: dependência nova, usada em transições do Shell (abrir/fechar sidebar mobile, hover de item de
  menu) e do Dashboard (entrada de card, troca de estado loading→dado), com `prefers-reduced-motion`
  respeitado.
- Shell: migrar `Layout.jsx`/`SidebarContent()` para o padrão novo (shadcn `Sidebar` + Phosphor + Motion),
  preservando 100% do comportamento atual (filtro por perfil/`adminOnly`, rotas, logout, drawer mobile).
- Dashboard como tela-piloto: migrar para os componentes/tokens novos, com os 4 estados (loading/success/
  empty/error) explicitamente desenhados — hoje só loading e um `toast.error` de erro existem.
- Responsividade e acessibilidade (navegação por teclado, foco visível, contraste, `aria-*` onde necessário)
  no Shell e no Dashboard.
- Testes de componente (Vitest + Testing Library) para o que for migrado: `SidebarContent` (filtro por
  perfil, item ativo), `Layout` (drawer mobile abre/fecha), `Dashboard` (loading/success/empty/error).
- Documentação: `ENGINEERING_GUIDE.md` ganha uma seção "Design System" descrevendo o padrão; amendment do
  `ADR-001`; `CHANGELOG.md`/`PROJECT_STATUS.md` atualizados ao final.

**Fora de Escopo (explícito — não é ambiguidade, é decisão deliberada desta fase):**

- ❌ Next.js — frontend continua React + Vite (`ADR-001` reafirmado, não revisado).
- ❌ Qualquer mudança em `app.py`, `fluxoly_*.py`, backend, endpoints ou contrato de API.
- ❌ Qualquer mudança de schema de banco/migration.
- ❌ GSAP, Three.js, Anime.js — não entram nesta fase (nem em nenhuma fase do produto, só landing/marketing
  futura, fora do escopo do produto autenticado).
- ❌ Redesign completo de qualquer outro módulo (Estoque, OS, Vendas, Financeiro, etc.) — só Shell e
  Dashboard.
- ❌ Qualquer alteração de regra de negócio, fluxo financeiro, autenticação ou matriz de permissões
  (`ROUTE_PERMISSIONS`, perfis, `usuario_pode_*`).
- ❌ Migração em massa de ícones `lucide-react` → Phosphor fora do Shell/Dashboard.
- ❌ Meta de cobertura de teste frontend para o projeto inteiro — só os componentes tocados nesta fase.

**Regra não negociável desta fase (decisão explícita do CTO, 2026-08-16):** a reforma visual não é
oportunidade para "já que estamos mexendo, corrigir X". Qualquer achado de bug, dívida técnica ou melhoria
de funcionalidade fora do escopo acima — mesmo que na mesma tela sendo migrada — **não entra
automaticamente nesta fase**. Vira um item registrado (`KNOWN_ISSUES.md` se for bug, backlog se for
melhoria) para decisão separada, exatamente como o projeto já trata qualquer achado fora de escopo em
qualquer outra sprint (`ENGINEERING_GUIDE.md` §11 — mesmo espírito, aplicado aqui a UX/funcionalidade, não
só a bugs).

---

## Dependências novas

| Pacote | Escopo | Motivo |
|---|---|---|
| `motion` | produção | Animações do Shell/Dashboard (substitui/é o sucessor de `framer-motion`) |
| `phosphor-react` (ou `@phosphor-icons/react`, confirmar nome do pacote atual na instalação) | produção | Ícones dos componentes novos/migrados |
| `@radix-ui/react-tooltip` | produção | Primitiva do componente shadcn `tooltip` (ainda não presente em `package.json`) |
| `shadcn` (CLI) | dev, não fica no bundle | Gera os componentes faltantes; não é dependência de runtime além das primitivas Radix que já instala |
| `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom` | dev | Testes de componente — inaugurados nesta fase |

Todas aditivas — nenhuma remoção/downgrade de dependência existente. Segue `ENGINEERING_GUIDE.md` §2
("antes de adicionar qualquer nova dependência: verificar se o problema não pode ser resolvido com o que já
existe, avaliar tamanho/manutenção/licença, documentar a razão no PR") — `lucide-react`/`sonner`/Radix
primitivas já em uso são reaproveitadas onde já resolvem o problema; só o que realmente falta é novo.

---

## Amendment do ADR-001

`docs/engineering/adr/ADR-001.md` decidiu manter React + Vite + Radix UI + Tailwind CSS (não migrar para
Next.js/SvelteKit). Esta fase **não revisa** essa decisão — adiciona uma nota de amendment ao final do
ADR, sem reabrir "Alternativas Avaliadas":

> **Amendment (2026-08-XX):** o projeto formaliza shadcn/ui como padrão de composição e implementação dos
> componentes de interface, construído sobre as mesmas primitivas Radix UI já adotadas por esta decisão.
> Não substitui Radix UI nem reabre a escolha de framework — é uma camada de composição sobre a mesma base.
> Ver `docs/engineering/plans/PLAN-design-system-fase1.md` para o contexto completo.

Commit isolado (`docs(adr): amendment ADR-001 — shadcn/ui como padrão de composição`), antes de qualquer
instalação de dependência, conforme a ordem pedida.

---

## Arquitetura proposta

### Design Tokens

Adicionar ao `@theme` de `frontend/src/index.css`, na mesma seção onde já vivem os tokens de cor:

- Escala de espaçamento nomeada (ex.: `--spacing-*` se divergir do default do Tailwind — a avaliar se o
  scale default do Tailwind v4 já cobre 4/8/12/16/24/32/48/64 antes de introduzir tokens redundantes).
- Escala de radius nomeada (`--radius-sm`/`--radius-md`/`--radius-lg`, hoje só `rounded-lg`/`rounded-xl`
  usados ad-hoc nas classes).
- Escala de shadow nomeada, deliberadamente pequena (2-3 níveis) — decisão já alinhada com o CTO de "poucas
  sombras, direção Linear/Stripe/Vercel", não "dashboard genérico de template".

Nenhuma cor nova ou redesenhada — os tokens de cor de `index.css` (paleta #FF0125 + fundo escuro) são a
fonte única e não mudam nesta fase.

### shadcn/ui

1. Rodar `npx shadcn@latest init` apontando para a estrutura já existente (`components/ui`, alias `@/`,
   `cn()` já presente em `lib/utils.js`) — confirmar que o CLI reconhece o setup atual sem sobrescrever os
   11 componentes já existentes.
2. Adicionar via CLI só os componentes necessários ao Shell/Dashboard piloto: `card`, `sheet`, `tooltip`,
   `skeleton`, `sidebar`. Qualquer componente adicional (`table`, `tabs`, `form`, `command`, `calendar`)
   fica para quando um módulo real precisar dele — não instalar especulativamente.
3. Componentes já existentes (`button`, `input`, `select`, etc.) não são recriados via CLI nesta fase —
   permanecem como estão, já que já seguem o padrão. Divergência com o output oficial do CLI, se houver, é
   avaliada caso a caso, não corrigida em bloco (evita mudar 11 arquivos sem necessidade real).

### Motion

Import direto de `motion/react` nos dois pontos de uso desta fase (drawer mobile do Shell, transições do
Dashboard) — sem wrapper/abstração própria nesta fase (evita over-engineering para 2 usos). Transições entre
150–250ms, `useReducedMotion()` respeitado (não animar quando o usuário pediu redução de movimento).

### Phosphor

Import direto de ícones Phosphor nos componentes migrados (Shell, Dashboard). `lucide-react` permanece a
dependência principal do resto do frontend — nenhuma remoção, nenhum "flag day" de migração.

### Shell (Sidebar + Header)

`Layout.jsx` migrado preservando comportamento 1:1: mesma lista `navItems`, mesmo filtro
`!item.adminOnly || user?.perfil === "admin"` e `!item.perfis || item.perfis.includes(user?.perfil)`, mesma
rota ativa (`currentPath.startsWith(path)`), mesmo fluxo de logout. Composição interna passa a usar o
componente `sidebar` do shadcn + Motion para a transição do drawer mobile (hoje é `translate-x-full`/
`translate-x-0` via classe condicional, sem animação real) + ícones Phosphor.

### Dashboard piloto

`Dashboard.jsx` migrado para os componentes/tokens novos. Os 4 estados exigidos pela proposta do CTO:

- **Loading:** substituir/complementar `ChartFallback` (hoje um spinner) por skeleton do shadcn nos KPIs e
  gráficos.
- **Success:** estado atual (dados renderizados) — preservado, só re-estilizado com os tokens novos.
- **Empty:** hoje inexistente — se `data` vier vazio (sem faturamento no período filtrado), desenhar um
  estado vazio explícito em vez de gráficos zerados sem contexto.
- **Error:** hoje só `toast.error` — adicionar um estado de erro persistente na tela (não só um toast que
  desaparece), com ação de retry.

---

## Estratégia de testes frontend

Vitest + `@testing-library/react`, escopo restrito aos componentes migrados nesta fase — não é meta de
cobertura do projeto inteiro (`KI-031`/`KI-033`, lacunas de cobertura de backend, continuam fora deste
plano, que é só frontend).

**Testes desta fase:**
- `SidebarContent`: item filtrado corretamente por `perfis`/`adminOnly` (3 perfis: `admin`/`tecnico`/
  `vendedor`); item ativo destacado pela rota atual.
- `Layout`: drawer mobile abre/fecha (`mobileOpen` state); logout dispara `navigate("/login")`.
- `Dashboard`: os 4 estados (loading/success/empty/error) renderizam o que devem; filtro de data dispara
  nova busca.

**Setup:** `vitest.config.js` (ou config dentro de `vite.config.js`), ambiente `jsdom`, mock de
`react-router-dom`/`AuthContext` conforme necessário — sem servidor real, sem tocar `database.db` (mesmo
princípio de isolamento já usado nos testes backend, `ENGINEERING_GUIDE.md` §6).

**CI:** novo job `Frontend Unit Tests` em `.github/workflows/ci.yml`, rodando em paralelo a `Frontend
Quality`/`Frontend Build` — **não-bloqueante** nesta fase (mesmo precedente do G-07 Playwright, que também
começou não-bloqueante). Vira gate formal (G-2X em `QUALITY_GATES.md`) numa revisão futura, quando a
cobertura de componente crescer além do escopo desta fase — decisão que não cabe a este plano tomar
sozinho.

---

## Acessibilidade

- Navegação por teclado completa no Shell (sidebar, drawer mobile, itens de menu) e no Dashboard (filtros,
  botão de busca).
- Foco visível em todo elemento interativo novo (herdado do Radix UI, que já trata isso nas primitivas —
  confirmar que a composição shadcn não sobrescreve).
- Labels/`aria-*` nos ícones sem texto (botão de abrir/fechar drawer mobile, por exemplo).
- Contraste verificado contra a paleta já existente (`#FF0125` sobre fundo escuro) — não é uma paleta nova,
  mas vale confirmar contraste mínimo AA nos elementos novos (skeleton, empty state).
- `prefers-reduced-motion` respeitado em toda animação Motion desta fase (`useReducedMotion()`).
- Áreas clicáveis com tamanho mínimo adequado (itens de menu, botões de ícone).

---

## Performance

- Motion e componentes shadcn novos carregados só onde usados (Shell, Dashboard) — sem import global que
  infle o bundle de páginas não tocadas nesta fase.
- Lazy loading já existente no Dashboard (`RevenueChartCard`/`TechnicianProfitChartCard`/`ServicesChartCard`
  via `lazy()`) é preservado, não revertido pela migração.
- Nenhuma dependência desta fase (`motion`, Phosphor, componentes shadcn) entra no bundle principal de
  páginas que não usam Shell/Dashboard — validar com `npm run build` que o tamanho de bundle das páginas não
  tocadas não muda.
- Sem GSAP/Three.js nesta fase — não há custo de bundle a mitigar por enquanto.

---

## Critérios de Aceite

- [ ] `docs/engineering/adr/ADR-001.md` tem o amendment, commitado antes de qualquer instalação de
      dependência.
- [ ] `frontend/package.json` reflete só as dependências novas listadas acima — nenhuma removida/rebaixada.
- [ ] Tokens de espaçamento/radius/shadow adicionados em `frontend/src/index.css`, documentados em
      `ENGINEERING_GUIDE.md`.
- [ ] Componentes shadcn novos (`card`/`sheet`/`tooltip`/`skeleton`/`sidebar`) presentes em
      `frontend/src/components/ui/`, sem alterar os 11 já existentes além do estritamente necessário para
      interoperar.
- [ ] `Layout.jsx`/`SidebarContent` migrados, comportamento de filtro por perfil e rota ativa idêntico ao
      atual (validado por teste + QA manual nos 3 perfis).
- [ ] `Dashboard.jsx` migrado, com os 4 estados (loading/success/empty/error) implementados e visíveis.
- [ ] Nenhuma mudança em `app.py`, qualquer `fluxoly_*.py`, endpoint, schema ou `ROUTE_PERMISSIONS`.
- [ ] Nenhum ícone Phosphor fora de Shell/Dashboard; nenhuma remoção de uso existente de `lucide-react`.
- [ ] Vitest configurado; testes de `SidebarContent`/`Layout`/`Dashboard` passando.
- [ ] `npm run lint` e `npm run build` (G-03/G-06) verdes.
- [ ] Navegação por teclado e `prefers-reduced-motion` validados manualmente no Shell e no Dashboard.
- [ ] QA Manual nos 3 perfis (`admin`/`tecnico`/`vendedor`) confirmando: menu idêntico ao atual por perfil,
      logout funcional, responsividade mobile/tablet/desktop, nenhuma regressão visual grosseira nas demais
      páginas (que só herdam tokens de cor/spacing, não são migradas).
- [ ] `CHANGELOG.md`/`PROJECT_STATUS.md`/`ENGINEERING_GUIDE.md` atualizados no Encerramento.

---

## Quality Gates

Gates existentes aplicáveis (`docs/engineering/QUALITY_GATES.md`):

- **G-03** (ESLint) e **G-06** (Build Frontend) — já bloqueantes em CI, sem mudança de critério.
- **G-09/G-10** (CHANGELOG/PROJECT_STATUS) — aplicam normalmente ao encerrar a fase.
- **G-11** (ADR) — o amendment do ADR-001 satisfaz este gate.
- **G-14** (Conventional Commits) — cada etapa da ordem de execução vira um commit/PR próprio, tipado
  corretamente (`chore(deps)`, `docs(adr)`, `feat(design-system)`, `feat(shell)`, `feat(dashboard)`,
  `test(frontend)`).

Gate novo proposto por este plano:

- **G-2X (a numerar em `QUALITY_GATES.md` no Encerramento) — Testes de Componente Frontend (Vitest).**
  Critério: componentes migrados nesta fase têm teste correspondente. Não-bloqueante em CI nesta fase
  (mesmo precedente do G-07 Playwright) — formalizar como bloqueante fica para decisão futura do CTO, fora
  do escopo deste plano.

---

## Riscos

| Risco | Mitigação |
|---|---|
| CLI do shadcn sobrescrever/divergir dos 11 componentes já existentes (hand-rolled, não gerados pelo CLI) | Rodar `init` primeiro, revisar diff antes de aceitar qualquer alteração em arquivo existente; só `add` para componentes que ainda não existem |
| Coexistência `lucide-react` + Phosphor aumentar bundle sem necessidade | Import só dos ícones usados (tree-shaking nativo de ambas as libs), sem import de barrel completo; validar tamanho de bundle no build |
| Motion introduzir jank ou movimento excessivo (contrário ao objetivo "fluido, não se mexendo demais") | Transições 150–250ms, revisão visual manual antes de considerar concluído, `prefers-reduced-motion` respeitado |
| Vitest mal configurado (mock de `react-router-dom`/`AuthContext`) mascarar teste que não testa nada | Confirmar que cada teste falha contra uma mudança deliberada no componente antes de considerar válido (mesmo princípio já usado nos testes backend do projeto) |
| Escopo crescer para outras páginas "já que estamos mexendo" | Escopo travado neste plano (seção "Fora de Escopo") — qualquer pedido de expansão vira um novo plano, não um adendo informal a este |
| CI ganhar um job novo (`Frontend Unit Tests`) e quebrar a ordem/dependência dos jobs existentes | Job novo roda em paralelo, não em `needs` de `Frontend Quality`/`Frontend Build`; não-bloqueante nesta fase |
| Tokens de spacing/radius/shadow novos conflitarem com classes Tailwind ad-hoc já usadas em outras páginas | Tokens são aditivos (novos nomes), nada é removido/renomeado nesta fase; páginas não migradas continuam funcionando com as classes atuais |

---

## Plano de Execução

**Revisado (2026-08-16, decisão do CTO):** 7 PRs temáticos em vez de 10 — cada PR continua sendo uma
mudança coerente e de um único tipo (nunca mistura `feat`+`fix`+`refactor` de propósitos diferentes,
`ENGINEERING_GUIDE.md`/`CLAUDE.md`), mas agrupada por tema em vez de fragmentada por dependência técnica
individual. Nenhuma instalação de dependência ou código de produção antes do amendment do ADR-001 (PR 1)
ser aprovado — a aprovação deste Plano Técnico não substitui a aprovação específica do amendment.

1. **PR 1 — Governance/ADR:** amendment do ADR-001, sem nenhuma dependência instalada ainda.
   `docs(adr): amendment ADR-001 — shadcn/ui como padrão de composição`.
2. **PR 2 — Design System Foundation:** tokens de spacing/radius/shadow, `shadcn init` + componentes base
   faltantes (`card`, `skeleton`), Phosphor instalado.
   `feat(design-system): fundação — tokens, shadcn e Phosphor`.
3. **PR 3 — Motion + componentes:** Motion instalado e configurado, componentes shadcn restantes
   (`sheet`, `tooltip`, `sidebar`), microinterações isoladas (sem ainda tocar Shell/Dashboard).
   `feat(design-system): motion e componentes de composição (sheet, tooltip, sidebar)`.
4. **PR 4 — Application Shell:** `Layout.jsx`/`SidebarContent` migrados, responsividade, navegação.
   `feat(shell): migrar Sidebar/Header para o Design System`.
5. **PR 5 — Dashboard Pilot:** `Dashboard.jsx` migrado, 4 estados (loading/success/empty/error),
   responsividade.
   `feat(dashboard): migrar Dashboard para o Design System com estados loading/success/empty/error`.
6. **PR 6 — Frontend Tests:** Vitest + Testing Library configurados, testes de `SidebarContent`/`Layout`/
   `Dashboard`.
   `test(frontend): configurar Vitest e cobrir Shell/Dashboard migrados`.
7. **PR 7 — Final QA:** acessibilidade, performance (tamanho de bundle), lint/build, regressão manual nos
   3 perfis, documentação de encerramento (`CHANGELOG`/`PROJECT_STATUS`/`ENGINEERING_GUIDE`).
   `docs: encerramento Fluxoly Design System Fase 1`.

Cada PR contra `main`, seguindo `CONTRIBUTING.md` — branch própria por PR (`feat/design-system-...`,
`docs/adr-001-amendment`, `test/design-system-frontend`), commits atômicos dentro de cada PR quando fizer
sentido separar (ex.: PR 2 pode ter um commit `feat(design-system): tokens` e outro
`feat(design-system): shadcn init + componentes base`, mas o PR em si é revisado/mergeado como unidade
temática).

---

## Rollback

Mudança inteiramente aditiva no frontend — nenhum schema, migration, endpoint ou dado de produção é
tocado. Rollback segue a política já documentada (`docs/company/GO_LIVE_PLAN.md`/`DEPLOY.md`): `git revert`
do PR problemático + push, mesmo fluxo de deploy normal (Vercel reconstrói a partir do commit revertido).
Como não há coordenação com o backend (Render) nesta fase, um rollback de frontend não tem o requisito de
"reverter os dois juntos" que a política de Rollback coordenado exige para mudanças que tocam os dois lados.
Se o Shell ou o Dashboard migrado apresentar regressão em produção, a etapa correspondente (passo 7 ou 8
acima) é revertida isoladamente, sem precisar desfazer tokens/dependências das etapas anteriores.

---

## Commits/PRs esperados

7 PRs temáticos, na ordem da seção "Plano de Execução" — cada PR agrupa mudanças do mesmo tema/propósito,
nunca mistura tipos de propósito diferente (feature de design system + bug fix + refatoração não relacionada
nunca no mesmo PR). Nenhum código de produto é escrito antes do PR 1 (amendment do ADR-001) ser aprovado, e
nenhuma dependência é instalada antes do PR 2.

---

## Questões em Aberto

Ambas resolvidas durante o PR 2 (detalhe técnico, não decisão de negócio — registrado aqui só para
fechamento do plano):

- **Nome do pacote Phosphor:** `@phosphor-icons/react` (pacote atual mantido; `phosphor-react` está em modo
  de manutenção) — instalado no PR 2.
- **Escala de spacing/radius/shadow do Tailwind v4 default:** confirmado que já cobre exatamente os valores
  aprovados (spacing 4/8/12/16/24/32/48/64; radius sm/lg/xl/full já em uso consistente; shadow sm/xl já em
  uso consistente) — decisão foi **não** criar tokens customizados redundantes, e sim formalizar a escala
  padrão como convenção documentada. Ver `docs/engineering/ENGINEERING_GUIDE.md` §3.2 para o registro
  completo.
