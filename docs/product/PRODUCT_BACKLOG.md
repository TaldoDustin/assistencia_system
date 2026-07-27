# PRODUCT_BACKLOG.md — Fila de Evolução do Produto

Diferente de `docs/operations/ROADMAP.md` (que responde **quando** — fases e sprints de engenharia) e de
`docs/company/RELEASE_STRATEGY.md` (que responde **em qual versão** cada coisa sai), este documento
responde **o quê** construir a seguir, em ordem de prioridade de negócio.

**Última revisão:** 2026-07-27
**Fonte:** priorização de negócio — input direto do Product Owner. Coluna "Status" verificada contra o
estado real do código/documentação (`docs/engineering/DOMAIN_MODEL.md`, `docs/product/features/`) antes
de publicar, não copiada às cegas do exemplo dado.

---

## Fila Priorizada

Coluna **Item do Release 1.0** referencia `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` (adicionada em
2026-07-25) — todo épico que avança a Release 1.0 deveria apontar para o item de checklist que ele
ajuda a marcar.

| Prioridade | Épico | Status | Valor de Negócio | Item do Release 1.0 | Fonte / Nota |
|---|---|---|---|---|---|
| P0 | Vendas | MVP implementado (backend) — `fluxoly_vendas_*.py`, 2026-07-27 (venda de 1 aparelho por vez, sem desconto/comissão/garantia/troca). Fluxo completo segue em Especificação (`docs/product/features/VENDAS.md`) | Muito Alto | Comercial completo | Prioridade #1 do produto — ver `VENDAS.md` "Por que existe". Fluxo completo condicionado a decisões do Product Owner ainda pendentes (timeout de reserva, % comissão, limite de desconto, prazo de garantia, critérios de avaliação de usado) |
| P0 | Clientes (entidade própria) | Implementado (backend) — `irflow_clientes_*.py`, 2026-07-11 (Sprint P0.1) | Muito Alto | Comercial completo | Pré-requisito estrutural de Vendas, entregue como fundação antes do módulo em si (`docs/engineering/DOMAIN_MODEL.md` seção 1.12). Sem tela — cadastro/busca só via API por enquanto. Decisões de negócio pendentes (deduplicação) seguem `TODO`, ver `CLIENTES.md` |
| P0 | IMEI Individual | Implementado (backend) — `irflow_unidades_serializadas_*.py`, 2026-07-11 (Sprint P0.1), evoluído de `estoque_unidades` na migração ADR-007 (2026-07-21) | Muito Alto | Comercial completo | Gap de schema resolvido — `docs/engineering/DOMAIN_MODEL.md` seção 1.13. Sem tela; reserva/venda (`reservado`/`vendido`) segue não implementada, depende de Vendas existir. Decisões de negócio pendentes (validação de formato, AirPods/série) seguem `TODO`, ver `IMEI.md` |
| P0 | Produtos (catálogo comercial) | Implementado (backend) — `irflow_produtos_*.py`, 2026-07-20 (Sprint Comercial 0.1) | Muito Alto | Comercial completo | Lacuna real identificada só agora: nenhum documento desenhava um catálogo comercial (categoria/marca/cor/capacidade/condição/preço) antes desta sprint — `estoque` é peça de reparo, não produto de venda. Domínio novo, separado de Estoque. Sem tela; rastreamento por unidade/IMEI de produtos fica para o Sprint Comercial 0.2, que também vai exigir revisar `vendas.estoque_unidade_id` em `VENDAS.md` |
| P1 | Financeiro (mínimo) | Não iniciado | Alto | Financeiro mínimo | Escopo restrito a caixa/entradas/saídas/contas a pagar-receber (`RELEASE_STRATEGY.md`, 2026-07-25) — "Financeiro avançado" (DRE, conciliação, indicadores) fica fora da 1.0 |
| P1 | Caixa | Não iniciado | Alto | Financeiro mínimo | Mesmo item de checklist que Financeiro mínimo — são o mesmo trabalho, não dois épicos separados |
| P1 | Dashboard Executivo | Parcial | Alto | Dashboard Executivo | **Nota de verificação:** já existe um dashboard básico (`frontend/src/pages/Dashboard.jsx`, KPIs de faturamento/lucro/serviços/técnico) — o que falta é a versão executiva completa descrita na visão original (ticket médio, OS atrasadas, top vendedores, margem) |
| P2 | WhatsApp | Não iniciado | Médio | Fase 4 (Automação) — fora do escopo da 1.0 | Notificação automática de status de OS/venda — pilar "Relacionamento", `BRAND_IDENTITY.md` seção 2 |
| P2 | CRM | Não iniciado | Médio | Fase 4 (Automação) — fora do escopo da 1.0 | Depende de Clientes (P0) existir como entidade primeiro |
| P3 | Multiempresa | ADR pendente | Estratégico | Fase 3 (Multiempresa) — fora do escopo da 1.0, depende da Fase 2 (Infraestrutura SaaS) | `docs/engineering/adr/ADR-005.md` — alternativas técnicas prontas, decisão de negócio ainda não tomada |

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
- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — checklist de certificação da Release 1.0; cada épico
  P0/P1 acima referencia o item que ajuda a marcar
- `docs/operations/ROADMAP.md` — roadmap de engenharia (fases/sprints técnicas, eixo separado, hoje
  desatualizado — ver aviso no topo daquele documento)
- `docs/company/DECISION_LOG.md` — decisões que justificam prioridade/sequenciamento acima
- `docs/product/features/VENDAS.md`, `CLIENTES.md`, `IMEI.md` — os três épicos P0 com spec hoje (2026-07-11)
- `docs/engineering/adr/ADR-005.md` — decisão pendente que bloqueia Multiempresa
