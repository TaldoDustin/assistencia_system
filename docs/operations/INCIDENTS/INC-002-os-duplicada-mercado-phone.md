# INC-002 — Ordens de Serviço duplicadas após sincronização com Mercado Phone

**Status:** Investigado — causa estrutural confirmada por leitura de código, com alta confiança;
**confirmação de que os dois registros existem de fato no banco (Cenário 1) ainda pendente** —
depende de acesso a produção
**Severidade:** P0 (crítico) — integridade de dados
**Impacto:** Alto — se confirmado, contamina dashboard, faturamento, contagem de aparelhos, relatórios;
risco futuro de vender/garantir/movimentar estoque contra a OS errada
**Ambientes:** Produção (suspeita); estrutura do bug existe também em qualquer ambiente com sync do
Mercado Phone habilitado e mais de um processo/worker
**Reportado por:** Usuário (CTO), 2026-07-23 — observou OS "1072" aparecendo duas vezes
**Investigado por:** Claude (Principal Engineer), 2026-07-23

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

## O que falta confirmar (limite desta investigação)

1. **Pergunta do usuário, ainda sem resposta:** a duplicidade aparece na tela de Ordens (listagem) ou só
   no Dashboard? Se só no Dashboard, a hipótese de JOIN/COUNT indevido (Cenário 2) precisa ser
   investigada em paralelo — não foi descartada nesta sessão.
2. **Confirmação direta no banco de produção:** esta investigação não teve acesso a produção. O achado
   acima é uma causa estrutural **plausível e suficiente** por leitura de código, mas não foi confirmado
   consultando o banco real para ver se `SELECT id FROM os WHERE id_externo_integracao='1072'` retorna
   de fato duas linhas.
3. **Se o Dashboard usa `COUNT(DISTINCT ordens.id)` ou `COUNT(*)` com JOIN** — não verificado nesta
   sessão; relevante mesmo se Cenário 1 for confirmado, porque os dois problemas podem coexistir.

---

## Próximo passo (aguardando usuário)

Não foi feita nenhuma correção nesta sessão — nem no schema, nem no importador, nem no dashboard —
seguindo o mesmo protocolo de INC-001 (investigar primeiro). Pendente:

1. Resposta à pergunta do sintoma (listagem vs. dashboard).
2. Acesso ou consulta ao banco de produção para confirmar `SELECT id, id_externo_integracao FROM os
   WHERE origem_integracao='mercado_phone' AND id_externo_integracao='1072'` — se retornar 2+ linhas,
   Cenário 1 confirmado.
3. Se confirmado, a correção mínima estrutural seria: (a) `UNIQUE INDEX` em
   `(origem_integracao, id_externo_integracao)` como cinto de segurança no schema, e (b) mover a
   coordenação da thread de sync para fora da memória de processo (ex.: lock em SQLite, mesmo padrão já
   usado para `login_attempts` no KI-001) — mas isso é decisão de correção, não desta investigação.

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
