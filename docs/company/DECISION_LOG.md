# DECISION_LOG.md — Histórico Executivo de Decisões

Este documento é diferente de um ADR. **ADR é arquitetural** — registra alternativas técnicas avaliadas
e a escolha entre elas (`docs/engineering/adr/`). **Decision Log é executivo** — registra decisões de
produto/negócio, o motivo e o impacto, em ordem cronológica, para que ninguém precise reconstruir "por
que decidimos isso" a partir de conversas antigas.

**Última revisão:** 2026-07-25

**Regra de escrita:** toda entrada cita a fonte onde a decisão foi originalmente registrada (a maioria já
está documentada em outro lugar — este log não substitui esses documentos, indexa-os cronologicamente
para leitura executiva rápida). Nenhuma decisão nova é tomada aqui; este documento cataloga, não decide.

**Formato de cada entrada:**

```
## AAAA-MM-DD — Título curto

**Decisão:** o que foi decidido.
**Motivo:** por que essa opção e não outra.
**Impacto:** o que isso afeta (áreas, documentos, sprints).
**Fonte:** onde a decisão completa está registrada.
```

---

## 2026-07-09 — Módulo de Vendas: um único fluxo para novo, usado e troca

**Decisão:** Vendas de aparelho novo e troca (usado) seguem o mesmo fluxo, com avaliação de usado como
sub-etapa — não é um módulo à parte.
**Motivo:** Mais simples de especificar e implementar primeiro.
**Impacto:** Arquitetura do domínio Vendas (quando implementado); escopo da Sprint P2.
**Fonte:** `docs/product/features/VENDAS.md` — "Decisões já tomadas".

## 2026-07-09 — Aprovação de desconto reaproveita o perfil `admin`

**Decisão:** Desconto acima do limite do vendedor é aprovado por qualquer usuário com perfil `admin`;
**não** será criado um perfil `gerente` agora.
**Motivo:** Reaproveita perfil já existente — zero mudança de schema de permissões no momento.
**Impacto:** `docs/product/BUSINESS_RULES.md` BR-018; revisitar apenas quando houver mais de uma loja/equipe.
**Fonte:** `docs/product/features/VENDAS.md` — "Quem usa", "Decisões já tomadas".

## 2026-07-09 — Reserva de IMEI com expiração automática

**Decisão:** Reservar um IMEI durante o atendimento, com expiração automática se a venda não fechar.
**Motivo:** Evita venda duplicada do mesmo aparelho sem travar estoque indefinidamente por atendimento
abandonado.
**Impacto:** `docs/product/BUSINESS_RULES.md` BR-017; valor exato do timeout segue `TODO` — ver
`docs/company/NON_FUNCTIONAL_REQUIREMENTS.md`.
**Fonte:** `docs/product/features/VENDAS.md` — "Fluxo completo", "Decisões já tomadas".

## 2026-07-09 — Comissão calculada sobre margem, não sobre valor bruto

**Decisão:** A comissão do vendedor incide sobre a margem (venda − custo), nunca sobre o valor bruto da venda.
**Motivo:** Alinha o incentivo do vendedor com rentabilidade real — desconto exagerado corta a comissão
dele também.
**Impacto:** `docs/product/BUSINESS_RULES.md` BR-019; percentual exato segue `TODO`, decisão futura do Product Owner.
**Fonte:** `docs/product/features/VENDAS.md` — "Decisões já tomadas".

## 2026-07-09 — Garantia de venda desacoplada da garantia de reparo

**Decisão:** Garantia de venda tem prazo próprio por tipo de aparelho (novo/seminovo) — não reaproveita
os 90 dias hardcoded do reparo.
**Motivo:** Desacopla desde o início da regra hardcoded de reparo, já registrada como dívida técnica.
**Impacto:** `docs/product/BUSINESS_RULES.md` BR-020; `docs/company/OPERATION_SYSTEM.md` bloco "Garantia".
**Fonte:** `docs/product/features/VENDAS.md` — "Decisões já tomadas".

## 2026-07-09 — Cliente vira entidade própria no V1 de Vendas

**Decisão:** Vendas cria uma tabela `clientes` própria — nenhuma venda salva nome de cliente como texto solto.
**Motivo:** Pré-requisito estrutural já identificado (histórico de cliente hoje é só texto em `os.cliente`,
sem identidade real) — base para histórico e pós-venda.
**Impacto:** Domínio de Vendas; futuro CRM (`docs/company/BRAND_IDENTITY.md` pilar Relacionamento);
`docs/engineering/DOMAIN_MODEL.md` seção 2.
**Fonte:** `docs/product/features/VENDAS.md` — "Decisões já tomadas"; `docs/product/BUSINESS_RULES.md` BR-022.

## 2026-07-09 — Caixa/Financeiro formal adiado para depois

**Decisão:** A V1 de Vendas registra pagamento simples, sem caixa formal (abertura/fechamento, sangria, suprimento).
**Motivo:** Evita que o módulo mais prioritário do produto (Vendas) dependa de construir o Financeiro
completo primeiro.
**Impacto:** Blocos "Financeiro" e "Caixa" ficam `TODO` em `docs/company/OPERATION_SYSTEM.md`, por decisão
explícita — não por lacuna de documentação. Financeiro/Caixa viram Épico próprio.
**Fonte:** `docs/product/features/VENDAS.md` — "Decisões já tomadas".

## 2026-07-10 — Adotar a marca Fluxoly

**Decisão:** O produto passa a se chamar Fluxoly (negócio) / Fluxoly Platform (documentação técnica);
repositório e infraestrutura mantêm o nome legado por ora.
**Motivo:** Marcar a transição de "sistema de assistência técnica" para plataforma SaaS verticalizada
para lojas de dispositivos móveis premium.
**Impacto:** Toda a documentação (rename aplicado); `README.md`, `CLAUDE.md`; não afeta código, domínio de
produção nem módulos `irflow_*.py` nesta etapa.
**Fonte:** `docs/company/BRAND_IDENTITY.md` (V1.0, seção 9 — cronograma de transição).

## 2026-07-10 — Reorganizar `docs/` por audiência

**Decisão:** `docs/` passa a ter quatro pastas — `company/`, `product/`, `engineering/`, `operations/` —
por critério de audiência, não mais lista plana.
**Motivo:** Evitar que a lista de ~19 arquivos continue crescendo sem organização conforme novos domínios
de negócio trouxessem seus próprios documentos.
**Impacto:** Todos os links internos da documentação; `CLAUDE.md` seção "Estrutura de Documentos".
**Fonte:** `docs/engineering/adr/ADR-006.md` (esta é uma decisão com componente arquitetural — ver o ADR
para alternativas avaliadas; aqui registrado pelo impacto executivo).

## 2026-07-10 — Persona reestruturada: Cliente (compra) vs Personas Operacionais (usam)

**Decisão:** Substituída a ideia de uma única "Persona Secundária" por um grupo "Personas Operacionais"
(Vendedor, Técnico, Financeiro, Estoque, Administrador), distinto do Cliente (Dono da Loja) que compra o sistema.
**Motivo:** Comum em produtos SaaS B2B — quem compra e quem usa no dia a dia são pessoas diferentes, com
necessidades diferentes; tratar como uma persona só escondia isso.
**Impacto:** `docs/company/PRODUCT_REQUIREMENTS.md`; abre caminho para o princípio de interface por perfil (abaixo).
**Fonte:** `docs/company/PRODUCT_REQUIREMENTS.md` seção "Personas Operacionais".

## 2026-07-10 — Interface por perfil como princípio oficial de UX

**Decisão:** "Cada profissional deve enxergar apenas o que precisa para executar seu trabalho com máxima
eficiência" — telas diferentes por perfil (Vendedor, Técnico, Financeiro, Estoque, Administrador), não uma
tela única para todos com campos desabilitados por permissão.
**Motivo:** Reduz curva de aprendizado; é um diferencial competitivo já identificado (interfaces
especializadas por função, não ERP genérico).
**Impacto:** Frontend, UX, permissões, roadmap de qualquer domínio novo com perfil próprio (Financeiro, Estoque).
**Fonte:** `docs/company/VISION.md` (Valores); `docs/engineering/ENGINEERING_GUIDE.md` seção 4.0.

## 2026-07-10 — Retomar o Sprint 2 técnico antes de continuar a frente de produto

**Decisão:** Pausar a criação de novos documentos de produto/marca e fechar o Sprint 2 (CI/CD com GitHub
Actions, cobertura de testes para 40%, merge da branch `test/sprint-2-4-regras-negocio-os`) antes de
continuar.
**Motivo:** O Sprint 2 técnico ficou parado por toda a extensão da frente de documentação de
produto/marca — CI/CD ausente e cobertura abaixo da meta são dívida que cresce silenciosamente se não for
tratada conscientemente. Decisão explícita, não inercial.
**Impacto:** Próximo trabalho é engenharia (CI, testes), não documentação; `docs/operations/PROJECT_STATUS.md`
e `docs/operations/ROADMAP.md` voltam a ser a referência ativa.
**Fonte:** Decisão do Product Owner nesta conversa, 2026-07-10.

---

## 2026-07-20 — Catálogo comercial (`produtos`) é domínio novo, não extensão de Estoque

**Decisão:** o catálogo de itens à venda (iPhone, Apple Watch, AirPods, Acessório) vira uma tabela e um
domínio (`produtos`) inteiramente separados de `estoque` (peças de reparo) — não uma extensão dele.
**Motivo:** investigação antes de implementar (2 agentes de pesquisa, docs + código real) confirmou que
`estoque.tipo`/`qualidade` são listas fechadas hardcoded para vocabulário de peça de reparo (`Tela`/
`Bateria`/...) com coerção silenciosa para um valor default, e que o frontend (`Stock.jsx`) é inteiramente
rotulado "peças" — sem preço de venda, margem ou condição. Estender `estoque` misturaria dois modelos
mentais diferentes na mesma tabela/tela em uso real hoje.
**Impacto:** `docs/engineering/DATABASE.md` (tabela `produtos`), `docs/engineering/DOMAIN_MODEL.md` seção
1.14, `docs/product/BUSINESS_RULES.md` BR-027 a BR-029. `docs/product/features/VENDAS.md` precisa ser
revisado no Sprint Comercial 0.2 — hoje aponta `vendas.estoque_unidade_id` para `estoque_unidades`, que
não serve mais para produto comercial.
**Fonte:** conversa entre usuário (CTO) e Claude, 2026-07-20 — `docs/operations/SPRINTS/SPRINT_COMERCIAL_0.1.md`.

## 2026-07-22 — Numeração de OS do MercadoPhone: manter para o cliente atual, isolada por empresa no futuro

**Decisão:** manter `getOrderDisplayNumber` exibindo o número externo do MercadoPhone
(`id_externo_integracao`) para OS de `origem_integracao === "mercado_phone"`, como corrigido no Hotfix
H-003 (KI-021) — isso reflete como o cliente atual já opera na prática. Para os próximos clientes
(pós-multiempresa), a numeração de OS não deve depender de nenhuma integração externa: cada empresa terá
sua própria sequência independente, começando em 1.
**Motivo:** o cliente atual já usa o MercadoPhone como fonte de numeração no dia a dia — mudar isso agora
quebraria a operação real. Mas isso é específico desse cliente, não uma regra geral do produto; a Fluxoly
não pode depender de uma integração de terceiro para numerar OS de clientes que não usam o MercadoPhone.
**Impacto:** requisito novo para ADR-005 (Estratégia de Multiempresa, ainda `PROPOSTA`) — qualquer que
seja a opção de isolamento escolhida (banco por empresa / `empresa_id` / schema por empresa), a numeração
de OS por empresa precisa ser uma sequência própria (ex.: `numero_os` com contador por `empresa_id`, não
o `id INTEGER PRIMARY KEY AUTOINCREMENT` global nem um número de integração externa). Não implementado
agora — só registrado como requisito para quando ADR-005 for decidida.
**Fonte:** conversa entre usuário (CTO) e Claude, 2026-07-22, no acompanhamento do Hotfix H-003.

## 2026-07-25 — Adoção das 6 Fases estratégicas; Financeiro básico entra na Release 1.0

**Decisão:** adotado um horizonte de 6 Fases (0–5: Estabilização, Release 1.0, Multiempresa,
Escalabilidade, Automação, Inteligência) como a camada de propósito de negócio acima do versionamento
técnico já existente (0.8/0.9/1.0/2.0). Resolvida a pendência registrada em 2026-07-21: Financeiro
básico (caixa, contas, despesas, receitas) entra na Fase 1 / versão 1.0, não fica adiado para a 2.0.
**Motivo:** mudança de foco proposta pelo usuário (CTO) — de "próxima sprint" para "o que falta para o
primeiro cliente pagante não cancelar no primeiro mês". Financeiro básico é parte do critério "cliente
opera a empresa inteira sem depender de planilha paralela" que já justificava a Release 1.0.
**Impacto:** `docs/company/RELEASE_STRATEGY.md` (nova seção "As 6 Fases estratégicas", resolve a
pendência de Financeiro); `docs/operations/ROADMAP.md` recebeu aviso de desatualização/reconciliação de
terminologia (sua numeração "Fase 1-4" é um eixo diferente, mais estreito, não deve ser confundida com
as 6 Fases). Também registrada, não resolvida: tensão entre a ordem de Fase 2 (Multiempresa) e Fase 3
(migração para Postgres) — os incidentes INC-001/INC-002 desta sprint técnica nasceram de limitações do
SQLite com múltiplos processos, e Multiempresa aumentaria esse tipo de escrita concorrente antes da
migração planejada para depois.
**Fonte:** conversa entre usuário (CTO) e Claude, 2026-07-25 — `docs/company/RELEASE_STRATEGY.md` seção
"As 6 Fases estratégicas".

## 2026-08-05 — Multiempresa adiada para depois de Automação e Inteligência; ideias de stack SaaS registradas como não-decisões

**Decisão:** dentro das 6 Fases estratégicas, Multiempresa passa de Fase 3 para Fase 5 — depois de
Automação (Fase 3) e Inteligência (Fase 4), não mais logo após a Infraestrutura SaaS. Também decidido:
uma proposta externa de evolução do Fluxoly para SaaS (Next.js, BetterAuth, Supabase, Redis, Resend,
Firebase) **não** vira ADR agora — nenhuma dessas decisões precisa ser tomada hoje. Registradas como
avaliação de longo prazo em `docs/engineering/FUTURE_TECH_EVALUATIONS.md`, explicitamente não-vinculante.
**Motivo:** Automação e Inteligência entregam valor direto aos clientes já existentes sem o custo de
meses construindo isolamento multiempresa, planos, licenças e billing — investimento que só se paga com
múltiplos clientes pagantes. Diferente da posição da Fase 2 (bloqueio técnico real, escrita concorrente em
SQLite — ver INC-001/INC-002), esta reordenação é priorização de negócio, não dependência de engenharia:
a única dependência técnica de Multiempresa continua sendo a Fase 2 pronta e a decisão pendente em
`ADR-005.md`. Sobre a proposta de stack: ADR nasce quando existe decisão concreta a registrar, não uma
possibilidade futura (princípio já usado em `ADR-010.md`) — tratar Next.js/BetterAuth/Supabase como
decisões agora contradiria o próprio ADR-001 (que já rejeitou Next.js) e o estado real do repositório
(sem ADR-012, sem `frontend-next/`, verificado nesta sessão antes de responder à proposta).
**Impacto:** `docs/company/RELEASE_STRATEGY.md` (ordem das Fases 3-5 revisada, nova subseção "Decisão:
Multiempresa adiada..."); novo documento `docs/engineering/FUTURE_TECH_EVALUATIONS.md` (não é ADR,
não é roadmap ativo); `docs/README.md` recebeu entrada de índice para o novo documento. Nenhuma mudança
de código, schema ou stack nesta sessão — só planejamento e documentação.
**Fonte:** conversa entre usuário (CTO) e Claude, 2026-08-05 — proposta externa de evolução SaaS revisada
contra o estado real do repositório antes de qualquer registro.

## 2026-07-25 — Correção same-day: Infraestrutura SaaS antes de Multiempresa; Financeiro dividido em mínimo/avançado

**Decisão:** revisão da entrada anterior (mesmo dia), antes de consolidar como estratégia oficial. Duas
mudanças: (1) Fase 2 e Fase 3 invertidas — **Infraestrutura SaaS** (PostgreSQL, Redis, workers, filas,
observabilidade, backup, CI/CD) passa a vir **antes** de **Multiempresa**, não depois; (2) Financeiro na
Release 1.0 deixa de ser "básico" genérico e passa a ser explicitamente **mínimo** (caixa, entradas,
saídas, contas a pagar/receber, fluxo de caixa simples) — o restante (DRE, centros de custo, conciliação
bancária, múltiplas contas, indicadores, projeções) vai para "Financeiro avançado" na versão 2.x.
**Motivo:** a tensão registrada como "não resolvida" na entrada anterior foi resolvida no mesmo dia —
os incidentes INC-001 (`database is locked`) e INC-002 (OS duplicada) nasceram de limitações do SQLite
com múltiplos processos escrevendo concorrentemente. Com poucos clientes hoje (1-4), não compensa
investir meses em Multiempresa sobre uma base ainda em SQLite: isolamento por `empresa_id` aumentaria
exatamente esse tipo de escrita concorrente antes da migração que eliminaria o problema pela raiz.
Financeiro dividido para permitir lançar a 1.0 mais cedo sem perder qualidade no essencial.
**Impacto:** `docs/company/RELEASE_STRATEGY.md` — seção "As 6 Fases estratégicas" reescrita com a nova
ordem e o Financeiro dividido; `docs/engineering/adr/ADR-005.md` (Multiempresa) passa a depender também
da Fase 2 (Infraestrutura) estar pronta, não só da decisão de negócio já pendente lá.
**Fonte:** conversa entre usuário (CTO) e Claude, 2026-07-25 — `docs/company/RELEASE_STRATEGY.md` seções
"Decisão: Infraestrutura SaaS antes de Multiempresa" e "Decisão: Financeiro dividido em mínimo (1.0) e
avançado (2.x)".

## 2026-07-25 — Novo perfil `estoque`; OS e Estoque restritos por perfil na API

**Decisão:** triagem de um scan de segurança (Aikido) encontrou que as rotas de mutação de OS e Estoque
na API aceitavam qualquer perfil autenticado (achado já registrado em `docs/engineering/DATA_DICTIONARY.md`
desde 2026-07-10, nunca corrigido até agora). Decidido: mutação de OS exige `admin`/`tecnico`; mutação
de Estoque exige `admin`/`estoque` — perfil novo, criado nesta decisão (antes só existiam
`admin`/`tecnico`/`vendedor`). `vendedor` perdeu acesso de mutação a ambos os domínios.
**Motivo:** parte da Sprint Segurança 1.0 (resposta ao scan Aikido) — reduzir superfície de autorização
antes do primeiro cliente pagante (Release 1.0). A criação do perfil `estoque` também resolve uma
lacuna já registrada em `docs/company/PRODUCT_REQUIREMENTS.md` ("Estoque como perfil de usuário" — TODO
desde a escrita original das personas operacionais).
**Impacto:** `irflow_core.py` (`PERFIS_OPCOES`), `irflow_blueprints_api.py` (7 rotas de mutação de
OS/Estoque + validação de perfil em `criar_usuario`/`atualizar_usuario`), `irflow_blueprints_auth.py`
(mesma validação nas views legadas), `frontend/src/pages/Users.jsx` (novo perfil na tela de usuários).
`docs/product/BUSINESS_RULES.md` BR-030 (nova), BR-003 (corrigida — `ROUTE_PERMISSIONS` não cobre
`/api/*`). Persona operacional completa do perfil Estoque segue `TODO` em
`docs/company/PRODUCT_REQUIREMENTS.md` — esta decisão resolve a lacuna de segurança, não substitui a
pesquisa de produto.
**Fonte:** conversa entre usuário (CTO) e Claude, 2026-07-25 — `docs/security/SECURITY_AUDIT_2026-07.md`.

## 2026-08-20 — Liberdade criativa total para o redesign visual (Fase 3), incluindo a identidade de marca

**Decisão:** o CTO/Product Owner revogou o "PRINCÍPIO FUNDAMENTAL" definido na própria sessão de
brainstorming da Fase 3 ("não altere a identidade de marca já definida") e concedeu autoridade criativa
total para o redesign visual — incluindo reinventar `#FF0125`, o wordmark Onest e o ícone, não só a
composição em cima deles. Confirmado via pergunta direta: (1) a marca em si está aberta, não só a
composição; (2) o processo de engenharia (plano aprovado, branch, PR, CI, testes) permanece inalterado —
a liberdade é só sobre direção criativa; (3) o escopo é o produto interno inteiro (~24 telas
autenticadas), não a Landing Page pública.
**Motivo:** o CTO considerou o resultado da Fase 2 (consistência técnica) insuficiente e, mesmo depois de
um brainstorming detalhado que definiu uma direção com a marca fixa, decidiu remover essa restrição para
permitir uma transformação mais ousada.
**Impacto:** `docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` (seção 0.1, nova;
seção 13, revisada); `docs/company/BRAND_IDENTITY.md` deixa de ser autoridade travada para esta
iniciativa e precisará ser atualizado quando uma nova identidade concreta for produzida e aprovada.
Nenhum código escrito ainda — a Fase 3 continua exigindo um plano de implementação formal antes de
qualquer commit.
**Fonte:** conversa entre usuário (CTO) e Claude, 2026-08-20 —
`docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` seção 0.1.

## 2026-08-20 — Direção de identidade "Pulse" escolhida para o redesign visual (Fase 3)

**Decisão:** entre três direções concretas de identidade (cor + wordmark + ícone como sistema fechado)
exploradas num canvas visual (artifact "Fluxoly Identity Directions", Claude Design) — A "Ember" (evolução
refinada, mantém `#FF0125`/ícone-F/Onest), B "Pulse" (reinvenção: vermelho-sinal `#FF3D5A` + ciano de
fluxo ao vivo `#29E0C9`, ícone vira um traço de pulso/seta em vez de letra, wordmark em Space Grotesk) e C
"Atelier" (editorial: papel + serifada Instrument Serif, vermelho-tinta `#C81E3A`) — o CTO/Product Owner
escolheu **B — Pulse** como direção formal.
**Motivo:** direção mais "tech-forward" e diferenciada, e mais alinhada ao próprio nome Fluxoly (fluxo
como sinal vivo, não uma letra); avaliada como preferida clara depois de comparar as três lado a lado
(a direção C recebeu avaliação positiva, mas B foi escolhida sem ambiguidade).
**Impacto:** `docs/company/BRAND_IDENTITY.md` §10 reescrito (ícone, wordmark, paleta, histórico em 10.4);
`docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md` recebeu seção 0.2 e teve as linhas
de "vermelho" das seções 3/4 atualizadas para a nova cor. Onest **não** foi abandonada — continua como
fonte de UI/corpo; só o wordmark (logotipo) muda para Space Grotesk. Nenhum código mudou — `index.css`,
favicon e SVGs finais do ícone continuam pendentes da Fase 3.0/3.1.
**Fonte:** conversa entre usuário (CTO) e Claude, 2026-08-20 — canvas "Fluxoly Identity Directions"
(Claude Design); `docs/company/BRAND_IDENTITY.md` §10.4.

## Documentos relacionados

- `docs/engineering/ARCHITECTURE_DECISIONS.md` — decisões arquiteturais (ADR), complementar a este log
- `docs/product/features/VENDAS.md` — fonte da maioria das decisões de 2026-07-09
- `docs/company/BRAND_IDENTITY.md` — fonte das decisões de marca de 2026-07-10
