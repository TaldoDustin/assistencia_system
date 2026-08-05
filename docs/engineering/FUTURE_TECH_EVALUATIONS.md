# FUTURE_TECH_EVALUATIONS.md — Ideias Técnicas de Longo Prazo (Não-Decisões)

**Status:** Planejamento estratégico. **Nada neste documento é uma decisão aprovada.**
**Criado em:** 2026-08-05, a partir de uma proposta externa de evolução do Fluxoly para SaaS, revisada e
recalibrada contra o estado real do repositório (ver `docs/company/RELEASE_STRATEGY.md` e os ADRs
citados abaixo).

---

## Por que este documento existe

`docs/README.md` (regra de governança, 2026-07-10) exige que todo documento novo responda "que decisão
ele ajuda a tomar?". Este documento ajuda a decisão **"quando vale a pena abrir um Discovery/ADR para
este tema?"** — sem tomar a decisão de arquitetura em si. Isso é deliberado: uma ADR nasce quando existe
uma decisão concreta a registrar, não uma possibilidade futura (ver `engineering/ARCHITECTURE_DECISIONS.md`
e o princípio da Separação de Decisões em `ADR-010.md`). Registrar essas ideias aqui evita duas coisas:
perder o raciocínio já feito sobre cada uma, e o risco oposto — tratá-las como decisões já tomadas antes
da hora (o erro que este próprio documento nasceu para corrigir, ver seção "Origem" abaixo).

**O que este documento NÃO cobre:** itens que já têm ADR (mesmo pendente) ou já estão no roadmap ativo.
Design System (shadcn/ui sobre Radix+Tailwind) e Motion básico **não** entram aqui — são polimento de UX
sequenciado para logo após a Release 1.0, sem mudança de stack e sem necessidade de ADR (ver conversa que
originou este documento). Multiempresa/Billing também não é reavaliado aqui em profundidade — já tem
`ADR-005.md` com as alternativas técnicas avaliadas; este documento só referencia, não duplica.

---

## Como usar

Cada item tem: **Contexto**, **Benefícios**, **Riscos**, **Momento recomendado de avaliação**. Quando um
tema virar prioridade real (isto é, uma sprint está prestes a começar e depende dessa decisão), o próximo
passo é um Discovery (ou, se já houver informação suficiente, direto um ADR usando
`engineering/templates/ADR_TEMPLATE.md`) — nunca implementar a partir do que está escrito aqui.

---

## Next.js (para superfícies fora do sistema interno)

**Contexto:** `ADR-001` (2026-07-06, Aceita) avaliou migrar o frontend inteiro para Next.js e decidiu manter
React + Vite — reescrever a lógica de negócio madura do Flask (`irflow_os.py`, `irflow_reports.py` etc.)
em JS/TS não compensava, e o sistema é majoritariamente autenticado (SSR não resolve um problema de SEO
que não existe atrás de login). Essa decisão continua válida hoje: mantenedor único, nenhuma demanda
documentada de SSR/TypeScript. O cenário diferente é uma superfície nova e desacoplada — landing page
institucional, blog, documentação pública — sem sessão, sem dado de cliente, onde SEO/SSR têm valor real.

**Benefícios:** SSR nativo para SEO, deploy simples na Vercel, zero acoplamento ao backend Flask/SQLite.

**Riscos:** Nenhum para o sistema atual, **se e somente se** ficar isolado (deploy e repositório/pasta
próprios, sem importar nada do `frontend/` atual). O risco real é escopo rastejar — começar como "só a
landing" e virar pressão para unificar com o app interno.

**Momento recomendado de avaliação:** quando houver decisão de negócio de investir em marketing/aquisição
orgânica (Fase 4 — Automação, ou antes, se o Product Owner priorizar). Não depende de nenhuma outra fase
técnica. Se algum dia a ideia for usar Next.js **no sistema interno**, isso não é uma reavaliação deste
documento — é uma revisão formal do `ADR-001`, com evidência de que suas condições de revisão (equipe
maior, demanda real de SSR/TS) se tornaram verdadeiras.

---

## BetterAuth

**Contexto:** proposta para substituir a autenticação atual (Flask session + `FLASK_SECRET_KEY`) por
BetterAuth (OAuth Google/GitHub, Magic Link, MFA). Tecnicamente, BetterAuth é pensado para runtime
Node/Next.js — rodar sobre um backend Flask exigiria um serviço de auth separado em Node, emitindo tokens
que o Flask validaria, ou aceitar a duplicação de lógica de sessão. A autenticação atual já foi endurecida
com esforço real e específico: rate limiting por IP (KI-001), expiração de sessão por inatividade,
fail-secure em `verificar_autenticacao()` (KI-024), comparação constant-time no webhook (KI-023).

**Benefícios:** OAuth social, Magic Link, MFA nativos — reduz fricção de login se/quando isso for uma
demanda real de produto.

**Riscos:** incompatibilidade de runtime (não é plug-and-play sobre Flask), risco de reintroduzir
vulnerabilidades já fechadas se a nova camada não replicar cada proteção existente, complexidade
operacional de mais um serviço.

**Momento recomendado de avaliação:** só quando existir uma demanda de produto documentada (PRD) por
OAuth social, Magic Link ou MFA — hoje nenhum documento de produto pede isso. Se/quando o backend migrar
para um runtime Node (cenário não previsto em nenhum ADR atual), reavaliar então.

---

## PostgreSQL (motor de banco)

**Contexto:** diferente dos itens acima, a migração de SQLite para PostgreSQL **já é uma decisão
estratégica tomada** — é o objetivo central da Fase 2 oficial ("Infraestrutura SaaS",
`docs/company/RELEASE_STRATEGY.md`), motivada diretamente pelos incidentes de concorrência já vividos
(INC-001 "database is locked", INC-002 OS duplicada — ambos raiz em SQLite com múltiplos processos
escrevendo). O que **não** está decidido é o hosting/vendor: Postgres self-hosted (Render, Railway, Neon)
vs. Postgres gerenciado como parte de um pacote maior (Supabase — ver item abaixo).

**Benefícios:** elimina a classe inteira de bug de concorrência de escrita que gerou dois incidentes
reais; WAL do SQLite já é um paliativo, não uma solução para múltiplos workers.

**Riscos:** migração de dados de produção com clientes reais — exige plano de migração, backup verificado,
janela de manutenção (mesma cautela de qualquer mudança de schema, `CLAUDE.md` "o banco é sagrado").

**Momento recomendado de avaliação:** Discovery da Fase 2, quando ela começar (depende de TD-01 +
Release 1.0 fechadas). A pergunta a responder no Discovery não é "migrar ou não" (já decidido), é "qual
provedor/hosting".

---

## Supabase (pacote Postgres + Auth + Storage + Realtime)

**Contexto:** diferente do item acima, adotar o **pacote** Supabase (não só o Postgres dele) é uma decisão
própria — combina banco, autenticação e storage num único vendor. Nenhum documento do projeto avaliou essa
comparação ainda.

**Benefícios:** menos peças para operar (um único provedor para banco+auth+storage+realtime), bom
ecossistema com Vercel se a landing page (item Next.js acima) também usar a plataforma.

**Riscos:** vendor lock-in — decisão de infraestrutura tomada por conveniência de pacote em vez de
comparação real com alternativas (Postgres self-hosted + Redis já é a direção da Fase 2; storage
separado como S3-compatível). Empacotar banco+auth+storage numa decisão só reduz a flexibilidade de trocar
uma peça sem afetar as outras duas.

**Momento recomendado de avaliação:** mesmo Discovery da Fase 2 do item PostgreSQL — comparar
explicitamente contra Postgres self-hosted + Redis + storage separado antes de decidir. Merece um ADR
próprio quando chegar a hora (`ADR-01X — Vendor de Infraestrutura da Fase 2`), não decidir por peça
isolada.

---

## Redis

**Contexto:** cache, sessões, locks distribuídos e rate limiting — hoje resolvidos ad-hoc em SQLite
(`login_attempts` para rate limiting, lock cross-processo em tabela própria para o MercadoPhone). Faz
parte do objetivo da Fase 2 oficial junto do PostgreSQL.

**Benefícios:** locks/rate-limit/cache nativos, sem sobrecarregar o banco principal com esse tipo de
escrita de alta frequência.

**Riscos:** mais um serviço de infraestrutura para operar e monitorar; baixo risco técnico em si (padrão
maduro), risco está mais em subdimensionar o esforço operacional de manter mais um serviço com um único
mantenedor.

**Momento recomendado de avaliação:** junto do Discovery da Fase 2 — mesma decisão de infraestrutura do
PostgreSQL/Supabase.

---

## Resend (e-mail transacional)

**Contexto:** hoje o único uso de e-mail no sistema é notificação de backup, com falhas só logadas, sem
alerta visível ao operador (KI-006, aberto). Não existe nenhum fluxo de e-mail para o usuário final (a
recuperação de senha é token gerado pelo admin, não self-service por e-mail).

**Benefícios:** API HTTP simples, sem dependência de framework — Flask pode chamar via `requests` sem
nenhuma mudança de stack. Risco técnico de adoção é baixo.

**Riscos:** baixo tecnicamente; o risco real é adotar a ferramenta antes de existir a regra de negócio que
a justifica (recuperação de senha self-service, aviso de garantia, cobrança) — construir a integração
antes do fluxo estar desenhado gera retrabalho.

**Momento recomendado de avaliação:** Fase 4 (Automação) — quando os fluxos de comunicação (garantia,
cobrança, notificação de OS pronta) forem de fato especificados. Pode adiantar isoladamente se o KI-006
(alerta de falha de backup) virar prioridade antes disso — nesse caso é uma correção pontual, não a
adoção da Fase 4 inteira.

---

## Firebase Cloud Messaging (push mobile)

**Contexto:** não existe app nativo Android/iOS em nenhum documento de produto ou roadmap. Push
notification pressupõe um canal (app nativo) que ainda não foi decidido em lugar nenhum.

**Benefícios:** notificações em tempo real para Android/iOS/Web Push, se/quando existir um app nativo.

**Riscos:** investimento em canal que não está no backlog — adotar isso antes de existir a decisão de
app mobile seria, na prática, uma feature não solicitada (`CLAUDE.md`, Regras Absolutas).

**Momento recomendado de avaliação:** só depois de uma decisão explícita e documentada de construir um
app mobile nativo (própria ADR, hoje inexistente). Sem isso, este item fica parado indefinidamente.

---

## Multiempresa / Billing (referência, não avaliação nova)

**Contexto:** já tem ADR própria — `ADR-005.md` — com as alternativas técnicas avaliadas (banco por
empresa / coluna `empresa_id` / schema por empresa). A decisão de negócio (qual alternativa, e quando)
ainda está pendente do Product Owner. Mapeada como Fase 3 em `RELEASE_STRATEGY.md`, depois da
Infraestrutura SaaS — decisão deliberada para não multiplicar escrita concorrente sobre uma base ainda em
SQLite (mesma raiz do INC-001/INC-002).

**Momento recomendado de avaliação:** quando a Fase 2 (Infraestrutura SaaS) estiver pronta **e** o
Product Owner resolver a decisão pendente em `ADR-005.md`. Não reavaliar as alternativas técnicas aqui —
já estão em `ADR-005.md`.

---

## Documentos relacionados

- `docs/engineering/adr/ADR-001.md` — decisão vigente sobre frontend (React + Vite)
- `docs/engineering/adr/ADR-005.md` — alternativas técnicas de multiempresa, decisão de negócio pendente
- `docs/company/RELEASE_STRATEGY.md` — as 6 Fases estratégicas e o versionamento oficial
- `docs/engineering/adr/ADR-010.md` — ciclo de feature com regra de negócio (Discovery → ADR, quando aplicável)
- `docs/engineering/ARCHITECTURE_DECISIONS.md` — índice de ADRs já aceitas
