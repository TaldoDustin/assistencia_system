# RELEASE_1.0_MASTER_CHECKLIST.md — Certificação para o primeiro cliente pagante

**Status:** 🔵 Em construção — criado em 2026-07-25
**Última revisão:** 2026-08-10 (auditoria de estado real — ver "Correção" na seção "Visão executiva")
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
| Produto (Assistência, Comercial, Financeiro, Dashboard, Configurações) | 🟡 | ~68% |
| Confiabilidade (bugs, backup, restore, carga) | 🟡 | ~66% |
| Segurança e Compliance | 🟡 | ~55% |
| Observabilidade | 🟢 | ~85% |
| Operação (deploy, rollback, manual, demo, piloto) | 🔴 | ~30% |

```
Release 1.0:  ████████████░░░░░░░░  ~61%
```

**Correção (2026-08-10, auditoria de estado real):** esta tabela media há duas semanas contra um estado
que não existia mais — os itens individuais tinham sido corrigidos (ver detalhamento item a item abaixo:
Comercial/Vendas, Dashboard Executivo, Bugs/INC-001, Logs estruturados, Monitorização, Deploy
documentado), mas a agregação nunca foi recalculada. Cálculo por área, mesma régua já definida acima
(❌≈0-15%, 🟡≈30-70%, ✅=100%), média simples entre os itens de cada seção do checklist detalhado:

| Área | Itens e % individual estimado | Média |
|---|---|---|
| Produto | Assistência 70% · Comercial 65% · Financeiro 100% · Dashboard 65% · Configurações 40% | ~68% |
| Confiabilidade | Bugs 70% · Backup 60% · Restore 100% · Carga 35% | ~66% |
| Segurança | Segurança revisada 100% · LGPD 10% | ~55% (inalterada — nenhum dos dois itens mudou) |
| Observabilidade | Logs 100% · Monitorização 70% | ~85% |
| Operação | Deploy 100% · Rollback 40% · Manual 5% · Demo 5% · Piloto 0% | ~30% |

Visão geral recalculada de ~29% para ~55% em 2026-08-10 (auditoria de estado real), no mesmo dia de ~55%
para ~59% com o fechamento do item Restore validado (Discovery → testes automatizados → QA manual →
merge, ver detalhamento abaixo), e novamente de ~59% para ~61% com a definição da política de Rollback
(Discovery da Parte B da Operação → decisão do CTO, uma pergunta de cada vez → registro em
`GO_LIVE_PLAN.md`/`DEPLOY.md`, ver detalhamento abaixo) — cada salto **é** trabalho novo, diferente da
correção de medição que gerou o primeiro. **Segurança não mudou** — controle de que o método não foi
inflado arbitrariamente fora do item que de fato avançou.

Maior bloco de trabalho real pela % (não pela quantidade de itens) continua sendo **Operação** — Rollback
agora tem política completa (escopo, critério, autoridade, mecanismo, verificação) mas nenhum teste de
dry-run real; os demais (manual, demo, piloto) seguem do zero. Ver detalhamento item a item abaixo.

---

## Checklist de Certificação — Release 1.0

### Produto

- [ ] **Assistência completa** — OS, peças, estoque, garantias, histórico
  Estado: 🟡 Em produção há meses (OS, Estoque, Garantias, Lista de Compras). Dívida de autorização
  (rotas de mutação de OS/Estoque sem restrição por perfil) corrigida em 2026-07-25 (Sprint Segurança
  1.0). Segue aberto: KI-005 (paginação ausente em `GET /api/ordens`).
  Link: `docs/engineering/DOMAIN_MODEL.md`, `docs/operations/KNOWN_ISSUES.md` (KI-005)

- [ ] **Comercial completo** — produtos, vendas, clientes, unidades serializadas, IMEI
  Estado: 🟡 Produtos/Clientes/Unidades Serializadas implementados com tela própria. Vendas em produção
  desde 2026-07-27 (MVP: venda de 1 aparelho por vez) com evolução contínua — V1.2 Cancelamento, V1.3
  Descontos e Aprovação, V1.4 Comissão, V1.5 Garantia, todas com `frontend/src/pages/Vendas.jsx`/
  `VendaDetalhe.jsx` (histórico, filtros, paginação). Falta: fluxo de troca/avaliação de usado, timeout de
  reserva de IMEI (decisões de negócio ainda pendentes do Product Owner, ver `VENDAS.md`).
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
  Estado: 🟡 Parcial — `frontend/src/pages/Dashboard.jsx` já tem faturamento, lucro bruto, serviços por
  status, desempenho por técnico, **Ticket Médio** e **Resultado Líquido** (confirmado no código,
  linhas 112-113). Falta: OS atrasadas e top vendedores (confirmado ausentes — nenhuma ocorrência no
  componente).
  Link: `docs/product/PRODUCT_BACKLOG.md` (linha Dashboard Executivo)

- [ ] **Configurações** — empresa, usuários, integrações
  Estado: 🟡 Usuários existe (`frontend/src/pages/Users.jsx`). Sem tela de "empresa" (faz sentido só
  pós-Multiempresa) nem de configuração de integrações (Mercado Phone é configurado hoje só via
  variável de ambiente/backend, sem UI).
  Link: —

### Confiabilidade

- [ ] **0 bugs críticos conhecidos**
  Estado: 🟡 INC-002 (OS duplicada) resolvido 2026-07-24. INC-001 (`database is locked`) **causa raiz
  confirmada e corrigida em produção em 2026-08-05** (commit por registro na sincronização Mercado Phone,
  ver `docs/operations/INCIDENTS/INC-001-database-is-locked.md`). 10 KIs abertos hoje em
  `KNOWN_ISSUES.md` (KI-002, KI-005, KI-006, KI-007, KI-019, KI-029, KI-030, KI-031, KI-033, KI-034) —
  **nenhum classificado como "Crítico"**; o de maior impacto é KI-029 ("Alto em potencial" — arquivos de
  backup de banco versionados no histórico git, decisão de remoção pendente do usuário).
  Link: `docs/operations/INCIDENTS/`, `docs/operations/KNOWN_ISSUES.md`

- [ ] **Backup validado** — backup automático funcionando
  Estado: 🟡 Backup manual e automático existe em produção (`/api/backup/criar`, `/api/backup/listar`,
  usado nesta própria sessão para investigar INC-002). KI-006 aberto: sem alerta se o backup automático
  parar de rodar silenciosamente.
  Link: `docs/operations/KNOWN_ISSUES.md` (KI-006)

- [x] **Restore validado** — processo de restauração testado de ponta a ponta
  Estado: ✅ Concluído (2026-08-10). Cobertura automatizada nova: `tests/test_backup_restore.py`
  (7 cenários — restore altera o banco de fato, backup `pre-restore-*.db` criado com o estado anterior,
  rejeita extensão/header/corrupção sem alterar o banco, 403 sem sessão/sem perfil admin), com fixture de
  isolamento local ao arquivo (banco real da sessão de testes preservado via `PRAGMA wal_checkpoint(FULL)`
  + snapshot/restore, `tests/conftest.py` global intocado). **QA manual de ponta a ponta** (11/11) rodado
  contra um backend descartável isolado (porta própria, `IR_FLOW_DATA_DIR` próprio, nunca
  `database.db` de desenvolvimento/produção): restore de arquivo válido altera o banco, pré-restore
  criado com o estado anterior, integridade pós-restore ok, app responde normalmente pós-restore,
  arquivo sem `.db`/não-SQLite/corrompido rejeitados sem alterar o banco, sem sessão e sem permissão
  retornam 403. Achado de portabilidade (não é bug — ver `ENGINEERING_GUIDE.md` §11, nenhum critério de
  interrupção se aplica): `PRAGMA integrity_check` diverge por build de SQLite para o mesmo arquivo
  corrompido — runner Linux do CI levanta `sqlite3.DatabaseError` direto em vez de retornar 400 limpo;
  teste ajustado para aceitar os dois desfechos reais, sempre provando que o banco original permanece
  inalterado. Merge em `main` via PR #21 (commit `f73f6f86`), CI 6/6 verde antes e depois do merge.
  Nenhum código de produção alterado neste ciclo.
  Link: `tests/test_backup_restore.py`, `api_backup.py` (`restaurar_backup_upload`)

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

- [x] **Logs estruturados**
  Estado: ✅ Concluído (Sprint Observabilidade, ver `docs/operations/SPRINTS/SPRINT_OBSERVABILIDADE.md`) —
  `fluxoly_logging.py` implementa logging estruturado em JSON com correlation ID por request, testado em
  `tests/test_logging_json.py`.
  Link: `docs/operations/SPRINTS/SPRINT_OBSERVABILIDADE.md`, `fluxoly_logging.py`

- [ ] **Monitorização / alertas** (Sentry, Grafana, Prometheus ou equivalente)
  Estado: 🟡 Implementado, pendente de ativação em produção — Sentry integrado no backend (`app.py`,
  `sentry_sdk`) e no frontend, `/metrics` (Prometheus, modo multiprocess) validado com Docker real. Falta
  configurar `SENTRY_DSN`/`VITE_SENTRY_DSN` nos dashboards reais do Render/Vercel para a captura entrar
  em vigor em produção (`docs/operations/PROJECT_STATUS.md`, linha "Observabilidade").
  Link: `docs/operations/SPRINTS/SPRINT_OBSERVABILIDADE.md`, `docs/engineering/plans/PLAN-Observabilidade-Sentry-Frontend.md`

### Operação

- [x] **Deploy documentado**
  Estado: ✅ `DEPLOY.md` (raiz do repositório) cobre o procedimento completo de deploy: backend no
  Render (Docker, variáveis de ambiente, disco persistente) e frontend na Vercel (build, variáveis),
  mais um passo a passo resumido. Não cobre rollback — esse é o item separado abaixo, que continua ❌.
  Link: `DEPLOY.md`

- [ ] **Rollback testado**
  Estado: 🟡 Política definida e aprovada (2026-08-10): escopo coordenado (backend+frontend sempre
  juntos), critério de acionamento (bug crítico/perda de dados/indisponibilidade prolongada), autoridade
  (só o CTO autoriza), regra de interação com migrations (nunca cruza uma migration já aplicada — TD-03
  roll-forward only), mecanismo (`git revert` + `git push`) e verificação (smoke test manual). Dois
  exercícios locais conduzidos no mesmo dia (Dry-Run 1A e 1B, branch `dry-run/rollback-f5fdb23`,
  preservada): o 1A validou o mecanismo de `git revert` sem conflito (commit `f5fdb23`, só testes); o 1B,
  com um commit real de produção (`609619f`), encontrou um **conflito real** em
  `docs/operations/KNOWN_ISSUES.md` — o que originou a nova regra "conflito = condição de parada +
  decisão explícita do CTO", cobrindo qualquer tipo de arquivo, também documentada em
  `DEPLOY.md`/`GO_LIVE_PLAN.md`. `git revert --abort` executado com sucesso, `main`/`origin/main` nunca
  tocadas. **Ainda não há um dry-run local completo sem interrupção, nem dry-run de infraestrutura
  (Render/Vercel)** — permanece 🟡, não ✅. Percentual mantido em 40% (ver "Visão executiva" abaixo e
  raciocínio no `PROJECT_STATUS.md`): a política ficou mais robusta, mas este item mede se o rollback foi
  *testado* de ponta a ponta, o que ainda não aconteceu.
  Link: `DEPLOY.md`, `docs/company/GO_LIVE_PLAN.md`

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
- ✅ = concluído e verificado (5 itens em 2026-08-10: Financeiro mínimo, Segurança revisada, Logs
  estruturados, Deploy documentado, Restore validado)
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
- `docs/operations/KNOWN_ISSUES.md` — os 10 KIs abertos citados acima
- `docs/operations/INCIDENTS/` — INC-001 e INC-002
