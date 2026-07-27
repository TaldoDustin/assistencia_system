# INC-001 — `database is locked`

**Status:** Parcialmente corrigido — `POST /api/auth/login` e as 4 rotas de checklist corrigidas via
hotfix isolado (4 rotas de shopping-list reclassificadas como risco estrutural, não vazamento
confirmado); instrumentação de runtime pronta, reprodução local por carga (2 rodadas, até 120
threads/60s) não confirmou a causa raiz — aguardando decisão do usuário sobre os próximos vetores
(instrumentação em ambiente real / transação do MercadoPhone). **INC-001 continua aberto** — esta
correção elimina um vetor confirmado, não a causa raiz (ver nota ao final da seção da correção).
**Severidade:** P0 (crítico)
**Impacto:** Alto — afeta operações de escrita centrais (criar/editar OS, cadastrar/alterar estoque)
**Ambientes:** Produção, Desenvolvimento
**Reportado por:** Usuário (CTO), 2026-07-23
**Investigado por:** Claude (Principal Engineer), 2026-07-23
**Hotfixes aplicados (Claude, Principal Engineer):**
- 2026-07-23 — login, branch `hotfix/conexao-login-database-locked`
- 2026-07-27 — rotas de checklist, branch `fix/checklist-conexao-database-locked`

---

## Sintomas relatados

- `database is locked` ao editar OS
- `database is locked` ao criar OS
- `database is locked` ao cadastrar item de estoque
- `database is locked` ao alterar item de estoque
- Comportamento intermitente ("às vezes funciona, às vezes não")

---

## Decisão de processo

Por pedido explícito do usuário: **investigar primeiro, não corrigir ainda**. Este documento registra
só os achados. Nenhuma linha de código de correção foi escrita nesta sessão — os commits, se houver,
serão só deste documento.

---

## O que foi confirmado (não é a causa)

| Hipótese do usuário | Verificado | Resultado |
|---|---|---|
| WAL desabilitado | ✅ Verificado empiricamente (`PRAGMA journal_mode` numa conexão nova via `conectar()`) | **Descartada** — WAL está ativo. `criar_tabelas()` habilita WAL uma vez (`habilitar_wal=True`) na primeira execução; por ser uma propriedade persistida no arquivo do banco (não por conexão), continua ativo em toda conexão seguinte mesmo sem reafirmar o pragma |
| Timeout pequeno | ✅ Lido em `app.py` | **Descartada** — `SQLITE_TIMEOUT_SECONDS = 30` (configurável via `IR_FLOW_SQLITE_TIMEOUT_SECONDS`), aplicado via `timeout=` no `sqlite3.connect()` **e** via `PRAGMA busy_timeout` em toda conexão (`_configurar_conexao_sqlite`) |
| As 4 rotas citadas como sintoma (criar/editar OS, criar/editar estoque) fazem tudo dentro da mesma transação sem proteção | ✅ Lidas as 4 rotas por completo (`criar_ordem`, `atualizar_ordem`, `criar_estoque`, `atualizar_estoque`, `irflow_blueprints_api.py`) | **Descartada como causa direta** — as 4 já têm `try/except Exception: conn.rollback() ... finally: conn.close()` corretos. Se travam, é porque **outra conexão, em outra rota, já segura o lock de escrita** quando elas tentam escrever — não porque elas mesmas vazam |

---

## Correção aplicada — `POST /api/auth/login`

Decisão do usuário (CTO): corrigir apenas `/api/auth/login` agora, como hotfix isolado e mínimo —
não os outros 13 pontos identificados na investigação (ver tabela abaixo), que seguem em aberto até
decisão separada.

`irflow_blueprints_api.py::auth_login()` — conexão envolvida em `try/except/finally`: qualquer exceção
entre `conectar()` e o fim da função agora faz `rollback()` e `close()` antes de propagar/retornar erro,
em vez de vazar a conexão com a transação de escrita aberta. Nenhum outro comportamento da rota foi
alterado (mesmos códigos de resposta, mesma lógica de rate limit e registro de tentativa).

Prova por teste automatizado (`tests/test_inc001_login_connection_leak.py`): injeta uma exceção real no
ponto exato da causa raiz (`registrar_tentativa`, o INSERT em `login_attempts`) via substituição do
conteúdo da cell da closure (`cell.cell_contents`, técnica necessária porque `registrar_tentativa` é
vinculada via `deps` uma única vez na criação do blueprint — não é monkeypatch-ável como atributo de
módulo). Confirmado que, contra o código **antes** da correção, o mesmo teste falha (a exceção propaga
sem tratamento); contra o código **depois** da correção, passa — inclusive a asserção de que uma
escrita imediatamente seguinte não trava (prova de que a conexão foi de fato fechada, não só que a
resposta HTTP teve o código certo). Suíte completa (480 testes) e `ruff check .` sem regressão.

---

## Correção aplicada — 4 rotas de checklist (2026-07-27)

Branch `fix/checklist-conexao-database-locked`, mesmo padrão do hotfix de login. As 4 rotas
identificadas como "confirmado sem proteção" na tabela abaixo (`GET /api/ordens/<id>/checklist`,
`POST /api/ordens/<id>/checklist/token`, `GET /api/checklist/<token>` e `POST /api/checklist/<token>` —
as duas últimas públicas, sem login) agora envolvem a conexão em `try/except/finally`:
`conn = conectar()` antes do bloco, `except Exception as exc: conn.rollback(); return err(str(exc))`,
`finally: conn.close()`. Nenhum outro comportamento das rotas foi alterado (mesmos códigos de resposta,
mesmo payload, mesmas mensagens de erro) — mudança restrita a `try`/`except`/`finally`, sem refactor ou
alteração de estilo.

Prova por teste automatizado (`tests/test_inc001_checklist_connection_leak.py`, 8 casos — 2 por rota):
para cada rota, um teste confirma que o contrato HTTP não mudou (status/payload no caminho feliz e no
404) e outro injeta uma exceção real no ponto de leitura/escrita da rota (`_garantir_checklist_os` nas
rotas 1 e 2 — que executa um INSERT real antes do commit da própria rota, reproduzindo fielmente o
mecanismo do INC-001; `_buscar_checklist_por_token` nas rotas 3 e 4) via a mesma técnica de
`cell.cell_contents` do teste de login. A prova de fechamento é um login imediatamente seguinte
(escrita em `login_attempts`, tabela não relacionada) não travar — em WAL o lock de escrita é por
arquivo de banco, não por tabela, então uma conexão vazada com transação pendente em `os_checklists`
bloquearia também a escrita em `login_attempts`. **Confirmado que os 8 testes travam e estouram timeout
contra o código anterior à correção** (validado com `git stash` temporário do arquivo alterado,
restaurado imediatamente após) — mesmo rigor do teste de login. Suíte completa (533 testes) e
`ruff check .` sem regressão.

**Nota importante — o que esta correção não prova:** ela elimina um vetor de vazamento de conexão
**confirmado por leitura de código e agora também reproduzido em teste automatizado** nas 4 rotas de
checklist. Isso **não confirma nem elimina** a hipótese principal ainda em aberto relacionada à
transação de `sincronizar_mercado_phone()` (ver seção "Instrumentação dinâmica..." acima) — essa
continua sendo investigada separadamente. Não concluir, a partir desta correção, que o INC-001 foi
causado pelas rotas de checklist; sabe-se apenas que elas eram um risco real e confirmado, agora
eliminado.

---

## Achado principal — hipótese com forte evidência estática, ainda **não comprovada em runtime**

> Revisão do usuário (CTO), 2026-07-23: a formulação original desta seção afirmava "causa raiz mais
> provável" como se fosse conclusão. Correto é tratar como **hipótese principal, bem fundamentada, mas
> ainda não comprovada** — falta a ligação direta e observada entre exceção → conexão presa aberta →
> `database is locked`. Essa ligação só é confirmada com instrumentação em runtime (ver seção abaixo),
> não por leitura de código. Este documento foi corrigido para refletir isso.

**Hipótese: conexões que fazem escrita (INSERT/UPDATE/DELETE) sem `try/except/finally` vazam a conexão
inteira, com a transação de escrita ainda aberta, se qualquer exceção ocorrer entre o `conectar()` e o
`conn.close()`.**

Em WAL, leitores não bloqueiam escritores nem vice-versa — mas **escritores bloqueiam escritores**.
Uma conexão vazada que tinha um `INSERT`/`UPDATE` pendente (mesmo que a query em si tenha sido bem
sucedida, mas o código quebrou antes do `commit()`/`close()`) mantém o lock de escrita **até o processo
Python coletar aquele objeto via GC** — o que não é determinístico nem imediato, especialmente com
`--workers 2` em produção (`Dockerfile`). Isso bate exatamente com o sintoma relatado: funciona até uma
exceção vazar uma conexão, e a partir daí qualquer escrita nova trava até o worker reiniciar ou o GC
agir.

### O ponto de maior risco: `POST /api/auth/login`

```python
# irflow_blueprints_api.py:417 — auth_login()
conn = conectar()
cursor = conn.cursor()

if limite_excedido(cursor, identificador):
    conn.close()
    return err(...)
...
registrar_tentativa(cursor, identificador, sucesso)
conn.commit()
conn.close()
```

Sem `try/except`. **É escrita** (`registrar_tentativa` grava em `login_attempts`, depois `commit()`).
É a rota **de maior frequência de chamada de todo o sistema** — todo login passa por aqui. Qualquer
exceção não prevista entre `conectar()` e o `conn.close()` final (incluindo, ironicamente, um
`sqlite3.OperationalError: database is locked` vindo de contenção normal e transitória com **outra**
conexão) deixa esta conexão aberta permanentemente, com sua própria escrita pendente — transformando
uma contenção passageira e normal em um lock persistente.

### Lista completa — rotas de escrita sem proteção contra exceção (achado nesta investigação)

> **Correção de registro (2026-07-23), após leitura completa de cada rota (não só grep):** a varredura
> estática original classificou as 4 rotas de `/api/shopping-list*` como "sem proteção", pelo mesmo
> critério usado nas outras — ausência de um bloco `try/finally` explícito. Lendo o corpo completo de
> cada uma, isso é impreciso: elas usam um padrão diferente (não idiomático, mas efetivo) — `conn.close()`
> manual antes de cada `return` antecipado, mais um `except Exception` amplo ao redor de toda a função
> que também fecha a conexão. Em todo caminho de código rastreado, a conexão é fechada. **Reclassificadas
> abaixo como risco estrutural (frágil a mudanças futuras), não como vazamento confirmado.** As 4 rotas de
> checklist, em contraste, **não têm nenhum `try/except` nem fechamento no caminho de exceção** — essas
> continuam como risco confirmado por leitura de código.

| Rota | Arquivo:linha | Status após releitura completa |
|---|---|---|
| ✅ `POST /api/auth/login` — **corrigido** (ver seção acima) | `irflow_blueprints_api.py:417` | Corrigido |
| 🟡 `POST /api/shopping-list` | `irflow_blueprints_api.py:826` | Reclassificado — fecha em todo caminho (`except` amplo + `close()` manual antes de cada `return`); risco estrutural, não vazamento confirmado |
| 🟡 `PUT /api/shopping-list/<id>` | `irflow_blueprints_api.py:865` | Idem |
| 🟡 `PATCH /api/shopping-list/<id>/status` | `irflow_blueprints_api.py:924` | Idem |
| 🟡 `DELETE /api/shopping-list/<id>` | `irflow_blueprints_api.py:1019` | Idem |
| ✅ `GET /api/ordens/<id>/checklist` — **corrigido (2026-07-27)** | `irflow_blueprints_api.py:1315` | Corrigido — ver "Correção aplicada — 4 rotas de checklist" acima |
| ✅ `POST /api/ordens/<id>/checklist/token` — **corrigido (2026-07-27)** | `irflow_blueprints_api.py:1354` | Corrigido — idem |
| ✅ `GET /api/checklist/<token>` (checklist público) — **corrigido (2026-07-27)** | `irflow_blueprints_api.py:1402` | Corrigido — idem, pública |
| ✅ **`POST /api/checklist/<token>`** (salvar checklist público) — **corrigido (2026-07-27)** | `irflow_blueprints_api.py:1449` | Corrigido — era o maior risco restante entre as rotas de escrita reais (pública, sem login) — ver "Correção aplicada — 4 rotas de checklist" acima |
| `POST /nova` (view legada de criar OS) | `irflow_blueprints_orders.py:202` | **Provavelmente morta** — frontend usa `/api/ordens`, não este form legado |
| `GET/POST /custos-operacionais` (view legada) | `irflow_blueprints_admin.py:48` | **Provavelmente morta** — `OperationalCosts.jsx` usa `/api/custos`, não este form legado |
| `GET/POST /login` (view legada) | `irflow_blueprints_auth.py:43` | **Confirmado morta** — `Login.jsx` usa exclusivamente `/api/auth/login` |
| `POST /usuarios/editar/<id>`, `POST /usuarios/deletar/<id>` (views legadas) | `irflow_blueprints_auth.py:125`, `:157` | Provavelmente mortas, não confirmado — `Users.jsx` provavelmente usa `/api/usuarios/*` |
| `POST /estoque/deletar/<id>` (view legada) | `irflow_blueprints_inventory.py:161` | Provavelmente morta, não confirmado |
| `sincronizar_reparos_padrao()` (só roda no startup) | `app.py:1084` | Baixíssima — 1x por boot |

Resumo após releitura: das rotas realmente em uso pelo frontend hoje, **4 são risco confirmado** (as de
checklist, incluindo a pública) e **4 são risco estrutural, não vazamento confirmado** (shopping-list) —
não mais "13 pontos" tratados como equivalentes.

---

## Hipótese investigada e descartada — conexão aninhada dentro de OS/Estoque

Revisão do usuário (CTO), 2026-07-23: os sintomas relatados (criar/editar OS, cadastrar/alterar estoque)
não batem com a rota corrigida no hotfix (`/api/auth/login`). Hipótese levantada: as próprias rotas de
OS/Estoque abrem uma segunda conexão internamente (ex.: auditoria ou movimentação de estoque chamando
`conectar()` de novo enquanto a primeira conexão ainda está com escrita pendente) — o que causaria
`database is locked` sem depender de nenhuma exceção vazando nada.

**Verificado (só leitura de código, nenhuma mudança):** `criar_ordem`, `atualizar_ordem`,
`criar_estoque` e `atualizar_estoque` passam o mesmo `cursor` por toda a cadeia de chamadas
(`irflow_os.py::validar_reparo_ids/salvar_reparos_os/consumir_peca_da_os/devolver_pecas_da_os/
adicionar_peca_os_sem_consumir`, `_recalcular_custo_medio`, `registrar_movimentacao`) — nenhuma dessas
funções chama `conectar()` internamente. O módulo de auditoria central (`irflow_audit.py::
registrar_log_auditoria`) também recebe `cursor` do chamador, sem abrir conexão própria — mas note que
OS/Estoque (domínios legados) não chamam esse módulo hoje; só Produtos, Unidades Serializadas e Clientes
o usam. Único `conectar()` duplicado encontrado no arquivo (`irflow_blueprints_api.py:621`, `conn2`) é
numa rota de dashboard, só leitura (`SELECT COUNT`), e abre depois que a primeira conexão do mesmo
handler já foi fechada — sem sobreposição.

**Conclusão:** hipótese de conexão aninhada **descartada para estas 4 rotas especificamente**, por
leitura de código. Isso reforça — mas não prova — a hipótese original: se o lock existe quando essas 4
rotas escrevem, ele foi adquirido por **outra conexão, em outra rota**, ainda aberta no momento da
tentativa de escrita. A pergunta em aberto é qual.

---

## Instrumentação dinâmica + reprodução por carga — resultado (2026-07-23)

Implementada instrumentação temporária em `app.py::conectar()` (branch
`chore/inc-001-instrumentacao-conexoes`, não mergeada ainda) — gated por
`IR_FLOW_DEBUG_CONN_TRACE=1`, zero impacto desligada (480 testes + `ruff check .` sem mudança).
Liga um wrapper (`_ConexaoRastreada`) que loga `OPEN`/`COMMIT`/`ROLLBACK`/`CLOSE` por conexão (id, rota,
thread, duração) e, via `weakref.finalize`, avisa com o stack trace de abertura se uma conexão for
coletada pelo GC sem `close()` — a evidência direta do mecanismo suspeito.

**Instrumentação validada em isolamento:** testada com uma conexão deliberadamente vazada (aberta,
sem `close()`) — o aviso disparou corretamente, com o stack trace exato apontando para o ponto de
vazamento. O mecanismo de detecção funciona.

**Reprodução por carga — resultado negativo:** rodado localmente contra `gunicorn --workers 2`
(mesma configuração de produção, `Dockerfile`), banco isolado, script de carga concorrente
(`requests` + `threading`) martelando simultaneamente `POST/PUT /api/ordens`, `POST/PUT /api/estoque`,
`POST /api/shopping-list` + `PATCH .../status`, as 4 rotas de checklist (incluindo a pública, alvo
prioritário — sem nenhuma proteção confirmada), e tentativas de login com senha errada (ruído
proposital no rate limiter). Duas rodadas:

| Rodada | Threads | Duração | Escritas concluídas | `database is locked` | Aviso de vazamento (GC) |
|---|---|---|---|---|---|
| 1 | 40 | 45s | ~4.700 | 0 | 0 |
| 2 (concentrada num único registro de checklist compartilhado, para maximizar contenção) | 120 | 60s | ~11.300 | 0 | 0 |

Nenhuma das duas rodadas reproduziu o erro nem disparou o aviso de vazamento, mesmo martelando
diretamente as 4 rotas confirmadas sem proteção. Interpretação: os payloads usados são todos
bem-formados — a validação de entrada roda **antes** de `conectar()` nessas rotas, então a única forma
realista de uma exceção ocorrer no meio da transação é uma contenção genuína do SQLite (ex.: o próprio
`busy_timeout` estourando sob carga muito mais sustentada, ou I/O mais lento que o SSD local usado
neste teste). 16.000 escritas em ~2 minutos num disco local rápido não foi suficiente para gerar essa
condição.

**Conclusão:** a instrumentação está pronta e comprovadamente funcional, mas a reprodução local não
confirmou a causa raiz. Decisão de próximo passo pendente do usuário (ver seção seguinte).

**Atualização (2026-07-23) — novo candidato encontrado durante a investigação de INC-002:**
`sincronizar_mercado_phone()` (`irflow_mercadophone.py:738-836`) abre uma única conexão e mantém uma
única transação aberta durante todo um ciclo de sincronização (múltiplas chamadas HTTP + INSERT/UPDATE
por OS, só commitando no final) — e, por um bug estrutural separado (ver
`docs/operations/INCIDENTS/INC-002-os-duplicada-mercado-phone.md`), **essa rotina roda em cada um dos 2
workers do Gunicorn de forma independente e concorrente**, sem nenhuma coordenação entre processos. Isso
é o tipo de "transação muito grande, concorrente, de verdade" que a reprodução por carga sintética acima
nunca simulou (só requisições HTTP curtas). Candidato mais realista do que qualquer coisa testada até
agora — não confirmado, mas prioritário para a próxima rodada de investigação.

---

## O que NÃO foi confirmado ainda (limite desta investigação)

- **Qual exceção especificamente dispara o vazamento em produção** — a varredura é estática (leitura de
  código), não captura o evento real acontecendo. Não sabemos se é o próprio `busy_timeout` sendo
  estourado, um erro de validação inesperado, ou outra causa.
- **Se as rotas legadas (`irflow_blueprints_auth.py`, `irflow_blueprints_orders.py`,
  `irflow_blueprints_admin.py`, `irflow_blueprints_inventory.py`) ainda recebem tráfego real** —
  confirmado que o frontend React não as chama, mas não descartado 100% (bookmark antigo, integração
  externa, etc.)
- **Se existem mais pontos de vazamento em código de leitura** que, mesmo não bloqueando escritores em
  WAL, ainda vazam recursos (conexões nunca fechadas se acumulam na memória do processo ao longo do
  tempo, o que por si só degrada o sistema)

---

## Próximo passo — aguardando decisão do usuário

`POST /api/auth/login` e as 4 rotas de checklist permanecem corrigidas (ver "Correção aplicada" e
"Correção aplicada — 4 rotas de checklist" acima) — mantidas independente do resultado da investigação,
por serem melhorias objetivas mesmo que não sejam a causa raiz do incidente.

A reprodução local por carga não confirmou a causa raiz (ver seção anterior). Opções, não excludentes:

1. ~~Corrigir as 4 rotas de checklist agora~~ — **feito em 2026-07-27**, branch
   `fix/checklist-conexao-database-locked`.
2. **Rodar a instrumentação num ambiente real** (dev/staging com uso real ao longo de dias, não só um
   teste de carga sintético de 2 minutos) — I/O de produção (disco de rede, latência) e padrões de uso
   real podem gerar a contenção sustentada que o teste local não conseguiu simular.
3. **Escalar ainda mais o teste local** (mais threads, mais duração, ou simular disco lento) —
   risco de retorno decrescente; já foram 2 rodadas (40 e 120 threads) sem resultado.
4. **Reduzir a transação de `sincronizar_mercado_phone()`** (candidato mais realista, ver seção
   "Instrumentação dinâmica..." acima) — requer investigação de atomicidade antes de alterar, já
   apontada como próximo passo.

Branch `chore/inc-001-instrumentacao-conexoes` permanece pronta e não mergeada, aguardando qual dessas
opções o usuário quer seguir.

---

## Documentos relacionados

- `app.py` (linhas 344-372) — `conectar()`, `_configurar_conexao_sqlite()`, configuração de WAL/timeout
- `docs/engineering/DATABASE.md` — convenções de acesso a banco
- `docs/operations/KNOWN_ISSUES.md` — KI-012 (padrão semelhante de bug de inicialização, resolvido) para referência de como incidentes de banco já foram tratados antes
