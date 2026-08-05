# RELEASE_STRATEGY.md — Estratégia de Versionamento

**Status:** ✅ DECIDIDO pelo usuário (CTO/Product Owner) em 2026-07-21 — substitui integralmente a
proposta técnica anterior (2026-07-10), que usava um esquema de numeração diferente e incompatível.
Ampliado em 2026-07-25 com as 6 Fases estratégicas (visão de longo prazo, além da 2.0). Ordem das Fases
3-5 revisada em 2026-08-05 (Multiempresa passa para o final — ver "Decisão: Multiempresa adiada para
depois de Automação e Inteligência" abaixo).

**Última revisão:** 2026-08-05

---

## As 6 Fases estratégicas (visão de longo prazo)

Proposta do usuário (CTO) em 2026-07-25, **corrigida no mesmo dia** após revisão (ver
`docs/company/DECISION_LOG.md` para as duas entradas — a proposta original e a correção — e o motivo de
cada mudança). Reorganiza o horizonte completo da Fluxoly — desde a estabilização atual até inteligência
de negócio — em 6 fases, cada uma com um objetivo de negócio único. **Diferente do versionamento abaixo**
(que é sobre *o quê sai em cada release*), as Fases respondem *por que* essa sequência existe — é a
camada de propósito acima das versões.

```
Fase 0 — Estabilização da Plataforma     (agora)
Fase 1 — Release 1.0 (primeiro cliente)
Fase 2 — Infraestrutura SaaS
Fase 3 — Automação
Fase 4 — Inteligência
Fase 5 — Multiempresa
```

| Fase | Objetivo de negócio | Mapeamento no versionamento abaixo |
|---|---|---|
| **0 — Estabilização** | "Nenhum bug crítico conhecido." Bugs (INC-001, INC-002 — ver `docs/operations/INCIDENTS/`), auditoria (permissões, SQL injection, uploads, autenticação), performance (índices, queries, paginação, cache), observabilidade (logs, métricas, monitorização) | Não é uma versão — é o gate contínuo antes de qualquer release sair. Trabalho já em andamento nesta sprint técnica |
| **1 — Release 1.0** | "O cliente consegue operar a empresa inteira usando somente a Fluxoly." Assistência (OS, peças, estoque, garantias, histórico), Comercial (produtos, vendas, clientes, unidades serializadas, IMEI), **Financeiro mínimo** (caixa, entradas, saídas, contas a pagar/receber, fluxo de caixa simples), Dashboards, Relatórios, Configurações | Cobre as versões **0.9 (Commercial Preview)** e **1.0 (Commercial Release)** abaixo — a Fase 1 é o destino, 0.9/1.0 são os incrementos até lá |
| **2 — Infraestrutura SaaS** | "Elimina a classe de problema de concorrência antes de multiplicá-la." PostgreSQL (fim do SQLite), Redis (cache/sessões/locks/rate limit), separação de workers (API/Worker/Scheduler), filas (Mercado Phone/e-mail/WhatsApp/backups), observabilidade (Sentry/Grafana/Prometheus), backup automático versionado, CI/CD completo | Não existia como fase própria antes — estava implícita dentro da "2.0 Escala". **Adiantada para antes de Multiempresa** (decisão de 2026-07-25, corrigindo a ordem original) |
| **3 — Automação** | "Eliminar trabalho manual." WhatsApp, e-mail (garantias/orçamentos/cobranças), integração Mercado Livre, Nota Fiscal, APIs | Era a parte "CRM/WhatsApp" da versão **2.0 (Escala)** abaixo. **Adiantada para antes de Multiempresa** (decisão de 2026-08-05 — ver "Decisão: Multiempresa adiada" abaixo) |
| **4 — Inteligência** | IA respondendo perguntas de negócio (lucro, top vendedores, atraso por técnico, sugestão de compra, retenção), alertas e previsões | Pilar "Inteligência" já existe em `BRAND_IDENTITY.md` seção 2. **Adiantada para antes de Multiempresa** (decisão de 2026-08-05) |
| **5 — Multiempresa** | "Primeiros clientes reais — agora sobre infraestrutura pronta e produto validado por Automação/IA." Isolamento por `empresa_id`, planos (Starter/Professional/Enterprise), licenças, assinatura, billing, trial, cancelamento | Era a parte "Multiempresa" da versão **2.0 (Escala)** abaixo. **Bloqueada por decisão pendente em `ADR-005.md`** (alternativas técnicas já avaliadas, decisão de negócio ainda não tomada), depende da Fase 2 estar pronta, e agora deliberadamente feita por último (2026-08-05) |

### Decisão: Infraestrutura SaaS antes de Multiempresa

A proposta original de 2026-07-25 tinha Multiempresa como Fase 2 e Infraestrutura (Postgres/Redis) como
Fase 3. **Invertida no mesmo dia**, por decisão do usuário (CTO): os dois incidentes fechados na sprint
técnica de estabilização (INC-001 `database is locked`, INC-002 OS duplicada — ver
`docs/operations/INCIDENTS/`) nasceram de limitações do SQLite com múltiplos processos escrevendo
concorrentemente, e exigiram um lock manual porque não existe coordenação nativa entre processos no
SQLite. Com poucos clientes hoje (1–4), não compensa investir meses em Multiempresa sobre uma base ainda
em SQLite — construir isolamento por `empresa_id` aumentaria exatamente esse tipo de escrita concorrente
antes da migração que eliminaria o problema pela raiz. Infraestrutura primeiro: elimina definitivamente
essa classe de problema, prepara o sistema para crescer, e deixa o desenvolvimento de Multiempresa mais
limpo quando chegar sua vez.

### Decisão: Multiempresa adiada para depois de Automação e Inteligência (2026-08-05)

A ordem de 2026-07-25 tinha Multiempresa como Fase 3, logo após a Infraestrutura SaaS — antes de
Automação e Inteligência. **Revisada em 2026-08-05**, por decisão do usuário (CTO/Product Owner), ao
analisar uma proposta externa de evolução do Fluxoly para SaaS: Automação (WhatsApp, e-mail, integrações)
e Inteligência (IA respondendo perguntas de negócio) entregam valor direto e mensurável aos clientes que
a Fluxoly já tem hoje, sem exigir o investimento de meses em isolamento multiempresa, planos, licenças e
billing — trabalho que só se paga quando já existem múltiplos clientes pagantes para atender. Adiar
Multiempresa para depois de validar o produto com Automação/Inteligência reduz o risco de construir
infraestrutura de escala (billing, planos, trial) antes de o produto ter demonstrado esse valor.

Diferente da Fase 2 (bloqueio técnico real — escrita concorrente em SQLite), a posição de Multiempresa
depois de Automação/Inteligência é uma **decisão de priorização de negócio**, não uma dependência técnica:
nada em Automação ou Inteligência é pré-requisito de engenharia para Multiempresa. A dependência técnica
que continua valendo é só a Fase 2 (Infraestrutura SaaS) e a decisão pendente em `ADR-005.md`.

### Decisão: Financeiro dividido em mínimo (1.0) e avançado (2.x)

A proposta original de 2026-07-25 colocava Financeiro inteiro na Fase 1 / versão 1.0. **Corrigida no
mesmo dia**: só o **mínimo** necessário para o lojista abandonar a planilha entra na 1.0 — caixa,
entradas, saídas, contas a pagar, contas a receber, fluxo de caixa simples. O **avançado** (DRE, centros
de custo, conciliação bancária, múltiplas contas, indicadores financeiros, projeções) fica na versão
2.x, junto do restante da "2.0 Escala". Motivo: permite lançar a 1.0 mais cedo sem perder qualidade no
essencial.

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
ciclo de vida completo já desenhado no ADR-007) e o **Financeiro mínimo** necessário para o lojista
abandonar a planilha paralela: caixa, entradas, saídas, contas a pagar, contas a receber, fluxo de caixa
simples (decidido em 2026-07-25, ver seção "As 6 Fases estratégicas" acima). Financeiro avançado fica
na 2.x.

### Fluxoly 2.0+ — Escala

Ordem revisada em 2026-07-25 e novamente em 2026-08-05 (ver "As 6 Fases estratégicas" acima): dentro
desta faixa de versão, **Infraestrutura SaaS** (PostgreSQL, Redis, workers, filas, observabilidade,
CI/CD) vem primeiro — bloqueio técnico real —, seguida de **Automação** (WhatsApp, e-mail, Mercado Livre,
Nota Fiscal) e **Inteligência** (IA), e só depois **Multiempresa** (P5, bloqueada por decisão pendente em
`ADR-005.md` e por decisão de priorização de negócio — validar o produto via Automação/IA antes de
investir em billing/planos/isolamento multiempresa). Também nesta faixa: **CRM** (pilar
"Relacionamento", depende de Clientes maduro), **Financeiro avançado** (DRE, centros de custo,
conciliação bancária, múltiplas contas, indicadores, projeções), e itens sem backlog/spec/ADR hoje (API
pública, Marketplace, app mobile nativo) — registrados só para não perder o fio, não como compromisso.

---

## Em aberto — decidir antes de fechar o escopo de cada versão

- ~~Critério de "pronto para lançar" por versão~~ — resolvido em 2026-07-25 por
  `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` (checklist de certificação da Release 1.0).
- Se alguma versão deve ser dividida (ex.: Venda MVP sair sozinha na 0.9 antes de Unidades Serializadas
  ter tela completa).

---

## Documentos relacionados

- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — checklist de certificação da Release 1.0 (o que
  precisa estar pronto antes do primeiro cliente pagante) e a tabela dos "3 níveis de planejamento"
  (Visão / Releases / Sprints) que explica como este documento se relaciona com `PRODUCT_BACKLOG.md` e
  `ROADMAP.md`
- `docs/product/PRODUCT_BACKLOG.md` — fonte dos épicos e prioridades usados nesta proposta (nota:
  revisado em 2026-07-20, anterior a Produtos/Clientes ganharem tela e à migração `unidades_serializadas`
  — vale conferir contra `docs/operations/PROJECT_STATUS.md` antes de assumir o status de cada épico)
- `docs/company/DECISION_LOG.md` — decisão de desacoplar Vendas de Caixa/Financeiro (2026-07-09); decisão
  de adotar as 6 Fases, com a correção de ordem (Infraestrutura antes de Multiempresa) e divisão do
  Financeiro (mínimo/avançado) no mesmo dia (2026-07-25)
- `docs/operations/ROADMAP.md` — roadmap de engenharia (sprints técnicas), eixo separado e hoje
  desatualizado (ver aviso no topo daquele documento)
- `docs/engineering/adr/ADR-005.md` — decisão pendente que bloqueia Multiempresa (Fase 3 / 2.0+)
- `docs/engineering/adr/ADR-007.md` — ciclo de vida de `unidades_serializadas` que fundamenta o escopo
  de Garantias/Trocas citado na versão 1.0 acima
- `docs/company/BRAND_IDENTITY.md` seção 2 — os 6 pilares macrossistêmicos que fundamentam as Fases 1-5
