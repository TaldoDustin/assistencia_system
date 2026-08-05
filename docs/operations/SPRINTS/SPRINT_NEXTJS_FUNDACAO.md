# SPRINT NEXTJS-FUNDAÇÃO — Track paralelo de modernização de frontend (Fase 1 — Fundação)

**Status:** EM PLANEJAMENTO
**Período:** A definir — não bloqueia nem é bloqueada pela Fase 1 (Release 1.0) em andamento
**Tipo:** Infraestrutura / Exploração arquitetural (não-produção)

---

## Objetivo

Construir, num diretório novo e isolado (`frontend-next/`), um protótipo Next.js + TypeScript +
TailwindCSS + shadcn/ui + Phosphor Icons + Motion que reproduza 2 telas reais do Fluxoly consumindo a
API Flask já existente — para validar a stack de UI proposta pelo CTO contra o produto real, sem
nenhum risco de produção. Ver `docs/engineering/adr/ADR-012.md` para a decisão que autoriza este track.

## Motivação

O CTO propôs uma modernização completa de frontend (Next.js/TypeScript/shadcn/Motion), inspirada em
Linear/Stripe/Vercel/Notion. `ADR-012` restringiu o escopo imediato a um track paralelo, frontend-only,
não-produção — para poder validar a proposta sem interromper `TD-01` nem a corrida pelo primeiro cliente
pagante (Fase 1 do `RELEASE_STRATEGY.md`), e sem reabrir `ADR-003` (banco) ou `ADR-005` (multiempresa)
antes da hora.

O custo de não fazer nada seria adiar indefinidamente a resposta à condição de revisão que a própria
`ADR-001` já previa ("revisitar se houver demanda por SSR ou TypeScript").

---

## Escopo — o que ENTRA e o que NÃO entra

**Entra (Fase 1 — Fundação, conforme documento original do CTO, restrito por ADR-012):**
- Next.js (App Router) + TypeScript estrito + TailwindCSS + shadcn/ui
- Phosphor Icons (exclusivamente — nunca misturar com Lucide/Heroicons/FontAwesome/Material Icons)
- Motion para microinterações (hover, focus, fade, scale, loading, skeleton — 150–300ms, sempre discretas)
- Consumo somente-leitura da API Flask já em produção (mesmos endpoints, nenhuma rota nova)
- Dark mode, responsividade, acessibilidade básica

**NÃO entra nesta sprint** (ver "Pontos em aberto" da ADR-012):
- Qualquer mudança em `frontend/`, `app.py`, `fluxoly_*.py`, banco de dados ou schema
- BetterAuth, Resend, Supabase Storage, Firebase Cloud Messaging — todos dependem de decisão futura
  sobre o backend, fora de escopo aqui
- GSAP, Three.js, Anime.js — por regra do próprio CTO, são para Landing Page/Marketing/telas especiais,
  não para as telas internas do sistema que este protótipo reproduz
- Multiempresa, billing/Stripe, SEO/Search Console — ADR-005 continua pendente, não antecipada aqui
- Deploy, CI/CD, merge em `main` — este track vive em branch própria até uma decisão explícita de
  promover (ou não) para produção

---

## Arquivos Envolvidos

| Arquivo/Diretório | Mudança prevista |
|---|---|
| `frontend-next/` (novo) | Scaffold completo do protótipo Next.js — não existe hoje |
| `frontend-next/README.md` (novo) | Deixar explícito: "protótipo de avaliação, não-produção", link para ADR-012 |
| `.env.local` (novo, dentro de `frontend-next/`, **não commitado**) | URL da API Flask de dev (`http://127.0.0.1:5080`) |
| `.env.example` (raiz, opcional) | Se necessário, adicionar nota sobre `IR_FLOW_CORS_ORIGINS` precisar incluir a porta do Next.js dev (ex.: `:3000`) — **só em dev local**, nunca em produção |

Nenhum arquivo de produção (`frontend/`, `app.py`, `fluxoly_*.py`, `requirements*.txt`) é tocado.

---

## Ordem de implementação

Seguindo a sequência definida pelo próprio CTO no documento de arquitetura, adaptada ao escopo desta
fase (sem GSAP/Three.js, que não se aplicam a telas internas do sistema):

1. **Planejamento** — escolher as 2 telas a prototipar (proposta: Dashboard + Lista/Detalhe de OS, por
   serem as mais visualmente representativas do padrão Linear/Stripe que se quer validar); definir fluxo
   de UX antes de escrever código
2. **Estrutura** — scaffold Next.js + Tailwind + shadcn/ui, layout base
3. **Ícones** — Phosphor Icons, exclusivamente
4. **Microinterações** — Motion (hover, focus, fade, scale, loading, skeleton)
5. **Validação** — antes de considerar a sprint concluída, checar por tela: responsividade,
   acessibilidade (navegação por teclado, contraste), performance (lazy loading onde fizer sentido),
   consistência com o Design System, estados vazios/erro/loading/skeleton, dark mode

Etapas "Animações específicas" (Anime.js), "Marketing" (GSAP) e "Efeitos 3D" (Three.js) do documento
original do CTO **não se aplicam** a esta sprint — ficam reservadas para quando (e se) uma Landing Page
ou área de marketing entrar em escopo, conforme as próprias regras de uso que o CTO definiu para essas
bibliotecas.

---

## Princípio de engenharia (aplicado a cada componente novo)

Antes de implementar qualquer elemento de UI nesta sprint, responder nesta ordem:

1. Existe um componente do shadcn/ui que resolve isso?
2. A interação pode ser feita só com CSS?
3. Se não, Motion resolve?
4. A solução respeita o Design System (muito espaço em branco, bordas suaves, sombras discretas,
   tipografia limpa, alto contraste) e mantém consistência visual?
5. O impacto em performance foi avaliado?
6. É acessível, responsiva e reutilizável?

Nunca pular direto para Anime.js/GSAP/Three.js sem esgotar 1–3 primeiro (regra do CTO).

---

## Pergunta em aberto que precisa de decisão antes da implementação começar

**Como o protótipo autentica contra a API Flask?** A API atual usa sessão via cookie Flask
(`flask-cors` já configurado, `IR_FLOW_CORS_ORIGINS`). Duas opções, a decidir no início da implementação
(não nesta etapa de planejamento):
- **Proxy de dev** (`next.config` rewrites apontando para o Flask local) — o cookie de sessão funciona
  como same-origin do ponto de vista do browser, sem mudança nenhuma no backend
- **Login de teste dedicado** — um usuário de teste local, mesma API `/api/login` existente, sem
  BetterAuth nem qualquer vendor novo

Ambas as opções usam a autenticação **já existente** do Flask — nenhuma delas introduz um vendor novo.

---

## Critérios de Aceitação

- [ ] `frontend-next/` scaffolded, roda localmente (`npm run dev`) independente de `frontend/`
- [ ] TypeScript modo estrito, ESLint e Prettier configurados
- [ ] shadcn/ui instalado com pelo menos: Button, Input, Table, Dialog, Card, Sidebar, Dropdown, Badge,
      Tooltip, Toast
- [ ] Phosphor Icons exclusivamente — nenhuma outra biblioteca de ícones no `package.json`
- [ ] Motion instalado, com pelo menos hover/focus/loading/skeleton demonstrados nas telas prototipadas
- [ ] 2 telas reais prototipadas, consumindo a API Flask existente em modo somente-leitura
- [ ] Decisão de autenticação do protótipo documentada (ver seção acima)
- [ ] Dark mode funcional nas telas prototipadas
- [ ] Responsividade validada (mobile/tablet/desktop)
- [ ] Acessibilidade básica: navegação por teclado, contraste adequado
- [ ] Zero mudança em qualquer arquivo de produção (`frontend/`, `app.py`, `fluxoly_*.py`, banco, testes)
- [ ] `frontend-next/README.md` deixa explícito que é protótipo de avaliação, não-produção

---

## Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| RS-01 | CORS entre o dev server do Next.js e a API Flask | Média | Baixo | Adicionar a origem de dev (`http://localhost:3000`) a `IR_FLOW_CORS_ORIGINS` **só em `.env` local**, nunca em produção |
| RS-02 | Duas bases de frontend confundirem contribuidores sobre "qual é a de verdade" | Média | Médio | `frontend-next/README.md` explícito + branch própria, nunca mergeada em `main` sem decisão formal |
| RS-03 | Escopo crescer organicamente para produção sem decisão explícita do CTO | Baixa | Alto | Critérios de aceitação desta sprint não incluem deploy nem merge em `main`; qualquer promoção a produção exige nova decisão registrada (ADR de revisão da ADR-012) |

---

## Dependências

- Depende de: `ADR-012` aceita (já está — este documento é a execução dela)
- Não bloqueia: `TD-01` (extração de blueprints) nem a Fase 1 (Release 1.0) — rodam em paralelo, sem
  interseção de arquivos

---

## Definition of Done

- [ ] Todos os critérios de aceitação atingidos
- [ ] `frontend-next/README.md` publicado com o escopo e link para `ADR-012`
- [ ] Nenhum commit fora da branch própria deste track (nunca direto em `main`)
- [ ] `PROJECT_STATUS.md` atualizado com uma linha mencionando o track (sem alterar o score/fase da Fase 1
      atual, que é independente)
- [ ] Decisão de continuidade registrada ao final: promover a produção (nova ADR), manter como track
      permanente de exploração, ou descontinuar

---

## Retrospectiva (preencher ao concluir)

### O que funcionou bem

### O que poderia ter sido melhor

### Lições aprendidas

### Decisão de continuidade

---

## Documentos relacionados

- `docs/engineering/adr/ADR-012.md` — decisão que autoriza este track e define os limites de escopo
- `docs/engineering/adr/ADR-001.md` — decisão original de frontend (React + Vite), parcialmente revisada
- `docs/company/RELEASE_STRATEGY.md` — as 6 Fases estratégicas já decididas, não alteradas por este track
- `docs/operations/SPRINTS/SPRINT_TD01_MODULARIZACAO_API.md` — trabalho em paralelo no stack atual
