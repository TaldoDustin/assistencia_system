# SPRINT Housekeeping — Rebranding Técnico (TD-12)

**Status:** EM PLANEJAMENTO
**Período:** A definir (início após Fase 0 — Baseline)
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

| Documento | Escopo |
|-----------|--------|
| `AUDIT_REPOSITORY.md` | Estrutura geral de pastas, arquivos soltos, duplicações |
| `AUDIT_BRANCHES.md` | Toda branch local/remota não mergeada — analisada por conteúdo antes de qualquer decisão |
| `AUDIT_LEGACY.md` | Busca automatizada dos termos legados (lista abaixo) em código, comentários, docs, variáveis de ambiente, imports, nomes de pacote, workflows do GitHub Actions, Docker, README, templates, `.env`, URLs, títulos HTML |
| `AUDIT_INFRA.md` | Render, Vercel, variáveis de ambiente em produção, nomes de serviço |
| `AUDIT_DOCUMENTATION.md` | Referências a nomes legados na documentação (`docs/**`, `CLAUDE.md`) |

**Termos legados a buscar (Fase 1):** `assistencia_system`, `assistencia-system`, `IRFlow`, `irflow`,
`IR_FLOW`, `nt-driver`, `nt_driver`, `NT Driver`.

Branches existentes a analisar por conteúdo (situação em 2026-07-31, antes de qualquer merge/delete) —
30+ branches locais, incluindo `chore/*`, `docs/*`, `feat/*`, `hotfix/*`, `test/*`, `release/ux-001`, e
**`demo/commercial-preview`**. Ver regra abaixo.

### Fase 2 — Planejamento

Tabela única consolidando os achados da Fase 1:

| Item | Prioridade | Risco | Ação proposta |
|------|-----------|-------|----------------|
| (preencher a partir das auditorias) | | | |

Nada é removido ou renomeado nesta fase — apenas decidido o que fazer com cada item.

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

Ao final: "Housekeeping Completed" registrado nesta sprint + `PROJECT_STATUS.md` + `CHANGELOG.md`.

---

## Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| RS-01 | Renomear módulo usado em produção sem atualizar todos os imports | Média | Alto | Testes rodam após cada commit de renomeação (Fase 4), nunca em lote |
| RS-02 | Apagar branch com trabalho não mergeado | Baixa | Alto | Regra obrigatória: investigar conteúdo antes de apagar (Fase 3) |
| RS-03 | Variável de ambiente renomeada em código sem atualizar Render/Vercel | Média | Alto | `AUDIT_INFRA.md` mapeia todas as vars antes de qualquer rename (Fase 1) |
| RS-04 | Sprint se estender por muitas sessões e perder contexto | Alta | Médio | Documentação (`BASELINE_HOUSEKEEPING.md`, audits, esta sprint) é a fonte de verdade, não a memória da conversa |

---

## Dependências

- Depende de: nenhuma sprint em andamento bloqueia isto (V1.5 Garantia e Sprint CI/CD 1.1 já concluídas)
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
