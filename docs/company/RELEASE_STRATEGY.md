# RELEASE_STRATEGY.md — Estratégia de Versionamento

**Status:** ✅ DECIDIDO pelo usuário (CTO/Product Owner) em 2026-07-21 — substitui integralmente a
proposta técnica anterior (2026-07-10), que usava um esquema de numeração diferente e incompatível.

**Última revisão:** 2026-07-21

---

## Por que este documento existe

Evita o problema mais comum de produto novo: tentar colocar tudo na primeira versão e atrasar o
lançamento indefinidamente. Responde **em qual versão** cada épico do `docs/product/PRODUCT_BACKLOG.md`
sai — diferente do backlog (que responde **o quê** e em que ordem de importância) e do
`docs/operations/ROADMAP.md` (que responde **quando**, em sprints de engenharia).

## Nota de reconciliação (2026-07-21)

A proposta de 2026-07-10 chamava de **"Fluxoly 1.0"** o estado que já estava em produção naquela época
(login, OS, estoque, lista de compras, tabela de preços, relatórios, backup — sem nenhum épico
comercial ainda). Isso criava um problema real: "1.0" ficaria associado, tanto interna quanto
comercialmente, a uma versão que **não entrega o objetivo comercial da Fluxoly** (vender aparelhos,
não só dar assistência). Encontrado ao formalizar o RC da migração `unidades_serializadas`
(2026-07-21) — dois documentos diferentes chamavam coisas diferentes de "1.0" ao mesmo tempo.

**Reconciliação:** o esquema abaixo substitui o de 2026-07-10 por completo. Tudo que já foi construído
até aqui (OS, Estoque, Segurança/Sprint 3, Clientes, Produtos, `unidades_serializadas`) deixa de ser
"a versão 1.0" e passa a ser a **fundação** sobre a qual a Fluxoly comercial é construída — versão
`0.x`, não `1.x`. "Fluxoly 1.0" fica reservado para o momento em que o produto realmente cumpre a
promessa comercial (`docs/company/BRAND_IDENTITY.md`) e pode ser vendido a clientes pagantes.

---

## Versionamento

### Fluxoly 0.8 — Foundation

O que já existe hoje (2026-07-21) ou está em RC: infraestrutura (CI/CD, testes, lint), segurança e
auditoria (rate limiting, sessão, `audit_log`, recuperação de senha — Sprint 3), Ordens de Serviço,
Estoque, Lista de Compras, Tabela de Preços, Relatórios, Backup, domínios **Clientes**, **Produtos** e
**Unidades Serializadas** (backend — `ADR-007`, migração validada em RC em 2026-07-21, telas ainda
pendentes). Não é uma meta futura — é o estado real, verificado, não uma intenção.

### Fluxoly 0.9 — Commercial Preview

Primeiro fluxo comercial de fato utilizável por um lojista: telas de **Produtos** e **Clientes**
(consumindo o backend já existente), tela de **Unidades Serializadas** (busca por IMEI, histórico,
status, localização — Sprint Comercial 1.3, depende da migração `unidades_serializadas` estar em
produção), e uma **Venda MVP** (épico **Vendas** do backlog, escopo mínimo — Sprint Comercial 2).
**Por que "Preview" e não "Release":** cobre o fluxo comercial ponta a ponta pela primeira vez, mas
ainda sem Garantias/Trocas/RMA formalizados sobre `unidades_serializadas` (ver ADR-007, "Escopo desta
migração") nem Financeiro.

### Fluxoly 1.0 — Commercial Release

Primeira versão oficialmente comercial da Fluxoly, pronta para os primeiros clientes pagantes. Fecha o
que a 0.9 deixou em aberto no fluxo de venda (Garantias/Trocas sobre uma unidade vendida, conforme o
ciclo de vida completo já desenhado no ADR-007) e o mínimo de Financeiro/Caixa necessário para o
lojista operar sem depender de planilha paralela. Escopo exato (que parte de Financeiro/Caixa entra
aqui vs. na 2.0) **ainda não decidido** — ver "Em aberto" abaixo.

### Fluxoly 2.0 — Escala

Épicos do backlog: **Multiempresa** (P3, bloqueado por decisão pendente em `ADR-005.md`), **CRM**,
**WhatsApp** (pilar "Relacionamento", depende de Clientes maduro), **Financeiro avançado**, e itens sem
backlog/spec/ADR hoje (API pública, Marketplace, app mobile nativo) — registrados só para não perder o
fio, não como compromisso.

---

## Em aberto — decidir antes de fechar o escopo de cada versão

- **Financeiro/Caixa:** a proposta de 2026-07-10 colocava o básico logo após Vendas (era "1.2") e o
  resto ficava para depois. Nesta reconciliação, ainda não está decidido se o Financeiro básico entra
  na 1.0 (Commercial Release) ou fica inteiramente na 2.0 junto do "Financeiro avançado" — precisa de
  uma decisão explícita do CTO/PO antes de fechar o escopo da 1.0.
- Critério de "pronto para lançar" por versão — hoje não existe um Definition of Done comercial
  (diferente do Definition of Done técnico já existente por sprint em `docs/operations/ROADMAP.md`).
- Se alguma versão deve ser dividida (ex.: Venda MVP sair sozinha na 0.9 antes de Unidades Serializadas
  ter tela completa).

---

## Documentos relacionados

- `docs/product/PRODUCT_BACKLOG.md` — fonte dos épicos e prioridades usados nesta proposta (nota:
  revisado em 2026-07-20, anterior a Produtos/Clientes ganharem tela e à migração `unidades_serializadas`
  — vale conferir contra `docs/operations/PROJECT_STATUS.md` antes de assumir o status de cada épico)
- `docs/company/DECISION_LOG.md` — decisão de desacoplar Vendas de Caixa/Financeiro (2026-07-09)
- `docs/operations/ROADMAP.md` — roadmap de engenharia (sprints técnicas), eixo separado
- `docs/engineering/adr/ADR-005.md` — decisão pendente que bloqueia Multiempresa (2.0)
- `docs/engineering/adr/ADR-007.md` — ciclo de vida de `unidades_serializadas` que fundamenta o escopo
  de Garantias/Trocas citado na versão 1.0 acima
