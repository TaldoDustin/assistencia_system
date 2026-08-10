# NEXT_SESSION — Onde retomar

**Última atualização:** 2026-08-10
**Estado do repositório:** `main` limpa, sincronizada com `origin/main` em `99ee94e`, CI 6/6 verde.

> Este arquivo é o ponto de partida rápido da próxima sessão — não substitui `PROJECT_STATUS.md`
> (estado vivo completo), `KNOWN_ISSUES.md` (lista de bugs) nem `docs/operations/INCIDENTS/` (incidentes).
> Sempre releia os três antes de agir, conforme o protocolo deste `CLAUDE.md`.

---

## Estado do Git

```
main         99ee94ebe7b2b9c3de07547928f2e1ca23e0d1cb
origin/main  99ee94ebe7b2b9c3de07547928f2e1ca23e0d1cb
CI            6/6 verde
working tree  limpa
```

**Branches locais preservadas, não apagar sem decisão explícita** (evidência do Dry-Run de Rollback):
- `dry-run/rollback-f5fdb23` — Dry-Run 1A (mecanismo Git/local, sem conflito)
- `dry-run/rollback-872496e` — Dry-Run 1B, caminho sem conflito (commit real revertido com sucesso)
- `test/render-preview-isolation` (local + `origin/test/render-preview-isolation`) — base da PR #22

**PR #22** (`https://github.com/TaldoDustin/assistencia_system/pull/22`) — **aberta, não mergeada, não
fechada** — preserva evidência do INC-003. Não fechar/mergear sem decisão explícita.

**Render PR Preview** (`srv-d9t2ms0u01pc73bmuaqg`, associado à PR #22) — **suspenso** desde
2026-08-10 17:08. Não reativar sem decisão explícita da Frente B (correção arquitetural).

---

## O que foi concluído nesta sessão (2026-08-10)

Sessão inteira dedicada à **Operação Release 1.0 — Parte B, item Rollback**, a partir do handoff da
sessão anterior (Restore validado, `04cece3`).

### 1. Política de Rollback definida (commit `b04216f`)
Escopo coordenado (backend+frontend), critério de acionamento, autoridade exclusiva do CTO, regra de
interação com migrations (nunca cruza uma já aplicada — TD-03 roll-forward only), mecanismo (`git revert`
+ `git push`), verificação (smoke test manual). Documentado em `docs/company/GO_LIVE_PLAN.md` e
`DEPLOY.md`.

### 2. Dry-Run 1A — mecanismo Git/local, sem conflito (branch `dry-run/rollback-f5fdb23`)
Reverteu `tests/test_backup_restore.py` (commit `f5fdb23`) sem conflito. Testes (7/7) e `ruff check`
verdes após o revert. Validou o mecanismo isoladamente.

### 3. Dry-Run 1B — caminho com conflito real (commit `d7ef012`)
Usou `609619f` (fix de UI real): código reverteu limpo, mas `docs/operations/KNOWN_ISSUES.md`
(append-only) gerou conflito real — resolvê-lo exigiria decisão de conteúdo, não é operação mecânica.
`git revert --abort` executado, `main`/`origin/main` nunca tocadas. **Levou à nova regra formal**:
qualquer conflito durante rollback é condição de parada (cobre qualquer tipo de arquivo) — não resolver
automaticamente, informar o CTO, aguardar decisão explícita.

### 4. Dry-Run 1B — caminho sem conflito (branch `dry-run/rollback-872496e`)
Usou `872496e` (fix de responsividade do Dashboard): revert sem conflito, lint/build idênticos ao
baseline. Confirma que o mecanismo funciona de ponta a ponta quando o candidato é bem escolhido.

### 5. KI-035 registrado (commit `2fa3b3c`)
Durante deploy manual de `d7ef012` em produção (Render), condição de corrida real em
`migrations/runner.py::run_migrations()` — dois workers Gunicorn tentando aplicar migrations pendentes
simultaneamente, um recebe `sqlite3.IntegrityError` não capturado pelo tratamento existente de "database
is locked". Segunda tentativa de deploy teve sucesso (corrida intermitente). Também descoberto e
corrigido no processo: **Render estava com auto-deploy travado desde 3 de agosto** (GitHub App sem
autorização completa) — reautorizado, auto-deploy confirmado funcionando de novo.

### 6. INC-003 — dado real importado no Render PR Preview (commit `99ee94e`)
Dry-Run 2A (validar se o Preview seria seguro para o Dry-Run 2B de rollback de infraestrutura): PR #22
provisionou um preview que herdou `MERCADO_PHONE_SYNC_ENABLED`/`MERCADO_PHONE_API_TOKEN` de produção
(comportamento documentado do Render) e importou **405 Ordens de Serviço reais** do MercadoPhone em 4
ciclos de sincronização. Disco/banco do preview permaneceram fisicamente isolados de produção o tempo
todo — o problema foi herança de credenciais de integração externa, não vazamento de disco. Nenhuma
escrita de volta ao MercadoPhone (confirmado por leitura de código, só 2 call sites, ambos de leitura).
KI-035 foi reproduzido de forma independente no primeiro boot deste mesmo preview. **Contido**: preview
suspenso, PR mantida aberta para preservar evidência, produção confirmada intocada. Relatório completo em
`docs/operations/INCIDENTS/INC-003-mercadophone-preview-dados-reais.md`.

---

## Decisões tomadas (CTO, 2026-08-10)

- Rollback é sempre coordenado (backend+frontend juntos).
- Só o CTO autoriza rollback real — Claude nunca executa sem aprovação explícita a cada ocorrência.
- Conflito durante `git revert` = parada obrigatória, qualquer tipo de arquivo.
- `demo/commercial-preview` (branch antiga) não deve ser usada como base de nenhum teste — defasada.
- Render PR Preview, modo **Manual** (`[render preview]` no título ou label `render-preview`), não
  Automatic.
- Preferência por defesa em profundidade para a correção do INC-003: configuração **e** guard de código,
  não só uma das duas.

## Decisões pendentes

1. **Correção do INC-003** (Frente B) — como impedir que um preview futuro herde credenciais/integrações
   externas de produção. Não implementada ainda.
2. **Correção do KI-035** — capturar `sqlite3.IntegrityError` explicitamente, ou coordenar migrations via
   lock/processo mestre único. Não implementada ainda — decisão de arquitetura pendente.
3. Destino final do preview suspenso e da PR #22 (quando a investigação for considerada encerrada).
4. Se/quando destravar o Dry-Run 2B — bloqueado por INC-003 + KI-035, ambos precisam de decisão de
   correção antes.

---

## Estado da Release 1.0 (checklist)

- Rollback testado: 🟡, **40%** (mantido — política mais robusta, mas rollback de infraestrutura ainda
  não validado de ponta a ponta; ver raciocínio em `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md`).
- Operação geral: ~30%. Release 1.0 geral: ~61%. Nenhum desses números foi alterado pelo INC-003 (decisão
  explícita — achado de infraestrutura, não conclusão adicional do teste).
- Manual do usuário, Ambiente de demonstração, Piloto/homologação: sem decisão, como antes.

---

## Próximo passo exato

**Discovery/decisão da arquitetura de Preview seguro**, incorporando o aprendizado do INC-003 e do
KI-035, **antes** de qualquer nova tentativa de Dry-Run 2B. Opções já esboçadas no relatório do INC-003
(seção 9): configuração (desabilitar credenciais externas no preview), guard de código
(`if IS_PULL_REQUEST: não iniciar jobs externos`), ou as duas juntas (preferência já registrada do CTO).

## O que NÃO fazer ainda

- Não reativar o Render PR Preview (`srv-d9t2ms0u01pc73bmuaqg`).
- Não fechar/mergear a PR #22.
- Não remover os 405 registros importados no preview (evidência preservada).
- Não implementar a correção do INC-003 nem do KI-035 sem uma decisão de arquitetura explícita primeiro.
- Não iniciar o Dry-Run 2B enquanto os dois bloqueadores (INC-003, KI-035) não tiverem correção decidida.
- Não avançar para Manual/Demo/Piloto — a ordem de prioridade (Rollback primeiro) continua valendo.

## Issues abertos relevantes

`KI-035` (condição de corrida em migrations, reproduzida 2×) e `INC-003` (dado real importado em preview,
contido) são os dois itens mais recentes e mais relevantes para a próxima sessão. Lista completa de KIs
abertos em `docs/operations/KNOWN_ISSUES.md` (sem alteração nesta sessão além do KI-035).
