# RELEASE_STRATEGY.md — Estratégia de Versionamento

**Status:** ✅ DECIDIDO pelo usuário (CTO/Product Owner) em 2026-07-21 — substitui integralmente a
proposta técnica anterior (2026-07-10), que usava um esquema de numeração diferente e incompatível.
Ampliado em 2026-07-25 com as 6 Fases estratégicas (visão de longo prazo, além da 2.0).

**Última revisão:** 2026-07-25

---

## As 6 Fases estratégicas (visão de longo prazo, 2026-07-25)

Proposta do usuário (CTO), adotada nesta data. Reorganiza o horizonte completo da Fluxoly — desde a
estabilização atual até inteligência de negócio — em 6 fases, cada uma com um objetivo de negócio único.
**Diferente do versionamento abaixo** (que é sobre *o quê sai em cada release*), as Fases respondem *por
que* essa sequência existe — é a camada de propósito acima das versões.

```
Fase 0 — Estabilização da Plataforma     (agora)
Fase 1 — Release 1.0 (primeiro cliente)
Fase 2 — Multiempresa
Fase 3 — Escalabilidade
Fase 4 — Automação
Fase 5 — Inteligência
```

| Fase | Objetivo de negócio | Mapeamento no versionamento abaixo |
|---|---|---|
| **0 — Estabilização** | "Nenhum bug crítico conhecido." Bugs (INC-001, INC-002 — ver `docs/operations/INCIDENTS/`), auditoria (permissões, SQL injection, uploads, autenticação), performance (índices, queries, paginação, cache), observabilidade (logs, métricas, monitorização) | Não é uma versão — é o gate contínuo antes de qualquer release sair. Trabalho já em andamento nesta sprint técnica |
| **1 — Release 1.0** | "O cliente consegue operar a empresa inteira usando somente a Fluxoly." Assistência (OS, peças, estoque, garantias, histórico), Comercial (produtos, vendas, clientes, unidades serializadas, IMEI), **Financeiro** (caixa, contas, despesas, receitas), Dashboards, Relatórios, Configurações | Cobre as versões **0.9 (Commercial Preview)** e **1.0 (Commercial Release)** abaixo — a Fase 1 é o destino, 0.9/1.0 são os incrementos até lá |
| **2 — Multiempresa** | "Primeiros clientes reais." Isolamento por `empresa_id`, planos (Starter/Professional/Enterprise), licenças, assinatura, trial, cancelamento | Era a parte "Multiempresa" da versão **2.0 (Escala)** abaixo — agora quebrada em fase própria. **Bloqueada por decisão pendente em `ADR-005.md`** (alternativas técnicas já avaliadas, decisão de negócio ainda não tomada) |
| **3 — Escalabilidade** | "100 empresas simultâneas." PostgreSQL (fim do SQLite), Redis (cache/sessões/locks/rate limit), separação de workers (API/Worker/Scheduler), filas (Mercado Phone/e-mail/WhatsApp/backups), CDN, backup automático versionado, monitorização (Sentry/Grafana/Prometheus) | Não existia como fase própria antes — estava implícita dentro da "2.0 Escala". Quebrada em fase própria por ser trabalho de infraestrutura, não de produto |
| **4 — Automação** | "Eliminar trabalho manual." WhatsApp, e-mail (garantias/orçamentos/cobranças), integração Mercado Livre, Nota Fiscal, APIs | Era a parte "CRM/WhatsApp" da versão **2.0 (Escala)** abaixo |
| **5 — Inteligência** | IA respondendo perguntas de negócio (lucro, top vendedores, atraso por técnico, sugestão de compra, retenção), alertas e previsões | Novo — pilar "Inteligência" já existe em `BRAND_IDENTITY.md` seção 2, mas nunca tinha uma fase própria de execução |

### Decisão resolvida nesta data: Financeiro entra na 1.0

A seção "Em aberto" abaixo (versão original de 2026-07-21) deixava em aberto se Financeiro/Caixa entrava
na 1.0 ou ficava inteiramente na 2.0. **Resolvido em 2026-07-25**: Financeiro básico (caixa, contas,
despesas, receitas) entra na Fase 1 / versão 1.0 — é parte do critério "o cliente consegue operar a
empresa inteira sem depender de planilha paralela" que já justificava a Commercial Release desde a
reconciliação original. "Financeiro avançado" (o que exatamente isso significa ainda não está definido)
permanece na 2.0/Fase 2+. Ver `docs/company/DECISION_LOG.md` para o registro executivo desta decisão.

### Tensão em aberto: ordem de Fase 2 (Multiempresa) vs. Fase 3 (Postgres/Redis)

Registrada em 2026-07-25, não resolvida — decisão do usuário quando a Fase 2 se aproximar. Os dois
incidentes resolvidos na sprint técnica de estabilização (INC-001 `database is locked`, INC-002 OS
duplicada) nasceram de limitações do SQLite com múltiplos processos (workers do Gunicorn) escrevendo
concorrentemente — a correção de INC-002 precisou de um lock manual porque não existe coordenação nativa
entre processos no SQLite. Multiempresa (Fase 2) aumenta a escrita concorrente e adiciona isolamento por
`empresa_id` — construir isso sobre SQLite antes da migração para Postgres (Fase 3) arrisca reproduzir a
mesma classe de problema em maior escala, exigindo mais soluções manuais que seriam descartadas ao migrar
depois. Vale avaliar, quando a Fase 2 for planejada em detalhe, se Postgres deveria vir *durante* ou
*antes* dela, não estritamente depois.

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
lojista operar sem depender de planilha paralela. Financeiro básico (caixa, contas, despesas, receitas)
entra nesta versão — decidido em 2026-07-25, ver seção "As 6 Fases estratégicas" acima. "Financeiro
avançado" fica na 2.0.

### Fluxoly 2.0 — Escala

Épicos do backlog: **Multiempresa** (P3, bloqueado por decisão pendente em `ADR-005.md`), **CRM**,
**WhatsApp** (pilar "Relacionamento", depende de Clientes maduro), **Financeiro avançado**, e itens sem
backlog/spec/ADR hoje (API pública, Marketplace, app mobile nativo) — registrados só para não perder o
fio, não como compromisso.

---

## Em aberto — decidir antes de fechar o escopo de cada versão

- Critério de "pronto para lançar" por versão — hoje não existe um Definition of Done comercial
  (diferente do Definition of Done técnico já existente por sprint em `docs/operations/ROADMAP.md`).
  Candidato a ser resolvido pelo `RELEASE_1.0_MASTER_CHECKLIST.md` planejado (ainda não criado).
- Se alguma versão deve ser dividida (ex.: Venda MVP sair sozinha na 0.9 antes de Unidades Serializadas
  ter tela completa).
- Ordem de Fase 2 (Multiempresa) vs. Fase 3 (Postgres/Redis) — ver seção "As 6 Fases estratégicas" acima.

---

## Documentos relacionados

- `docs/product/PRODUCT_BACKLOG.md` — fonte dos épicos e prioridades usados nesta proposta (nota:
  revisado em 2026-07-20, anterior a Produtos/Clientes ganharem tela e à migração `unidades_serializadas`
  — vale conferir contra `docs/operations/PROJECT_STATUS.md` antes de assumir o status de cada épico)
- `docs/company/DECISION_LOG.md` — decisão de desacoplar Vendas de Caixa/Financeiro (2026-07-09); decisão
  de adotar as 6 Fases e resolver Financeiro na 1.0 (2026-07-25)
- `docs/operations/ROADMAP.md` — roadmap de engenharia (sprints técnicas), eixo separado e hoje
  desatualizado (ver aviso no topo daquele documento)
- `docs/engineering/adr/ADR-005.md` — decisão pendente que bloqueia Multiempresa (Fase 2 / 2.0)
- `docs/engineering/adr/ADR-007.md` — ciclo de vida de `unidades_serializadas` que fundamenta o escopo
  de Garantias/Trocas citado na versão 1.0 acima
- `docs/company/BRAND_IDENTITY.md` seção 2 — os 6 pilares macrossistêmicos que fundamentam as Fases 1-5
