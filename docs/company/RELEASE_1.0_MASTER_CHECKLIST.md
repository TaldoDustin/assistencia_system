# RELEASE_1.0_MASTER_CHECKLIST.md — Certificação para o primeiro cliente pagante

**Status:** 🔵 Em construção — criado em 2026-07-25
**Última revisão:** 2026-07-25
**Regra de uso:** este não é um backlog nem um roadmap — é um checklist de certificação. Quando todos os
itens estiverem `[x]`, a Fluxoly está pronta para o primeiro cliente pagante (Fase 1 / Release 1.0, ver
`docs/company/RELEASE_STRATEGY.md`). Toda sprint nova deveria responder: *"isto marca algum item deste
checklist?"* — se não, questionar se deve entrar no escopo agora.

Cada item tem: objetivo, critério de aceitação, estado verificado (não aspiracional), e link para onde
o trabalho real acontece.

**Guardrail (usuário/CTO, 2026-07-25):** este documento não deve virar um segundo backlog. A regra é
`backlog → trabalho`, `roadmap → sequência`, `checklist → certificação`. Todo item aqui deve poder
terminar só em `[ ] Não atende` / `[x] Atende` — sem histórias, tarefas ou subtarefas de implementação
dentro deste arquivo. Trabalho de implementação vive em `docs/product/PRODUCT_BACKLOG.md`; passos de
execução operacional (ex.: implantação de cliente) vivem em `docs/company/GO_LIVE_PLAN.md`, não aqui.

---

## Os 3 níveis de planejamento (para não confundir os documentos entre si)

Sugestão do usuário (CTO), 2026-07-25 — separa por que existe cada documento estratégico do projeto:

| Nível | Pergunta que responde | Documento |
|---|---|---|
| 1 — Visão (longo prazo, raramente muda) | Por que essa sequência de fases existe? | `docs/company/RELEASE_STRATEGY.md` seção "As 6 Fases estratégicas" |
| 2 — Releases (o que entrega cada versão) | O que sai em cada versão (0.8 → 2.0)? | `docs/company/RELEASE_STRATEGY.md` seção "Versionamento" |
| 3 — Sprints (o que fazemos agora) | O que fazemos nesta semana/sprint? | `docs/operations/ROADMAP.md` (desatualizado, ver aviso no topo) e `docs/operations/SPRINTS/` |

Este documento (`RELEASE_1.0_MASTER_CHECKLIST.md`) é transversal aos 3 — é o critério de aceitação da
Fase 1 / versão 1.0, não um nível novo de planejamento.

---

## Visão executiva — quanto falta

Sugestão do usuário (CTO), 2026-07-25. **Método:** cada item do checklist abaixo tem um estado
(❌/🟡/✅); a % por área é a média simples desses estados, usando ❌≈0-15%, 🟡≈30-70% (conforme o quão
parcial, com base na descrição real do item), ✅=100%. **É uma leitura executiva rápida, não uma métrica
de esforço/pontos de história** — não pesa por dificuldade nem por quantos itens tem cada área. As áreas
abaixo são as mesmas seções do checklist detalhado, não uma categorização nova.

| Área | Status | % |
|---|---|---|
| Produto (Assistência, Comercial, Financeiro, Dashboard, Configurações) | 🟡 | ~40% |
| Confiabilidade (bugs, backup, restore, carga) | 🟡 | ~44% |
| Segurança e Compliance | 🟡 | ~55% |
| Observabilidade | 🔴 | ~3% |
| Operação (deploy, rollback, manual, demo, piloto) | 🔴 | ~2% |

```
Release 1.0:  ██████░░░░░░░░░░░░░░  ~29%
```

**Correção (2026-07-25):** a revisão anterior desta tabela havia posto Segurança e Compliance em ~75%
olhando só para o item "Segurança revisada" (que de fato ficou ✅). A área tem 2 itens — o outro,
"LGPD", segue ❌ não iniciado — então a média da área é ~55%, não ~75%. Visão geral recalculada de
~33% para ~29%.

Maiores blocos de trabalho pela % (não pela quantidade de itens): **Operação** e **Observabilidade**
estão praticamente do zero — nenhum dos dois tem código/documento nenhum ainda, diferente de
**Produto**/**Confiabilidade**, onde já existe base real, só falta completar. Ver detalhamento item a
item abaixo.

---

## Checklist de Certificação — Release 1.0

### Produto

- [ ] **Assistência completa** — OS, peças, estoque, garantias, histórico
  Estado: 🟡 Em produção há meses (OS, Estoque, Garantias, Lista de Compras). Dívida de autorização
  (rotas de mutação de OS/Estoque sem restrição por perfil) corrigida em 2026-07-25 (Sprint Segurança
  1.0). Segue aberto: KI-005 (paginação ausente em `GET /api/ordens`).
  Link: `docs/engineering/DOMAIN_MODEL.md`, `docs/operations/KNOWN_ISSUES.md` (KI-005)

- [ ] **Comercial completo** — produtos, vendas, clientes, unidades serializadas, IMEI
  Estado: 🟡 Backend de Produtos/Clientes/Unidades Serializadas implementado, sem tela completa em
  produção. **Vendas ainda é só especificação** (`docs/product/features/VENDAS.md`), nenhuma linha de
  código do domínio existe. Maior item em aberto deste checklist.
  Link: `docs/product/PRODUCT_BACKLOG.md`, `docs/product/features/VENDAS.md`

- [x] **Financeiro mínimo** — caixa, entradas, saídas, contas a pagar/receber, fluxo de caixa simples
  Estado: ✅ Entregue (2026-08-10, BR-067 a BR-069, ciclo ADR-010 encerrado): `movimentacoes_caixa`,
  `contas_pagar`, `contas_receber` (migration `m0002`), `/api/caixa`, `/api/contas-pagar`,
  `/api/contas-receber`, hook automático Vendas→Caixa, e tela `frontend/src/pages/Financeiro.jsx`
  (`/financeiro`, gate `admin`/`financeiro`). Fluxo de caixa simples entregue como relatório de saldo +
  listagem de movimentações (sem o gráfico de `GET /api/caixa/relatorio`, deliberadamente fora desta
  fatia — evolução futura de dashboard/relatórios financeiros). Achado da Revisão Arquitetural registrado
  em KI-034 (Ajuste Comercial de venda não resincroniza a entrada de caixa), não bloqueante.
  Link: `docs/company/RELEASE_STRATEGY.md` (Financeiro mínimo x avançado),
  `docs/engineering/plans/PLAN-financeiro-minimo.md`

- [ ] **Dashboard Executivo**
  Estado: 🟡 Parcial — dashboard básico existe (`frontend/src/pages/Dashboard.jsx`, KPIs de
  faturamento/lucro/serviços/técnico). Falta a versão executiva completa (ticket médio, OS atrasadas,
  top vendedores, margem).
  Link: `docs/product/PRODUCT_BACKLOG.md` (linha Dashboard Executivo)

- [ ] **Configurações** — empresa, usuários, integrações
  Estado: 🟡 Usuários existe (`frontend/src/pages/Users.jsx`). Sem tela de "empresa" (faz sentido só
  pós-Multiempresa) nem de configuração de integrações (Mercado Phone é configurado hoje só via
  variável de ambiente/backend, sem UI).
  Link: —

### Confiabilidade

- [ ] **0 bugs críticos conhecidos**
  Estado: 🟡 INC-002 (OS duplicada) resolvido 2026-07-24. INC-001 (`database is locked`) parcialmente
  corrigido — hotfix em `/api/auth/login`, mas 4 rotas de checklist confirmadas sem proteção contra
  exceção seguem abertas, causa raiz ainda não confirmada em runtime. 8 KIs abertos em
  `KNOWN_ISSUES.md` (KI-002 a KI-020), 4 deles com impacto "Alto": KI-003 (módulo API monolítico),
  KI-004 (sem sistema de migrations formal), KI-019, KI-020.
  Link: `docs/operations/INCIDENTS/`, `docs/operations/KNOWN_ISSUES.md`

- [ ] **Backup validado** — backup automático funcionando
  Estado: 🟡 Backup manual e automático existe em produção (`/api/backup/criar`, `/api/backup/listar`,
  usado nesta própria sessão para investigar INC-002). KI-006 aberto: sem alerta se o backup automático
  parar de rodar silenciosamente.
  Link: `docs/operations/KNOWN_ISSUES.md` (KI-006)

- [ ] **Restore validado** — processo de restauração testado de ponta a ponta
  Estado: ❌ Endpoint de restore existe (`/api/backup/restaurar`), **mas nenhum teste automatizado
  cobre o fluxo de restauração** (confirmado: nenhum `test_restore`/`test_restaurar` em `tests/`).
  Nunca exercitado de ponta a ponta nesta sessão nem documentado como validado.
  Link: `irflow_blueprints_api.py` (`restaurar_backup_upload`)

- [ ] **Teste de carga** — múltiplos usuários simultâneos
  Estado: 🟡 Feito de forma ad-hoc durante a investigação de INC-001 (até 120 threads concorrentes,
  `gunicorn --workers 2`), mas não é uma suíte de teste de carga formal nem repetível — foi descartado
  após a investigação, não faz parte do CI.
  Link: `docs/operations/INCIDENTS/INC-001-database-is-locked.md`

### Segurança e Compliance

- [x] **Segurança revisada** — permissões, SQL injection, uploads, autenticação
  Estado: ✅ Sprint Segurança 1.0 concluída em 2026-07-25: SQL Injection/File Inclusion/SSRF
  confirmados falsos positivos; `FLASK_SECRET_KEY` rotacionada em produção e fallback hardcoded
  corrigido (falha no boot fora de dev local); gap de autorização em OS/Estoque corrigido (perfil
  obrigatório); todos os P1 corrigidos e validados (CSP/X-Frame-Options, Docker non-root — testado com
  `docker build`/`docker run` reais antes do merge, `persist-credentials`, gunicorn e dependências JS
  atualizadas). Restam só 2 itens P3 (risco aceite/build-only, sem urgência) e um novo scan Aikido
  planejado para confirmar o estado pós-sprint (não bloqueia este item).
  Link: `docs/security/SECURITY_AUDIT_2026-07.md`, `docs/engineering/SECURITY.md`,
  `docs/engineering/DATA_DICTIONARY.md`

- [ ] **LGPD**
  Estado: ❌ Não iniciado — nenhum documento sobre LGPD existe no projeto hoje (confirmado, busca sem
  resultado em `docs/`).
  Link: —

### Observabilidade

- [ ] **Logs estruturados**
  Estado: ❌ Não iniciado — o projeto usa `print()` para tudo (confirmado: nenhuma biblioteca de
  logging estruturado importada em nenhum módulo `.py`). Item já estava no critério de aceitação do
  Sprint 3 original (`docs/operations/ROADMAP.md`) e nunca foi marcado como concluído.
  Link: `docs/operations/ROADMAP.md` (Sprint 3, critério não marcado)

- [ ] **Monitorização / alertas** (Sentry, Grafana, Prometheus ou equivalente)
  Estado: ❌ Não iniciado — nenhuma dependência de monitoramento em `requirements.txt`, nenhuma
  integração no código.
  Link: `docs/operations/ROADMAP.md` (Sprint 3, critério não marcado)

### Operação

- [ ] **Deploy documentado**
  Estado: ❌ Não existe um documento dedicado de "como fazer deploy" — só o `Dockerfile` e a
  configuração do Render/Vercel, sem passo a passo escrito.
  Link: `Dockerfile`

- [ ] **Rollback testado**
  Estado: ❌ Não evidenciado — nenhum registro de um rollback de deploy já ter sido exercitado e
  documentado.
  Link: —

- [ ] **Manual do usuário**
  Estado: ❌ Não existe.
  Link: —

- [ ] **Ambiente de demonstração**
  Estado: ❌ Não confirmado — não identificado nenhum ambiente separado de produção para demo/trial.
  Link: —

- [ ] **Cliente piloto homologou**
  Estado: ❌ Não aplicável ainda — depende de todos os itens acima.
  Link: —

---

## Como ler este checklist

- ❌ = não iniciado, confirmado por busca no código/docs (não é suposição)
- 🟡 = parcial — existe algo, mas não cobre o critério de aceitação inteiro
- ✅ = concluído e verificado (nenhum item ainda, 2026-07-25)
- Todo item "🟡" ou "❌" deveria ter uma entrada correspondente em
  `docs/product/PRODUCT_BACKLOG.md` (ver seção seguinte) quando virar trabalho planejado.

---

## Documentos relacionados

- `docs/company/RELEASE_STRATEGY.md` — as 6 Fases estratégicas e o versionamento 0.8-2.0
- `docs/company/GO_LIVE_PLAN.md` — plano de execução para colocar o primeiro cliente em produção
  (diferente deste documento: responde "como fazemos", não "estamos prontos"). Pré-requisito: este
  checklist 100% concluído
- `docs/product/PRODUCT_BACKLOG.md` — fila de épicos priorizados, cada um deveria referenciar o item
  deste checklist que ele avança
- `docs/operations/PROJECT_STATUS.md` — estado vivo do projeto, atualizado a cada sprint
- `docs/operations/KNOWN_ISSUES.md` — os 8 KIs abertos citados acima
- `docs/operations/INCIDENTS/` — INC-001 e INC-002
