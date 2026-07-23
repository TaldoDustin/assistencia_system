# INC-001 — `database is locked`

**Status:** Investigado — causa raiz hipotetizada com evidência concreta, correção **não iniciada**
**Severidade:** P0 (crítico)
**Impacto:** Alto — afeta operações de escrita centrais (criar/editar OS, cadastrar/alterar estoque)
**Ambientes:** Produção, Desenvolvimento
**Reportado por:** Usuário (CTO), 2026-07-23
**Investigado por:** Claude (Principal Engineer), 2026-07-23

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

## Achado principal — causa raiz mais provável

**Conexões que fazem escrita (INSERT/UPDATE/DELETE) sem `try/except/finally` vazam a conexão inteira,
com a transação de escrita ainda aberta, se qualquer exceção ocorrer entre o `conectar()` e o
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
| `POST /api/auth/login` | `irflow_blueprints_api.py:417` | **Altíssima — todo login** |
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

## Próximo passo recomendado (não decidido, aguardando o usuário)

Duas opções, não excludentes:

1. **Instrumentar antes de corrigir** — adicionar log temporário (contagem de conexões abertas/fechadas,
   ou captura de exceção com stack trace quando uma conexão é objeto de GC ainda aberta via
   `sqlite3.Connection.__del__`/`gc` callback) para confirmar em produção/desenvolvimento real qual
   rota realmente vaza, antes de tocar em 14 pontos de código.
2. **Corrigir pelo padrão de maior risco já identificado** — `POST /api/auth/login` é evidência forte o
   suficiente (maior frequência + já é escrita + já está comprovadamente sem proteção) para justificar
   correção isolada e imediata via hotfix, mesmo sem confirmação por instrumentação, seguida de
   correção sistemática dos outros 13 pontos como chore separado.

Nenhuma das duas foi executada nesta sessão — decisão do usuário antes de prosseguir.

---

## Documentos relacionados

- `app.py` (linhas 344-372) — `conectar()`, `_configurar_conexao_sqlite()`, configuração de WAL/timeout
- `docs/engineering/DATABASE.md` — convenções de acesso a banco
- `docs/operations/KNOWN_ISSUES.md` — KI-012 (padrão semelhante de bug de inicialização, resolvido) para referência de como incidentes de banco já foram tratados antes
