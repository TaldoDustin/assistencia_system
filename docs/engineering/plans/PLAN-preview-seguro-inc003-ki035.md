# PLAN-preview-seguro-inc003-ki035 — Preview Seguro (INC-003 Frente B + KI-036 + KI-035)

**Data:** 2026-08-11
**Feature:** Discovery de arquitetura de "Preview seguro" (Operação Release 1.0, Parte B), conduzida em
sessão de 2026-08-11 a partir do handoff em `docs/operations/NEXT_SESSION.md`. Referências de fato:
`docs/operations/INCIDENTS/INC-003-mercadophone-preview-dados-reais.md`, `docs/operations/KNOWN_ISSUES.md`
(KI-035, KI-036).
**Status:** Rascunho

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação — não é mantido atualizado como `ARCHITECTURE.md`
> ou `DATABASE.md`. Se algo aqui continuar relevante depois, promova para o documento vivo correspondente.

**Estado**

- [x] Discovery — aprovada (Discovery de Preview seguro, 2026-08-11: inventário de integrações externas,
      credenciais, identificação de ambiente, migrations, critérios de desbloqueio; decisões do CTO:
      defesa em profundidade, guard cobre todos os background jobs, fix do KI-035 via captura de
      `IntegrityError`, registro do KI-036)
- [ ] Plano Técnico — aguardando aprovação
- [ ] Implementação
- [ ] Testes
- [ ] QA Manual
- [ ] Revisão Arquitetural — obrigatória (toca >3 arquivos: `fluxoly_config.py`, `app.py`,
      `migrations/runner.py`, `docs/`)
- [ ] Encerramento

---

## Objetivo

Impedir que um Render PR Preview repita o INC-003 (herdar credenciais/integrações externas de produção e
executar jobs de background reais) e corrija o KI-036 (Sentry marcando erros de preview como
`environment=production`), introduzindo um sinal de ambiente (`IS_PULL_REQUEST`) que hoje não existe em
lugar nenhum do código. Corrige também o KI-035 (condição de corrida em `migrations/runner.py`), pré-
requisito independente para qualquer boot confiável em múltiplos workers — inclusive o de um preview.
Estas três correções, juntas, são o que o CTO definiu como critério mínimo para reautorizar o Dry-Run 2B.

---

## Escopo

1. Nova constante `IS_PULL_REQUEST` em `fluxoly_config.py`, lida de `os.environ` (Render seta essa
   variável como `"true"`/ausente — comparação case-insensitive).
2. `BACKGROUND_JOBS_ENABLED` (`fluxoly_config.py`) passa a ser `False` automaticamente quando
   `IS_PULL_REQUEST` é verdadeiro, **independente** do valor de `IR_FLOW_ENABLE_BACKGROUND_JOBS` herdado.
   Único ponto de mudança que desliga, ao mesmo tempo, os dois jobs de background hoje existentes — a
   thread de sync do MercadoPhone (`app.py:1013`) e a thread de backup automático (`app.py:485-486`) —
   porque ambas já são gateadas por essa mesma constante.
3. Log explícito no boot (`app.py`, mesmo padrão de log estruturado já usado no projeto) quando
   `IS_PULL_REQUEST` é detectado e background jobs são desligados por causa disso — visibilidade em vez de
   silêncio, para que o comportamento não pareça um bug caso alguém esqueça deste plano no futuro.
4. Sentry (`app.py`, linha ~156): `environment` passa a considerar `IS_PULL_REQUEST` antes de
   `IS_SERVER_RUNTIME`, reportando um valor distinto de `"production"` quando é um preview (KI-036).
5. `migrations/runner.py::run_migrations()`: captura de `sqlite3.IntegrityError` por migration (não pela
   função inteira), tratada como no-op — mesmo idioma já usado para `sqlite3.OperationalError`
   ("locked") — e o loop continua tentando as próximas migrations pendentes no mesmo boot (KI-035).
   **Restrição obrigatória (adicionada após revisão do CTO nesta etapa de aprovação):** a captura precisa
   distinguir especificamente a corrida esperada — violação da `UNIQUE constraint` em
   `schema_migrations.id`, causada pelo `INSERT INTO schema_migrations` da linha 67 — de qualquer outro
   `IntegrityError` que possa ser levantado de dentro de `modulo.apply()` (ex.: uma constraint de negócio
   violada por um backfill de dado real). Só o primeiro caso é no-op seguro; qualquer outro
   `IntegrityError` deve propagar (fail loud), nunca ser silenciosamente engolido — do contrário uma
   falha real de schema/dado ficaria mascarada como "outro worker já aplicou".
6. Documentação (`DEPLOY.md`/`GO_LIVE_PLAN.md`): registrar a recomendação de também desabilitar
   explicitamente `MERCADO_PHONE_SYNC_ENABLED`/`IR_FLOW_ENABLE_BACKGROUND_JOBS` no painel Render ao criar
   qualquer preview futuro — camada de configuração, complementar ao guard de código (defesa em
   profundidade, decisão já tomada pelo CTO em 2026-08-10).

---

## Fora de Escopo

- Reativar o Render PR Preview suspenso (`srv-d9t2ms0u01pc73bmuaqg`) ou mergear/fechar a PR #22.
- Migrar o deploy para `render.yaml`/IaC (hoje é 100% manual via painel) — fora do escopo desta correção.
- Lock de processo mestre único para migrations — opção descartada pelo CTO nesta Discovery em favor da
  captura de `IntegrityError`.
- KI-034 (Financeiro/Vendas) — achado não relacionado, já registrado separadamente.
- Qualquer nova integração externa (pagamentos, webhooks novos) — não existe nenhuma hoje além de
  MercadoPhone/e-mail/Google Drive, já cobertas pelo guard de `BACKGROUND_JOBS_ENABLED`.
- O Dry-Run 2B em si — este plano só remove os dois bloqueadores; reautorizar o Dry-Run é uma decisão
  separada do CTO, depois que este plano estiver implementado, testado e revisado.

---

## Impacto no Banco

Nenhum. Nenhuma tabela/coluna nova, nenhuma migration nova. `migrations/runner.py` muda só o tratamento
de exceção ao aplicar migrations existentes — nenhuma mudança de dado ou schema.

---

## Impacto no Backend

- `fluxoly_config.py`: nova constante `IS_PULL_REQUEST`; `BACKGROUND_JOBS_ENABLED` passa a incorporar
  `and not IS_PULL_REQUEST`. Nenhuma mudança de assinatura pública, nenhum novo import necessário em quem
  já consome `BACKGROUND_JOBS_ENABLED`.
- `app.py`: log estruturado adicional no boot quando `IS_PULL_REQUEST` for verdadeiro; ajuste da linha do
  Sentry (`environment=...`) para usar `IS_PULL_REQUEST` importado de `fluxoly_config.py`. Nenhuma mudança
  na lógica de `iniciar_sync_mercadophone_se_habilitado()`/`iniciar_thread_backup_automatico()` em si —
  elas continuam só lendo `BACKGROUND_JOBS_ENABLED`, que já reflete a nova regra.
- `migrations/runner.py`: `try/except` por migration dentro do loop (hoje é um único `try` para a função
  inteira) — captura `sqlite3.IntegrityError` **só quando a mensagem identifica a constraint
  `schema_migrations.id`** (ex.: checar `"schema_migrations.id" in str(exc)` ou equivalente explícito,
  nunca um `except sqlite3.IntegrityError` genérico) e trata como "outro worker já aplicou esta",
  seguindo para a próxima migration pendente. Qualquer `IntegrityError` que não bata com essa assinatura
  específica propaga normalmente. Preserva o tratamento existente de `OperationalError`/"locked".

---

## Impacto no Frontend

Nenhum. Mudança inteiramente de bootstrap/backend, sem endpoint novo/alterado.

---

## Estratégia de Migração

Não aplicável — sem mudança de schema. Deploy normal (mesmo fluxo de sempre); nenhuma variável de
ambiente nova precisa ser configurada manualmente em produção (`IS_PULL_REQUEST` só existe naturalmente em
previews, é o próprio Render quem seta).

---

## Testes

- `tests/test_ambiente_preview.py` (novo):
  - `IS_PULL_REQUEST=true` → `BACKGROUND_JOBS_ENABLED is False`, mesmo com
    `IR_FLOW_ENABLE_BACKGROUND_JOBS=1` explicitamente setado (prova que o preview vence o override manual
    herdado).
  - `IS_PULL_REQUEST` ausente/`false` → comportamento idêntico ao de hoje (nenhuma regressão em produção
    /dev local/testes).
  - Sentry: `environment` configurado é diferente de `"production"` quando `IS_PULL_REQUEST=true` (teste
    de unidade sobre a função/expressão que monta o valor, sem exigir um DSN real).
- `tests/test_migrations_race.py` (novo ou extensão de teste de migrations existente): simula duas
  conexões concorrentes inserindo o mesmo `id` em `schema_migrations` — confirma que a segunda não
  propaga `IntegrityError` (a chamada retorna normalmente) e que uma migration pendente subsequente,
  sem conflito, ainda é aplicada na mesma chamada de `run_migrations()`. Regressão dedicada: reproduzir
  contra o código anterior à correção (mesmo rigor já usado nos hotfixes de INC-001/INC-002) para provar
  que o teste falha antes e passa depois.
  - **Caso obrigatório adicional (guarda contra falso-negativo):** simular um `IntegrityError` que **não**
    seja a corrida de `schema_migrations.id` (ex.: uma migration fictícia de teste cujo `apply()` viola
    uma `UNIQUE` de dado de negócio) e confirmar que esse erro **propaga** normalmente, não é engolido —
    prova de que a captura é específica, não um `except IntegrityError` genérico.
- Suíte completa (`pytest tests/`) e `ruff check .` confirmados sem regressão antes do merge.

Observação de implementação: `iniciar_sync_mercadophone_se_habilitado()`/`iniciar_thread_backup_automatico()`
são disparadas no nível de módulo (`app.py`, fora de qualquer função testável isoladamente sem reimportar o
módulo) — os testes acima validam a constante `BACKGROUND_JOBS_ENABLED` e o valor de `environment` do
Sentry diretamente, não o efeito colateral do import; isso já é evidência suficiente porque os dois
disparadores só decidem com base nessa constante.

---

## Critérios de Aceite

- [ ] `IS_PULL_REQUEST=true` desliga a thread de sync do MercadoPhone e a de backup automático, mesmo com
      todas as credenciais/flags herdadas de produção — provado por teste automatizado, não só leitura de
      código.
- [ ] Log estruturado no boot confirma quando isso acontece (visível em qualquer ambiente real).
- [ ] Sentry nunca reporta `environment="production"` quando `IS_PULL_REQUEST=true`.
- [ ] `migrations/runner.py` não derruba o boot do worker quando dois processos concorrem pela mesma
      migration; migrations pendentes subsequentes no mesmo boot continuam sendo aplicadas.
- [ ] Teste de regressão do KI-035 confirmado falhando contra o código anterior e passando depois da
      correção.
- [ ] A captura de `IntegrityError` em `migrations/runner.py` é comprovadamente específica à constraint
      `schema_migrations.id` — um `IntegrityError` de outra origem (ex.: violação de dado de negócio
      dentro de `apply()`) propaga e não é mascarado como "outro worker já aplicou".
- [ ] Suíte completa + `ruff check .` sem regressão.
- [ ] Nenhuma mudança de comportamento observável em produção real ou em desenvolvimento local
      (`IS_PULL_REQUEST` nunca é setado nesses ambientes).
- [ ] `DEPLOY.md`/`GO_LIVE_PLAN.md` atualizados com a recomendação de configuração como segunda camada de
      defesa.
- [ ] `KI-035`/`KI-036` movidos para "Resolvidos" em `KNOWN_ISSUES.md`, com data e commit.

---

## Riscos

- **Dependência de um contrato não documentado formalmente pelo Render** (`IS_PULL_REQUEST=true`) — se a
  plataforma mudar o nome/formato da variável no futuro, o guard para de funcionar silenciosamente.
  Mitigação: o log estruturado do item 3 do Escopo torna essa falha visível (ausência do log esperado num
  preview real seria um sinal claro), em vez de descoberta só por incidente.
- **Captura de `IntegrityError` por migration não é um lock real** — evita o crash, mas não impede as
  duas conexões de tentarem aplicar a mesma migration ao mesmo tempo (só a que perde a corrida do INSERT
  é tratada). Aceito deliberadamente (decisão do CTO): a idempotência de cada `apply()` já garante
  convergência eventual, e o objetivo aqui é eliminar o `Worker failed to boot`, não implementar
  coordenação forte entre processos.
- **Captura genérica demais mascararia bug real de dado** — se o `except` não checar a assinatura
  específica da constraint `schema_migrations.id`, uma `IntegrityError` real vinda de dentro de
  `apply()` (ex.: violação de `UNIQUE` de negócio por um backfill malformado) seria silenciosamente
  tratada como "corrida entre workers" e o boot seguiria normalmente com a migration na verdade não
  aplicada corretamente. Mitigado pela restrição já incorporada ao Escopo/Impacto no Backend acima e
  coberta por caso de teste dedicado.
- **`BACKGROUND_JOBS_ENABLED` passa a ter uma segunda razão para ser `False`** — alguém lendo só
  `IR_FLOW_ENABLE_BACKGROUND_JOBS=1` no painel de um preview pode se surpreender que o job não rodou.
  Mitigação: comentário explícito em `fluxoly_config.py` no ponto da mudança, mais o log de boot do item 3.

---

## Rollback

Mudança inteiramente aditiva/condicional em bootstrap — nenhuma migration, nenhum dado tocado. Reverter é
um `git revert` padrão, sem risco de cruzar migration (não há nenhuma neste plano) — segue a política de
Rollback já definida em `docs/company/GO_LIVE_PLAN.md`.

---

## Questões em Aberto

- Nome exato do valor de `environment` a reportar ao Sentry para um preview (`"preview"`? outro nome?) —
  decisão de nomenclatura, não bloqueante para o restante do plano; proposta default é `"preview"` a
  menos que o CTO prefira outro valor.
