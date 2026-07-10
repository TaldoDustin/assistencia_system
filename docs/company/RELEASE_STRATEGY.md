# RELEASE_STRATEGY.md — Estratégia de Versionamento

**Status:** Proposta técnica de reconciliação — decisão final de versionamento é do Product Owner, mesmo
padrão de `docs/engineering/adr/ADR-005.md`. Não é uma versão decidida, é um ponto de partida para decidir.

**Última revisão:** 2026-07-10

---

## Por que este documento existe

Evita o problema mais comum de produto novo: tentar colocar tudo na primeira versão e atrasar o
lançamento indefinidamente. Responde **em qual versão** cada épico do `docs/product/PRODUCT_BACKLOG.md`
sai — diferente do backlog (que responde **o quê** e em que ordem de importância) e do
`docs/operations/ROADMAP.md` (que responde **quando**, em sprints de engenharia).

## Nota de reconciliação

A primeira proposta de versionamento desta conversa (2026-07 — antes de qualquer análise de código ou
decisão registrada) agrupava "Vendas, Caixa, Financeiro" numa única v1.1. Isso não reflete mais a
prioridade real: `docs/company/DECISION_LOG.md` (2026-07-09) registra a decisão explícita de que Vendas
não depende de Caixa/Financeiro formal para sair — são desacoplados de propósito. A proposta abaixo
reflete essa decisão e o restante do trabalho feito desde então (`docs/product/PRODUCT_BACKLOG.md`), não
o agrupamento original.

---

## Proposta de Versionamento

### Fluxoly 1.0 — já em produção

O que já existe e está rodando hoje: Login básico, Ordens de Serviço, Estoque, Lista de Compras, Tabela
de Preços, Relatórios, Backup, Dashboard básico (KPIs de faturamento/lucro). Não é uma meta futura — é o
estado atual documentado em `docs/operations/PROJECT_STATUS.md`.

### Fluxoly 1.1 — Segurança Comercial + Base de Vendas (proposta)

Épicos do backlog: **Vendas** (P0), **Clientes** (P0), **IMEI Individual** (P0) — mais o eixo de
"Segurança Comercial" já discutido nesta conversa antes do foco em marca/produto (login robusto,
recuperação de senha, rate limiting, auditoria, sessões — sobreposto com a Sprint 3 já planejada em
`docs/operations/ROADMAP.md`).
**Por que junto:** os três P0 do backlog são interdependentes — Vendas não funciona sem Clientes nem sem
IMEI rastreável. Segurança comercial é pré-requisito de vender uma assinatura paga, independente do que
mais entrar na versão.

### Fluxoly 1.2 — Financeiro e Caixa (proposta)

Épicos do backlog: **Financeiro** (P1), **Caixa** (P1), **Dashboard Executivo** completo (P1).
**Por que depois:** decisão já registrada de que Vendas não espera o Financeiro formal existir
(`DECISION_LOG.md`, 2026-07-09) — mas uma vez que Vendas está rodando, o dado de caixa/fluxo financeiro
passa a ser urgente para o mesmo cliente que já está usando o resto.

### Fluxoly 1.3 — Relacionamento (proposta)

Épicos do backlog: **WhatsApp** (P2), **CRM** (P2).
**Por que depois:** ambos dependem de Clientes (v1.1) existir como entidade madura, com histórico
suficiente para um CRM fazer sentido.

### Fluxoly 2.0 — Escala (proposta, mais especulativa)

Épicos do backlog: **Multiempresa** (P3, bloqueado por decisão pendente em `ADR-005.md`). Itens
mencionados na visão original desta conversa mas **sem backlog, sem spec, sem ADR hoje** — API pública,
Marketplace, Aplicativo mobile nativo. Registrados aqui só para não perder o fio, não como compromisso.

---

## O que fica decidido só quando o Product Owner confirmar

- Os nomes de versão acima (`TODO` — pode ser semver real, pode ser outro esquema)
- Se alguma versão deve ser dividida (ex.: Vendas sair sozinha antes de Clientes/IMEI estarem 100% prontos)
- Critério de "pronto para lançar" por versão — hoje não existe um Definition of Done comercial (diferente
  do Definition of Done técnico já existente por sprint em `docs/operations/ROADMAP.md`)

---

## Documentos relacionados

- `docs/product/PRODUCT_BACKLOG.md` — fonte dos épicos e prioridades usados nesta proposta
- `docs/company/DECISION_LOG.md` — decisão de desacoplar Vendas de Caixa/Financeiro, citada acima
- `docs/operations/ROADMAP.md` — roadmap de engenharia (sprints técnicas), eixo separado
- `docs/engineering/adr/ADR-005.md` — decisão pendente que bloqueia a versão 2.0 (Multiempresa)
