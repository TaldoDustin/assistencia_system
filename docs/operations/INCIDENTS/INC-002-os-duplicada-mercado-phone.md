# INC-002 — Ordens de Serviço duplicadas após sincronização com Mercado Phone

**Status:** Resolvido — mecanismo corrigido (lock cross-processo), duplicatas confirmadas e limpas em
produção, `UNIQUE INDEX` como proteção definitiva aplicado (via deploy). Migração arquitetural para
worker/cron dedicado segue como melhoria futura não decidida.
**Severidade:** P0 (crítico) — integridade de dados
**Impacto:** Alto — confirmado: 3 OS duplicadas em produção, uma delas (832) com edições divergentes
(peça consumida duas vezes, reparo extra, checklist duplicado) — não só contagem incorreta no dashboard
**Ambientes:** Produção (confirmado)
**Reportado por:** Usuário (CTO), 2026-07-23 — observou OS "1072" aparecendo duas vezes
**Investigado por:** Claude (Principal Engineer), 2026-07-23
**Corrigido por:** Claude (Principal Engineer), 2026-07-23/24 — branches
`hotfix/mercado-phone-sync-lock-cross-processo`, `hotfix/mercado-phone-sync-lock-ajustes-revisao`,
`fix/os-unique-index-mercado-phone-inc002`
**Duplicatas limpas em produção por:** Usuário (CTO), 2026-07-24, com script preparado e verificado por
Claude

---

## Sintoma relatado

OS identificada como "1072" aparentemente duplicada. **Ainda não confirmado com o usuário**: se a
duplicidade aparece na tela de Ordens (listagem) ou só no Dashboard — essa resposta define se o
problema nasce no banco (Cenário 1) ou é um efeito de consulta/JOIN (Cenário 2), conforme distinção
levantada pelo próprio usuário. Ver seção "O que falta confirmar".

Contexto importante: **não existe coluna `numero_os`** no schema (`app.py`, tabela `os`). O "1072" quase
certamente é `os.id_externo_integracao` — o identificador do Mercado Phone, exibido como `#MP-1072` pela
função `getOrderDisplayNumber` (`frontend/src/lib/constants.js`), corrigida ontem (KI-021, resolvido
2026-07-22, `hotfix/os-numero-mercadophone`) para preferir esse número externo em vez do `id` interno.
**Isso pode explicar por que a duplicidade só ficou visível agora**: antes do KI-021, duas OS com o
mesmo `id_externo_integracao` apareciam com `id`s internos diferentes (`#845`, `#846`) — fácil de não
notar. Depois do KI-021, ambas exibem `#MP-1072` — a duplicidade fica óbvia.

---

## Achado principal — causa estrutural confirmada por leitura de código

**O schema não impõe unicidade em `(origem_integracao, id_externo_integracao)`, e a thread de
sincronização do Mercado Phone inicia uma vez por processo do Gunicorn — não uma vez por deploy.**
Produção roda `--workers 2` (`Dockerfile`), sem `--preload`. Isso significa **dois processos
independentes, cada um rodando seu próprio loop de sincronização, sem nenhuma coordenação entre eles.**

### 1. Sem UNIQUE constraint

```python
# app.py — CREATE TABLE os (schema base) + ALTER TABLE (migrações)
# nenhuma dessas colunas tem UNIQUE nem índice:
cursor.execute("ALTER TABLE os ADD COLUMN origem_integracao TEXT")
cursor.execute("ALTER TABLE os ADD COLUMN id_externo_integracao TEXT")
```

Não existe `CREATE UNIQUE INDEX` nem `CREATE INDEX` algum sobre `id_externo_integracao` em todo
`app.py`. Nada no banco impede duas linhas com o mesmo `(origem_integracao, id_externo_integracao)`.

### 2. O importador confia inteiramente num "check antes de inserir" (TOCTOU)

```python
# irflow_mercadophone.py:393-401 — importar_os_mercado_phone()
cursor.execute(
    "SELECT id FROM os WHERE origem_integracao=? AND id_externo_integracao=?",
    ("mercado_phone", external_id),
)
existente = cursor.fetchone()

if existente:
    # ... UPDATE
else:
    # ... INSERT (linha ~703, sem ON CONFLICT/INSERT OR IGNORE)
```

Isso é seguro **só se for garantido que apenas uma execução do sync roda por vez**. Não é.

### 3. A thread de sync inicia por processo, não por deploy

```python
# app.py:1751-1778
_MERCADO_PHONE_SYNC_THREAD_STARTED = False  # variável de módulo — vive só na memória do processo

def iniciar_sync_mercadophone_se_habilitado():
    global _MERCADO_PHONE_SYNC_THREAD_STARTED
    if _MERCADO_PHONE_SYNC_THREAD_STARTED:
        return
    ...
    sync_thread = threading.Thread(target=loop_sincronizacao_mercado_phone, ..., daemon=True)
    sync_thread.start()
    _MERCADO_PHONE_SYNC_THREAD_STARTED = True

# Em produção (Render/Gunicorn), o módulo é importado sem passar por __main__.
# Por isso iniciamos a sincronização aqui também.
iniciar_sync_mercadophone_se_habilitado()
```

`_MERCADO_PHONE_SYNC_THREAD_STARTED` é uma flag em memória do processo Python. Com `--workers 2` (2
processos gunicorn, cada um com seu próprio `import app`), **cada worker importa `app.py`
independentemente e cada um inicia sua própria thread de sync** — a flag só impede duplicar a thread
*dentro do mesmo processo*, não entre processos.

`loop_sincronizacao_mercado_phone` (`irflow_mercadophone.py:909-920`) roda para sempre, chamando
`sincronizar_mercado_phone()` a cada `max(30, sync_interval_seconds)` segundos — em cada um dos 2
processos, para sempre, sem parar.

### 4. A corrida (TOCTOU) entre os dois processos

```
Processo A (worker 1)                    Processo B (worker 2)
──────────────────────                   ──────────────────────
SELECT ... id_externo=1072
→ não encontrado
                                          SELECT ... id_externo=1072
                                          → não encontrado (A ainda não commitou)
INSERT ... id_externo=1072
(ainda sem commit — sincronizar_mercado_phone
 só commita 1x, no fim do loop inteiro)
                                          INSERT ... id_externo=1072
                                          (sem UNIQUE para barrar — aceito)
conn.commit()
                                          conn.commit()

Resultado: duas linhas com id_externo_integracao='1072', ids internos diferentes.
```

Isso bate exatamente com a hipótese de corrida levantada pelo usuário, e é uma consequência estrutural
garantida da arquitetura atual — não depende de nenhuma condição rara. Só depende dos dois workers
tentarem sincronizar a mesma OS nova num intervalo próximo o bastante (o que o `time.sleep` de
`sync_interval_seconds` não impede entre processos diferentes).

### Precedente já registrado no projeto

`docs/operations/KNOWN_ISSUES.md` (KI-001, resolvido) já identificou exatamente esta classe de bug —
estado em memória de processo não é confiável com `--workers 2` — para o rate limiter de login, e
corrigiu movendo o contador para SQLite (compartilhado entre workers via WAL). **A mesma lição nunca foi
aplicada à thread de sincronização do Mercado Phone.**

---

## Correção aplicada — lock cross-processo

Decisão do usuário (CTO): corrigir a arquitetura da sincronização agora (lock em SQLite, mesmo padrão
do KI-001), em vez de esperar a migração maior para um worker/cron dedicado — essa migração fica
registrada como melhoria arquitetural futura, não bloqueia a correção imediata.

`irflow_mercadophone.py` — `adquirir_lock_sync_mercado_phone()`/`liberar_lock_sync_mercado_phone()`
implementam um lease com expiração usando a tabela `integracao_sync_estado` (já existente, sem mudança
de schema): antes de sincronizar, cada processo tenta reivindicar o lock via um `UPDATE ... WHERE valor
< <agora>` atômico; só um processo consegue. `sincronizar_mercado_phone()` agora tenta adquirir o lock
primeiro — se outro worker já está sincronizando, retorna `lock_ocupado=True` imediatamente, sem chamar
a API do Mercado Phone nem tocar no banco. Se o processo que detém o lock cair sem liberar, o lease
expira sozinho — não trava a sincronização permanentemente.

Efeito colateral corrigido no mesmo commit: `reprocessar_todas_os_mercado_phone()` (reimportação
completa, que primeiro apaga todas as OS do Mercado Phone e depois reimporta) tratava
`importadas=0, ignoradas=0` como "nada para importar, sucesso" — exatamente o que o lock ocupado também
retorna. Sem o ajuste, um lock ocupado na primeira tentativa faria a reimportação completa terminar sem
reimportar nada, depois de já ter apagado tudo. Corrigido para tratar `lock_ocupado` como motivo de
retry (orçamento próprio, não conta contra as tentativas normais).

**Refinamentos de uma segunda revisão (usuário/CTO), no mesmo dia:**
- **TTL reduzido de 300s para 90s** (`LOCK_SYNC_TTL_SEGUNDOS_PADRAO`) — intervalo padrão de sync é 30s
  e um ciclo sem novidades é rápido; 300s deixaria o sistema esperando até 5 minutos após um worker
  morrer no meio de um sync, mais do que o necessário. 90s (3x o intervalo) dá folga para ciclos com
  várias OS novas/atualizadas sem exagerar no tempo de espera pós-crash.
- **Log quando o lock está ocupado** — antes só retornava `lock_ocupado=True` silenciosamente;
  agora também imprime `[MercadoPhone] Sincronização ignorada: lock ocupado por outro worker.`, para
  diagnosticar rápido se "o sync não rodou" for reportado no futuro.
- **Teste de corrida escalado de 2 para 100 threads simultâneas** — mesma prova de atomicidade, mais
  margem de confiança (produção só tem 2 workers reais, mas 100 concorrentes de uma vez é uma prova
  bem mais forte contra qualquer não-atomicidade sutil no `UPDATE ... WHERE`).
- **Novo teste de estresse: 300 aquisições reais (20 threads × 15 rodadas, cada rodada tenta até
  conseguir)**, com um contador de seção crítica clássico — se o `UPDATE ... WHERE` não fosse atômico,
  mais de uma thread entraria "dentro do lock" ao mesmo tempo e o contador passaria de 1 em algum
  momento das 300 aquisições. Reduzido de 1000 para 300 aquisições depois de medir o impacto no tempo
  da suíte (1000 acrescentava ~29s ao total; 300 acrescenta ~5s e já é duas ordens de grandeza acima
  dos 2 workers reais).

7 novos testes (`tests/test_inc002_mercado_phone_sync_lock.py`, 486 no total): aquisição/liberação/
expiração do lock, curto-circuito de `sincronizar_mercado_phone()` sem chamada de rede quando ocupado,
corrida real entre 100 threads confirmando que exatamente uma vence, e o teste de estresse de 300
aquisições acima — suíte inteira rodada 3x seguidas para descartar flakiness. `ruff check .` limpo, zero
regressão.

**O que esta correção NÃO faz:** não confirma nem limpa duplicatas que já possam existir em produção
(pendente da consulta SQL abaixo); não adiciona a `UNIQUE INDEX` — isso é deliberadamente adiado até as
duplicatas existentes serem resolvidas, porque criar um índice único sobre dados que já violam essa
unicidade falha. Ver "Próximo passo" atualizado.

---

## Bônus — possível conexão com INC-001 (`database is locked`)

`sincronizar_mercado_phone()` (`irflow_mercadophone.py:738-836`) abre **uma única conexão** e mantém
**uma única transação aberta durante todo o ciclo de sincronização** — que pode incluir múltiplas
páginas de listagem, uma chamada HTTP (`detalhar_os_mercado_phone`) por OS nova/atualizada, e um
INSERT/UPDATE por OS — só commitando no final (`conn.commit()`, linha 833).

Com os 2 workers rodando esse ciclo de forma independente e concorrente, isso produz exatamente o tipo
de "transação muito grande" que era a hipótese 7 do usuário na investigação original de INC-001 — e é um
candidato mais realista do que qualquer coisa testada na reprodução por carga sintética feita até agora
(`docs/operations/INCIDENTS/INC-001-database-is-locked.md`), já que aquele teste só simulou requisições
HTTP curtas, nunca duas transações longas concorrentes de verdade. **Não confirmado ainda** — registrado
aqui como pista para quando INC-001 voltar a ser investigado.

---

## Confirmação em produção (2026-07-24)

Consulta rodada pelo usuário (CTO) direto no banco de produção (`/data/database.db`, via Shell do
Render — o container não tem o binário `sqlite3`, a consulta foi feita com o módulo `sqlite3` do
Python, já disponível):

```sql
SELECT origem_integracao, id_externo_integracao, COUNT(*) AS total
FROM os
WHERE origem_integracao = 'mercado_phone'
GROUP BY origem_integracao, id_externo_integracao
HAVING COUNT(*) > 1;
```

**Cenário 1 confirmado.** 3 pares duplicados — `id_externo_integracao` 1083, 1093 e 832 (não o "1072"
citado de memória originalmente, mas o mesmo padrão de bug). Nota: a pergunta sobre listagem vs.
dashboard ficou sem resposta explícita, mas como os pares são registros reais no banco (não um efeito de
JOIN), o Cenário 1 por si só já explica o sintoma — a hipótese de JOIN/COUNT indevido (Cenário 2) não
precisou ser investigada.

**Análise de cada par** (dados completos + registros filhos: `os_pecas`, `os_reparos`,
`os_checklists`, `shopping_list`, `compras`, `audit_log`):

| Par | Natureza | Decisão |
|---|---|---|
| 1083 (`876`/`877`) | Duplicata limpa — linhas idênticas em todos os campos, nenhum filho em nenhuma tabela | Mantido `876`, apagado `877` |
| 1093 (`887`/`888`) | Duplicata limpa — idem | Mantido `887`, apagado `888` |
| 832 (`528`/`529`) | **Não é duplicata limpa** — as duas linhas divergiram depois de criadas (tipo, valor, reparo extra, peça consumida diferente, checklist próprio em cada uma) | Usuário confirmou `529` (Upgrade, R$180, bateria+auricular) como a versão real; `528` apagado |

O caso 832 é o achado mais importante desta etapa: a duplicação não ficou "parada" — alguém continuou
trabalhando numa das duas linhas fantasmas (editou tipo/valor, adicionou reparo, consumiu peça própria,
preencheu checklist próprio) como se fosse a OS real. Isso confirma que o impacto do bug vai além de
contagem duplicada no dashboard — pode gerar baixa de estoque duplicada e histórico de reparo
fragmentado entre duas linhas.

Limpeza executada em produção (script Python transferido em base64 por causa de limitação de paste no
terminal web do Render, rodado com `BEGIN`/verificação humana do resultado antes de `COMMIT` — nenhuma
alteração foi feita sem confirmação visual do "antes" e "depois"). Verificação pós-limpeza: consulta de
duplicatas retornou `[]`.

---

## Correção aplicada — UNIQUE INDEX (proteção definitiva)

Decisão do usuário (CTO): manter a ordem original — só criar o índice depois de confirmar e limpar as
duplicatas existentes (feito acima).

`app.py::criar_tabelas()` — adicionado
`CREATE UNIQUE INDEX IF NOT EXISTS idx_os_origem_id_externo ON os (origem_integracao, id_externo_integracao)`,
no mesmo padrão de todas as outras migrações aditivas do projeto (roda automaticamente a cada boot,
idempotente). Diferente do `DELETE` de limpeza, **não precisou de execução manual em produção** — é uma
mudança de código normal, aplicada sozinha no próximo deploy/restart dos workers.

SQLite trata cada `NULL` como distinto num índice `UNIQUE` (comportamento padrão do SQL), então OS
nativas (criadas direto no app, sem integração — `origem_integracao`/`id_externo_integracao` ambos
`NULL`) nunca conflitam entre si; o índice só passa a valer quando ambos os campos têm valor real,
exatamente o caso do Mercado Phone hoje e de qualquer integração futura.

Validado localmente: OS nativas continuam inserindo livremente; uma segunda OS com o mesmo
`(origem_integracao, id_externo_integracao)` de uma já existente é rejeitada com
`sqlite3.IntegrityError: UNIQUE constraint failed`. 3 novos testes
(`tests/test_inc002_unique_index_os_mercado_phone.py`, 489 no total), `ruff check .` limpo, zero
regressão.

Com isso, mesmo que o lock cross-processo falhe por algum motivo não previsto (bug futuro, script manual,
nova integração escrevendo direto na tabela), o banco em si impede a duplicata — a garantia deixa de
depender só de disciplina de código.

---

## Status final

| Etapa | Status |
|---|---|
| Confirmar causa estrutural (leitura de código) | ✅ |
| Corrigir o mecanismo (lock cross-processo) | ✅ |
| Confirmar duplicatas em produção | ✅ — 3 pares encontrados |
| Limpar duplicatas existentes | ✅ — 3 linhas removidas, decisão registrada acima |
| `UNIQUE INDEX` como proteção definitiva | ✅ — aplicado automaticamente no próximo deploy |
| Migração arquitetural (worker/cron dedicado) | Não decidida — registrada como melhoria futura, requer ADR |

INC-002 pronto para ser encerrado após o deploy da branch com o `UNIQUE INDEX` (ver
`docs/operations/PROJECT_STATUS.md` para a decisão formal de fechamento).

---

## Documentos relacionados

- `docs/operations/KNOWN_ISSUES.md` — KI-001 (mesma classe de bug, já resolvida para rate limiting) e
  KI-021 (exibição do número externo, resolvido ontem — possível motivo da duplicidade ter ficado visível)
- `docs/operations/INCIDENTS/INC-001-database-is-locked.md` — possível causa raiz compartilhada (seção
  "Bônus" acima)
- `irflow_mercadophone.py` — `importar_os_mercado_phone` (393-736), `sincronizar_mercado_phone` (738-836),
  `loop_sincronizacao_mercado_phone` (909-920)
- `app.py` (1751-1778) — `iniciar_sync_mercadophone_se_habilitado()`
- `Dockerfile` — `gunicorn ... --workers 2` (sem `--preload`)
