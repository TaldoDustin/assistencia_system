# PLAN-landing-page-implementacao — Implementação da Landing Page Institucional do Fluxoly

**Data:** 2026-08-17
**Feature:** iniciativa de produto/UX, sem regra de negócio nova — mesmo gate usado em
`PLAN-design-system-fase1.md` ("apresentar plano e aguardar aprovação" do `CLAUDE.md`, não o ciclo `ADR-010`
completo, por não haver BR envolvida). O Discovery de conteúdo/UX já existe e foi aprovado pelo CTO em
2026-08-16 — ver `docs/product/features/LANDING_PAGE.md`, cujo item final do checklist ("Plano Técnico de
implementação redigido e aprovado pelo CTO... antes de qualquer código React ser escrito") é exatamente o
que este documento resolve.
**Status:** ✅ Encerrado (2026-08-17) — PR #49 mergeado em `main` (`a339de19`). Ver
`docs/operations/PROJECT_STATUS.md` (seção "Landing Page Institucional") para o registro executivo de
fechamento.

> Este documento é efêmero (mesmo princípio do `ADR-010`/`CONTRIBUTING.md` §9, mesma nota do
> `PLAN-design-system-fase1.md`). Depois do encerramento, permanece só como histórico da decisão de
> implementação.

**Decisões do CTO que definem este plano (2026-08-17):**
- Roteamento: **`/` pública quando deslogado** (landing) e continua Dashboard quando autenticado — padrão
  Linear/Stripe/Vercel, mesma referência já usada no Design System.
- Escopo desta fatia: **estrutura completa das 14 seções agora**, com os itens ainda `[DEFINIR]` (preço,
  prova social, trial) exibidos como placeholder textual definido no próprio `LANDING_PAGE.md`, sem bloquear
  o resto.

**Estado**

- [x] Plano Técnico — aprovado pelo CTO
- [x] Implementação (3 commits: Design System aditivo → conteúdo/seções → roteamento + testes)
- [x] Testes (18/18 — 11 pré-existentes + 7 novos, `App.test.jsx`/`Landing.test.jsx`)
- [~] QA Manual — desktop confirmado ao vivo (`npm run dev` + Claude in Chrome, todas as 14 seções, FAQ
      abre/fecha, CTA aponta para `/login`); **mobile não confirmado visualmente** (resize da ferramenta de
      automação não afetou o viewport real da página — mesma limitação já registrada na QA da Fase 1 do
      Design System) — coberto só por revisão de código (breakpoints `sm:`/`lg:` seguem o mesmo padrão já
      testado do `Sidebar`/PR #47) e pelos testes automatizados, não por inspeção visual real. Aceito
      explicitamente pelo CTO antes da abertura do PR.
- [x] Revisão Arquitetural — aprovada pelo CTO nos 4 eixos: roteamento, isolamento de
      Auth/Login/Layout/APIs/banco, dependência nova validada pelo CI, conteúdo sem invenções. Achado de
      conteúdo revisado (uso de "premium" no `<title>`) confirmado consistente com
      `docs/company/BRAND_IDENTITY.md` e com o FAQ já aprovado da própria Landing — mantido como estava.
- [x] Encerramento — PR #49 mergeado em `main` (`a339de19`), branch deletada, produção confirmada saudável
      pós-merge (`/health` backend → 200, frontend Vercel → 200). `PROJECT_STATUS.md`, `CHANGELOG.md` e o
      checklist da Parte 8 de `docs/product/features/LANDING_PAGE.md` atualizados.

---

## Objetivo

Implementar em código React as 14 seções especificadas em `docs/product/features/LANDING_PAGE.md`,
reaproveitando 100% do Fluxoly Design System já formalizado (PRs #41–#47), sem alterar nenhuma regra de
negócio, endpoint ou schema, e com uma única mudança cirúrgica no fluxo de autenticação: a raiz (`/`) passa
a servir conteúdo diferente para visitante deslogado (Landing) e usuário autenticado (Dashboard, como hoje).

---

## Contexto atual (investigação de código, não hipótese)

- **`frontend/src/App.jsx`** hoje trata `/` como o Dashboard autenticado: está dentro do grupo de rotas
  protegidas (`<Route element={<ProtectedRoute><Layout /></ProtectedRoute>}>`), e `ProtectedRoute`
  redireciona incondicionalmente para `/login` quando `!user`, para qualquer path.
- **`frontend/src/components/Layout.jsx`** é uma rota-wrapper baseada em `<Outlet />` (React Router
  nested routes) — não aceita `children` diretamente. Ou seja: não dá para simplesmente passar
  `<Layout><Dashboard /></Layout>` fora da árvore de rotas atual sem reescrever `Layout`.
- **`frontend/vercel.json`** já reescreve qualquer rota não-API para `/` (`"source": "/(.*)", "destination":
  "/"`) — rota nova client-side não exige nenhuma mudança de configuração de deploy.
- **Tokens de cor** (`frontend/src/index.css`, `@theme`) já cobrem exatamente a paleta que
  `LANDING_PAGE.md` Parte 4 propõe: `--color-chart-2` (verde, sucesso), `--color-chart-3` (âmbar, atenção),
  `--color-chart-5` (ciano, informativo) — confirma o item do checklist "confirmação dos tokens de
  sucesso/atenção/informativo contra `index.css`" sem precisar de nenhum token novo.
- **`frontend/src/components/ui/button.jsx`** hoje só tem `size: default | sm | icon` — falta `lg`, que o
  Hero e o CTA final da Landing Page precisam (spec Parte 4: "avaliar se `lg` precisa ser adicionado").
- **Não existe `accordion`** em `frontend/src/components/ui/` — necessário para a seção FAQ (spec Parte 4:
  "precisa ser adicionado via `npx shadcn add accordion`").
- **GSAP não está instalado** (confirmado via busca no repositório) — a spec (Parte 7) reserva GSAP só para
  a sequência de entrada do Hero e um eventual scroll storytelling, e é explícita que Motion (já instalado,
  PR #43) cobre tudo que não for isso.
- **Não há mecanismo de meta tag por rota** — é uma SPA sem SSR/SSG (`index.html` único, `<title>` estático).
  Existe uma branch exploratória `explore/nextjs-fundacao` não relacionada a este plano e fora de escopo
  aqui (mudança de framework exigiria ADR próprio, `RELEASE_STRATEGY.md`/decisão de alto custo do
  `CLAUDE.md`).
- **Padrão de teste de rota autenticada já existe** (`frontend/src/components/Layout.test.jsx`,
  `frontend/src/pages/Dashboard.test.jsx`, PR #47): `vi.mock("@/contexts/AuthContext")` com `mockUser`
  mutável + `MemoryRouter`. Reaproveitado para o teste de roteamento da raiz.

---

## Escopo

### Dentro desta fatia

**1. Roteamento — mudança cirúrgica em `ProtectedRoute` (`frontend/src/App.jsx`):**

```jsx
function ProtectedRoute({ children }) {
  const { user, loading } = useAuth();
  const location = useLocation();
  if (loading) { /* mesmo spinner de hoje */ }
  if (!user) {
    if (location.pathname === "/") return <Landing />;
    return <Navigate to="/login" replace />;
  }
  return children;
}
```

Único ponto de mudança na árvore de rotas — a estrutura existente (`/`, `/ordens`, `/vendas`, etc. dentro
do grupo protegido) **não é reestruturada**. Todos os outros paths continuam redirecionando para `/login`
exatamente como hoje — só `/` ganha um comportamento novo quando deslogado. `Landing` é importado como rota
`lazy()`, mesmo padrão de todas as outras páginas em `App.jsx`.

**2. Componentes novos — `frontend/src/pages/Landing.jsx`** compõe 14 componentes de seção em
`frontend/src/components/landing/` (mapeamento 1:1 com a tabela da Parte 2 do `LANDING_PAGE.md`, para
rastreabilidade direta na QA manual):

| Arquivo | Seção |
|---|---|
| `LandingNavbar.jsx` | Navbar |
| `LandingHero.jsx` | Hero |
| `LandingProblem.jsx` | Problema |
| `LandingSolution.jsx` | Solução |
| `LandingBenefits.jsx` | Benefícios |
| `LandingFeatures.jsx` | Funcionalidades (6 pilares) |
| `LandingHowItWorks.jsx` | Como funciona |
| `LandingSystemPreview.jsx` | Visão do sistema |
| `LandingDifferentiators.jsx` | Diferenciais |
| `LandingSocialProof.jsx` | Prova social (`[DEFINIR]`) |
| `LandingPricing.jsx` | Planos (`[DEFINIR]`) |
| `LandingFaq.jsx` | FAQ (usa `Accordion` novo) |
| `LandingCta.jsx` | CTA final |
| `LandingFooter.jsx` | Footer |

Mais **`frontend/src/components/landing/content.js`**: única fonte da copy (arrays de cards de
Problema/Benefícios/Pilares/Diferenciais/FAQ, textos de cada seção), extraída literalmente da Parte 3 do
`LANDING_PAGE.md` — nenhum texto novo é inventado, nenhum item `[DEFINIR]` é preenchido. Mantém os
componentes de seção como puramente apresentacionais e centraliza a próxima edição de copy (quando preço/
prova social forem decididos) em um único arquivo.

**3. Design System — extensões aditivas, sem alterar o que já existe:**
- `frontend/src/components/ui/button.jsx`: adicionar variante de tamanho `lg` (`h-11 px-8 text-base`,
  a validar no code review) — aditivo, `default`/`sm`/`icon` inalterados.
- `frontend/src/components/ui/accordion.jsx`: novo, via `npx shadcn add accordion` (adiciona
  `@radix-ui/react-accordion` a `frontend/package.json` — única dependência nova desta fatia). Colapso via
  `data-state` do Radix (CSS), **não** Motion — mesma regra já registrada em `ENGINEERING_GUIDE.md` §3.2
  ("Motion vs. transição CSS": Radix `Presence` não detecta a animação via WAAPI do Motion).

**4. Visão do sistema (seção 8) sem imagem real:** mockup fiel construído com `Card`/`Skeleton` do próprio
Design System (dados fictícios, mesmos componentes do Dashboard real) — não banco de imagens, não
ilustração genérica, conforme a regra explícita da spec. Trocar por um screenshot real é um follow-up
trivial (troca de um componente por uma tag `<img>`), não parte desta fatia.

**5. Animação:** só Motion (`whileInView` para entrada de seção ao rolar, hover de card, scale sutil em
CTA — 150–300ms, `useReducedMotion()` respeitado, mesmo padrão do PR #43). **GSAP não entra nesta fatia** —
decisão de reduzir a superfície de dependência nova desta implementação; a sequência de entrada do Hero
fica com Motion (`staggerChildren`) em vez de GSAP, funcionalmente equivalente para o efeito descrito na
spec. Se o CTO julgar o resultado insuficiente após o QA visual, GSAP entra como follow-up isolado (nova
dependência = novo pedido de aprovação, por regra do `CLAUDE.md`).

**6. `index.html`:** `<title>` e `<meta name="description">` atualizados para refletir a Landing Page como
entrada pública em `/` (hoje é genérico, "Fluxoly — Assistência Técnica"). Sem mecanismo de meta por rota
(SPA sem SSR) — mesma limitação documentada no Contexto atual, aceita nesta fatia.

### Fora de escopo desta fatia, deliberadamente

- Preencher qualquer item `[DEFINIR]` (preço, prova social, trial, suporte) — permanece como placeholder
  textual até `PRODUCT_REQUIREMENTS.md`/`RELEASE_STRATEGY.md` decidirem.
- Fonte Inter — proposta ainda não decidida como amendment do Design System (`LANDING_PAGE.md` Parte 4);
  esta fatia usa a pilha tipográfica atual (`system-ui`).
- GSAP, Three.js, Anime.js.
- Screenshot real do Dashboard (usa mockup em componentes do Design System).
- Captura de lead / formulário de e-mail no CTA (decisão de produto não tomada).
- SEO avançado (Open Graph dinâmico, sitemap, SSR) — exigiria mudança de framework, fora do escopo desta
  spec e desta fatia.
- Qualquer alteração em `Login.jsx`, `AuthContext`, endpoints de autenticação — `ProtectedRoute` muda só a
  decisão de *o que renderizar* quando `!user` em `/`, não a lógica de autenticação em si.

---

## Arquivos afetados

| Arquivo | Tipo de mudança |
|---|---|
| `frontend/src/App.jsx` | Modificado — `ProtectedRoute` ganha o caso especial de `/`, nova rota lazy `Landing` |
| `frontend/src/pages/Landing.jsx` | Novo |
| `frontend/src/components/landing/*.jsx` (14 arquivos) | Novo |
| `frontend/src/components/landing/content.js` | Novo |
| `frontend/src/components/ui/button.jsx` | Modificado — variante `lg` aditiva |
| `frontend/src/components/ui/accordion.jsx` | Novo (via shadcn CLI) |
| `frontend/package.json` | Modificado — `@radix-ui/react-accordion` |
| `frontend/index.html` | Modificado — `<title>`/meta description |
| `frontend/src/App.test.jsx` | Novo — cobre o roteamento condicional de `/` |
| `frontend/src/pages/Landing.test.jsx` | Novo — smoke test das 14 seções |
| `docs/product/features/LANDING_PAGE.md` | Modificado — marcar checklist da Parte 8 conforme concluído |

19 arquivos no total — acima do limiar de 3 do `CLAUDE.md`, por isso este plano formal.

---

## Testes planejados

Reaproveita o padrão já estabelecido no PR #47 (`vi.mock("@/contexts/AuthContext")`, `MemoryRouter`):

- **`App.test.jsx`** (novo): `/` deslogado renderiza a Landing (texto do Hero visível, sem Sidebar); `/`
  autenticado renderiza o Dashboard dentro do `Layout` (Sidebar visível), sem regressão; `/ordens` deslogado
  continua redirecionando para `/login` (garante que a mudança é isolada em `/`, não afeta as outras rotas
  protegidas).
- **`Landing.test.jsx`** (novo): as 14 seções renderizam; CTA primário ("Começar agora") aponta para
  `/login`; placeholders `[DEFINIR]` de Prova Social/Planos estão visíveis (não texto inventado); FAQ abre/
  fecha via `Accordion` (`userEvent.click`); `useReducedMotion` respeitado (sem depender de animação real
  no teste, mesmo padrão do `Sidebar.test.jsx`/PR #47 para o hook `useIsMobile`).
- Suíte completa (`npm run test`) roda sem regressão nos testes existentes de `Layout`/`Dashboard`.

---

## Riscos e mitigação

- **Risco:** o caso especial em `ProtectedRoute` (`location.pathname === "/"`) é fácil de ler errado como
  "toda rota pública vira Landing". Mitigação: comentário no código explicando que é intencionalmente só a
  raiz, e teste explícito de `/ordens` deslogado no `App.test.jsx` para travar a regra.
- **Risco:** bundle da rota `/` cresce com 14 componentes de seção + Accordion. Mitigação: `Landing` já é
  `lazy()` como toda página em `App.jsx` — não entra no chunk principal (Shell), só carrega quando alguém
  visita `/` deslogado. Sem impacto no bundle do Dashboard/produto autenticado.
- **Risco:** mockup da "Visão do sistema" (item 4 do escopo) ficar parecendo dado real de cliente.
  Mitigação: dados obviamente fictícios (nomes/valores placeholder), mesmo cuidado já usado em
  `scripts/seed_demo.py` para o Ambiente de Demonstração.

---

## Próximo passo

Após aprovação deste Plano Técnico: implementação em branch `feat/landing-page-implementacao`, commits
atômicos (Design System aditivo → conteúdo/seções → roteamento → testes), CI 6/6, QA Manual visual (desktop
+ mobile, os 3 breakpoints da Parte 6 do `LANDING_PAGE.md`), Revisão Arquitetural contínua a cada commit
(mesmo padrão da Fase 1 do Design System), Encerramento com atualização de `PROJECT_STATUS.md`,
`CHANGELOG.md` e o checklist da Parte 8 do `LANDING_PAGE.md`.
