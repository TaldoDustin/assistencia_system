# INC-001 — `database is locked`

**Status:** Parcialmente corrigido — `POST /api/auth/login` corrigido via hotfix isolado; **13 pontos
de risco identificados na investigação seguem em aberto**, correção sistemática não iniciada
**Severidade:** P0 (crítico)
**Impacto:** Alto — afeta operações de escrita centrais (criar/editar OS, cadastrar/alterar estoque)
**Ambientes:** Produção, Desenvolvimento
**Reportado por:** Usuário (CTO), 2026-07-23
**Investigado por:** Claude (Principal Engineer), 2026-07-23
**Hotfix por:** Claude (Principal Engineer), 2026-07-23 — branch `hotfix/conexao-login-database-locked`

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

| Rota | Arquivo:linha | Frequência de uso |
|---|---|---|
| ✅ `POST /api/auth/login` — **corrigido** (ver seção acima) | `irflow_blueprints_api.py:417` | **Altíssima — todo login** |
| `POST /api/shopping-list` | `irflow_blueprints_api.py:826` | Alta (toda criação de item de compra) |
| `PUT /api/shopping-list/<id>` | `irflow_blueprints_api.py:865` | Alta |
| `PATCH /api/shopping-list/<id>/status` | `irflow_blueprints_api.py:924` | Alta |
| `DELETE /api/shopping-list/<id>` | `irflow_blueprints_api.py:1019` | Média |
| `GET /api/ordens/<id>/checklist` | `irflow_blueprints_api.py:1310` | Média (grava token) |
| `POST /api/ordens/<id>/checklist/token` | `irflow_blueprints_api.py:1344` | Baixa |
| **`POST /api/checklist/<token>`** (salvar checklist público) | `irflow_blueprints_api.py:1445` | **Confirmado ativo — usado por `ChecklistDevice.jsx`, rota pública sem login, exposta a clientes finais via link compartilhado** |
| `POST /nova` (view legada de criar OS) | `irflow_blueprints_orders.py:202` | **Provavelmente morta** — frontend usa `/api/ordens`, não este form legado |
| `GET/POST /custos-operacionais` (view legada) | `irflow_blueprints_admin.py:48` | **Provavelmente morta** — `OperationalCosts.jsx` usa `/api/custos`, não este form legado |
| `GET/POST /login` (view legada) | `irflow_blueprints_auth.py:43` | **Confirmado morta** — `Login.jsx` usa exclusivamente `/api/auth/login` |
| `POST /usuarios/editar/<id>`, `POST /usuarios/deletar/<id>` (views legadas) | `irflow_blueprints_auth.py:125`, `:157` | Provavelmente mortas, não confirmado — `Users.jsx` provavelmente usa `/api/usuarios/*` |
| `POST /estoque/deletar/<id>` (view legada) | `irflow_blueprints_inventory.py:161` | Provavelmente morta, não confirmado |
| `sincronizar_reparos_padrao()` (só roda no startup) | `app.py:1084` | Baixíssima — 1x por boot |

**14 pontos em código ativo** (mais 3 em scripts fora do app), levantados por varredura estática
(regex + análise de bloco de função) — não é uma lista garantida 100% exaustiva, é o melhor
levantamento possível sem instrumentação em runtime. Das rotas confirmadas **realmente em uso pelo
frontend hoje**: `POST /api/auth/login` (altíssima frequência), as 4 rotas de `/api/shopping-list*`
(alta frequência — usadas por `Compras.jsx`), e `POST /api/checklist/<token>` (pública, exposta a
clientes finais).

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

## Próximo passo decidido — instrumentação dinâmica antes de corrigir o restante

Decisão do usuário (CTO), 2026-07-23: não corrigir os 13 pontos restantes ainda. Primeiro, instrumentar
a criação/fechamento de conexões e reproduzir o erro, para identificar exatamente qual rota ou fluxo
segura o lock — só então padronizar as demais rotas. Plano técnico da instrumentação (chokepoint único:
`app.py::conectar()`, gated por variável de ambiente, sem impacto se desligada) apresentado ao usuário
para aprovação antes de implementar, por alterar `app.py` (regra de `CLAUDE.md`: mudança em `app.py`
exige plano e aprovação).

`POST /api/auth/login` permanece corrigido (ver "Correção aplicada" acima) — mantido independente do
resultado da instrumentação, por ser uma melhoria objetiva mesmo que não seja a causa raiz do incidente.

---

## Documentos relacionados

- `app.py` (linhas 344-372) — `conectar()`, `_configurar_conexao_sqlite()`, configuração de WAL/timeout
- `docs/engineering/DATABASE.md` — convenções de acesso a banco
- `docs/operations/KNOWN_ISSUES.md` — KI-012 (padrão semelhante de bug de inicialização, resolvido) para referência de como incidentes de banco já foram tratados antes
