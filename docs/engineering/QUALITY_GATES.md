# QUALITY_GATES.md — Contrato de Qualidade

Este documento define os critérios objetivos que um PR deve satisfazer antes de ser aprovado.
Não há espaço para interpretação: cada gate é verdadeiro ou falso.

Um PR com qualquer gate bloqueante em **❌ FALHOU** não entra em `main`.

**Última revisão:** 2026-07-06

---

## Gates Automatizados (CI)

Executados pelo GitHub Actions em todo push e PR.
Falha em qualquer um destes bloqueia o merge automaticamente.

### G-01 — Lint Backend (Ruff)

```bash
ruff check .
```

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Zero erros ou avisos nas regras `E`, `F`, `W`, `I` |
| ❌ FALHOU | Qualquer erro reportado fora das exceções documentadas em `pyproject.toml` |

**Status:** Planejado para Sprint 2  
**Responsável:** CI pipeline

---

### G-02 — Formatação Backend (Ruff Format)

```bash
ruff format --check .
```

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Nenhum arquivo com formatação divergente do padrão |
| ❌ FALHOU | Qualquer arquivo que `ruff format` alteraria |

**Nota:** `ruff format` substitui Black neste projeto. Mesmos resultados, mesma ferramenta.  
**Status:** Planejado para Sprint 2  
**Responsável:** CI pipeline

---

### G-03 — Lint Frontend (ESLint)

```bash
cd frontend && npm run lint
```

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Zero erros ESLint; warnings são permitidos mas não recomendados |
| ❌ FALHOU | Qualquer erro (`error`-level) reportado |

**Status:** Ativo (ESLint configurado, CI pendente)  
**Responsável:** CI pipeline

---

### G-04 — Testes Backend (pytest)

```bash
pytest tests/ --tb=short
```

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | 100% dos testes passando — zero falhas, zero erros |
| ❌ FALHOU | Qualquer teste com status FAILED ou ERROR |

**Status:** Planejado para Sprint 2  
**Responsável:** CI pipeline

---

### G-05 — Cobertura de Testes

```bash
pytest tests/ --cov --cov-fail-under=40
```

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Cobertura global nos módulos alvo >= threshold configurado em `pyproject.toml` |
| ❌ FALHOU | Cobertura caiu abaixo do threshold **ou** cobertura da área modificada < 40% |

**Threshold atual:** 40% (sobe com cada sprint — ver tabela de evolução)  
**Status:** Planejado para Sprint 2  
**Responsável:** CI pipeline

---

### G-06 — Build Frontend

```bash
cd frontend && npm run build
```

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Build completa sem erros |
| ❌ FALHOU | Qualquer erro de compilação ou import inválido |

**Status:** Ativo (build manual)  
**Responsável:** CI pipeline

---

### G-07 — Testes E2E (Playwright)

```bash
cd frontend && npm run test:e2e
```

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Todos os testes Playwright passando |
| ⚠️ NÃO BLOQUEANTE | Falhas em E2E não bloqueiam merge até Sprint 3 |
| ❌ BLOQUEANTE (Sprint 3+) | Qualquer teste E2E falhando |

**Status:** Não-bloqueante (`continue-on-error: true`) até Sprint 3  
**Responsável:** CI pipeline

---

### G-08 — Auditoria de Segurança de Dependências

```bash
# Backend
pip install safety && safety check -r requirements.txt

# Frontend
cd frontend && npm audit --audit-level=high
```

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Zero vulnerabilidades de severidade High ou Critical |
| ⚠️ AVISAR | Vulnerabilidades Low ou Medium — documentar em KNOWN_ISSUES.md |
| ❌ FALHOU | Qualquer vulnerabilidade High ou Critical não resolvida |

**Status:** Planejado para Sprint 2  
**Responsável:** CI pipeline

---

## Gates de Documentação (Manual)

Verificados pelo revisor (ou pelo autor em projeto solo) antes de aprovar.

### G-09 — CHANGELOG atualizado

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | `docs/operations/CHANGELOG.md` tem entrada na seção `[Não lançado]` para qualquer `feat:` ou `fix:` |
| ❌ FALHOU | PR contém `feat:` ou `fix:` sem entrada correspondente no CHANGELOG |
| N/A | PR contém apenas `docs:`, `test:`, `chore:`, `refactor:`, `style:` |

---

### G-10 — PROJECT_STATUS atualizado

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | `docs/operations/PROJECT_STATUS.md` reflete o estado atual (bugs, cobertura, score) |
| ❌ FALHOU | Bug corrigido não foi movido para "Resolvidos" **ou** nova dívida técnica não foi registrada |
| N/A | PR não altera estado do projeto (docs puras, testes isolados) |

---

### G-11 — ADR documentada se decisão arquitetural foi tomada

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Nova ADR em `docs/engineering/adr/` e entrada no índice `ARCHITECTURE_DECISIONS.md` |
| ❌ FALHOU | Mudança de framework, banco, estratégia de deploy ou estrutura de pastas sem ADR correspondente |
| N/A | PR não contém decisão arquitetural |

**Como identificar se é necessária:** se você pensou "poderíamos fazer de outra forma e estamos escolhendo X porque Y" — é uma ADR.

---

### G-12 — Sem segredos ou credenciais

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Nenhuma chave, senha, token ou URL de produção hardcoded no diff |
| ❌ FALHOU | Qualquer segredo detectado no código, mesmo que em comentário ou string de teste |

**Verificar em:** strings com `key`, `token`, `password`, `secret`, `senha`, URLs de produção em código.

---

### G-13 — Sem código de debug

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Nenhum `print()`, `console.log()`, `debugger`, `breakpoint()` ou similar no diff |
| ❌ FALHOU | Qualquer instrução de debug encontrada no código de produção |

---

### G-14 — Commits seguem Conventional Commits

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | 100% dos commits do PR no formato `<tipo>(<escopo>): <descrição>` |
| ❌ FALHOU | Qualquer commit com mensagem no formato livre ("att", "fix", "wip", etc.) |

**Referência:** `docs/engineering/CODE_STYLE.md` — seção Git.

---

## Gates de Revisão de Código (Manual)

Aplicáveis quando houver revisão por par (dois ou mais colaboradores).

### G-15 — Sem lógica duplicada

Novo código não replica lógica já existente em outro módulo.
Consulte `docs/engineering/ENGINEERING_GUIDE.md` — seção DRY.

### G-16 — Complexidade dentro dos limites

Funções Python <= 40 linhas. Componentes React <= 200 linhas.
Consulte `docs/engineering/CODE_STYLE.md` para os limites completos.

### G-17 — Testes novos para código novo

Toda lógica de negócio nova tem cobertura de teste correspondente.
Exceção: código de infraestrutura (migrations, config) pode ser sem teste se o risco for baixo e documentado.

---

## Gates de Processo (Manual)

Aplicável a qualquer sprint de teste, QA ou validação — ver `CLAUDE.md` e `docs/engineering/ENGINEERING_GUIDE.md` §11 (ADR-004).

### G-18 — Achados que atendem critérios de interrupção seguem fluxo `hotfix/`

| Estado | Critério |
|--------|---------|
| ✅ PASSOU | Todo achado que atendeu a algum critério objetivo de interrupção (`ENGINEERING_GUIDE.md` §11) foi corrigido via branch `hotfix/*` própria, a partir de `main`, mergeada em `main` antes da sprint continuar |
| ❌ FALHOU | Achado que atendeu a algum critério foi corrigido direto na branch da sprint, ou não foi corrigido nem reportado |
| N/A | Nenhum achado da sprint atendeu a critério de interrupção — achados, se houver, foram caracterizados por teste e reportados |

**Status:** Ativo a partir de 2026-07-07 (ADR-004) — **não retroativo**, não se aplica a sprints concluídas antes dessa data.
**Responsável:** quem executa a sprint (self-review em projeto solo, revisão por par quando houver mais de um colaborador).

---

## Evolução do Threshold de Cobertura

Cobertura cresce junto com os testes — nunca à frente deles.

| Sprint | Threshold | Escopo |
|--------|-----------|--------|
| Sprint 1 (concluída) | 0% | — |
| **Sprint 2 (atual)** | **0%** | Infraestrutura — primeiros testes ainda sendo escritos |
| Sprint 3 | 20% | login, usuários, sessão |
| Sprint 4 | 40% | auth, OS, preços, shopping |
| Sprint 5 | 60% | + segurança, checklist, estoque |
| Sprint 6 | 70% | + módulos decompostos |
| Sprint 7 | 80% | global |

O threshold é definido em `pyproject.toml`:
```toml
[tool.coverage.report]
fail_under = 0  # atualizar a cada sprint conforme tabela acima
```

---

## Checklist de PR (copie para a descrição)

```markdown
## Quality Gates

### Automatizados (CI)
- [ ] G-01 Ruff lint passou
- [ ] G-02 Ruff format passou
- [ ] G-03 ESLint passou
- [ ] G-04 pytest passou (zero falhas)
- [ ] G-05 Cobertura não regrediu
- [ ] G-06 Build frontend passou
- [ ] G-07 Playwright passou (ou não-bloqueante se Sprint < 3)
- [ ] G-08 Auditoria de dependências (sem High/Critical)

### Documentação
- [ ] G-09 CHANGELOG atualizado (se feat/fix)
- [ ] G-10 PROJECT_STATUS atualizado (se estado mudou)
- [ ] G-11 ADR criada (se decisão arquitetural)
- [ ] G-12 Sem segredos no código
- [ ] G-13 Sem código de debug
- [ ] G-14 Commits em Conventional Commits

### Qualidade (quando revisado por par)
- [ ] G-15 Sem lógica duplicada
- [ ] G-16 Complexidade dentro dos limites
- [ ] G-17 Testes para lógica nova

### Processo (sprints de teste/QA/validação)
- [ ] G-18 Achados que atendem critérios de interrupção viraram `hotfix/*` mergeado em `main` (N/A se nenhum achado atendeu)
```

---

## Status Atual dos Gates

| Gate | Status | Sprint de implementação |
|------|--------|------------------------|
| G-01 Ruff lint | ❌ Ausente | Sprint 2 |
| G-02 Ruff format | ❌ Ausente | Sprint 2 |
| G-03 ESLint | ⚠️ Local apenas | Sprint 2 (CI) |
| G-04 pytest | ❌ Ausente | Sprint 2 |
| G-05 Cobertura | ❌ Ausente | Sprint 2 |
| G-06 Build frontend | ⚠️ Manual | Sprint 2 (CI) |
| G-07 Playwright | ⚠️ Manual | Sprint 3 (bloqueante) |
| G-08 Dep audit | ❌ Ausente | Sprint 2 |
| G-09 CHANGELOG | ⚠️ Manual | Ativo |
| G-10 PROJECT_STATUS | ⚠️ Manual | Ativo |
| G-11 ADR | ⚠️ Manual | Ativo |
| G-12 Sem segredos | ⚠️ Manual | Sprint 2 (git-secrets no CI) |
| G-13 Sem debug | ⚠️ Manual | Ativo |
| G-14 Conventional Commits | ❌ Não enforçado | Sprint 2 (commitlint) |
| G-15 DRY | ⚠️ Manual | Ativo |
| G-16 Complexidade | ⚠️ Manual | Ativo |
| G-17 Testes para novo código | ❌ Não enforçado | Sprint 2 |
| G-18 Hotfix para achados críticos | ⚠️ Manual | Ativo (2026-07-07, ADR-004) |
