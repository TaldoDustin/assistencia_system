# SPRINT Housekeeping — Rebranding Técnico (TD-12)

**Status:** EM ANDAMENTO — Fases 0-2 concluídas em 2026-07-31; Fase 3 (Limpeza/Renomeação) em execução:
Lote 1, Lote 2 e Lote 4 concluídos (2026-08-03); Lote 3 parcial (Categoria B pendente); só resta
`irflow_blueprints_api.py` (Lote 5) com prefixo legado entre os módulos `.py`
**Período:** Iniciada 2026-07-31
**Tipo:** Infraestrutura / Refatoração / Chore

---

## Objetivo

Eliminar a nomenclatura legada `irflow_*` / `IR_FLOW_*` / `assistencia_system` que ainda convive com a
convenção `fluxoly_*` estabelecida na ADR-008 (2026-07-27), e fazer uma limpeza de repositório (branches,
docs obsoletas, scripts mortos, assets não usados) — sem alterar comportamento funcional do sistema.

## Motivação

Esta sprint corresponde ao item **TD-12** já documentado em `docs/operations/PROJECT_STATUS.md`
("Nomenclatura legada... Épico de Rebranding Técnico completo... não escopado nem agendado | Baixo | Baixa").

Decisão explícita do usuário (CTO/Product Architect) em 2026-07-30/31: priorizar este trabalho agora, antes
de retomar features de valor de negócio — mesmo com TD-12 originalmente classificado como Prioridade Baixa,
e mesmo tendo sido dito anteriormente nesta mesma conversa que a próxima sprint deveria voltar a ser de
negócio. Confirmação explícita e informada via pergunta direta: *"Confirma priorizar a Sprint Housekeeping
(rebranding técnico, TD-12) agora, antes de voltar a funcionalidades de negócio?"* → **"Sim, priorizar
agora."**

Custo de não fazer agora: nenhum funcional (é dívida cosmética/organizacional). O custo é de continuar
acumulando módulos mistos (`irflow_*` e `fluxoly_*` lado a lado) à medida que mais features novas chegam,
tornando o rebranding cada vez maior e mais arriscado de fazer depois.

---

## Estrutura (6 Fases)

Cada fase só avança depois que a anterior estiver validada. Nenhuma fase pula direto para exclusão/renomeação
sem passar por auditoria e planejamento antes.

### Fase 0 — Baseline (antes de qualquer mudança)

Ponto de restauração completo antes de tocar em qualquer arquivo.

- [x] Confirmar `main` sincronizada com `origin/main` (checado em 2026-07-31: sim, working tree limpo)
- [x] Confirmar que todos os PRs importantes estão fechados (`gh pr list --state open`: vazio)
- [x] Validar CI verde na `main` (últimos 3 runs: success)
- [x] Validar suíte de testes local (`pytest tests/ --cov`: 682 passed, 65.22%)
- [x] Criar nova tag se houve alteração desde a última (não necessário — `v1.2-cicd-hardening` já cobre o
      commit atual, nenhuma mudança desde então)
- [x] Gerar `docs/operations/SPRINTS/BASELINE_HOUSEKEEPING.md` com snapshot: commit atual, tag, número de
      testes, cobertura, branches existentes (`git branch --list`), estado do CI

### Fase 1 — Auditoria

Documentos de auditoria por categoria em `docs/engineering/audits/` (novos, um por categoria). Apenas
levantamento — nada é alterado nesta fase.

Graphify configurado e validado em 2026-07-31 (`docs/engineering/GRAPHIFY.md`) — a auditoria agora
parte do grafo em vez de grep manual arquivo por arquivo, na seguinte ordem:

1. **Auditoria de nomenclatura legada** (`graphify query`) — quais módulos ainda usam `irflow_*`,
   quais documentos citam `assistencia_system`, quais imports dependem da nomenclatura antiga
2. **Auditoria de dependências** (`graphify query` / `graphify path`) — o que seria impactado por
   renomear cada módulo/arquivo identificado no passo 1
3. **Auditoria de documentação** (Graphify + inspeção manual) — referências a nomes legados que o
   grafo não capturou (ex.: texto solto sem citação estrutural)
4. **Auditoria de branches** (Git, manual) — não delegada ao Graphify; branches não fazem parte do
   corpus indexado

| Documento | Escopo | Fonte | Status |
|-----------|--------|-------|--------|
| `AUDIT_LEGACY.md` | Módulos/docs/imports/env vars/nomes de pacote/workflows/Docker/README/templates/`.env`/URLs/títulos HTML que citam os termos legados (lista abaixo) | Graphify (`query`/`path`) + grep de confirmação | ✅ Concluído |
| `AUDIT_DEPENDENCIES.md` | Impacto de renomear cada item da auditoria de nomenclatura — quem importa, quem chama, quem cita | Graphify (`path`/`explain`) | ✅ Concluído |
| `AUDIT_DOCUMENTATION.md` | Referências a nomes legados na documentação não capturadas estruturalmente pelo grafo | Graphify + inspeção manual | ✅ Concluído |
| `AUDIT_REPOSITORY.md` | Estrutura geral de pastas, arquivos soltos, duplicações | Inspeção manual | ✅ Concluído |
| `AUDIT_BRANCHES.md` | Toda branch local/remota não mergeada — analisada por conteúdo antes de qualquer decisão | Git (manual) | ✅ Concluído |
| `AUDIT_INFRA.md` | Render, Vercel, variáveis de ambiente em produção, nomes de serviço | Inspeção manual (fora do corpus indexado) | ✅ Concluído |

**Fase 1 concluída em 2026-07-31.** Todos os 6 documentos em `docs/engineering/audits/`. Nenhum arquivo
de código alterado durante toda a fase. Achados fora do escopo de nomenclatura, registrados à parte:
KI-029 (bancos versionados no git), decisão de estratégia pendente (`ADR-008` vs. rename direto, ver
Fase 2), e uma lista de itens que exigem confirmação manual nos dashboards Render/Vercel
(`AUDIT_INFRA.md` seção 4).

**Termos legados a buscar (Fase 1):** `assistencia_system`, `assistencia-system`, `IRFlow`, `irflow`,
`IR_FLOW`, `nt-driver`, `nt_driver`, `NT Driver`.

Branches existentes a analisar por conteúdo (situação em 2026-07-31, antes de qualquer merge/delete) —
30+ branches locais, incluindo `chore/*`, `docs/*`, `feat/*`, `hotfix/*`, `test/*`, `release/ux-001`, e
**`demo/commercial-preview`**. Ver regra abaixo.

### Fase 2 — Planejamento

**Concluída em 2026-07-31.** Consolidação dos 6 documentos de auditoria em um plano de execução único.
Nada foi removido, renomeado ou alterado nesta fase — apenas decidido o que fazer com cada item e em
que ordem. A execução em si é a Fase 3 (Limpeza) e a Fase 4 (Renomeação), a seguir.

#### Tabela consolidada

| Item | Origem | Prioridade | Risco | Complexidade | Estratégia | Ação | Decisão necessária | Sprint |
|------|--------|:--:|:--:|:--:|------------|------|---------------------|--------|
| 38 branches locais + 21 remotas já mergeadas | `AUDIT_BRANCHES` | Alta | Baixo | 🟢 | Remoção em lote (`git branch -d`) | Executar | — | Housekeeping |
| `frontend/dist/` desatualizado (4 arquivos) | `AUDIT_REPOSITORY` | Alta | Baixo | 🟢 | Destrackear (já no `.gitignore`) | Executar | — | Housekeeping |
| `database.db-shm`/`database.db-wal` versionados | `AUDIT_REPOSITORY` / KI-029 | Alta | Baixo (ação em si) | 🟢 | Destrackear + ajustar `.gitignore` | Executar | — | Housekeeping |
| 3 entradas mortas em `pyproject.toml` | `AUDIT_DEPENDENCIES` | Alta | Nenhum | 🟢 | Remover direto | Executar | — | Housekeeping |
| 18 módulos `irflow_*.py` de baixo risco | `AUDIT_DEPENDENCIES` | Alta | Baixo | 🟢 | Rename direto, em lotes pequenos + commit de imports em `app.py` | Executar | — | Housekeeping |
| Branding residual frontend (README, `client.js`, `index.css`, senha `irflow@2024` em `app.spec.js`/`debug_shopping.py`) | `AUDIT_DEPENDENCIES` / `AUDIT_REPOSITORY` | Média | Baixo | 🟢 | Rename direto | Executar (confirmar antes que a senha não é credencial real) | — | Housekeeping |
| `irflow_os.py` | `AUDIT_DEPENDENCIES` | Alta | Médio | 🟠 | Rename em lote, com suíte de garantia (V1.5) validada à parte | Executar (depois dos módulos 🟢) | — | Housekeeping |
| `irflow_core.py` | `AUDIT_DEPENDENCIES` | Alta | Médio | 🟠 | Rename em lote, só depois que os dependentes já estiverem estáveis | Executar (por último entre os hubs) | — | Housekeeping |
| `irflow_blueprints_api.py` | `AUDIT_DEPENDENCIES` | Média | Alto | 🔴 | Rename isolado + validação completa | Planejar (decidir se TD-01 vem antes) | CTO | Housekeeping |
| Estratégia geral do rename (ADR-008 alias/fallback vs. rename direto) | `AUDIT_DOCUMENTATION` | Alta | — | — | `ADR-008` é a fonte de verdade por padrão | Confirmar/decidir antes da Fase 4 | CTO | Housekeeping |
| `cleanup_db.py` (raiz) | `AUDIT_REPOSITORY` | Baixa | Baixo | 🟢 | Remover ou justificar | Avaliar | Usuário | Housekeeping |
| 8 scripts em `scripts/` sem referência (prováveis pré-pytest) | `AUDIT_REPOSITORY` | Baixa | Baixo | 🟠 | Comparar cobertura com a suíte pytest atual antes de remover | Avaliar | Usuário | Housekeeping |
| `assets/ir_flow.ico` + `build_exe.ps1`/`build_setup.ps1`/`installer.iss` | `AUDIT_REPOSITORY` / `AUDIT_DEPENDENCIES` | Baixa | Baixo | 🟠 | Remover como bloco único, se confirmado sem uso | Avaliar — distribuição desktop ainda é um canal? | Usuário | Housekeeping |
| `FLY_DATA_DIR` código morto em `app.py` | `AUDIT_REPOSITORY` | Baixa | Baixo | 🟢 | Remover fallback de hospedagem descontinuada | Avaliar (fora do escopo de TD-12, achado incidental) | Usuário | Housekeeping |
| `chore/inc-001-instrumentacao-conexoes` (branch) | `AUDIT_BRANCHES` | Baixa | Baixo | 🟠 | Remover (precisa `-D`, não `-d`) | Confirmar antes de forçar remoção | Usuário | Housekeeping |
| `origin/ajuste-render-webhook`, `origin/refactor/system-audit`, `origin/worktree-quizzical-cuddling-stardust` (branches remotas) | `AUDIT_BRANCHES` | Baixa | Baixo | 🟢 | Remover (`git push origin --delete`) | Executar | — | Housekeeping |
| `docs/company-sales-materials` (branch) | `AUDIT_BRANCHES` | Média | Baixo | 🟠 | Não é limpeza — é decisão de negócio (mergear, revisar, ou descartar deliberadamente) | Avaliar | Product Owner | Product (fora da Housekeeping) |
| Variáveis `IR_FLOW_*` (14) | `AUDIT_LEGACY` / `AUDIT_INFRA` | Média | Alto | 🔴 | Alias `FLUXOLY_*` com fallback (`ADR-008`) | Adiar — janela coordenada com o Render | CTO / DevOps | Pós-Housekeeping |
| Repositório GitHub + URLs Render/Vercel | `AUDIT_DEPENDENCIES` / `AUDIT_DOCUMENTATION` | Baixa (sem prazo definido) | Alto | 🔴 | Janela de manutenção antes do lançamento comercial (já em `ADR-006`/`ADR-008`/`BRAND_IDENTITY.md`) | Adiar | CTO | Ligado a `RELEASE_1.0_MASTER_CHECKLIST.md`, não à Housekeeping |
| Confirmação manual Render/Vercel (`IR_FLOW_DATA_DIR` setada?, build settings, webhooks MercadoPhone) | `AUDIT_INFRA` | Média | — | — | Levantamento nos dashboards | Confirmar | DevOps | Pós-Housekeeping |
| Bancos versionados no git (KI-029, incl. `-shm`/`-wal`) | `AUDIT_REPOSITORY` | Alta (mas não é execução mecânica) | Alto | 🔴 | Decidir: `git rm` vs. reescrever histórico vs. avaliar sensibilidade real | Adiar — iniciativa própria de segurança | CTO / Segurança | Fora da Housekeeping (ver KI-029) |

#### Ordem de implementação proposta (lotes de commits, menor para maior risco)

1. **✅ Lote 1 — limpeza mecânica sem dependência de código (CONCLUÍDO em 2026-07-31)**
   (`chore(repo): ...`): 40 branches locais + 21 remotas mergeadas removidas (incluindo
   `feat/produtos-catalogo`, que exigiu investigação individual — commit exclusivo local não pushado
   à própria remote-tracking, mas já confirmado ancestral de `main`, removida com `-D` só depois dessa
   confirmação); `frontend/dist/` destrackeado (`dea6fb9`); `database.db-shm`/`database.db-wal`
   destrackeados e `.gitignore` ajustado para `database.db*` (`5291c37`, fecha a lacuna do KI-029 sem
   tocar nos dois backups, que continuam decisão em aberto); 3 entradas mortas removidas de
   `pyproject.toml` (`9eb9344`, confirmado antes que os módulos foram excluídos deliberadamente no
   commit `a655695`, fix de segurança CSRF). `ruff check .` limpo e 682 testes passando após cada
   commit. Branches restantes: `demo/commercial-preview` (preservada), `docs/company-sales-materials`
   (decisão de Product), `chore/inc-001-instrumentacao-conexoes` + `origin/ajuste-render-webhook` +
   `origin/refactor/system-audit` + `origin/worktree-quizzical-cuddling-stardust` (Lote 6, aguardando
   confirmação do usuário).
2. **✅ Lote 2 — módulos 🟢, em grupos pequenos (CONCLUÍDO em 2026-08-03)** (`refactor(rebrand): ...`,
   um commit por grupo de domínio): `clientes` (`8a085f8`), `produtos` (`468315b`), `unidades_serializadas`
   (`558a47c`), `validation`/`audit`/`reference_data`/`price_tables`/`mercadophone` (`f301d62`),
   `logging`/`web`/`blueprints_auth`/`blueprints_main`/`rate_limit`/`reports`/`storage` (`c04bd29`).
   Todos os 18 módulos 🟢 identificados em `AUDIT_DEPENDENCIES.md` estão renomeados; só restam
   `irflow_core.py`, `irflow_os.py` (Lote 4) e `irflow_blueprints_api.py` (Lote 5) com o prefixo legado.
3. **Lote 3 — branding frontend (parcial, concluído em 2026-08-03)** (`refactor(rebrand): ...`):
   - ✅ **Categoria A — texto/comentários puros** (`06264d7`): título de `frontend/README.md`,
     comentário da paleta em `frontend/src/index.css`, comentário de cabeçalho e 5 prefixos de log
     `[IR Flow]` → `[Fluxoly]` em `frontend/src/api/client.js`. Zero risco funcional, sem mudança de
     comportamento.
   - ⏸️ **Categoria B — senha de seed `irflow@2024` (pendente, decisão do CTO)**: toca `app.py:1346`
     (seed do usuário `admin` padrão) além de `scripts/debug_shopping.py`, `smoke_test_full.py`,
     `test_routes.py`, `test_shopping_list.py`, `frontend/tests/e2e/app.spec.js` e
     `docs/engineering/TESTING.md:187`. Confirmado como senha de seed local/dev (não é credencial real
     de nenhum ambiente — `TESTING.md` já a documenta como tal), mas como muda o valor efetivo da
     senha padrão e toca `app.py`, requer plano apresentado e aprovação explícita antes de executar
     (regra do `CLAUDE.md` para mudanças em `app.py`), incluindo decidir a nova senha de seed.
   - Fora do Lote 3 (não confundir com branding): `frontend/playwright.config.js`
     (`IR_FLOW_NO_BROWSER`/`IR_FLOW_PORT`) pertence ao grupo de variáveis `IR_FLOW_*` adiado para
     janela pós-Housekeeping; comentários em `frontend/src/lib/constants.js` e
     `frontend/src/pages/Users.jsx` que citam `irflow_core.py` pelo nome pertencem ao Lote 4, junto do
     rename do próprio arquivo; a URL `irflow-backend.onrender.com` em `README.md` (raiz) é
     infraestrutura Render, fora do escopo desta sprint.
4. **✅ Lote 4 — hubs 🟠 (CONCLUÍDO em 2026-08-03)**: `irflow_os.py` → `fluxoly_os.py` primeiro
   (`80a3b31`), depois `irflow_core.py` → `fluxoly_core.py` (`f51e195`), cada um em commit isolado.
   Antes de cada rename, `graphify explain` + grep de confirmação validaram o mapa de dependências
   contra `AUDIT_DEPENDENCIES.md` (nenhuma divergência nas duas rodadas); depois de cada rename,
   `ruff check .`, suíte completa (681 passed / 1 failed — KI-030, ambiente, não relacionado) e
   reindexação do Graphify confirmando o mesmo grafo. Comentários frontend que citavam os dois módulos
   (`Users.jsx`, `constants.js`) atualizados junto de cada rename.
5. **Lote 5 — `irflow_blueprints_api.py` (🔴)**: isolado, sozinho, com validação completa antes de
   seguir — decisão prévia sobre TD-01 necessária.
6. **Lote 6 — itens que exigem confirmação do usuário antes de executar**: `cleanup_db.py`, scripts de
   `scripts/`, bloco de build desktop, `FLY_DATA_DIR`, as 4 branches que precisam de remoção forçada ou
   confirmação.
7. **Fora desta sprint** (registrados, não executados aqui): env vars `IR_FLOW_*` + infraestrutura
   externa (janela de manutenção própria, ligada ao lançamento comercial), `docs/company-sales-materials`
   (decisão de Product), KI-029 (iniciativa de segurança própria).

Cada lote passa pela suíte de testes antes do próximo começar — nunca acumular múltiplos lotes em
trânsito simultaneamente (mesma disciplina já aplicada em `AUDIT_DEPENDENCIES.md`).

**Decisão de estratégia obrigatória nesta fase (achado de `AUDIT_DOCUMENTATION.md`):** `ADR-008`
(2026-07-27, já aceita) propõe alias/fallback temporário para infraestrutura e variáveis de ambiente,
diferente do "rename direto" inicialmente esboçado em `AUDIT_DEPENDENCIES.md`. **`ADR-008` é a fonte de
verdade por padrão** — a Fase 4 não segue automaticamente "rename direto" só porque foi a primeira
sugestão. Se, ao planejar, a decisão for by-passar a estratégia da ADR, **a ADR precisa ser atualizada
antes da execução** (nova decisão registrada, não uma divergência silenciosa entre documentação e
código).

### Fase 3 — Limpeza

Commits pequenos e atômicos, `chore(...)`, cada um revisável isoladamente:

- `chore(repo): remove merged branches references`
- `chore(docs): remove obsolete documentation`
- `chore(repo): remove dead scripts`
- `chore(repo): remove unused assets`
- `chore(repo): remove legacy files`

**Regras obrigatórias desta fase:**
- Nunca apagar uma branch sem antes investigar seu conteúdo (`git log`, `git diff main...branch`).
- `demo/commercial-preview` é **preservada por enquanto** — não removida, não mergeada integralmente.
- Apenas branches confirmadas como mergeadas ou obsoletas (por conteúdo, não por nome) são removidas.

### Fase 4 — Renomeação

Commits pequenos, `refactor(...)`, cada um validado por testes antes do próximo:

1. Renomear módulos Python (`irflow_*.py` → `fluxoly_*.py`)
2. Atualizar imports em todo o repositório
3. Atualizar nomes de pacote (`known_first_party` em `pyproject.toml`, `pytest` config)
4. Atualizar referências em documentação (`docs/**`, `CLAUDE.md`)
5. Atualizar branding visível em UI (se houver strings residuais `IRFlow`/`IR Flow`)

Cada passo roda a suíte de testes antes de avançar para o próximo — nunca acumular múltiplos renomeios
sem validar entre eles.

### Fase 5 — Validação

Checklist completo antes de declarar a sprint concluída:

- [ ] Testes passando (100% da suíte, sem skip novo)
- [ ] Lint (Ruff) sem erros novos
- [ ] CI verde (todos os jobs bloqueantes: Lint, Backend Tests, Frontend Quality, Frontend Build,
      Coverage Report, Docker Build)
- [ ] Cobertura não regrediu (mínimo 60%, ver `pyproject.toml`)
- [ ] Build do frontend sem erros (`npm run build`)
- [ ] `docker build .` sem erros
- [ ] Deploy validado (Render + Vercel) — sem quebra em produção
- [ ] Sentry sem novos erros pós-deploy
- [ ] Nenhum link/badge/URL/imagem quebrado em `README.md` ou docs
- [ ] Nenhum import quebrado, nenhum script órfão referenciando nome antigo
- [ ] **Reindexação do Graphify** (`graphify . --update` ou rebuild completo) e nova consulta pelos
      mesmos termos legados da Fase 1 (`assistencia_system`, `IRFlow`, `irflow`, `IR_FLOW`, `nt-driver`,
      `NT Driver`). Se a reindexação ainda encontrar referências relevantes, a migração ficou
      incompleta — volta para a Fase 4 nesses pontos específicos antes de fechar a sprint. Isso torna
      o grafo uma ferramenta de verificação do resultado, não só de descoberta do trabalho.

Ao final: "Housekeeping Completed" registrado nesta sprint + `PROJECT_STATUS.md` + `CHANGELOG.md`.

---

## Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| RS-01 | Renomear módulo usado em produção sem atualizar todos os imports | Média | Alto | Testes rodam após cada commit de renomeação (Fase 4), nunca em lote |
| RS-02 | Apagar branch com trabalho não mergeado | Baixa | Alto | Regra obrigatória: investigar conteúdo antes de apagar (Fase 3) |
| RS-03 | Variável de ambiente renomeada em código sem atualizar Render/Vercel | Média | Alto | `AUDIT_INFRA.md` mapeia todas as vars antes de qualquer rename (Fase 1) |
| RS-04 | Sprint se estender por muitas sessões e perder contexto | Alta | Médio | Documentação (`BASELINE_HOUSEKEEPING.md`, audits, esta sprint) é a fonte de verdade, não a memória da conversa |
| RS-05 | Auditoria de nomenclatura via Graphify não capturar 100% das referências (arestas "dangling" — ver `docs/engineering/GRAPHIFY.md`) | Média | Médio | Grep de confirmação sobre os termos legados além da consulta ao grafo (Fase 1); reindexação de validação confirma cobertura na Fase 5 |

---

## Dependências

- Depende de: nenhuma sprint em andamento bloqueia isto (V1.5 Garantia e Sprint CI/CD 1.1 já concluídas).
  Graphify configurado e validado em 2026-07-31 (`docs/engineering/GRAPHIFY.md`) antes do início da Fase 1.
- Bloqueia: nada tecnicamente, mas adia o retorno a features de valor de negócio (decisão consciente do
  usuário)

---

## Definition of Done

- [ ] Todas as 6 fases concluídas na ordem
- [ ] Nenhum termo legado remanescente fora de contexto histórico (changelog/ADRs antigos podem mantê-los)
- [ ] `demo/commercial-preview` preservada intacta
- [ ] Testes obrigatórios passando, CI verde, cobertura não regrediu
- [ ] `CHANGELOG.md`, `PROJECT_STATUS.md`, `KNOWN_ISSUES.md` atualizados
- [ ] TD-12 movido para "Resolvido" em `PROJECT_STATUS.md` com data e commit

---

## Retrospectiva (preencher ao concluir)

### O que funcionou bem

### O que poderia ter sido melhor

### Lições aprendidas para a próxima sprint

### Dívida técnica gerada (se houver)

| ID | Descrição | Prioridade |
|----|-----------|-----------|
