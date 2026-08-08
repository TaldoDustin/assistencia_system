# SPRINT TD-02 — Bootstrap de `app.py`

**Status:** EM ANDAMENTO (Phase 2 — Fatia 1: `fluxoly_config.py`)
**Início:** 2026-08-07
**Tipo:** Refatoração (arquitetura)

---

## Objetivo

Reorganizar `app.py` (2.490 linhas / 100KB) — hoje inicialização, config, camada de conexão/schema de
banco, middleware de autenticação e bootstrap de 20 blueprints todos misturados no mesmo arquivo — em
módulos coesos por responsabilidade, sem quebrar nenhum teste existente nem mudar comportamento.

## Motivação

TD-02 (`docs/operations/PROJECT_STATUS.md`, dívida técnica registrada desde a Sprint 00) — "`app.py`
acumula inicialização, DB e lógica misturadas". Achado concreto e mais recente: **TD-17**, registrado
durante o Architecture Checkpoint pós-MercadoPhone da TD-01 (2026-08-06) — cada domínio extraído de
`fluxoly_blueprints_api.py` encolhia o monólito mas *movia* complexidade para `app.py` (2.414 → 2.490
linhas ao longo da Phase 2 da TD-01, mesmo com o monólito original encolhendo 97%). Decisão do CTO ao
encerrar a TD-01 (2026-08-07): reavaliar TD-02 nesse ponto, já que o tamanho final de `app.py` estava
claro. Sequência a partir daqui, por escolha do CTO: seguir a mesma metodologia validada da TD-01
(Discovery antes de qualquer extração).

## Método

Mesmas quatro fases da TD-01, mesmo compromisso — nenhuma extração de código antes da Phase 1 estar
aprovada:

```
Phase 0 — Architecture Discovery   (este documento)
Phase 1 — Architecture Design      (plano de módulos + ordem de extração + rollback)
Phase 2 — Incremental Extraction   (um módulo por vez: extração → testes → CI → Graphify → checkpoint)
Phase 3 — Cleanup                  (se sobrar código morto/wrappers temporários)
```

---

## Phase 0 — Architecture Discovery

**Método:** mapeamento determinístico via leitura completa + `grep` sobre `app.py` (não estimativa) —
toda contagem abaixo é verificável linha a linha. Nenhum código foi alterado nesta fase.

### 1. Mapa de responsabilidades (11 blocos, por faixa de linha)

| # | Bloco | Linhas | Tamanho | O que faz |
|---|---|---|--:|---|
| A | Imports | 1–157 | 157 | Stdlib, Flask, Prometheus, e ~15 imports de módulos internos (`fluxoly_*`) |
| B | Config de ambiente/paths/feature-flags | 158–256 | ~98 | `DATA_DIR`, `DB_PATH`, diretórios de backup, flags MercadoPhone, `PUBLIC_BASE_URL` |
| C | Bootstrap Flask + segurança de sessão + CORS | 256–432 | ~176 | Sentry, `FLASK_SECRET_KEY` (fail-fast em produção), cookies de sessão, `CORS()`, `_security_headers` (CSP/X-Frame-Options) |
| D | Observabilidade por request | 432–496 | ~64 | Correlation ID (`X-Request-Id`), log estruturado de acesso, `Counter`/`Histogram` do Prometheus |
| E | Helpers soltos | 496–512 | ~16 | `parse_data_ymd`, partials de tabela de preços |
| F | Camada de conexão SQLite | 512–692 | ~180 | Locks de schema, `_configurar_conexao_sqlite`, `_ConexaoRastreada` (instrumentação transparente do INC-001), `conectar()` |
| G | **Schema + migração ad-hoc** | 692–1430 | **~738** | `criar_tabelas()` (24 `CREATE TABLE`, 37 `ALTER TABLE` ad-hoc em `try/except`, 22 `CREATE INDEX`), `forcar_migracao_schema()`, `criar_admin_padrao()` — **maior bloco do arquivo, 30% do total** |
| H | Webhook MercadoPhone (inline) | 1430–1642 | ~212 | `autenticar_integracao_mercado_phone()` + `receber_os_mercado_phone()` — únicas rotas MercadoPhone que a TD-01 **não** moveu para `api_mercadophone.py` (autenticação por token, não sessão) |
| I | Helpers de dashboard/alertas/custos | 1642–1814 | ~172 | `sincronizar_reparos_padrao`, `obter_alertas_sistema`, `listar_custos_operacionais` — injetados como `deps` em múltiplos blueprints (`main`, `api_system`) |
| J | Context processor legado | 1814–1832 | ~18 | `inject_system_alerts` (Jinja, só serve as views server-rendered ainda existentes) |
| K | **Bootstrap de blueprints + auth middleware** | 1838–2360 | **~522** | `ROUTE_PERMISSIONS`, `LEGACY_REACT_REDIRECTS`, `verificar_autenticacao()` (before_request), e **20 `app.register_blueprint(...)`** com dict de `deps` inline cada — achado original da TD-17 |
| L | Endpoints de infra | 2360–2416 | ~56 | `/health`, `/ready`, `/metrics` |
| M | SPA + thread de sync + entrypoint | 2416–2490 | ~74 | `serve_react`/`serve_react_assets`, `iniciar_sync_mercadophone_se_habilitado()`, bloco `__main__` |

### 2. Mapa dos 20 `register_blueprint()` (bloco K)

| # | Blueprint | Módulo | Tamanho do dict de `deps` |
|---|---|---|--:|
| 1 | `main_views` | `fluxoly_blueprints_main` | 18 chaves |
| 2 | `auth_views` | `fluxoly_blueprints_auth` | 7 chaves |
| 3 | `api_shopping` | `api_shopping.py` (TD-01 1º) | 1 chave |
| 4 | `api_garantias` | `api_garantias.py` (TD-01 2º) | 3 chaves |
| 5 | `api_costs` | `api_costs.py` (TD-01 3º) | 2 chaves |
| 6 | `api_prices` | `api_prices.py` (TD-01 4º) | 3 chaves |
| 7 | `api_users` | `api_users.py` (TD-01 5º) | 3 chaves |
| 8 | `api_auth` | `api_auth.py` (TD-01 6º) | 5 chaves |
| 9 | `api_mercadophone` | `api_mercadophone.py` (TD-01 7º) | 8 chaves |
| 10 | `api_reports` | `api_reports.py` (TD-01 9º) | 8 chaves |
| 11 | `api_backup` | `api_backup.py` (TD-01 8º) | 9 chaves |
| 12 | `api_system` | `api_system.py` (TD-01 10º) | 21 chaves |
| 13 | `api_stock` | `api_stock.py` (TD-01 11º) | 5 chaves |
| 14 | `api_os` | `api_os.py` (TD-01 12º) | 32 chaves |
| 15 | `api` (vazio) | `fluxoly_blueprints_api.py` | 0 chaves (KI-032, código morto — TD-18) |
| 16 | `clientes_api` | `fluxoly_clientes_*` | 1 chave (`conectar`) |
| 17 | `unidades_serializadas_api` | `fluxoly_unidades_serializadas_*` | 1 chave (`conectar`) |
| 18 | `produtos_api` | `fluxoly_produtos_*` | 1 chave (`conectar`) |
| 19 | `vendas_api` | `fluxoly_vendas_*` | 1 chave (`conectar`) |
| 20 | `tipos_garantia_api` | `fluxoly_tipos_garantia_*` | 1 chave (`conectar`) |

**Padrão confirmado:** os 5 domínios mais recentes (Clientes, Unidades Serializadas, Produtos, Vendas,
Tipos de Garantia — convenção controller/service/repository de `ENGINEERING_GUIDE.md` §3.1) já usam
`deps` mínimo (`{"conectar": conectar}` só). Os 14 blueprints derivados da TD-01 carregam `deps`
maiores porque herdaram funções que ainda não viraram services formais (ver bloco I e TD-16). `conectar`
aparece em 17 dos 20 dicts — única dependência universal.

### 3. Achado: `criar_tabelas()` (bloco G) é maior que o bootstrap de blueprints (bloco K)

738 linhas contra 522. TD-17 (o achado que motivou esta sprint) documentou só o crescimento do bloco K
— o bloco G nunca foi medido isoladamente antes. Ele já está referenciado por **KI-004/TD-03** ("sistema
de migrations usa `ALTER TABLE` ad-hoc, sem versionamento formal") como dívida técnica distinta. Ponto em
aberto para a Phase 1: mover o bloco G para um módulo próprio (`fluxoly_schema.py` ou similar) **é**
escopo de TD-02 (organização do bootstrap), mas *redesenhar* como sistema de migrations versionado **é**
TD-03 — risco real de confundir as duas se não decidir a fronteira explicitamente antes de extrair.

### 4. Achado: bloco H (webhook MercadoPhone) é a única superfície MercadoPhone que a TD-01 não tocou

A TD-01 (Phase 2, 7º domínio) extraiu `sincronizar`/`reprocessar`/`reimportar`/`status`/`config` para
`api_mercadophone.py`, mas `autenticar_integracao_mercado_phone()`/`receber_os_mercado_phone()` (o
webhook que a Mercado Phone chama de fora, autenticado por token — não por sessão) ficou para trás em
`app.py`. Não é um esquecimento documentado em nenhum KI — pode ser proposital (autenticação
estruturalmente diferente do resto da API) ou pode ser um domínio esquecido. Pergunta em aberto para a
Phase 1.

### 5. Achado: bloco I (`obter_alertas_sistema`/`listar_custos_operacionais`/`sincronizar_reparos_padrao`) é lógica de domínio, não bootstrap

Estas três funções são consumidas como `deps` por `main_views` **e** por `api_system` — não são
inicialização, são lógica de negócio (dashboard/alertas/custos) que mora em `app.py` por history, não por
necessidade. Candidatas naturais a um service formal (mesmo padrão já recomendado para
`estoque_service.py` em TD-16) — mas isso teria que decidir se nasce como parte da TD-02 (bootstrap) ou
fica de fora por ser lógica de domínio, não inicialização.

### 6. Cruzamento com achados já registrados

- **TD-17** (`PROJECT_STATUS.md`): já aponta o bloco K especificamente como candidato — confirmado,
  522 linhas, 20 chamadas, sem registry/factory.
- **KI-004/TD-03** (migrations formais): sobreposição parcial com o bloco G — fronteira a decidir na
  Phase 1 (ver item 3 acima).
- **TD-16** (`estoque_service.py` formal): mesmo padrão de achado que o bloco I acima (lógica de domínio
  presa fora de um service formal) — TD-16 é sobre estoque especificamente, bloco I é sobre
  dashboard/alertas/custos, mas o princípio é idêntico.
- **Nenhuma sobreposição com TD-18** (Phase 3 — Cleanup da TD-01): TD-18 é sobre remover
  `fluxoly_blueprints_api.py`/`create_api_blueprint({})` (linha 2305 do bloco K) — pode acontecer antes,
  depois, ou durante a TD-02 sem conflito real (é a remoção de 1 das 20 chamadas do bloco K).

### 7. Perguntas em aberto para a Phase 1 (não respondidas aqui, propositalmente)

1. O bloco G (schema/migração, 738 linhas) entra no escopo da TD-02 (só mover para módulo próprio, sem
   mudar o mecanismo `ALTER TABLE`/`try-except`) ou fica reservado para uma futura TD-03 (migrations
   formais versionadas)? Fazer as duas juntas violaria a regra de não misturar refatoração com feature/
   redesign.
2. O bloco H (webhook MercadoPhone inline) migra para `api_mercadophone.py` (fechando a lacuna que a
   TD-01 deixou) como parte da TD-02, ou é tratado como um achado à parte (`KI-0XX`) fora de escopo?
3. O bloco I (helpers de dashboard/alertas/custos) vira um service formal (`fluxoly_dashboard_service.py`
   ou similar) como parte da TD-02, ou só muda de arquivo sem virar service (adiando a formalização)?
4. Layout físico do bootstrap de blueprints (bloco K): um módulo único de registry
   (`fluxoly_blueprint_registry.py`, mapa domínio → factory + deps) ou uma função de bootstrap por
   domínio, cada uma perto do respectivo `create_*_blueprint`?
5. `ROUTE_PERMISSIONS`/`verificar_autenticacao()` (parte do bloco K, mas é middleware de segurança
   transversal, não bootstrap de blueprint) — extrai para módulo próprio (`fluxoly_auth_middleware.py`)
   ou permanece em `app.py` por ser o único `before_request` do processo?
6. Ordem de extração mais segura: bloco K (já mapeado por TD-17, menor risco de acoplamento cruzado,
   mesma metodologia comprovada de 12 extrações da TD-01) parece o candidato natural para começar —
   confirmar na Phase 1.
7. Estratégia de rollback por módulo extraído e ponto de checkpoint (Architecture Checkpoint por fatia,
   como na TD-01) — formalizar no plano da Phase 1.

---

## Definition of Done da Phase 0

- [x] Mapa completo de responsabilidades de `app.py` por faixa de linha, com contagem determinística
- [x] Mapa dos 20 `register_blueprint()` e seus `deps`
- [x] Achados cruzados com TD-17, KI-004/TD-03, TD-16, TD-18 — sem sobreposição não identificada
- [x] Perguntas em aberto registradas para a Phase 1, não respondidas nesta fase
- [x] Aprovação do CTO para avançar para a Phase 1 (Architecture Design) — 2026-08-07, escopo fixado
      na matriz de responsabilidades abaixo, sem ampliação

---

## Phase 1 — Architecture Design

**Escopo aprovado pelo CTO (2026-08-07), fixado nesta matriz — nenhum item fora dela entra nesta sprint:**

| Área | Decisão | Tratamento |
|---|---|---|
| Config/env (bloco B) | **Dentro da TD-02** | Módulo próprio |
| CORS/security headers (bloco C) | **Dentro da TD-02** | Factory que recebe `app`; secret key/cookie de sessão continuam em `app.py` (bootstrap real) |
| Blueprint registry + `deps` (bloco K, parte) | **Dentro da TD-02** | Módulo próprio — núcleo da sprint |
| Webhook MercadoPhone (bloco H) | **Dentro da TD-02** | Decisão tomada abaixo (seção 6): reincorporar a `api_mercadophone.py` |
| DB connection (bloco F) | **Fora nesta fatia** | Permanece em `app.py`; `conectar` é passado por injeção para o registry (ver seção 3) |
| Schema/migrations (bloco G) | **Fora — aguarda TD-03** | Nenhuma mudança |
| Helpers de domínio (bloco I) | **Fora da TD-02** | Nenhuma mudança; candidato a um TD novo (dashboard/alertas/custos como service formal) |
| `ROUTE_PERMISSIONS`/`verificar_autenticacao` (parte do bloco K) | **Fora nesta fatia** | Não estava na matriz aprovada — é middleware de segurança transversal, tratamento diferente de "registrar blueprint". Fica em `app.py`; risco de mexer em auth sem pedido explícito é desproporcional ao ganho. Registrado como pergunta em aberto para uma TD-02 futura, não decidido aqui. |

### 1. Layout físico dos novos módulos

Convenção seguida: módulos de infraestrutura/composição usam o prefixo `fluxoly_<assunto>.py`, mesmo
padrão já usado por `fluxoly_logging.py`, `fluxoly_audit.py`, `fluxoly_rate_limit.py`, `fluxoly_web.py` —
**não** a convenção controller/service/repository (`ENGINEERING_GUIDE.md` §3.1), porque essa é para
domínios de negócio com regra própria; bootstrap/composição não é um domínio.

| Módulo novo | Responsabilidade | Linhas estimadas (origem) |
|---|---|---|
| `fluxoly_config.py` | Constantes de ambiente/paths/feature-flags (bloco B) | ~98 |
| `fluxoly_app_security.py` | Factory `configurar_seguranca(app, cors_origins)` — CORS, headers de segurança, handlers `after_request` associados (parte do bloco C) | ~120 |
| `fluxoly_blueprint_registry.py` | Função única `registrar_blueprints(app, runtime)` — as 20 chamadas `register_blueprint(...)` reorganizadas em tabela declarativa + `deps` (bloco K, só a parte de registro) | ~350–400 (redução de ~522, ver seção 5) |

`api_mercadophone.py` (já existe, TD-01) ganha a rota do webhook (bloco H) — não é um módulo novo, é uma
adição a um módulo já extraído.

`app.py` não ganha nenhum módulo novo de sua parte — ele passa a **importar e chamar** os três acima,
mais o que já chama hoje.

### 2. Responsabilidade de cada módulo (contrato)

- **`fluxoly_config.py`**: só leitura de `os.environ` e derivação de constantes — zero import de Flask,
  zero I/O além do `os.makedirs` que já existe hoje (criação de diretórios de dados). Testável por
  importação direta, sem precisar de `app` nem de banco. Mesma garantia que os módulos `fluxoly_reference_data.py`/`fluxoly_core.py` já têm hoje.
- **`fluxoly_app_security.py`**: uma função pública, `configurar_seguranca(app, cors_origins)`, chamada
  uma vez por `app.py` logo após `Flask(__name__)`. Registra `CORS()` (se disponível) e os dois
  `@app.after_request` (`_cors_fallback_headers`, `_security_headers`) internamente — `app.py` não vê
  mais os decoradores, só o resultado. `cors_origins` continua calculado em `app.py` (depende de
  `VERCEL_URL`/`IR_FLOW_CORS_ORIGINS`, que após a extração vêm de `fluxoly_config.py`) e é passado como
  parâmetro — a função não lê `os.environ` diretamente, para não duplicar a fonte de verdade de config.
- **`fluxoly_blueprint_registry.py`**: uma função pública, `registrar_blueprints(app, runtime)`, chamada
  uma vez por `app.py` depois que `conectar`/estado do MercadoPhone/etc. já existem. `runtime` é o único
  objeto que carrega os valores que **não podem** ser importados diretamente (ver seção 3) — tudo o resto
  que os 20 blueprints precisam, o módulo importa direto da fonte real (`fluxoly_os`, `fluxoly_reports`,
  `fluxoly_reference_data`, `fluxoly_config`, etc.), do mesmo jeito que `app.py` faz hoje.

### 3. Como o registry será construído — evitar recriar o problema do bloco K dentro de um arquivo novo

Achado central desta Phase 1: dos ~150 valores distintos usados nos 20 `deps` dicts hoje, a maioria já é
importável diretamente de onde vive de verdade (`fluxoly_os.py`, `fluxoly_reports.py`,
`fluxoly_reference_data.py`, `fluxoly_price_tables.py`, etc.) — só um pequeno grupo é **construído em
runtime dentro de `app.py`** e por isso não pode simplesmente ser importado pelo módulo novo (criaria
import circular: `app.py` importaria o registry, que importaria de volta de `app.py`).

Esse grupo, levantado por evidência (grep dos `deps` atuais que apontam para nomes definidos em `app.py`,
não importados de outro módulo):

| Valor construído em `app.py` | Por quê não é importável direto |
|---|---|
| `conectar` | Fecha sobre `DB_PATH`/config resolvida em runtime |
| `carregar_tabelas_preco`/`salvar_tabelas_preco` | `functools.partial` fechando sobre `PRICE_TABLES_PATH` |
| `forcar_migracao_schema` | Fecha sobre `conectar` |
| `MERCADO_PHONE_RUNTIME_CONFIG`/`MERCADO_PHONE_HELPERS` | Estado mutável de runtime (não constante estática) |
| `listar_custos_operacionais`/`obter_alertas_sistema` | Ficam em `app.py` (bloco I, fora de escopo) — continuam sendo passados por referência, sem mudança |

**Design:** `runtime` é um `dataclass` simples (`fluxoly_blueprint_registry.py::RuntimeDeps`) com esses
~8 campos nomeados — nada de `dict` solto ou `**kwargs` (perderia checagem de nome/typo, que é exatamente
o tipo de erro que um dict inline já esconde hoje). `app.py` monta o `RuntimeDeps` com os valores que já
tem em escopo e chama `registrar_blueprints(app, runtime)`. Tudo o mais que os 20 blueprints precisam
(constantes, funções puras de outros módulos) o registry importa direto no topo do arquivo — exatamente
como `app.py` faz hoje, só que none desses imports precisa mais passar por `app.py`.

**Por que isso não vira "outro monólito":** o registry não ganha nenhuma lógica nova — ele só monta os
mesmos 20 dicts que já existem, na mesma forma. A diferença estrutural é que hoje esses dicts competem
por espaço com config/CORS/schema/webhook/helpers de dashboard no mesmo arquivo (11 responsabilidades
diferentes); no módulo novo, a única responsabilidade é "montar e registrar blueprints" — uma tabela
declarativa (nome → factory → deps), não um script procedural com 11 preocupações misturadas. O tamanho
absoluto (~350–400 linhas) não é o problema — `criar_tabelas()` também é grande e ninguém está propondo
quebrá-la só por tamanho (ver bloco G, fora de escopo). O problema que a TD-17 registrou nunca foi "muitas
linhas", foi "sem registry/factory, cresce a cada domínio sem estrutura" — isso é resolvido pela tabela
declarativa, independente de quantas linhas ela ocupa.

### 4. Como serão as factories de `deps`

Não há "factory" por domínio nova a criar — as 12 factories `create_api_<dominio>_blueprint(deps)` (TD-01)
e as 5 `create_<dominio>_blueprint(deps)` (Clientes/Unidades/Produtos/Vendas/Tipos de Garantia) **já
existem e não mudam**. O que muda é só onde e como o dict `deps` de cada uma é montado — hoje inline
dentro de `app.py`, depois de extraído, inline dentro de `fluxoly_blueprint_registry.py`, seguindo a
mesma tabela `nome_blueprint → função_factory → dict_deps` para as 20 entradas, sem introduzir nenhuma
metaprogramação (nenhuma tentativa de "descobrir" deps automaticamente por reflexão) — decisão deliberada
de manter explícito, mesmo padrão que a TD-01 já validou em 12 extrações.

### 5. Ordem incremental das extrações

Critério: menor acoplamento cruzado primeiro, mesmo princípio da TD-01 (Phase 0, pergunta 1).

| # | Fatia | Risco | Por quê nessa posição |
|---|---|---|---|
| 1 | `fluxoly_config.py` | Muito baixo | Zero dependência de Flask/DB; puramente aditivo, nenhum outro bloco depende de mudança de comportamento aqui |
| 2 | `fluxoly_app_security.py` | Baixo | Depende só de `app` (já existe no momento da chamada) e de `cors_origins` (que passa a vir de `fluxoly_config.py` na fatia 1) — sem depender do registry |
| 3 | `fluxoly_blueprint_registry.py` | Médio | Maior fatia, mas mecânica (mover 20 chamadas já existentes) — feita depois de 1–2 para que `RuntimeDeps` já possa importar config direto em vez de reprocessar o que a fatia 1 acabou de mover |
| 4 | Webhook MercadoPhone → `api_mercadophone.py` | Médio-alto (único com contrato externo ao vivo) | Feita por último, depois que o registry (fatia 3) já registra `api_mercadophone` — evita reordenar registro de blueprint no meio da migração do webhook |

Cada fatia é um commit isolado, testado e validado (Graphify + suíte + smoke) antes da próxima — mesma
disciplina da TD-01, nenhuma fatia começa antes da anterior fechar verde.

### 6. Tratamento específico do webhook MercadoPhone

Confirmado por leitura do código (não suposição): a rota é `POST /api/integracoes/mercadophone/os`
(`app.py:1554`), autenticada por `MERCADO_PHONE_WEBHOOK_TOKEN` via `hmac.compare_digest` (KI-023, já
fail-secure). `api_mercadophone.py` já é um `Blueprint("api_mercadophone", url_prefix="/api")` — adicionar
`@api_mercadophone.route("/integracoes/mercadophone/os", methods=["POST"])` dentro da mesma factory
preserva a **URL efetiva idêntica** (`/api/integracoes/mercadophone/os`), sem quebrar o contrato que o
servidor da Mercado Phone já chama em produção.

`deps` adicionais necessários em `create_api_mercadophone_blueprint`, levantados por grep do corpo atual
de `autenticar_integracao_mercado_phone`/`receber_os_mercado_phone`: `mercado_phone_webhook_token`,
`importar_os_mercado_phone`, `detalhar_os_mercado_phone` — os outros 3 usados
(`conectar`/`mercado_phone_runtime_config`/`mercado_phone_helpers`) **já estão** no dict hoje registrado
pela TD-01, zero duplicação nova.

**Achado colateral (evidência, não decidido aqui):** `ROUTE_PERMISSIONS["receber_os_mercado_phone"] = []`
(`app.py:1898`) já é código morto hoje — `verificar_autenticacao()` retorna antes de consultar
`ROUTE_PERMISSIONS` para qualquer path que comece com `/api/` (bypass por path, não por endpoint), e o
webhook já está sob `/api/`. Mover a rota não muda esse fato. Remover a entrada morta é um `chore:` de
uma linha, seguro para incluir no mesmo commit da fatia 4 (é consequência direta da mudança, não escopo
novo).

**Validação obrigatória antes de considerar a fatia 4 concluída:** requisição real (`curl`, token válido,
payload de amostra) contra o endpoint antes e depois da mudança, resposta idêntica — mesmo rigor usado nos
hotfixes de INC-001/INC-002, por ser contrato externo ao vivo.

### 7. Arquivos tocados por fatia

| Fatia | Arquivos criados | Arquivos modificados |
|---|---|---|
| 1 — Config | `fluxoly_config.py` | `app.py` (remove bloco B, importa de `fluxoly_config`) |
| 2 — Security | `fluxoly_app_security.py` | `app.py` (remove parte do bloco C, chama `configurar_seguranca`) |
| 3 — Registry | `fluxoly_blueprint_registry.py` | `app.py` (remove as 20 chamadas do bloco K, monta `RuntimeDeps`, chama `registrar_blueprints`) |
| 4 — Webhook | — | `api_mercadophone.py` (rota + deps novos), `app.py` (remove bloco H, remove entrada morta de `ROUTE_PERMISSIONS`), `docs/engineering/API_DEPENDENCY_MATRIX.md` (atualizar mapa de deps do domínio) |

Nenhuma fatia toca `tests/` diretamente — a suíte existente já cobre comportamento via `flask.testing`
client, que importa `app` de `app.py` independente de onde o código de composição mora.

### 8. Dependências e consumidores de cada módulo

- `fluxoly_config.py`: sem dependência de outro módulo novo. Consumido por `app.py`,
  `fluxoly_app_security.py` (fatia 2) e `fluxoly_blueprint_registry.py` (fatia 3).
- `fluxoly_app_security.py`: depende de `fluxoly_config.py` (via parâmetro, não import direto de
  `os.environ`). Consumido só por `app.py`.
- `fluxoly_blueprint_registry.py`: depende de `fluxoly_config.py` e de todos os módulos `fluxoly_*`/`api_*`
  já existentes (mesma lista de imports que `app.py` tem hoje para essa finalidade, só que movida).
  Consumido só por `app.py`. Recebe `RuntimeDeps` de `app.py` — não importa nada de `app.py`
  (evita ciclo).
- `api_mercadophone.py`: ganha 3 chaves novas de `deps`, fornecidas por `app.py` via
  `fluxoly_blueprint_registry.py` (fatia 3+4 juntas nesse ponto específico).

### 9. Estratégia de testes

Refatoração pura (composição, não comportamento) — a suíte existente (via `flask.testing` client contra
`app` importado de `app.py`) é a prova primária de regressão, mesmo princípio usado nas 12 extrações da
TD-01. Critério: suíte completa passando, sem regressões (número exato de testes não fixado aqui de
propósito — muda a cada sprint, checar a contagem real no momento de cada fatia em vez de citar um
número que a documentação deixaria desatualizado). Nenhum teste novo é estritamente necessário, mas duas
validações adicionais entram no checklist de cada fatia (mesmo padrão do "diff de rotas antes/depois" do
Sprint 4 original do `ROADMAP.md`):

- **Diff de `app.url_map`** antes/depois de cada fatia — confirma que nenhuma rota foi perdida, duplicada
  ou teve o path alterado (crítico especialmente na fatia 4).
- **Smoke manual** do webhook MercadoPhone (fatia 4, ver seção 6) — único ponto sem cobertura automática
  de contrato externo real. Usar credencial de teste/ambiente controlado (nunca o
  `MERCADO_PHONE_WEBHOOK_TOKEN` real de produção) e payload sintético representativo — a validação prova
  o mecanismo de auth/roteamento, não precisa do segredo real para isso.

### 10. Validações Graphify antes/depois

`graphify update .` ao final de cada fatia (não só no final da sprint) — mesma disciplina da TD-01.
`graphify explain "app.py bootstrap"` antes da fatia 1 (baseline) e depois da fatia 4 (estado final),
comparação manual para confirmar que os novos módulos aparecem como donos das responsabilidades certas e
que `app.py` deixou de aparecer como nó central de bootstrap.

### 11. Estratégia de rollback

Cada fatia é commit único e autocontido (módulo novo + remoção do bloco correspondente de `app.py` no
mesmo commit) — reverter uma fatia é `git revert` de um commit, restaura `app.py` ao estado anterior
exato. Nenhuma fatia depende de uma anterior *não ter sido revertida* para funcionar, exceto a ordem de
criação (fatia 3 assume que `fluxoly_config.py` já existe) — reverter fora de ordem (ex.: reverter a
fatia 1 depois da fatia 3 já ter sido mergeada) quebraria o import; documentado aqui para não ser
surpresa se precisar reverter no meio da sprint.

### 12. Critérios objetivos de Definition of Done (por fatia e da sprint)

Por fatia:
- [ ] Suíte completa passando (0 regressões), `ruff check .` limpo
- [ ] Cobertura não regrediu
- [ ] Diff de `app.url_map` idêntico antes/depois (nenhuma rota perdida/duplicada/com path alterado)
- [ ] `graphify update .` rodado
- [ ] CI verde
- [ ] Commit único, Conventional Commits

Da sprint (após fatia 4):
- [ ] As 4 fatias mergeadas, cada uma com checkpoint próprio
- [ ] Smoke manual do webhook MercadoPhone validado com credencial de teste/ambiente controlado e
      payload sintético representativo (nunca o token real de produção)
- [ ] `app.py` medido: linhas finais e responsabilidades restantes (Architecture Checkpoint Final, mesmo
      formato da TD-01)
- [ ] `PROJECT_STATUS.md`/`CHANGELOG.md`/`KNOWN_ISSUES.md` atualizados (TD-02 movida para Resolvidos,
      TD-17 idem)
- [ ] `API_DEPENDENCY_MATRIX.md` atualizado com o novo `deps` de `api_mercadophone.py`

### 13. Impacto esperado no `app.py`

**O critério de sucesso da TD-02 é arquitetural (responsabilidades corretamente separadas), não uma meta
de linhas.** A contagem abaixo é estimativa de referência para o Architecture Checkpoint, não um alvo —
se a fatia 4 fechar com um número diferente de ~1.740 mas cada responsabilidade estiver no módulo certo,
a sprint continua bem-sucedida.

Antes:
```
app.py
 ├── config
 ├── security (CORS + headers)
 ├── DB connection
 ├── schema/migrations
 ├── webhook MercadoPhone
 ├── helpers de dashboard
 └── 20 × register_blueprint() inline
```

Depois:
```
app.py
 ├── bootstrap mínimo (secret key, cookie de sessão)
 ├── DB connection            (fora de escopo — fica)
 ├── schema/migrations        (fora de escopo — aguarda TD-03)
 ├── helpers de dashboard     (fora de escopo — fica)
 ├── ROUTE_PERMISSIONS / auth middleware  (fora de escopo — fica)
 └── registrar_blueprints(app, runtime)   ← 1 chamada, não 20
```

| Métrica | Antes (hoje) | Depois (estimativa de referência) |
|---|---|---|
| Linhas totais | 2.490 | ~1.740 (estimativa — não é critério de aceite) |
| `register_blueprint()` chamados diretamente em `app.py` | 20 | **1** (chamada a `registrar_blueprints(app, runtime)`) — este sim é critério objetivo |
| Módulos de composição extraídos (config/security/registry) | 0 | 3 — critério objetivo |

A redução de linhas é menor que a da TD-01 (97%) porque o escopo aprovado deliberadamente deixa de fora o
maior bloco do arquivo (schema, 738 linhas) — número esperado, não um desvio a corrigir.

---

## Definition of Done da Phase 1

- [x] Layout físico dos módulos novos definido
- [x] Responsabilidade de cada módulo definida como contrato
- [x] Design do registry e das factories de `deps` (evidência de por que não recria o monólito)
- [x] Ordem incremental de extração com justificativa de risco
- [x] Arquivos tocados por fatia listados
- [x] Dependências/consumidores de cada módulo mapeados
- [x] Estratégia de testes, Graphify e rollback definidas
- [x] Critérios objetivos de DoD por fatia e da sprint
- [x] Tratamento específico do webhook MercadoPhone com evidência de path/deps
- [x] Impacto estimado em `app.py` (linhas e responsabilidades)
- [x] Aprovação do CTO para iniciar a Phase 2 (Fatia 1 — `fluxoly_config.py`) — 2026-08-07, com 3
      ajustes documentais aplicados (smoke test sem token real, número de testes não fixado, impacto em
      linhas tratado como estimativa — não critério de aceite)

---

## Phase 2 — Fatia 1: `fluxoly_config.py` (CONCLUÍDA em 2026-08-07)

Bloco B (`app.py` linhas 158–256 antes desta fatia) movido para `fluxoly_config.py` — só constantes
derivadas de `os.environ` + a função pura `_normalizar_url_publica` + os efeitos colaterais idempotentes
já existentes (`os.makedirs`, cópia condicional de seed de banco/tabela de preços). `app.py` passa a
importar 22 nomes de `fluxoly_config` (`APP_DIR`/`DATA_DIR`/`SEED_DB_PATH` não foram importados de volta —
grep confirmou zero consumidor restante em `app.py` após a extração). `import shutil` removido de `app.py`
(ficou sem uso — os dois `shutil.copy2` que o justificavam foram junto com o bloco).

**Validação:**
- `ruff check app.py fluxoly_config.py` → limpo
- `black --check app.py fluxoly_config.py` → sem alterações necessárias
- `app.url_map` antes/depois: **122 rotas, diff idêntico** (script comparando `sorted(methods) + rule` de
  cada `Rule`, rodado contra o código antes — via `git stash` temporário — e depois da mudança)
- Suíte completa: **682 passando**, 1 falha em `test_sentry_init.py` — confirmada **pré-existente e
  ambiental** (rodada também contra `main` sem a mudança, mesmo erro: `WinError 10106`, provedor Winsock
  do Windows local falhando dentro de `asyncio` importado pelo `sentry_sdk`; CI roda em Linux, não afetado)
- `graphify update .` rodado — `fluxoly_config.py` indexado, aresta `app.py --imports_from--> fluxoly_config` confirmada via `graphify explain`

Nenhuma limpeza adicional feita fora do bloco B (disciplina de não misturar a fatia com outras
oportunidades encontradas no caminho).
