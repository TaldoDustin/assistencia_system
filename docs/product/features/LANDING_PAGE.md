# LANDING_PAGE.md — Especificação da Landing Page Institucional do Fluxoly

**Status:** Rascunho — especificação de conteúdo/estrutura/Design System. **Não implementar ainda** (decisão
explícita do CTO, 2026-08-16) — implementação em React/JSX é uma etapa futura separada, com plano técnico
próprio, seguindo o mesmo gate do `CLAUDE.md` já usado na Fase 1 do Design System interno
(`docs/engineering/plans/PLAN-design-system-fase1.md`).

**Escopo desta etapa:** estrutura, copy, Design System (reaproveitando o que já foi formalizado nas PRs #41
a #43), regras de UX/responsividade/acessibilidade/performance/animação, e um checklist objetivo para a
implementação futura. Nenhum código React/JSX/CSS é criado aqui.

---

## Nota de Decisão — uso do site Mercado Phone como referência

Registrado aqui porque é uma decisão de negócio, não técnica (mesmo princípio de separação de decisões do
`ADR-010`).

- **Não há parceria entre Fluxoly e Mercado Phone.** O Fluxoly consome a API do Mercado Phone
  (`fluxoly_mercadophone.py`) porque é onde os dados reais de produção da loja hoje residem — uma
  dependência técnica de necessidade, não uma relação comercial (confirmado pelo CTO, 2026-08-16).
- **O Mercado Phone é tratado como concorrente direto** para fins de posicionamento de marketing (confirmado
  pelo CTO, 2026-08-16: "Estamos analisando o site como referência de mercado, e como concorrente direto").
- **O que foi analisado** (`https://mercadophone.app.br/`, 2026-08-16, via navegador real): estrutura de
  seções, hierarquia de conteúdo, abordagem comercial, e — por decisão explícita do CTO após um conflito
  identificado no brief original entre "não copiar identidade visual" e "usar as imagens para construir a
  base do Design System" — também elementos de identidade visual (paleta, tipografia, radius, estilo de
  componente), usados abaixo só como **referência de mercado**, nunca copiados literalmente.
- **Decisão de Design System (ver Parte 4):** as cores/tokens propostos abaixo **não** derivam da paleta do
  Mercado Phone. Reaproveitam a identidade que o Fluxoly já formalizou nas PRs #41-#43 (fundo escuro +
  vermelho `#FF0125`, já em produção no sistema interno). Razão: o próprio brief exige consistência visual
  entre Landing Page → Login → Sistema, e clonar a paleta azul/índigo de um concorrente direto no produto
  do Fluxoly seria o oposto de diferenciação — dois "sistemas para loja de celular" com a mesma cor de marca
  gera confusão, não conversão. Esse é um julgamento explícito desta especificação, não uma imposição — se
  a intenção era outra, é o primeiro ponto a corrigir antes de avançar.

## Decisões do CTO sobre este documento (2026-08-16)

| Item | Decisão |
|---|---|
| Criar `LANDING_PAGE.md` | ✅ Aprovado |
| Não implementar ainda | ✅ Aprovado |
| Usar Mercado Phone como benchmark de estrutura/conteúdo | ✅ Aprovado |
| Tratar Mercado Phone como concorrente (não parceiro) | ✅ Aprovado |
| Copiar identidade visual do Mercado Phone | ❌ Rejeitado |
| Usar a paleta Fluxoly já existente (`#FF0125` + fundo escuro) | ✅ Aprovado |
| Inventar depoimentos/métricas/preços | ❌ Rejeitado — mantido `[DEFINIR]` |
| Comparação nominal "Fluxoly vs. Mercado Phone" na Landing | ⏸️ Fora de escopo por ora |
| Narrativa Problema → Solução → Benefícios → Funcionalidades | ✅ Aprovado, com reordenação (ver Parte 2) |
| Landing Page como frente separada do PR #44 (Shell) | ✅ Aprovado — não interrompe a Fase 1 do Design System interno |
| "Inter" como fonte definitiva da Landing | ⚠️ Não decidido aqui — vira proposta ao Fluxoly Design System (ver Parte 4) |

**Princípio reafirmado pelo CTO:** a Landing Page deve responder "por que alguém escolheria o Fluxoly?",
não "como fazemos uma versão diferente do Mercado Phone?". E a hierarquia de identidade é
`Fluxoly Design System → Landing Page → Produto` — nunca `Mercado Phone → Landing Page`.

---

## 1. Conceito da Landing Page

O Mercado Phone se posiciona pela **amplitude**: "o único ERP e CRM feito exclusivamente para lojas de
iPhone e outros celulares", com uma enxurrada de recursos (IA Blue, módulo fiscal, CRM WhatsApp/Instagram,
consulta de CPF/IMEI, 3 planos por faixa de preço) — a mensagem é "fazemos tudo, fazemos mais que os
outros" (a própria seção "Mercado Phone vs. Outros ERPs" é explícita nisso).

O Fluxoly deve se posicionar pela **clareza e pelo controle**, não pela quantidade de recursos — consistente
com `docs/company/BRAND_IDENTITY.md` ("nunca será um sistema inflado com módulos inúteis", "nunca será um
software difícil de aprender") e com o princípio de UX já registrado em `ENGINEERING_GUIDE.md` §4.0
("cada profissional enxerga só o que precisa"). A landing page não promete "o sistema mais completo do
mercado" — promete "o fim da operação espalhada em planilhas, cadernos e grupos de WhatsApp", com prova
visual de que o sistema realmente resolve isso.

**Direção visual:** fundo escuro, um único acento de cor forte (`#FF0125`, já em produção), muito espaço em
branco (negativo), tipografia grande e confiante, poucos elementos por tela. Menos "dashboard cheio de
badge" do Mercado Phone, mais próximo de Linear/Stripe/Vercel — que é exatamente a referência que o próprio
CTO já definiu para o produto interno (ver conversa que originou `PLAN-design-system-fase1.md`).

---

## 2. Estrutura Completa da Página

**Revisado (2026-08-16, decisão do CTO):** narrativa reordenada para
`Hero → Problema → Solução → Benefícios → Funcionalidades → Como funciona → Visão do sistema →
Diferenciais → Prova social → Planos → FAQ → CTA`. O visitante precisa entender o problema antes da
solução, e a solução (promessa central) antes dos benefícios (ganhos concretos) e das funcionalidades
(como isso é entregue) — nessa ordem, não misturado. 14 seções ao todo (12 + Navbar/Footer).

| # | Seção | Objetivo | Título | Subtítulo | CTA | Elemento visual |
|---|-------|----------|--------|-----------|-----|------------------|
| 1 | **Navbar** | Orientar e permitir ação imediata sem rolar | logo Fluxoly | — | "Começar agora" (botão) | logo + 4-5 links + 1 CTA, fundo transparente sobre o Hero, sólido ao rolar |
| 2 | **Hero** | Comunicar em <5s o que é e para quem é | "O fluxo inteligente da sua loja de celulares" | "Vendas, estoque, ordens de serviço e financeiro em um único sistema — sem planilha, sem caderno, sem retrabalho." | "Começar agora" (primário) + "Ver como funciona" (secundário, scroll) | screenshot real do Dashboard (quando existir versão apresentável) ou mockup fiel à UI real — nunca ilustração genérica |
| 3 | **Problema** | Nomear a dor antes de vender a solução | "Sua loja roda no improviso?" | — | — | 3-4 cards curtos (planilha desatualizada, estoque sem controle, OS perdida, caixa sem visão real) |
| 4 | **Solução** | Apresentar o Fluxoly como resposta direta ao problema, ainda sem entrar em funcionalidades específicas | "Um único fluxo para toda a operação" | "O Fluxoly reúne vendas, estoque, financeiro e assistência técnica em um só lugar — sem planilha paralela." | — | diagrama simples "antes" (ferramentas espalhadas, ícones soltos) → "depois" (um único fluxo, ícones convergindo) |
| 5 | **Benefícios** | Comunicar ganhos concretos que o dono/gestor sente, não recursos técnicos | "O que muda na prática" | — | — | 4 blocos curtos, orientados a resultado (ver Parte 3) — sem ícone de módulo, sem jargão técnico |
| 6 | **Funcionalidades** | Mostrar profundidade real sem parecer inflado | "Um sistema, todas as frentes da loja" | "Vendas, Estoque, Financeiro, Assistência Técnica e Inteligência — os 6 pilares do Fluxoly." | — | grid com os 6 pilares de `BRAND_IDENTITY.md` §2, ícone Phosphor + 1 frase por pilar |
| 7 | **Como funciona** | Reduzir a barreira de "isso é complicado de adotar", agora que o visitante já sabe o que o sistema faz | "Do improviso ao controle, em 3 passos" | — | — | 3 passos numerados (Cadastre → Opere → Acompanhe), ícone Phosphor por passo |
| 8 | **Visão do sistema** | Prova concreta, não promessa abstrata | "Veja o Fluxoly de verdade" | — | — | screenshot real do Dashboard/tela de OS (Card + Skeleton do Design System, nunca imagem de banco de imagem) |
| 9 | **Diferenciais** | Argumentar contra o "improviso" e a "gestão tradicional", não contra um concorrente nomeado | "Por que usar o Fluxoly?" | — | — | tabela Fluxoly vs. "Gestão tradicional" (ver Parte 3 — **não** nomear Mercado Phone; comparação direta e pública contra concorrente nomeado é decisão jurídica/comercial que não cabe a esta especificação) |
| 10 | **Prova social** | Gerar confiança | "Quem usa, recomenda" — **placeholder até haver depoimento real** | — | — | **não inventar depoimento** (regra explícita do brief) — se não houver cliente real citável ainda, a seção fica marcada `[DEFINIR — aguardando primeiro cliente/piloto citável]` no lugar de texto fictício |
| 11 | **Planos** | Remover a última objeção antes da conversão | "Um plano para cada estágio da sua loja" | — | "Falar com o time" / "Começar agora" | **preço e faixas ainda não definidos** (`docs/company/PRODUCT_REQUIREMENTS.md`, monetização parcialmente TODO) — seção estrutural pronta, valores `[DEFINIR]` |
| 12 | **FAQ** | Resolver objeções recorrentes sem precisar de contato humano | "Perguntas frequentes" | — | — | acordeão (`Accordion` novo, avaliar no plano técnico de implementação) |
| 13 | **CTA final** | Última chance de conversão, sem repetir o Hero | "Pronto para organizar sua operação?" | — | "Começar agora" | fundo com o acento de marca, texto curto |
| 14 | **Footer** | Navegação secundária + confiança institucional | logo Fluxoly | — | — | links (Produto, Sobre, Contato), redes sociais, copyright |

**Removido deliberadamente da referência:** o Mercado Phone tem uma seção só de "Recursos e Ferramentas"
extremamente longa (lista de ~10 recursos em bullet solto, "IA BLUE", "Simuladores de Upgrade"). Isso reforça
a narrativa de amplitude deles — o Fluxoly usa a seção 6 (Funcionalidades) para o mesmo papel, mas organizada
pelos 6 pilares já existentes na marca, e só depois de Problema/Solução/Benefícios já terem construído o
contexto — não como lista solta logo no topo.

---

## 3. Copy Completa

Textos-base por seção. Onde uma informação real não existe ainda (preço, número de lojas, depoimento),
o texto está marcado como `[DEFINIR]` — nunca preenchido com número ou citação inventados, conforme regra
explícita do brief.

### Navbar
`Produto` · `Como funciona` · `Planos` · `FAQ` · `Contato` — CTA: **Começar agora**

### Hero
> **O fluxo inteligente da sua loja de celulares.**
> Vendas, estoque, ordens de serviço e financeiro em um único sistema — sem planilha, sem caderno, sem
> retrabalho.
>
> [Começar agora] [Ver como funciona ↓]

### Problema
> **Sua loja roda no improviso?**
>
> - Planilha que ninguém atualiza a tempo
> - Estoque que só é conferido quando falta peça
> - Ordem de serviço anotada em papel, perdida entre um cliente e outro
> - Caixa fechado sem saber de onde veio o resultado do mês
>
> O Fluxoly existe para substituir isso por um fluxo único — não para adicionar mais uma ferramenta à pilha.

### Solução
> **Um único fluxo para toda a operação.**
> O Fluxoly reúne vendas, estoque, financeiro e assistência técnica em um só lugar — sem planilha paralela,
> sem sistema que não conversa com o outro.

### Benefícios
> **O que muda na prática.**

- **Menos tempo perdido com tarefas manuais** — o que hoje é digitado duas vezes passa a ser digitado uma.
- **Decisão com dado real** — não com a planilha que alguém esqueceu de atualizar.
- **Atendimento mais rápido** — histórico do cliente e da OS num só lugar, sem procurar em outro sistema.
- **Controle real do estoque** — sem contar peça na mão pra saber o que tem na loja.

### Funcionalidades
> **Um sistema, todas as frentes da loja.**
> Vendas, Estoque, Financeiro, Assistência Técnica e Inteligência — sem depender de ferramentas separadas
> que não conversam entre si.

Os 6 pilares (`BRAND_IDENTITY.md` §2), uma frase de benefício cada — **sem emoji no texto de produção**,
os emoji do documento de marca são só organização interna do documento:

- **Vendas** — Fechamento rápido, do primeiro contato ao recibo.
- **Operação** — Estoque sob controle, sem contagem manual de última hora.
- **Financeiro** — Caixa e resultado real, sempre visíveis.
- **Relacionamento** — Histórico completo de cada cliente, sem precisar perguntar de novo.
- **Serviços** — Ordem de serviço organizada do check-in à entrega.
- **Inteligência** — Decisão com dado real, não com achismo.

### Como funciona
> **Do improviso ao controle, em 3 passos.**
>
> 1. **Cadastre** — clientes, estoque e catálogo, uma vez só.
> 2. **Opere** — abra OS, registre vendas, controle o caixa, tudo no mesmo lugar.
> 3. **Acompanhe** — veja o resultado real da loja, sem planilha paralela.

### Visão do sistema
> **Veja o Fluxoly de verdade.**
> Sem mockup genérico — a tela que você vai usar todos os dias.

### Diferenciais
> **Por que usar o Fluxoly?**
>
> | Fluxoly | Gestão tradicional |
> |---|---|
> | Operação centralizada | Ferramentas separadas |
> | Visão da operação | Informações dispersas |
> | Controle de estoque | Controle manual |
> | Financeiro integrado | Planilhas |
> | Assistência técnica organizada | Processos separados |
>
> Tabela conforme definida pelo CTO (2026-08-16) — comunica o diferencial sem citar ou atacar um concorrente
> nomeado.

### Prova social
`[DEFINIR — aguardando primeiro cliente/piloto citável antes de publicar qualquer depoimento ou logotipo]`

### Planos
> **Um plano para cada estágio da sua loja.**
> `[DEFINIR — faixas e valores dependem da decisão de monetização em docs/company/PRODUCT_REQUIREMENTS.md]`

### FAQ
> **Perguntas frequentes**

1. **O que é o Fluxoly?**
   O Fluxoly é uma plataforma de gestão para lojas especializadas em dispositivos móveis premium — reúne
   vendas, estoque, financeiro, assistência técnica e inteligência de negócio em um único sistema.
2. **Preciso trocar todo o meu processo para usar o Fluxoly?**
   Não. O Fluxoly se adapta à operação da loja — não o contrário (`BRAND_IDENTITY.md` §4).
3. **O Fluxoly serve para qualquer tipo de loja?**
   O Fluxoly é feito especificamente para lojas especializadas em dispositivos móveis premium, não para
   varejo genérico (`BRAND_IDENTITY.md` §4).
4. **Existe um período de teste?**
   `[DEFINIR — depende da estratégia comercial em docs/company/RELEASE_STRATEGY.md]`
5. **Como funciona o suporte?**
   `[DEFINIR]`

### CTA final
> **Pronto para organizar sua operação?**
> [Começar agora]

### Footer
Logo + `Produto` `Sobre` `Planos` `FAQ` `Contato` + redes sociais (quando existirem) + `© Fluxoly, todos os
direitos reservados.`

---

## 4. Design System da Landing Page

**Princípio:** reaproveitar integralmente o que já foi formalizado nas PRs #41–#43
(`docs/engineering/ENGINEERING_GUIDE.md` §3.2) — a Landing Page pode ter mais liberdade de composição
(seção "Design System do Fluxoly" abaixo), mas os tokens de marca são os mesmos do produto, não uma paleta
nova derivada do Mercado Phone (ver "Nota de Decisão" acima).

### Cores

| Nome | HEX (aprox.) | Finalidade |
|---|---|---|
| `--color-background` | `#141414` | Fundo base da página |
| `--color-foreground` | `#EBEBEB` | Texto principal sobre fundo escuro |
| `--color-card` | `#1F1F1F` | Superfície de cards/seções elevadas |
| `--color-card-foreground` | `#F5F5F5` | Texto sobre card |
| `--color-primary` | `#FF0125` | Acento de marca — CTA primário, destaques, ícones-chave |
| `--color-primary-foreground` | `#FFFFFF` | Texto sobre o acento primário |
| `--color-muted-foreground` | `#808080` | Texto secundário/legendas |
| `--color-border` | `#333333` | Bordas e divisores |
| `--color-sidebar` | `#0A0A0A` | Tom mais escuro que o fundo — reservado para faixas de maior contraste (ex.: footer, seção final) |
| Sucesso | `#22C55E` (a validar contra `--color-chart-2`) | Estados positivos (ex.: "resolvido", checkmarks de diferencial) |
| Atenção | `#F59E0B` (`--color-chart-3`) | Estados de atenção — uso raro na Landing Page |
| Erro | `#FF0125` (mesma cor do primário — **não** duplicar com um vermelho diferente) | Estados de erro, quando aplicável |
| Informativo | `#3B82F6`/`--color-chart-5` | Uso raro — só se um badge informativo for necessário |

Todos esses valores já existem em `frontend/src/index.css` (`@theme`) — **nenhuma cor nova é criada para a
Landing Page.** Os valores de sucesso/atenção/informativo acima precisam de confirmação exata contra os
`--color-chart-*` já definidos antes da implementação (marcado "a validar" porque este documento não
reabriu `index.css` para reconferir byte a byte).

### Tipografia

**Estado atual confirmado (não hipótese):** o produto interno usa a pilha padrão do sistema operacional
(`font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif`,
`frontend/src/index.css` linha 67) — não existe fonte customizada nem decisão de tipografia registrada em
nenhum documento do projeto hoje.

**Correção de escopo (2026-08-16, decisão do CTO):** a escolha de uma fonte nova **não é uma decisão da
Landing Page** — se adotada, é uma decisão do **Fluxoly Design System** (mesmo nível de `ENGINEERING_GUIDE.md`
§3.2), porque precisa valer igualmente para Landing → Login → Sistema. Este documento **propõe**, não decide:

**Proposta a validar no Design System: Inter** (Google Fonts, gratuita, licença OFL, excelente legibilidade
em qualquer tamanho, neutra o suficiente para não competir com o vermelho de marca) — evita tanto clonar a
"Plus Jakarta Sans" do Mercado Phone quanto inventar uma fonte sem justificativa. **Não implementado, não
decidido** — precisa de um amendment próprio (mesmo formato do amendment do ADR-001 nas PRs #41-#43) antes
de qualquer código, seja da Landing Page, seja do produto interno.

| Nível | Tamanho | Peso | Line-height | Uso |
|---|---|---|---|---|
| H1 (Hero) | `text-5xl`/`text-6xl` (48–60px) | 600 (semibold) | 1.1 | Título do Hero, único por página |
| H2 | `text-3xl`/`text-4xl` (30–36px) | 600 | 1.2 | Título de seção |
| H3 | `text-xl`/`text-2xl` (20–24px) | 600 | 1.3 | Subtítulo de card/bloco |
| H4 | `text-lg` (18px) | 500 | 1.4 | Título de item dentro de grid |
| Subtítulo | `text-lg`/`text-xl` (18–20px) | 400 | 1.5 | Texto de apoio abaixo de H1/H2, `text-muted-foreground` |
| Corpo | `text-base` (16px) | 400 | 1.6 | Parágrafos |
| Auxiliar | `text-sm` (14px) | 400 | 1.5 | Legendas, notas |
| Label | `text-xs`/`text-sm` uppercase, tracking-wide | 500–600 | 1.4 | Badges de seção (ex.: "FAQ", "Planos") |
| Botão | `text-sm` (14px) | 600 | 1 | Mesmo padrão já usado em `button.jsx` |

Escala inteiramente dentro do padrão Tailwind — mesma decisão já tomada em `ENGINEERING_GUIDE.md` §3.2
("Tipografia... seguem o mesmo princípio... escala padrão do Tailwind").

### Componentes

**Reaproveitar os componentes já existentes do Design System** (`frontend/src/components/ui/`) — não criar
um segundo sistema de componentes só para a Landing Page:

- **Buttons:** `button.jsx` já cobre `default`/`destructive`/`outline`/`ghost`/`secondary`. A Landing Page
  usa majoritariamente `default` (CTA primário, com o gradiente/acento de marca) e `outline` (CTA
  secundário, ex.: "Ver como funciona"). Tamanho `default`/`lg` (avaliar se `lg` precisa ser adicionado ao
  `button.jsx` na implementação — hoje só existem `default`/`sm`/`icon`).
- **Inputs:** reaproveitar `input.jsx` — usado só se houver captura de lead (ex.: campo de e-mail no CTA
  final), decisão de produto ainda não tomada aqui.
- **Cards:** `card.jsx` (PR #42) — usado nas seções Problema, Módulos, Diferenciais, FAQ (cada item como
  `Card`).
- **Badge:** `badge.jsx` já existente — usado nos rótulos de seção ("FAQ", "Planos", mesma função do
  "pill" que o Mercado Phone usa no topo de cada seção, mas com o vocabulário visual do Fluxoly, não o
  deles).
- **Accordion (FAQ):** **não existe ainda** no Design System (`frontend/src/components/ui/`) — precisa ser
  adicionado via `npx shadcn add accordion` numa fase futura de implementação, seguindo a mesma convenção já
  documentada (`ENGINEERING_GUIDE.md` §3.2) — não antecipado neste documento de especificação.
- **Tooltip/Sheet/Sidebar** (PR #43): sem uso previsto na Landing Page pública (são padrões do produto
  autenticado) — exceto se o menu mobile da Landing Page reaproveitar o `Sheet` para o drawer de navegação,
  decisão de implementação, não de especificação.

### Estética

Idêntica à decisão já registrada em `ENGINEERING_GUIDE.md` §3.2 — **não redecidida aqui**:

- **Radius:** `rounded-lg` (botões, inputs, itens de navegação), `rounded-xl` (cards, contêineres maiores).
  Nada tão arredondado quanto o Mercado Phone (`border-radius: 30px` nos CTAs, pill quase circular) — o
  Fluxoly usa o padrão já estabelecido, mais contido.
- **Shadow:** uso restrito (`shadow-sm` em elementos de formulário, `shadow-xl` em elementos flutuantes/
  overlay). Superfícies estáticas de conteúdo (cards de seção) não recebem shadow — separação visual via
  `border`/`bg-card` contra `bg-background`, evitando a estética "dashboard genérico de template" (mesma
  regra já registrada na Fase 1 do produto interno).
- **Spacing:** escala padrão do Tailwind, mesma decisão de `ENGINEERING_GUIDE.md` §3.2.
- **Bordas:** `border-border` padrão para divisores; um estado de hover mais visível
  (`hover:border-primary/40`, a validar na implementação) só em elementos interativos (cards clicáveis,
  se houver).
- **Superfícies:** hierarquia `background` (`#141414`) → `card` (`#1F1F1F`) → `sidebar`/faixa mais escura
  (`#0A0A0A`, reservada para o footer e a seção de CTA final, dando um "fecho" visual mais denso à página,
  eco do padrão de bandas claro/escuro que o próprio Mercado Phone usa — mas com a paleta do Fluxoly).

---

## 5. Regras de UX

- Uma pessoa que nunca ouviu falar do Fluxoly precisa responder, sem rolar mais que a Hero + Problema:
  "o que é" e "para quem é". Até o fim da página: "por que usar" e "qual o próximo passo".
- Um CTA primário por seção, no máximo — nunca dois botões de mesmo peso visual competindo.
- Hierarquia visual clara: H1 único por página, H2 um por seção, nunca pular nível (H1 → H3 direto).
- Contraste mínimo AA contra o fundo escuro — validar especialmente `--color-muted-foreground` sobre
  `--color-background` antes da implementação.
- Nenhum elemento decorativo sem função — linha do princípio já registrado em `ENGINEERING_GUIDE.md`
  (KISS) aplicado a marketing: se um elemento visual não ajuda a entender ou decidir, ele não entra.
- Feedback imediato em qualquer interação (hover, foco, clique) — mesmo padrão de estados já usado no
  produto interno.
- Cada seção da Parte 2 tem um único objetivo comunicacional — não misturar "prova social" com "diferencial"
  na mesma seção.

---

## 6. Regras de Responsividade

Definidas desde já, não como adaptação posterior:

- **Mobile (< 640px):** uma coluna, Hero com CTA logo abaixo do texto (sem exigir scroll para ver o botão),
  menu de navegação vira drawer (reaproveitando o `Sheet`/padrão de `Sidebar` mobile já construído no PR
  #43), grids de Módulos/Diferenciais empilham verticalmente, tabela comparativa da seção Diferenciais vira
  lista empilhada (não scroll horizontal de tabela).
- **Tablet (640–1024px):** grids de 2 colunas onde no mobile é 1 e no desktop é 3 (Módulos, FAQ mantém 1
  coluna em qualquer breakpoint — acordeão não se beneficia de grid).
  Corte de referência mesmo do Shell do produto interno (`lg:` = 1024px, `hooks/use-mobile.js` do PR #43).
- **Desktop (>= 1024px):** largura de conteúdo máxima (`max-w-6xl`/`max-w-7xl`, a definir na implementação),
  grids completos (3 colunas em Módulos/Diferenciais), navbar horizontal completa.
- **Imagens/mockups:** sempre com `srcset`/dimensões responsivas — nunca a mesma imagem em resolução total
  carregada no mobile (ver Performance abaixo).
- **CTA:** botão de largura total no mobile, largura de conteúdo no desktop — nunca um CTA que exija scroll
  horizontal ou fique cortado em qualquer breakpoint.

---

## 7. Regras de Animação

Estratégia apenas — **nenhuma implementação nesta etapa**, mesma regra já usada no Shell/Dashboard do
produto interno (PR #43, `ENGINEERING_GUIDE.md` §3.2 "Motion vs. transição CSS"):

- **Motion** (já instalado, PR #43): hover de card, fade de entrada de seção ao rolar (`whileInView`),
  scale sutil em CTA, transição de FAQ (respeitando a mesma regra "Radix Presence vs. Motion" já registrada
  — se o Accordion futuro for baseado em Radix, o colapso usa CSS `data-state`, não Motion). Duração
  150–300ms, sempre com `useReducedMotion()`.
- **GSAP** (não instalado ainda — só entra na implementação futura da Landing Page, nunca no produto
  autenticado): reservado para o Hero (entrada de elementos em sequência) e eventualmente scroll storytelling
  na seção Como Funciona/Módulos — nunca para um fade simples que o Motion já resolve.
- **Three.js:** sem justificativa visual identificada nesta especificação — não recomendado, a menos que uma
  necessidade real apareça na implementação (ex.: uma peça 3D do produto no Hero, decisão de produto, não
  antecipada aqui).
- **Anime.js:** não recomendado — Motion e GSAP juntos cobrem tudo que esta especificação define.

---

## 8. Checklist para Implementação Futura

- [ ] Design System validado (Parte 4 revisada e aprovada pelo CTO, incluindo a confirmação dos tokens de
      sucesso/atenção/informativo contra `index.css`)
- [ ] Copy validada (Parte 3 revisada — inclusive decisão sobre os itens `[DEFINIR]`: preço, prova social,
      trial)
- [ ] Estrutura validada (Parte 2 — 12 seções aprovadas ou ajustadas)
- [ ] Responsividade planejada (Parte 6)
- [ ] Acessibilidade planejada (Parte 5 + Parte 6)
- [ ] Performance planejada (lazy loading de imagens/seções abaixo da dobra, code splitting da rota da
      Landing Page separada do bundle autenticado, GSAP carregado só se/quando usado)
- [ ] Componentes definidos (Parte 4 — reaproveitar `button`/`input`/`card`/`badge`; `accordion` a adicionar)
- [ ] Animações definidas (Parte 7 — Motion agora, GSAP reservado, Three.js/Anime.js só com justificativa)
- [ ] CTAs definidos (Parte 2/3 — "Começar agora" como CTA único e consistente em toda a página)
- [ ] SEO planejado (título, meta description, Open Graph, `alt` de imagens — nenhuma dessas peças definida
      nesta especificação, fica para o plano técnico de implementação)
- [ ] Plano Técnico de implementação redigido e aprovado pelo CTO, seguindo o mesmo gate do `CLAUDE.md`
      (`docs/engineering/plans/PLAN-*.md`) antes de qualquer código React ser escrito
