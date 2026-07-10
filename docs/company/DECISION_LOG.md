# DECISION_LOG.md — Histórico Executivo de Decisões

Este documento é diferente de um ADR. **ADR é arquitetural** — registra alternativas técnicas avaliadas
e a escolha entre elas (`docs/engineering/adr/`). **Decision Log é executivo** — registra decisões de
produto/negócio, o motivo e o impacto, em ordem cronológica, para que ninguém precise reconstruir "por
que decidimos isso" a partir de conversas antigas.

**Última revisão:** 2026-07-10

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

## Documentos relacionados

- `docs/engineering/ARCHITECTURE_DECISIONS.md` — decisões arquiteturais (ADR), complementar a este log
- `docs/product/features/VENDAS.md` — fonte da maioria das decisões de 2026-07-09
- `docs/company/BRAND_IDENTITY.md` — fonte das decisões de marca de 2026-07-10
