# INC-003 — Render PR Preview importou dados reais de produção via integração MercadoPhone

**Status:** 🔴 Contido — causa identificada, correção pendente (Frente B, não implementada)
**Data do incidente:** 2026-08-10
**Severidade:** Alta (contida rapidamente, sem evidência de efeito externo ou impacto em produção)
**Descoberto durante:** Dry-Run 2A (Operação Release 1.0, Parte B — validação de isolamento do Render PR
Preview antes de autorizar o Dry-Run 2B de rollback de infraestrutura)

---

## 1. Resumo

Ao provisionar um Render PR Preview (PR #22, `[render preview]` no título, modo Manual) para validar se
esse ambiente seria seguro para exercitar o procedimento de rollback contra infraestrutura real, o
preview herdou — sem nenhuma ação deliberada nossa — as variáveis de ambiente
`MERCADO_PHONE_SYNC_ENABLED` e `MERCADO_PHONE_API_TOKEN` do serviço de produção (`irflow-backend`),
comportamento documentado do Render ("Preview instances copy all of their settings over from their base
service when they're first created. This includes environment variables, such as database connection
information."). A thread de sincronização automática do MercadoPhone (`iniciar_sync_mercadophone_se_habilitado()`,
disparada incondicionalmente no boot de `app.py`) iniciou sozinha e importou **405 Ordens de Serviço
reais** da API externa do MercadoPhone para o banco isolado do preview, em pelo menos 4 ciclos completos
de sincronização, antes de ser detectado e contido.

**O banco/disco do preview permaneceu fisicamente isolado do de produção o tempo todo** — o problema não
foi vazamento de disco, foi herança de credenciais de integração externa.

---

## 2. Timeline (horários UTC, confirmados por logs do Render)

| Horário (UTC) | Evento |
|---|---|
| 19:50:xx | PR #22 criada, título `[render preview] test(infra): Dry-Run 2A isolation test`; Render detecta e provisiona o preview (`srv-d9t2ms0u01pc73bmuaqg`) |
| 19:51:00–19:51:24 | Primeiro deploy do preview falha com `sqlite3.IntegrityError` (mesma condição de corrida do KI-035, reproduzida) — worker não sobe |
| 19:53:08 | Segundo deploy (manual, retry) inicia |
| 19:53:22 | Instância sobe; thread `mercadophone-sync` inicia (`mercadophone_sync_ignorada_lock_ocupado` — worker 2 aguardando lock do worker 1) |
| 19:53:27 | `Your service is live` — preview disponível em `https://irflow-backend-pr-22.onrender.com` |
| 19:53:52 | Job de backup automático também roda dentro do preview (`backup_automatico_criado`, achado secundário — ver seção 6) |
| ~19:54–19:58 | Ciclo de sincronização em andamento (múltiplas tentativas de lock registradas) |
| **19:58:14** | **`mercadophone_sync_resumo`: `importadas: 405, atualizadas: 0`** — primeira sincronização completa |
| 19:58:49 | `mercadophone_os_atualizada` (os_id: 3, campo `status`) — enriquecimento local pós-import |
| 19:59:19–19:59:30 | Checagens nossas de `/health`/`/ready` (não relacionadas ao incidente) |
| **20:00:14** | `mercadophone_sync_resumo`: `importadas: 0, atualizadas: 405` — segundo ciclo (incremental) |
| **20:03:33** | `mercadophone_sync_resumo`: `importadas: 0, atualizadas: 405` — terceiro ciclo |
| 20:04:10 | `mercadophone_os_atualizada` (os_id: 5, campo `status`) |
| **20:05:34** | `mercadophone_sync_resumo`: `importadas: 0, atualizadas: 405` — quarto ciclo |
| **20:08:43** | Preview suspenso (autorização explícita do CTO) — workers encerrados, sincronização parada |

Total: **~18 minutos** entre o preview ficar "live" e a contenção. Nenhum erro de rede/exceção registrado
em nenhum dos ciclos (`mercadophone_sync_falha_rede`/`mercadophone_sync_falha_inesperada` não aparecem
nos logs desta janela).

---

## 3. Causa raiz

`app.py:1006-1034`:

```python
def iniciar_sync_mercadophone_se_habilitado():
    ...
    if not BACKGROUND_JOBS_ENABLED:
        return
    if not (MERCADO_PHONE_SYNC_ENABLED and MERCADO_PHONE_API_TOKEN):
        return
    sync_thread = threading.Thread(
        target=loop_sincronizacao_mercado_phone, ..., daemon=True, name="mercadophone-sync",
    )
    sync_thread.start()
    ...

# Em produção (Render/Gunicorn), o módulo é importado sem passar por __main__.
# Por isso iniciamos a sincronização aqui também.
iniciar_sync_mercadophone_se_habilitado()
```

Chamada incondicional em nível de módulo (linha 1034) — roda em **todo** boot da aplicação, em qualquer
ambiente, sem checar se está rodando em produção, preview, ou qualquer outro contexto. As três condições
de guarda (`BACKGROUND_JOBS_ENABLED`, `MERCADO_PHONE_SYNC_ENABLED`, `MERCADO_PHONE_API_TOKEN`) foram
satisfeitas no preview porque as duas últimas vieram copiadas do serviço-base — comportamento documentado
e esperado do Render, não um bug da plataforma.

**Não existe hoje, em nenhum lugar do código, uma checagem de `IS_PULL_REQUEST` (variável real, confirmada
presente e `true` no shell do preview) que impeça jobs de integração externa de rodar num ambiente de
preview.**

---

## 4. Impacto

### Dados afetados

- **405 registros da tabela `os`**, todos com `origem_integracao = 'mercado_phone'`, período
  `2026-04-01` a `2026-08-08` (coincide exatamente com `MERCADO_PHONE_SYNC_START_DATE=2026-04-01`,
  documentado em `DEPLOY.md`).
- Campos potencialmente presentes (schema, não inspecionado linha a linha — nenhum PII foi consultado
  durante a investigação): `cliente`, `aparelho`, `imei`, `tecnico`, `vendedor`, `valor_cobrado`,
  `observacoes`.
- Tabela auxiliar `integracao_sync_estado` também recebeu registros de controle interno (não é dado de
  cliente).
- **Nenhuma outra tabela foi afetada** — `clientes = 0`, `vendas = 0`, `usuarios = 1` confirmados antes da
  suspensão; busca exaustiva por `INSERT INTO`/`UPDATE` em `fluxoly_mercadophone.py` confirma que a
  integração só escreve em `os` e `integracao_sync_estado`.

### Sistemas externos

Buscados **todos** os call sites de `chamar_api_mercado_phone()` (única função do arquivo que faz
requisição HTTP externa) — existem exatamente 2, ambos de **leitura**:

| Função | `method_name` da API | Natureza |
|---|---|---|
| `listar_os_mercado_phone()` | `"index"` | Leitura (listagem paginada) |
| `detalhar_os_mercado_phone()` | `"get"` | Leitura (detalhe) |

Nenhum call site de criação/atualização/exclusão existe no arquivo. **Não há evidência, nem no código nem
nos logs, de qualquer escrita de volta para a API do MercadoPhone.** O efeito foi exclusivamente de
entrada de dado real no ambiente de preview, não de alteração do lado externo.

### Produção

`https://irflow-backend.onrender.com/health` → `{"status":"ok"}`, confirmado antes e depois do incidente.
Preview e produção são serviços Render inteiramente separados (`srv-d9t2ms0u01pc73bmuaqg` vs.
`srv-d7okn0u7r5hc73dfkit0`), sem disco, banco ou processo compartilhado. Nenhum evento incomum no
histórico de deploy de produção durante a janela do incidente.

---

## 5. Contenção

1. Instância do preview **suspensa** via painel Render (`Settings → Suspend Web Service`), confirmado por
   dois canais independentes: evento `Service suspended` no painel, e a URL pública passou a retornar
   `"This service has been suspended by its owner."`.
2. PR #22 **mantida aberta**, não mergeada, não fechada — preserva o ambiente para eventual auditoria
   adicional.
3. Nenhum dado foi apagado do disco do preview.
4. Nenhuma alteração em produção, código, banco, migrations, ou variáveis de ambiente.

---

## 6. Achado secundário (relacionado, mesma causa raiz)

O job de backup automático (`BACKGROUND_JOBS_ENABLED`) também rodou dentro do preview
(`backup_automatico_criado`, 19:53:52), gravando `backup-auto-20260810.db` no próprio disco isolado do
preview. Sem risco adicional por si só (fica no disco que será destruído), mas é mais uma evidência de
que **qualquer** background job herdado se comporta como em produção dentro de um ambiente que deveria
ser isolado — não é exclusivo da integração MercadoPhone.

---

## 7. Evidências

- Logs completos do preview (Render, `srv-d9t2ms0u01pc73bmuaqg`), incluindo os timestamps da seção 2.
- Consultas agregadas ao banco do preview, feitas **antes** da suspensão: contagem por tabela
  (`os=405, clientes=0, vendas=0, usuarios=1`), `schema_migrations`, `MIN`/`MAX(data)` da tabela `os`,
  distribuição por `origem_integracao`. Nenhuma linha individual ou campo de PII foi consultado ou
  exibido em nenhum momento.
- Leitura de código de `app.py` (disparo da thread) e `fluxoly_mercadophone.py` (função de chamada HTTP
  externa e seus 2 únicos call sites).
- Confirmação de `IS_PULL_REQUEST=true` no ambiente do preview via shell.

---

## 8. Lacunas

- Não foi possível determinar quais campos específicos das 405 OS contêm dado de cliente real
  identificável — decisão deliberada de não consultar PII durante a investigação.
- Não há visibilidade, do nosso lado, sobre se a própria API do MercadoPhone registra/expõe de alguma
  forma essas chamadas de leitura extra — fora do nosso sistema e controle.
- Não confirmado se `MERCADO_PHONE_API_TOKEN` de produção tem escopo de permissão restrito a leitura no
  painel do MercadoPhone, ou se teria permissão de escrita caso o código a exercesse (o código atual não
  exerce, mas o *token* em si pode ter escopo mais amplo do que o necessário).

---

## 9. Ações corretivas (não implementadas — decisão de arquitetura pendente, Frente B)

Nenhuma correção foi implementada nesta sessão. Opções em avaliação, registradas para decisão futura:

1. **Configuração** — sobrescrever/desabilitar explicitamente variáveis de integração externa
   (`MERCADO_PHONE_SYNC_ENABLED`, `MERCADO_PHONE_API_TOKEN`, e qualquer outra futura) especificamente no
   ambiente de preview, se o Render oferecer essa granularidade.
2. **Guard de código** — não iniciar jobs de integração externa (`iniciar_sync_mercadophone_se_habilitado()`
   e equivalentes futuros) quando `IS_PULL_REQUEST=true`.
3. **Defesa em profundidade (preferência registrada pelo CTO)** — as duas camadas juntas: configuração
   E guard de código, para que uma falha em uma camada não seja suficiente para repetir o incidente.

## 10. Ações preventivas

- Regra proposta para qualquer Preview futuro: **nenhum Preview deve herdar credenciais ou ter
  integrações externas habilitadas por padrão** — cobre MercadoPhone, e-mail, pagamentos, webhooks, e
  qualquer outro serviço de terceiros, além de background jobs em geral (backup automático incluso).
- Antes de qualquer novo Dry-Run de infraestrutura (Render/Vercel), essa política precisa estar decidida
  e implementada.

## 11. Critérios para reabrir/reativar o Preview

Nenhum definido ainda — pendente da decisão de arquitetura da Frente B. No mínimo, reativar exigiria
primeiro confirmar que `MERCADO_PHONE_SYNC_ENABLED`/`MERCADO_PHONE_API_TOKEN` (e `BACKGROUND_JOBS_ENABLED`
para o backup automático) estão desabilitados especificamente para este preview antes de qualquer boot
novo.

---

## Relação com outros achados

- **KI-035** (condição de corrida em `migrations/runner.py::run_migrations()`) foi **reproduzido de forma
  independente** no primeiro boot deste mesmo preview (ver Timeline, 19:51:00–19:51:24) — segunda
  ocorrência real do mesmo bug, em ambiente diferente de onde foi originalmente descoberto (produção,
  2026-08-10, deploy do commit `d7ef012`).
- Ambos os achados (INC-003 e KI-035) são, juntos, os dois bloqueadores atuais do Dry-Run 2B (rollback de
  infraestrutura Render/Vercel) — ver `docs/operations/PROJECT_STATUS.md`.

## Documentos relacionados

- `docs/operations/KNOWN_ISSUES.md` (KI-035) — condição de corrida em migrations, reproduzida no mesmo
  incidente
- `docs/operations/INCIDENTS/INC-001-database-is-locked.md`, `INC-002-os-duplicada-mercado-phone.md` —
  incidentes anteriores envolvendo a mesma integração MercadoPhone
- `docs/company/GO_LIVE_PLAN.md`, `DEPLOY.md` (seção Rollback) — política de Rollback afetada por este
  achado
