# PLAN-design-system-fase3-visual-experience — Fluxoly Visual Experience Redesign

**Data:** 2026-08-20
**Feature:** mudança de direção de produto/UX — decisão do CTO após revisar o resultado visual da Fase 2.
Toca identidade de marca (só o Product Owner decide, `docs/company/BRAND_IDENTITY.md`) e restrutura como
componentes compartilhados se encaixam (nova camada de tema, nova hierarquia de superfície) — gate
arquitetural completo, não o "apresentar plano" simples de 3+ arquivos.
**Status:** 🟡 Planejado — spec aprovada em conversa, liberdade criativa total autorizada em 2026-08-20
(ver seção 0.1). Ainda aguardando virar plano de implementação (`writing-plans`) antes de codificar.
**Nenhum código escrito ainda.**

> Este documento é efêmero, mesmo princípio de `PLAN-design-system-fase1.md`/`PLAN-design-system-fase2.md`.
> Local escolhido para manter a mesma convenção dos planos de Design System já existentes neste diretório,
> em vez do local padrão da skill de brainstorming (`docs/superpowers/specs/`) — este repositório já tem
> uma estrutura de documentação própria e explícita (`docs/README.md`), e este plano segue essa estrutura.

---

## 0. Por que este documento existe

A Fase 2 (`PLAN-design-system-fase2.md`) teve um objetivo explícito e documentado desde o título:
"Foundation + Expansão às 24 telas... **sem criar uma identidade visual nova**". Isso foi cumprido —
5 PRs mergeados, consistência técnica real (Badge semântico, filtros padronizados, estados de
carregamento/vazio/erro, ícones únicos). Mas ao ver o resultado, o CTO identificou que esse objetivo
estava conservador demais: o sistema ficou tecnicamente consistente, mas visualmente continua parecendo
"mais um dashboard SaaS", porque nunca foi pedido — nem existia — nenhuma composição própria, nem modo
claro.

Este documento **não estende a Fase 2**. Abre a Fase 3: uma mudança de objetivo, de "consistência técnica"
para "linguagem visual autoral", com um requisito novo e obrigatório (Light Mode + Dark Mode) que a Fase 2
nunca teve.

**Nota sobre a origem do briefing:** a direção descrita abaixo foi baseada numa descrição textual muito
detalhada de referências visuais (dashboards, um estudo de composição editorial, um exemplo com Light/Dark
lado a lado) que o CTO trouxe para a conversa — as imagens em si não foram compartilhadas nesta sessão.
Os princípios abaixo foram extraídos da descrição, não das imagens. Se as imagens forem compartilhadas
depois, este documento deve ser revisto contra elas antes da implementação começar.

---

## 0.1. Autorização — Liberdade Criativa Total (2026-08-20)

Em 2026-08-20, o CTO/Product Owner revogou explicitamente o "PRINCÍPIO FUNDAMENTAL" registrado na
sessão de brainstorming original (seção 13, versão anterior deste documento): **"não altere a identidade
de marca já definida"**. A nova instrução, na íntegra: *"a partir de agora você tem autoridade total
para ser livre, essas regras não são mais obrigatórias — apenas transforme tudo em um site com uma
grande e bela identidade visual surpreendente."*

Escopo confirmado via pergunta direta ao CTO antes de registrar esta seção:

| Eixo | Decisão | Detalhe |
|---|---|---|
| **Identidade de marca** | Também está aberta | `#FF0125`, wordmark Onest e ícone deixam de ser fixos — podem ser reinventados como parte da liberdade criativa, não só a composição em cima deles. `docs/company/BRAND_IDENTITY.md` deixa de ser a autoridade travada para esta iniciativa e **precisará ser atualizado** quando uma nova identidade concreta for produzida (o documento continua sendo o registro oficial — muda o conteúdo, não a obrigação de mantê-lo atualizado). |
| **Processo de engenharia** | Mantido — sem mudança | Plano aprovado, branch de feature, PR, CI 6/6, revisão e testes continuam exatamente como em todas as fases anteriores (protocolo do `CLAUDE.md`). A liberdade é sobre **direção criativa**, não sobre o ritual de entrega. |
| **Escopo de superfície** | Produto inteiro | As ~24 telas internas autenticadas (Dashboard, Orders, Vendas, Estoque, Financeiro, etc.) — **não** inclui a Landing Page pública (`Landing.jsx`), que fica fora desta autorização por ora. |

**O que isso muda em relação ao resto deste documento:** as seções 1–12 abaixo (diagnóstico, princípios,
Light/Dark, tipografia, layout, componentes, dashboard, priorização, microinterações, diferenciação,
faseamento) continuam válidas como **ponto de partida analítico** — o diagnóstico de por que o visual
parece genérico não mudou. Mas deixam de ser **restrições rígidas**: onde qualquer princípio abaixo
(ex.: "vermelho como assinatura", paleta de cores específica, manter Onest) conflitar com uma direção
mais ousada, a liberdade desta seção prevalece. A seção 13 ("o que este documento preserva") foi
revisada para refletir isso — a marca não é mais parte do que é preservado.

**Por que isso não vira implementação imediata:** a liberdade concedida é sobre *direção artística*, não
sobre pular o processo (ver tabela acima). O próximo passo continua sendo transformar esta direção em um
plano de implementação formal (`writing-plans`) antes de qualquer commit de código — nada nesta seção
dispensa isso.

---

## 0.2. Direção de Identidade Escolhida — Pulse (2026-08-20)

A partir da liberdade concedida em 0.1, três direções concretas de identidade (cor + wordmark + ícone,
cada uma um sistema fechado) foram exploradas num canvas visual (Claude Design, artifact "Fluxoly Identity
Directions") e comparadas lado a lado pelo CTO. Escolhida: **B — Pulse**.

| Elemento | Direção escolhida | Substitui |
|---|---|---|
| Cor de assinatura | `#FF3D5A` (vermelho-sinal) | `#FF0125` |
| 2º acento | `#29E0C9` (ciano "fluxo ao vivo" — só indicadores positivos/tempo real) | Não existia como token de marca |
| Ícone | Traço contínuo tipo pulso/ECG terminando em seta — fluxo como sinal vivo, não uma letra | Monograma abstrato da letra "F" |
| Wordmark (logotipo) | Space Grotesk Bold 700 | Onest Bold 700 |
| Fonte de UI/corpo | Onest — **mantida**, não foi abandonada | — |

Registrado formalmente em `docs/company/BRAND_IDENTITY.md` §10 e `docs/company/DECISION_LOG.md`
(2026-08-20). **Nenhum código mudou ainda** — `frontend/src/index.css`, favicon e materiais continuam com
os valores antigos até a Fase 3.0 (infraestrutura de tema) ser implementada; os SVGs do ícone no canvas
são protótipos de direção, não arte vetorial final de produção.

**Efeito nas seções 1–12 abaixo:** onde essas seções (escritas antes da decisão de identidade) mencionam
`#FF0125` ou "Onest" como wordmark, leia como `#FF3D5A`/`#29E0C9` e Space Grotesk (as seções 3 e 4 já
foram atualizadas pontualmente nas linhas de "vermelho"; o resto dos princípios de composição — hierarquia
de superfície, respiro, Light/Dark como sistemas distintos — permanece válido sem mudança).

---

## 1. Diagnóstico — por que o visual atual ainda parece genérico

Achados concretos, não impressão geral:

1. **`Dashboard.jsx`**: 8 KPI cards idênticos em grid + 3 cards de gráfico do mesmo tamanho abaixo. Nenhum
   dado tem tratamento de "isso é o mais importante desta tela" — tudo tem o mesmo peso visual.
2. **Todas as telas de lista** (Orders, Stock, Vendas, Financeiro, Clientes, Produtos...) repetem a mesma
   forma: barra de filtro → tabela dentro de `bg-card border border-border rounded-xl` → paginação. A
   única coisa que muda de tela pra tela são os rótulos das colunas.
3. **`Layout.jsx`** (sidebar): 18 itens em lista plana, ícone+label, sem agrupamento nem hierarquia entre
   seções — "Dashboard" e "Backups" têm exatamente o mesmo peso visual, apesar de frequência de uso e
   importância completamente diferentes.
4. **Um único modo de cor.** `index.css` define só `--color-background: #141414` fixo, sem
   `@media (prefers-color-scheme)` nem toggle. "SaaS escuro" não é uma escolha de marca — é a única opção
   que existe.
5. **Card uniforme como recipiente universal.** A combinação `bg-card border border-border rounded-xl p-4`
   se repete literalmente em dezenas de lugares — é a receita padrão do shadcn/ui, sem nenhuma variação de
   peso/hierarquia entre "isso é o dado principal" e "isso é uma métrica de apoio".
6. **Vermelho subutilizado, não superutilizado.** `--color-primary` só aparece em botão/foco — nunca como
   assinatura de composição (destaque de gráfico, indicador crítico, acento). Isso paradoxalmente também
   contribui pro genérico: a cor de marca não é reconhecível em lugar nenhum além do botão "Salvar".
7. **Composição editorial existe em exatamente um lugar** (`Landing.jsx`, com componentes próprios não
   compartilhados) e em nenhum outro — ou seja, o "momento premium" da marca só existe na porta de entrada
   pública, nunca dentro do produto que o cliente realmente usa todo dia.

---

## 2. Direção artística — princípios, não um nome de marca

Cinco regras concretas, testáveis, que substituem "componentes soltos numa página" por composição:

1. **Hierarquia de superfície, não card uniforme.** Toda tela tem exatamente 1 elemento dominante (o dado
   mais importante daquela tela) e o resto se organiza em pelo menos 3 níveis de peso: dominante (grande,
   respiro próprio) → secundário (listas/métricas, peso médio) → apoio (texto solto, sem moldura). Regra
   prática: no máximo 2 elementos do mesmo peso lado a lado sem um elemento dominante acima/ao redor.
2. **Vermelho como assinatura, não decoração.** No máximo 1–2 elementos vermelhos "vivos" (fora hover/foco)
   visíveis por tela ao mesmo tempo — CTA primário, ou 1 indicador crítico, ou o item selecionado/ativo.
   Nunca em ícone de navegação em repouso, nunca em borda decorativa, nunca em fundo de card.
3. **Dois modos, duas intenções — não inverter.** Light usa sombra sutil pra dar profundidade (não pode
   clarear mais que branco); Dark usa camadas de cinza-quase-preto pra dar profundidade (sombra não
   funciona em fundo escuro). Espaçamento e tipografia são idênticos nos dois — só a linguagem de
   profundidade muda.
4. **Respiro é conteúdo.** O elemento dominante de cada tela precisa de pelo menos 32–48px de respiro puro
   ao redor antes de qualquer outro elemento — vazio ao redor do que importa não é espaço perdido, é o que
   sinaliza importância.
5. **Nem tudo é card.** Listas podem ser blocos sem moldura própria (só divisor sutil entre linhas);
   métricas de apoio podem ser número solto + rótulo pequeno, sem moldura nenhuma. Só o elemento dominante
   de cada tela ganha o tratamento "painel" (fundo distinto + leve elevação).

---

## 3. Light Mode

| Camada | Tratamento |
|---|---|
| `background` | Quase-branco, não branco puro (ex. `#F7F7F8`) — reserva o branco puro pra superfície, criando contraste de peso. |
| `surface` (painel dominante) | `#FFFFFF` puro, separado do fundo por sombra sutil, não por borda — sombra é a ferramenta de profundidade no light. |
| `texto primário` | Quase-preto (ex. `#1A1A1A`), não preto puro. |
| `borda` | Extremamente sutil (ex. `#EDEDEF`), usada com moderação — preferir sombra a borda pra separar superfícies. |
| `vermelho-sinal` | `#FF3D5A` (direção Pulse, decidida 2026-08-20 — ver seção 0.2) — fica ainda mais "vivo" por contraste em fundo claro, então a regra de moderação (princípio 2) importa mais aqui, não menos. `#29E0C9` (fluxo ao vivo) é o 2º acento, só para indicadores positivos/tempo real. |
| `estados` (success/warning/error/info) | Precisam de nova calibração de contraste — os tokens atuais em `index.css` foram calibrados só para fundo escuro (comentário explícito no arquivo: "recalibrados para legibilidade sobre `--color-background`/`--color-card`"). WCAG AA mínimo em fundo claro é requisito, não opcional. |
| `gráficos` | Fundo transparente, grid quase invisível, linha com peso maior que no dark (compensa a ausência do glow que só funciona em fundo escuro). |

---

## 4. Dark Mode

Não é herdar o que já existe — hoje só há 2 níveis (`background` #141414, `card` #1F1F1F). Precisa de um
sistema de camadas real:

| Camada | Tratamento |
|---|---|
| `background` | Nível mais fundo, quase preto puro. |
| `surface` (painel dominante) | Nível intermediário — o `--color-card` atual (#1F1F1F) vira este nível. |
| `surface-raised` (popover/dropdown/elemento flutuante) | Ligeiramente mais claro que `surface` — dá profundidade real em vez de tudo no mesmo cinza. |
| `texto` | `#EBEBEB` já calibrado, ok — considerar um segundo nível de branco pra distinguir título de corpo. |
| `borda` | Sutil mas visível — no dark, borda é a ferramenta de separação principal (sombra não funciona bem em fundo escuro). |
| `vermelho-sinal` | `#FF3D5A` (direção Pulse, decidida 2026-08-20), já tem bom contraste — reforçar como "a cor de assinatura da tela", com `#29E0C9` reservado para indicadores de fluxo ao vivo/positivo, o resto neutro. |
| `gráficos` | Glow/opacidade sutil no dado ativo/selecionado — recurso que só funciona bem em fundo escuro, reforça seleção sem precisar de mais uma cor. |

---

## 5. Tipografia

Space Grotesk (wordmark, decidido 2026-08-20 — seção 0.2) e Onest (UI/corpo, mantida) ganham escala de
hierarquia real — hoje quase tudo usa `font-bold`/
`font-medium` genérico sem escala documentada:

| Papel | Tratamento |
|---|---|
| Título de página | Onest Bold, 28–32px, só 1 por tela. |
| Número dominante (métrica principal) | Onest Bold/Black, 40–56px — hoje nenhum número do sistema recebe tratamento "hero"; todos têm o mesmo tamanho pequeno dentro de card. Isso é o que mais falta. |
| Corpo/rótulo | Peso regular/medium, tamanho pequeno-médio consistente, cor secundária. |
| Dado tabular (IMEI, valores) | Fonte monoespaçada — já usada informalmente em alguns lugares (`font-mono` em IMEI), vira regra documentada da Foundation, não escolha acidental por arquivo. |

---

## 6. Layout

- **Sidebar**: agrupar os 18 itens de `navItems` em seções com rótulo (os 6 Pilares Macrossistêmicos já
  documentados em `BRAND_IDENTITY.md` §2 — Vendas/Operação/Financeiro/Relacionamento/Serviços/Inteligência
  — são o agrupamento lógico natural, conecta marca e produto de um jeito que hoje não existe). Colapso já
  tem infraestrutura (`SidebarProvider`/`SidebarTrigger` do shadcn) — é questão de composição, não de
  infra nova.
- **Header de contexto**: hoje cada página resolve "título + ação" com o próprio `flex justify-between`
  duplicado. Propor um header de conteúdo compartilhado (título + ação primária da tela, talvez breadcrumb
  leve), reduzindo duplicação e dando um lugar fixo pro elemento dominante de cada tela se ancorar.
- **Grid assimétrico**: abandonar grid uniforme de N colunas iguais em telas de visão geral — usar
  `grid-template-areas` nomeadas (1 área grande + áreas de apoio menores) em vez de `grid-cols-4` repetido.

---

## 7. Componentes — evolução da Foundation, não substituição

| Componente | Evolução |
|---|---|
| Card | Deixa de ser o recipiente universal. Vira 1 de ~4 possíveis: **Painel** (dominante, fundo + leve elevação), **Bloco de lista** (sem moldura própria, só divisor), **Métrica solta** (sem moldura nenhuma), **Elemento flutuante** (dropdown/popover/toast, já via Radix). |
| Button/Input/Select | Mantém a API acessível do shadcn (não vale reescrever a base) — evolui só o skin (cor/radius/peso) pros 2 modos. |
| Badge | Já semântico (Fase 2) — recalibrar cores pros 2 modos. |
| Tabela | Hoje é HTML cru com bordas manuais repetidas por arquivo — vira componente `DataTable` real da Foundation (hover já existe via `interactiveRowClassName`, adicionar header sticky em listas longas). |
| Gráficos (Recharts) | Definir tema único (cor/grid/tooltip/dado ativo) consumido por todo gráfico, em vez de estilizado ad-hoc por chart card. |
| EmptyState/ErrorState/LoadingState | Já existem (Fase 2) — evoluir visual pros 2 modos, manter a API atual (nenhuma mudança de contrato). |
| Navigation (sidebar) | Conforme seção 6. |

---

## 8. Dashboard — composição proposta

Substitui "8 cards iguais + 3 gráficos iguais" por hierarquia real:

```
┌─────────────────────────────────────────────┐
│  Faturamento do período          [Painel]    │
│  R$ 84.320                                    │
│  ↑ 12% vs. período anterior                   │
└─────────────────────────────────────────────┘

  Vendas hoje    Ticket médio    OS abertas     ← métricas soltas, sem moldura,
    23              R$ 890          7             número + rótulo, lado a lado

┌───────────────────────┐  ┌──────────┐  ┌──────────┐
│                       │  │          │  │          │
│  Gráfico principal    │  │ Serviços │  │ Técnicos │  ← 1 gráfico grande + 2
│  (receita, 2/3)       │  │ (1/3)    │  │ (1/3)    │     de apoio, não 3 iguais
│                       │  │          │  │          │
└───────────────────────┘  └──────────┘  └──────────┘

  Atividade recente / alertas          ← lista sem moldura pesada, divisor
```

---

## 9. Classificação das 21 telas restantes por prioridade

`Login.jsx`, `Shell` (`Layout.jsx`) e `Dashboard.jsx`/`Landing.jsx` nunca foram redesenhados de fato — a
Fase 1 só aplicou tokens/consistência técnica a eles, o redesenho de composição começa do zero também
nessas 4 telas/áreas.

| Tier | Telas | Por quê |
|---|---|---|
| **1 — Vitrine** | Dashboard, Login, Shell/Sidebar, harmonização da Landing | Maior exposição, maior potencial de composição, prova a direção antes de escalar. Login é isolado e de baixo risco. Shell toca todas as telas — precisa vir logo depois do Dashboard. |
| **2 — Operação diária** | Orders, Kanban, Vendas, Stock, Financeiro, Clientes | Maior volume de uso real, maior ganho percebido pelo lojista no dia a dia. |
| **3 — Formulário/detalhe** | NewOrder, EditOrder, VendaDetalhe, ChecklistDevice | Superfície de composição menor — ganho é mais sutil (tipografia/hierarquia de campo), não elemento dominante. |
| **4 — Administrativo** | Produtos, UnidadesSerializadas, Reports, PriceTables, RepairTypes, TiposGarantia, Users, Garantias, OperationalCosts, Backup, ShoppingList, Compras | Baixo tráfego relativo — aplica o sistema já maduro (Foundation v2 + tema), esforço de composição sob medida, não redesenho individual profundo. |

---

## 10. Microinterações

- `Reveal` (já existe, `components/ui/reveal.jsx`) — mantém para entrada de conteúdo pós-fetch.
- **Novo**: transição de número quando métrica atualiza — contagem incremental sutil, não crossfade
  genérico.
- Hover em linha de tabela já existe (`interactiveRowClassName`) — mantém.
- Filtro aplicado: leve destaque temporário nos resultados que mudaram — reaproveita a técnica já usada em
  `nav-context-highlight` (`useListContext.js`), mesmo princípio, novo contexto de uso.
- Troca de tema (light/dark): transição de cor suave (150–200ms), nunca instantânea/piscando.

---

## 11. Diferenciação — por que isso não vai parecer SaaS genérico

- Nenhum concorrente direto do setor (assistência técnica/loja de celular) tem Light+Dark bem feito — a
  maioria usa sistemas antigos sem essa camada de cuidado visual.
- Composição por hierarquia de superfície em vez de grid de cards uniforme é uma escolha deliberada contra
  o padrão "out of the box" do shadcn/ui — a maioria dos produtos B2B recentes usa exatamente esse padrão
  sem questionar; evitá-lo já diferencia.
- Vermelho como assinatura rara (não onipresente) cria reconhecimento de marca sem cansar visualmente — o
  oposto do que a maioria dos SaaS faz (cor primária em tudo).

---

## 12. Plano de implementação (fases/PRs)

Mesmo ritual de todas as fases anteriores: checkpoint arquitetural antes de cada fase, 1 PR por fase (ou
por tela dentro da fase, como já é convenção), CI 6/6 + revisão antes do merge.

| Fase | Escopo | Depende de |
|---|---|---|
| 3.0 | ✅ Concluído — Infraestrutura de tema (tokens Light/Dark, ThemeProvider, toggle, persistência) — branch feat/design-system-fase3.0-theme-infra, aguardando PR. Padrão sem preferência salva permanece Dark (ver KNOWN_ISSUES.md) até a Fase 3.1 migrar as telas com classes Tailwind hardcoded. | — |
| 3.1 | ✅ Concluído -- PR #<a preencher>, 2026-08-22 | 3.0 |
| 3.2 | **Vitrine (Tier 1)** — Dashboard + Login + Shell/Sidebar + harmonização da Landing. Prova de conceito da direção antes de escalar pro resto. | 3.1 |
| 3.3 | **Operação (Tier 2)** — Orders/Kanban/Vendas/Stock/Financeiro/Clientes. | 3.2 |
| 3.4 | **Formulários (Tier 3)** — NewOrder/EditOrder/VendaDetalhe/ChecklistDevice. | 3.2 |
| 3.5 | **Administrativo (Tier 4)** — telas restantes. | 3.2 |
| 3.6 | **QA visual global** — contraste AA nos dois modos, performance (motion/tema não pode pesar o bundle), microinterações finais, correção de qualquer desvio encontrado nas fases anteriores. | 3.5 |

---

## 13. O que este documento preserva (não muda)

> **Revisado em 2026-08-20** — ver seção 0.1. A identidade de marca (`#FF0125`, wordmark, ícone) **deixou
> de estar nesta lista** por autorização explícita do CTO/Product Owner; o item abaixo é o que continua
> valendo mesmo depois da liberdade criativa total.

- O nome **Fluxoly** em si (o produto continua se chamando Fluxoly) — a liberdade concedida é sobre
  identidade visual (cor/wordmark/ícone/composição), não sobre renomear o produto.
- Nenhuma lógica de negócio, API, payload ou regra de permissão muda — escopo é 100% apresentação.
- Acessibilidade (contraste, foco visível, `aria-*`) e performance continuam sendo requisitos não
  negociáveis, não trade-off pela composição nova.
- O processo de engenharia do `CLAUDE.md` (plano aprovado, branch, PR, CI, testes) — inalterado (seção 0.1).
- `docs/company/BRAND_IDENTITY.md` continua sendo o registro oficial da identidade — muda o que ele
  documenta quando a nova identidade for definida, não a obrigação de mantê-lo atualizado.

---

## 14. Abertos — precisam de decisão antes da Fase 3.0 começar

1. **Toggle de tema**: seguir preferência do sistema operacional por padrão (`prefers-color-scheme`) com
   override manual salvo, ou sempre exigir escolha explícita do usuário no primeiro acesso? (Recomendação:
   seguir o sistema por padrão, com toggle acessível — é o padrão mais comum e menos fricção.)
2. **Imagens de referência**: as imagens mencionadas na conversa não foram compartilhadas nesta sessão —
   revisar este documento contra elas antes da Fase 3.0, se e quando forem anexadas.
3. **Nome interno da iniciativa**: este documento não cunhou um nome de marca pra direção nova
   (deliberado — nomes de marketing tendem a soar vazios sem necessidade). Se o CTO quiser um nome interno
   pra facilitar referência em commits/PRs, definir antes da Fase 3.0.

---

## Ver também

- `docs/company/BRAND_IDENTITY.md` — autoridade da marca (inalterada por este plano).
- `docs/engineering/plans/PLAN-design-system-fase1.md` — Fase 1 (fundação + Shell + Dashboard, tokens).
- `docs/engineering/plans/PLAN-design-system-fase2.md` — Fase 2 (consistência técnica, 24 telas, sem
  identidade nova — objetivo que este documento substitui).
- `docs/engineering/ENGINEERING_GUIDE.md` §3.2/§3.3 — convenções vivas do Design System (a evoluir junto
  com a Fase 3).
