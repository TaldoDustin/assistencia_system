# PLAN-Observabilidade-Sentry-Frontend — Completar Sentry (backend) + Integrar Sentry (frontend)

**Data:** 2026-07-30
**Feature:** `docs/operations/KNOWN_ISSUES.md` TD-02 (Sentry integrado mas inativo, `SENTRY_DSN` vazia);
`docs/operations/SPRINTS/SPRINT_OBSERVABILIDADE.md` (integração de backend original, 2026-07-25)
**Status:** Aprovado pelo CTO (2026-07-30)

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação — não é mantido atualizado como `ARCHITECTURE.md`
> ou `DATABASE.md`. Se algo aqui continuar relevante depois, promova para o documento vivo correspondente.

**Estado**

- [x] Discovery — não formal (não há regra de negócio nova, é infraestrutura); escopo alinhado direto
      com o CTO em conversa (conta Sentry já criada, dois projetos — `fluxoly-backend`/`fluxoly-frontend`,
      sem staging)
- [x] Plano Técnico — aprovado (2026-07-30)
- [x] Implementação
- [x] Testes
- [ ] QA Manual
- [ ] Revisão Arquitetural — recomendada (toca `app.py`, mas é aditivo e de baixo risco; não reverte
      comportamento nem combina com feature de negócio nova)
- [ ] Encerramento

---

## Objetivo

Fechar o gap de observabilidade real: o backend já tinha Sentry integrado desde a Sprint Observabilidade
(2026-07-25), mas inativo (`SENTRY_DSN` vazia, TD-02) e sem `environment`/`release`; o frontend nunca teve
nenhuma integração. Sem isso, uma exceção em produção só é descoberta se um usuário reportar.

---

## Escopo

- Backend: `environment` e `release` no `sentry_sdk.init()` já existente em `app.py`.
- Frontend: integração nova completa (`@sentry/react`), com `ErrorBoundary` de fallback.
- `release` dos dois lados via git commit injetado automaticamente pela plataforma de deploy
  (`RENDER_GIT_COMMIT`/`VERCEL_GIT_COMMIT_SHA`), sem exigir versionamento manual.

## Fora de Escopo

- `before_send` / filtro de erros conhecidos — `FlaskIntegration` já só captura exceção não tratada
  (5xx real), não as respostas `err(...)` deliberadas (400/401/403) que a API já usa; sem ruído real
  observado ainda para justificar um filtro agora (YAGNI).
- Alertas/notificação (e-mail, Slack) — configuração no painel do Sentry, não no código; fica para o CTO
  decidir depois que os primeiros eventos reais chegarem.
- Session Replay / tracing de performance (`tracesSampleRate` acima de 0) — mesma decisão já tomada no
  backend em 2026-07-25, mantida também no frontend.
- Correção das 7 vulnerabilidades reportadas por `npm audit` após instalar `@sentry/react` — confirmado
  que já existiam em `main` antes desta mudança (cadeia `eslint`→`minimatch`→`brace-expansion` e
  `react-router-dom`), nenhuma versão mudou por causa do `@sentry/react`; fora de escopo desta sprint.

---

## Impacto no Banco

Nenhum.

---

## Impacto no Backend

- `app.py`: `sentry_sdk.init()` ganha `environment=("production" if IS_SERVER_RUNTIME else "development")`
  (reaproveita a variável já usada em todo o resto do arquivo) e `release=os.environ.get("RENDER_GIT_COMMIT", "dev")`.
  `send_default_pii=False`/`traces_sample_rate=0` mantidos sem alteração.

## Impacto no Frontend

- `frontend/package.json`: dependência nova `@sentry/react@^10.69.0`.
- `frontend/src/main.jsx`: `Sentry.init()` condicional a `VITE_SENTRY_DSN` (mesmo padrão opcional do
  backend); `environment` via `import.meta.env.PROD` (nativo do Vite); `release` via
  `import.meta.env.VITE_SENTRY_RELEASE`; `App` envolvido em `Sentry.ErrorBoundary` com fallback simples
  ("Algo deu errado, recarregue a página") em vez de tela branca crashada.
- `frontend/vite.config.js`: `define` injeta `VITE_SENTRY_RELEASE` a partir de `VERCEL_GIT_COMMIT_SHA`
  (variável de sistema da Vercel, disponível em build) — não exige configuração manual na Vercel além do
  `VITE_SENTRY_DSN`.
- `frontend/.env.example` (novo arquivo — não existia antes) documentando `VITE_SENTRY_DSN`.

---

## Estratégia de Migração

Sem schema. Deploy: nada muda automaticamente até o `SENTRY_DSN` (backend) e `VITE_SENTRY_DSN` (frontend)
serem configurados nos respectivos dashboards (Render/Vercel) — até lá, o comportamento é idêntico a hoje
(Sentry segue desligado), então o merge em si não é arriscado.

---

## Testes

- `tests/test_sentry_init.py`: 2 casos novos — `environment`/`release` passados corretamente ao
  `sentry_sdk.init()` (via fake do módulo inteiro em `sys.modules`, não a rede real) e fallback de
  `release` para `"dev"` quando `RENDER_GIT_COMMIT` está ausente. Os 2 testes originais preservados.
- Sem teste automatizado para o frontend (SDK de terceiro, comportamento de inicialização condicional
  trivial) — coberto pelo QA Manual (disparo de exceção real).

---

## Critérios de Aceite

- [x] `ruff check .` / `npm run lint` / `npm run build` sem erros novos
- [x] Suíte de testes sem regressão (só a falha pré-existente e não relacionada de `test_sentry_init.py`
      em ambiente Windows local)
- [ ] Uma exceção proposital no backend aparece no painel do Sentry (projeto `fluxoly-backend`), com
      `environment`/`release` corretos
- [ ] Uma exceção proposital no frontend aparece no painel do Sentry (projeto `fluxoly-frontend`), com
      `environment`/`release` corretos
- [ ] Nenhum código de teste/gatilho de exceção proposital permanece no repositório após o QA Manual

---

## Riscos

| Risco | Mitigação |
|---|---|
| DSN vazando em log ou repositório | Nunca escrito em arquivo versionado; só em `.env` local (gitignored) ou direto nos dashboards Render/Vercel |
| Sentry capturar dado sensível de cliente (nome, IMEI) no frontend | `sendDefaultPii` não habilitado (default `false` no SDK JS), sem Session Replay, mesmo cuidado já validado no backend |
| Volume de eventos estourar o plano gratuito do Sentry | Fora de escopo mitigar agora — plano free tier escolhido deliberadamente para observar volume real antes de decidir sobre plano pago |

---

## Rollback

Reverter o commit é suficiente dos dois lados — nenhuma migração, nenhum dado persistido. Enquanto
`SENTRY_DSN`/`VITE_SENTRY_DSN` não estiverem configurados nos dashboards, o código sequer inicializa o SDK.

---

## Questões em Aberto

Nenhuma questão de negócio — é infraestrutura pura, sem decisão de produto envolvida.
