# PRODUCT_BACKLOG.md — Fila de Evolução do Produto

Diferente de `docs/operations/ROADMAP.md` (que responde **quando** — fases e sprints de engenharia) e de
`docs/company/RELEASE_STRATEGY.md` (que responde **em qual versão** cada coisa sai), este documento
responde **o quê** construir a seguir, em ordem de prioridade de negócio.

**Última revisão:** 2026-07-10
**Fonte:** priorização de negócio — input direto do Product Owner. Coluna "Status" verificada contra o
estado real do código/documentação (`docs/engineering/DOMAIN_MODEL.md`, `docs/product/features/`) antes
de publicar, não copiada às cegas do exemplo dado.

---

## Fila Priorizada

| Prioridade | Épico | Status | Valor de Negócio | Fonte / Nota |
|---|---|---|---|---|
| P0 | Vendas | Especificação (`docs/product/features/VENDAS.md`, atualizada em 2026-07-11 com modelo de dados e wireframes) | Muito Alto | Prioridade #1 do produto — ver `VENDAS.md` "Por que existe" |
| P0 | Clientes (entidade própria) | Implementado (backend) — `irflow_clientes_*.py`, 2026-07-11 (Sprint P0.1) | Muito Alto | Pré-requisito estrutural de Vendas, entregue como fundação antes do módulo em si (`docs/engineering/DOMAIN_MODEL.md` seção 1.12). Sem tela — cadastro/busca só via API por enquanto. Decisões de negócio pendentes (deduplicação) seguem `TODO`, ver `CLIENTES.md` |
| P0 | IMEI Individual | Especificação (`docs/product/features/IMEI.md`, 2026-07-11) | Muito Alto | Gap de schema já registrado — `docs/company/BRAND_IDENTITY.md` seção 2, `docs/engineering/DOMAIN_MODEL.md` seção 1.4; pré-requisito de Vendas (reserva de IMEI, BR-017). Spec ainda sem validação direta do Product Owner — ver "Decisões de negócio pendentes" em `IMEI.md` |
| P1 | Financeiro | Não iniciado | Alto | Deferido deliberadamente do V1 de Vendas (`docs/company/DECISION_LOG.md`, 2026-07-09) — não é lacuna, é sequenciamento |
| P1 | Caixa | Não iniciado | Alto | Mesma decisão de adiamento do Financeiro |
| P1 | Dashboard Executivo | Parcial | Alto | **Nota de verificação:** já existe um dashboard básico (`frontend/src/pages/Dashboard.jsx`, KPIs de faturamento/lucro/serviços/técnico) — o que falta é a versão executiva completa descrita na visão original (ticket médio, OS atrasadas, top vendedores, margem) |
| P2 | WhatsApp | Não iniciado | Médio | Notificação automática de status de OS/venda — pilar "Relacionamento", `BRAND_IDENTITY.md` seção 2 |
| P2 | CRM | Não iniciado | Médio | Depende de Clientes (P0) existir como entidade primeiro |
| P3 | Multiempresa | ADR pendente | Estratégico | `docs/engineering/adr/ADR-005.md` — alternativas técnicas prontas, decisão de negócio ainda não tomada |

---

## Como usar este documento

- **Prioridade (P0–P3)** é ordem de importância de negócio, não ordem de implementação necessariamente —
  dependências técnicas podem exigir sequenciar diferente (ex.: Clientes e IMEI são P0 mas são
  pré-requisitos de Vendas, também P0; não faz sentido implementar Vendas sem eles).
- **Status** reflete o estado real verificado, não a intenção. Atualizar aqui sempre que um épico mudar
  de fase — este documento fica desatualizado rápido se não for mantido junto com
  `docs/operations/PROJECT_STATUS.md`.
- Ao mover um épico de "Não iniciado" para "Especificação", criar o spec em
  `docs/product/features/<EPICO>.md` seguindo o formato de `VENDAS.md`.
- Toda decisão de priorização relevante (por que P0 e não P1) deveria ter uma entrada correspondente em
  `docs/company/DECISION_LOG.md` quando a razão não for óbvia.

---

## Documentos relacionados

- `docs/company/RELEASE_STRATEGY.md` — em qual versão cada épico deste backlog é planejado para sair
- `docs/operations/ROADMAP.md` — roadmap de engenharia (fases/sprints técnicas, eixo separado)
- `docs/company/DECISION_LOG.md` — decisões que justificam prioridade/sequenciamento acima
- `docs/product/features/VENDAS.md`, `CLIENTES.md`, `IMEI.md` — os três épicos P0 com spec hoje (2026-07-11)
- `docs/engineering/adr/ADR-005.md` — decisão pendente que bloqueia Multiempresa
