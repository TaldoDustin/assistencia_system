# Fluxoly — Brand Identity & Positioning Guide V1.0

**Status:** Aceito — certidão de nascimento e Constituição da Marca Fluxoly.
**Data:** 2026-07-10
**Autor:** Product Owner

Este documento consolida de forma atemporal a transição do sistema, antes focado isoladamente em
assistência técnica, para uma plataforma SaaS corporativa, unificada e verticalizada: **Fluxoly** —
o sistema operacional para lojas especializadas em dispositivos móveis premium.

Ver `docs/engineering/adr/ADR-006.md` para a decisão técnica de reorganização documental que acompanha
esta adoção, e a seção 9 abaixo para o cronograma de transição técnica de marca.

---

## 1. Nome Oficial e Significado

O nome Fluxoly nasce diretamente do conceito de fluxo. Não se limita ao fluxo de caixa ou de vendas
isoladamente, mas sim ao fluxo vital, integrado e contínuo de uma empresa de tecnologia mobile premium.
O objetivo central da marca é reduzir a dependência de controles paralelos, como planilhas e anotações
manuais, eliminando a dispersão operacional onde o lojista precisa consultar múltiplos sistemas, blocos
de notas e conversas para entender o próprio negócio. A Fluxoly unifica o caos em um fluxo inteligente.

---

## 2. Os 6 Pilares Macrossistêmicos

A arquitetura de marca e de produto da Fluxoly é sustentada por seis grandes avenidas conceituais,
projetadas para absorver quaisquer novos submódulos (como CRMs, APIs, Marketplaces ou integrações de
WhatsApp) nos próximos anos de escala:

- 📱 **Vendas** — Automação de balcão, check-out ágil, propostas comerciais e conversão rápida.
- 📦 **Operação** — Controle estrito de estoque rastreado individualmente por IMEI, compras, fornecedores
  e cadeia de suprimentos.
- 💰 **Financeiro** — Fluxo de caixa em tempo real, frentes de caixa integrados, conciliação e tesouraria.
- 👥 **Relacionamento** — CRM de reengajamento, pós-venda, canais de mensageria integrados e histórico
  unificado do cliente.
- 🔧 **Serviços** — Ordens de serviço (OS) especializadas, diagnósticos, rastreabilidade de peças e
  produtividade de bancada.
- 📊 **Inteligência** — Insights preditivos, motores de IA, dashboards executivos analíticos e geração de
  dados acionáveis.

> **Gap conhecido entre marca e código (2026-07-10):** o pilar Operação promete rastreamento individual
> por IMEI. A tabela `estoque` hoje (`app.py`, ver `docs/engineering/DOMAIN_MODEL.md` seção 1.4) não tem
> coluna de IMEI — o controle atual é por item agregado, não por unidade física. Isso não é um erro, é
> uma lacuna de escopo real entre a promessa de marca e a capacidade atual do domínio de Estoque, a ser
> resolvida quando esse domínio for revisitado.

---

## 3. Declaração Universal de Identidade

> "A Fluxoly desenvolve soluções inteligentes de gestão para lojas especializadas em dispositivos móveis
> premium, unindo vendas, estoque, financeiro, assistência técnica e inteligência de negócio em uma única
> plataforma."

**Diretriz de Uso:** Esta declaração é a definição padrão e imutável para o futuro site institucional,
propostas comerciais, apresentações a investidores, pitch decks e canais de posicionamento corporativo de
alto nível como o LinkedIn.

---

## 4. Princípios Inegociáveis (Escopo Negativo de Marca)

Para manter a identidade nítida e imune a desvios de mercado, o que a Fluxoly **nunca será e nunca fará**:

- A Fluxoly nunca será um ERP genérico e horizontal. Não atende mercados gerais, varejo alimentar ou
  indústrias. É cirúrgica no mercado mobile premium.
- A Fluxoly nunca será um sistema inflado com módulos inúteis. Cada funcionalidade precisa ter propósito
  claro e resolver uma dor real de gestão.
- A Fluxoly nunca será um software difícil de aprender. Rejeita interfaces complexas que exijam
  treinamentos exaustivos e burocráticos.
- A Fluxoly nunca obrigará o cliente a distorcer sua operação para se adaptar ao sistema. O produto é
  flexível e configurável por natureza.
- A Fluxoly nunca será uma empresa lenta para evoluir. Mantém um ritmo vivo de atualizações, iterações e
  melhorias semanais.
- A Fluxoly nunca tentará abraçar todos os mercados para agradar a todos. Mantém foco implacável no
  cliente ideal, preferindo a excelência verticalizada à mediocridade generalista.

---

## 5. A Promessa Fluxoly (Impacto de Mercado)

Linha de base de sucesso. Toda empresa que adota a Fluxoly deve, de maneira mensurável, atingir estes
cinco resultados fundamentais:

1. **Vender mais rápido** — fluxos de checkout dinâmicos que fecham carrinhos em menos de 60 segundos.
2. **Controlar melhor o estoque** — visibilidade total do inventário por IMEI, bloqueando furos e perdas
   ocultas de alto valor.
3. **Tomar decisões com dados reais** — substituição do "achismo" por dashboards interpretativos e
   diagnósticos escritos automáticos.
4. **Reduzir tarefas repetitivas** — automações nativas de comunicação e rotinas de digitação manual
   minimizadas ao extremo.
5. **Ter uma visão única do negócio** — centralização absoluta que elimina controles paralelos e
   ferramentas fragmentadas.

---

## 6. Governança e Decisões de Engenharia de Produto

Quando o time de engenharia e produto se deparar com múltiplos caminhos técnicos ou de design possíveis
para resolver um problema, a escolha deve obrigatoriamente priorizar a opção que:

1. Reduza o trabalho manual e operacional do usuário na ponta.
2. Reduza a quantidade de cliques necessários para concluir a ação.
3. Elimine por completo o retrabalho ou redigitação de informações.
4. Gere dados limpos, estruturados e inteligentes para o lojista.
5. Melhore de forma perceptível a experiência de compra do cliente final da loja.
6. Facilite futuras evoluções, manutenções e escalabilidade da arquitetura de código.

---

## 7. Visão de Futuro: Rumo a 2030

Meta de longo prazo não balizada por métricas voláteis de faturamento, mas por dominância de mercado e
autoridade de categoria:

> "Até 2030, a Fluxoly será solidamente reconhecida como a principal plataforma brasileira especializada
> na gestão integrada de lojas de dispositivos móveis premium, moldando o padrão tecnológico, operacional
> e de inteligência deste setor de ponta a ponta."

---

## 8. Matriz de Mídia e Comunicação (Taglines)

- **Aplicações institucionais e fachada corporativa:** Fluxoly — Inteligência para o seu negócio.
- **Campanhas de outbound e atração por dor operacional:** Fluxoly — Menos operação. Mais decisões.
- **Slogans de sustentação de marca:**
  - Fluxoly — O fluxo inteligente da sua empresa.
  - Fluxoly — Gestão que acompanha seu crescimento.
  - Fluxoly — Da venda ao pós-venda, em um único fluxo.

---

## 9. Cronograma de Transição Técnica de Marca

Para garantir estabilidade em pipelines e deploys, a transição do termo herdado "Assistência System"
obedece à seguinte governança interna de TI:

| Camada | Nomenclatura | Status |
|---|---|---|
| Negócio, telas e interfaces com o usuário | **Fluxoly** | Substituição total e imediata |
| Documentação técnica, APIs e integrações core | **Fluxoly Platform** | Em vigor a partir desta revisão da documentação |
| Repositório Git e infraestrutura interna (domínio, módulos `irflow_*.py`, `database.db`) | Nomenclatura legada mantida | Temporário — migração total em janela planejada antes do lançamento comercial |

**Aplicado nesta revisão da documentação (2026-07-10):** todo texto de documentação que descreve o
produto para o negócio passa a dizer "Fluxoly"; referências técnicas/API passam a dizer "Fluxoly
Platform". Nomes de repositório, domínio de produção (nomenclatura legada `assistencia-system`, hoje
servida via Render + Vercel — a hospedagem já migrou de Fly.io, mas o nome legado do slug não), arquivos
`irflow_*.py` e `database.db` **não são alterados** nesta etapa — ver `docs/engineering/adr/ADR-006.md`.

---

## 10. Identidade Visual (Logo e Tipografia)

**Status:** Revisado — 2026-08-20 (direção "Pulse", ver seção 10.4). Substitui a decisão de 2026-08-18
registrada anteriormente nesta seção. **Implementação em código ainda pendente** — ver nota de cada
subseção abaixo e `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (Fase 3.0/3.1).

### 10.1 Ícone

Traço contínuo que lê como um pulso/sinal de fluxo — um eletrocardiograma estilizado que termina numa
seta ascendente — em vez de uma letra. Substitui o monograma abstrato da letra "F" da decisão anterior.
A escolha é deliberada: a marca já se chama Fluxoly (fluxo), então um pulso comunica o conceito sem
precisar de uma letra como legenda, e é mais distintivo que um monograma — padrão comum entre marcas SaaS.

| Variação | Cor | Uso |
|---|---|---|
| Vermelho-sinal | `#FF3D5A` | Uso primário — fundo escuro, aplicação padrão da marca |
| Branco | `#FFFFFF` | Sobre fundos coloridos, fotográficos ou de alto contraste |
| Ciano de fluxo | `#29E0C9` | Variante "ao vivo" — contexto de indicador positivo/tempo real |
| Cinza | `#5B6178` | Uso monocromático discreto — marca d'água, estados desabilitados |
| Invertido | Ícone branco sobre badge vermelho-sinal sólido (`#FF3D5A`) | Favicon, ícone de app, avatar |

**Pendente:** o traço acima existe hoje como protótipo de direção num canvas de exploração (artifact
"Fluxoly Identity Directions", Claude Design) — ainda não é arte vetorial final de produção. Desenhar o
SVG definitivo, gerar as 5 variações de cor como arquivos (`frontend/public/brand/fluxoly-icon-*.svg`) e
aplicá-las (favicon, header, materiais) é trabalho da Fase 3.0/3.1, ainda não feito.

### 10.2 Tipografia

**Wordmark (logotipo):** Space Grotesk, peso **Bold (700)** — geométrica, mais técnica que a Onest,
alinhada à direção "Pulse" (fluxo como sinal vivo, não composição arredondada/amigável).

**UI e corpo de texto:** Onest — **mantida**, não foi abandonada. A mudança de wordmark não troca a
fonte usada em botões, tabelas, formulários e texto de produto; troca apenas a fonte do logotipo
"Fluxoly" em si.

Onest continua sendo o resultado do comparativo entre ~15 fontes candidatas (Cabinet Grotesk, Sora,
General Sans, Clash Display, Satoshi, Switzer, Supreme, Chillax, Manrope, Plus Jakarta Sans, Urbanist,
Inter, entre outras, além de "Surgena" e "Goodly" testadas e descartadas) — decisão de 2026-08-18,
válida para UI. Space Grotesk é uma decisão nova, específica do logotipo, de 2026-08-20.

### 10.3 Paleta de cores da marca

| Token | Valor decidido | Papel |
|---|---|---|
| Cor de assinatura | `#FF3D5A` | Vermelho-sinal — ação primária, ícone padrão. Substitui `#FF0125`. |
| 2º acento | `#29E0C9` | Ciano "fluxo ao vivo" — só indicadores positivos/tempo real. Token novo, não existia antes. |

**Pendente:** `frontend/src/index.css` (`--color-primary` e demais tokens `@theme`) ainda está com os
valores antigos (`#FF0125`, sem token de 2º acento) — atualizar o CSS é trabalho de código da Fase 3.0,
não feito nesta revisão de documentação. Até lá, `index.css` não é a fonte de verdade para a cor de
marca; esta tabela é.

### 10.4 Histórico da decisão (2026-08-20)

Em 2026-08-20 o CTO/Product Owner concedeu liberdade criativa total para o redesign visual da Fase 3,
incluindo reinventar a identidade em si (não só a composição em cima dela) — ver
`docs/company/DECISION_LOG.md` entrada 2026-08-20 "Liberdade criativa total...". A partir disso, três
direções concretas (cor + wordmark + ícone como sistema fechado) foram exploradas visualmente e
comparadas lado a lado; **Pulse** foi a escolhida. As duas alternativas descartadas foram: "Ember"
(evolução refinada mantendo `#FF0125`/ícone-F/Onest) e "Atelier" (composição editorial, papel + serifada
Instrument Serif, vermelho-tinta `#C81E3A`) — preservadas apenas no artifact de exploração, não neste
documento.

---

## Documentos relacionados

- `docs/company/VISION.md` — missão, visão, valores e critérios de sucesso (deriva deste documento)
- `docs/company/PRODUCT_REQUIREMENTS.md` — mercado-alvo, diferenciais e escopo negativo (deriva deste documento)
- `docs/engineering/DOMAIN_MODEL.md` — estado real do código, incluindo o gap de rastreamento por IMEI citado na seção 2
- `docs/engineering/adr/ADR-006.md` — decisão de reorganização documental e cronograma técnico de rename
