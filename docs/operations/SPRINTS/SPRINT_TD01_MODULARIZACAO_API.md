# SPRINT TD-01 — Modularização de `fluxoly_blueprints_api.py`

**Status:** EM ANDAMENTO (Phase 1 concluída, Phase 2 em andamento — 4/12 domínios extraídos)
**Início:** 2026-08-04
**Tipo:** Refatoração (arquitetura)

---

## Objetivo

Decompor `fluxoly_blueprints_api.py` (3.368 linhas, 70 rotas, 13 domínios, 79 valores injetados via
`create_api_blueprint(deps)`) em módulos por domínio, seguindo a decisão de fundo já aceita em `ADR-002`
(atualizada por `ADR-011` e por este Discovery), sem quebrar nenhum dos 682 testes existentes.

## Motivação

TD-01/KI-003 — módulo único demasiado grande, concentra 13 domínios de negócio sem separação. Qualquer
alteração aumenta risco de regressão e dificulta onboarding. Decisão de decompor já tomada há um mês
(`ADR-002`, 2026-07-06) e nunca executada — `ADR-011` formalizou a separação de escopo em relação à
Sprint Housekeeping (TD-12) para não repetir esse padrão.

## Método

Quatro fases, cada uma com saída própria antes de avançar para a próxima. Nenhuma extração de código
acontece antes da Phase 1 estar aprovada.

```
Phase 0 — Architecture Discovery   (este documento)
Phase 1 — Architecture Design      (ADR revisada + plano de migração + rollback)
Phase 2 — Incremental Extraction   (um domínio por vez: extração → testes → CI → Graphify → merge)
Phase 3 — Cleanup                  (código morto, wrappers temporários, documentação, reindexação)
```

Compromisso mantido ao longo das 4 fases: nenhuma mudança estrutural sem Discovery, nenhuma
implementação sem plano aprovado, nenhuma decisão arquitetural sem ADR/plano documentado, cada extração
pequena/testada/reversível/validada por CI (e Graphify, uma vez indexado) antes da próxima.

---

## Phase 0 — Architecture Discovery

**Método:** extração determinística via `grep`/`awk` sobre `fluxoly_blueprints_api.py` (não estimativa)
— toda contagem abaixo é verificável linha a linha. Cruzado contra `ADR-011` (2026-08-03),
`docs/engineering/DOMAIN_MODEL.md` e `docs/engineering/ENGINEERING_GUIDE.md` §3 (convenção
controller/service/repository). Nenhum código foi alterado nesta fase.

### 1. Mapa dos 70 endpoints

Todas as 70 rotas (`@api.route(...)`) mapeadas para método HTTP, path e função handler. Confirma
exatamente a contagem de `ADR-011` — nenhuma divergência encontrada.

| # | Domínio | Rotas | Endpoints (método, path → função) |
|---|---|--:|---|
| 1 | Autenticação | 3 | `POST /auth/login`→`auth_login`, `POST /auth/logout`→`auth_logout`, `GET /auth/me`→`auth_me` |
| 2 | Ordens de Serviço (OS) | 13 | `GET/POST /ordens`→`listar_ordens`/`criar_ordem`, `GET/PUT/DELETE /ordens/<id>`→`obter_ordem`/`atualizar_ordem`/`deletar_ordem`, `PATCH /ordens/<id>/status`→`atualizar_status_os`, `GET /ordens/<id>/checklist`→`obter_checklist_os`, `POST /ordens/<id>/checklist/token`→`gerar_token_checklist_os`, `GET/POST /checklist/<token>`→`obter_checklist_publico`/`salvar_checklist_publico`, `PATCH /ordens/<id>/reparos/<rid>/garantia`→`corrigir_garantia_reparo_route`, `GET /ordens/<id>/reparos/<rid>/historico-garantia`→`historico_garantia_reparo_route`, `GET /ordens/historico-cliente`→`historico_cliente` |
| 3 | Shopping List | 9 | `GET/POST /shopping-list`→`shopping_list`/`shopping_create`, `GET/PUT/DELETE /shopping-list/<id>`→`shopping_get`/`shopping_update`/`shopping_delete`, `PATCH /shopping-list/<id>/status`→`shopping_patch_status`, `GET /shopping-list/grouped`→`shopping_grouped`, `GET /shopping-list/<id>/logs`→`shopping_logs`, `GET /shopping-list/logs/export`→`shopping_logs_export` |
| 4 | Estoque | 6 | `GET/POST /estoque`→`listar_estoque`/`criar_estoque`, `PUT/DELETE /estoque/<id>`→`atualizar_estoque`/`deletar_estoque`, `GET /estoque/reposicao-sugerida`→`reposicao_sugerida_estoque`, `GET /estoque/movimentacoes`→`movimentacoes` |
| 5 | Relatórios (+PDF) | 6 | `GET /relatorios/{ir-phones,tecnicos,custos-operacionais}` + `GET /relatorios/pdf/{ir-phones,tecnicos,custos-operacionais}` |
| 6 | Usuários | 6 | `GET/POST /usuarios`→`listar_usuarios`/`criar_usuario`, `PUT/DELETE /usuarios/<id>`→`atualizar_usuario`/`deletar_usuario`, `POST /usuarios/<id>/reset-token`→`gerar_token_reset_senha`, `POST /password-reset/<token>`→`consumir_token_reset_senha` |
| 7 | Reparos (catálogo padrão) | 4 | `GET/POST /reparos`→`listar_reparos`/`criar_reparo`, `PUT/DELETE /reparos/<id>`→`atualizar_reparo`/`deletar_reparo` |
| 8 | Custos Operacionais | 4 | `GET/POST /custos`→`listar_custos`/`criar_custo`, `PUT/DELETE /custos/<id>`→`atualizar_custo`/`deletar_custo` |
| 9 | Preços | 4 | `GET/POST /precos`→`listar_precos`/`salvar_preco`, `POST /precos/excluir`→`excluir_preco`, `GET /precos/sugerir`→`sugerir_preco` |
| 10 | Backup | 4 | `POST /backup/criar`→`criar_backup_api`, `GET /backup/listar`→`listar_backups`, `GET /backup/download/<file>`→`download_backup`, `POST /backup/restaurar`→`restaurar_backup_upload` |
| 11 | Integrações MercadoPhone | 7 | `POST /integracoes/mercadophone/sincronizar`→`sincronizar_mercadophone`, `POST/GET /reprocessar`(+`/status`), `POST/GET /reimportar`(+`/status`), `GET /status`, `POST /config` |
| 12 | Meta/Sistema | 3 | `GET /constantes`, `GET /alertas`, `GET /dashboard` |
| 13 | Garantias (agregada) | 1 | `GET /garantias`→`listar_garantias` |
| | **Total** | **70** | |

### 2. Mapa das dependências injetadas

`create_api_blueprint(deps)` (linha 23) recebe **79 valores** desestruturados de `deps` logo no início da
função: **78** via `deps["chave"]` (obrigatórios) + **1** via `deps.get("public_base_url", "")`
(opcional). `ADR-011` registrou "78" — a diferença é essa única chave opcional, que grep de `deps\[`
sozinho não captura.

Categorias (não exaustivo por nome, mas cobre a totalidade das 79):
- **Funções de domínio** (a maioria): OS/garantia (`consumir_peca_da_os`, `devolver_pecas_da_os`,
  `resolver_garantias_reparo`, `obter_tipo_garantia`, ~20 nomes), relatórios (`agrupar_relatorio_*`,
  `montar_linhas_relatorio_*`, `montar_pdf_texto`, ~10 nomes), preços (`carregar_tabelas_preco`,
  `salvar_tabelas_preco`), auditoria (`registrar_log_auditoria`), backup
  (`criar_backup`/`enviar_backup_email`/`garantir_pasta_backup_google_drive`), rate limit
  (`resolver_ip_cliente`/`limite_excedido`/`registrar_tentativa`), MercadoPhone (`sincronizar_mercado_phone`
  e variantes), senha (`check_password_hash`/`generate_password_hash`)
- **Constantes/listas de referência**: `iphone_models`, `iphone_colors`, `vendedores`, `tecnicos`,
  `status_os_opcoes`, `os_tipos_opcoes`, `perfis_opcoes`, `categorias_custos`, `reparos_padrao`,
  `produtos_categorias`, `produtos_condicoes`, `garantia_reparo_dias_padrao`
- **Configuração/ambiente**: `backup_dir`, `google_drive_backup_dir`, `backup_email_*` (3), `db_path`,
  `integrations_config_path`, `public_base_url`, `mercado_phone_runtime_config`,
  `mercado_phone_helpers`
- **Infraestrutura**: `conectar` (conexão SQLite), `forcar_migracao_schema`

**Confirma o achado de `AUDIT_DEPENDENCIES.md`:** nenhum desses 79 aparece como `import` de módulo —
grep estrutural de imports subestima sistematicamente o acoplamento real deste arquivo. Qualquer
ferramenta de análise de impacto (Graphify incluso, até reindexação pós-Phase 2) deve tratar esta lista
como a superfície de acoplamento real, não os imports do topo do arquivo.

### 3. Pontos de acoplamento cruzado (evidência, não estimativa)

- **OS → Estoque:** 6 chamadas diretas a funções de estoque dentro da seção de rotas de OS (linhas
  1191-2031): `consumir_peca_da_os` (2×), `devolver_pecas_da_os` (3×), `adicionar_peca_os_sem_consumir`
  (1×) — em `criar_ordem`, `atualizar_ordem` e `atualizar_status_os`.
- **OS → Garantia de reparo:** 14 referências a funções/conceitos de garantia dentro da mesma seção —
  confirma a observação de `ADR-011` de que a maior parte da lógica de garantia injetada só serve rotas
  de OS.
- **OS → MercadoPhone (achado na Phase 1, não capturado aqui):** `listar_ordens()` chama
  `_carregar_config_mercadophone()`/`_atualizar_runtime_mercadophone()` para filtrar OS por
  `sync_start_date`. Ver `docs/engineering/API_DEPENDENCY_MATRIX.md` para o detalhe e a recomendação
  (mover essa lógica de config para `fluxoly_mercadophone.py`).
- **`ENGINEERING_GUIDE.md` §3 já prescreve a resolução para o primeiro ponto:** a lógica de movimentação
  de estoque hoje embutida em `fluxoly_os.py` (`registrar_movimentacao`, `consumir_peca_da_os`,
  `_consumir_lotes_fifo`) é "a candidata natural a virar `irflow_estoque_service.py` formal — OS, Vendas
  e Compras devem consumir esse mesmo service, nunca reimplementar a baixa de estoque cada um à sua
  maneira". Isto não é uma proposta nova deste Discovery — é uma decisão já registrada, ainda não
  executada, que a Phase 1 deveria adotar como parte do design de `api_os.py`/`api_stock.py`.

### 4. Validação da proposta de módulos (`ADR-002`, atualizada nesta Phase 0)

A aproximação preliminar do CTO citada em `ADR-011` (12 nomes) cobre 12 dos 13 domínios — não faltava
nome, faltava mapeamento: **"Reparos" (catálogo padrão, 4 rotas) funde-se em `api_os.py`**, confirmado por
`DOMAIN_MODEL.md` §1.3, que já lista a tabela `reparos` entre as tabelas do domínio OS. Lista completa e
validada registrada em `ADR-002` (seção "Módulos planejados", atualizada nesta sessão) — 12 módulos para
os 13 domínios reais.

### 5. Lacunas de documentação encontradas (não bloqueiam a Phase 1, mas devem ser corrigidas nela)

- `DOMAIN_MODEL.md` não tem entrada própria para **Custos Operacionais** — hoje só aparece na seção
  "O que ainda não é um domínio isolado", ligado a um futuro Financeiro/Caixa que não existe. A Phase 1
  precisa decidir se `api_costs.py` nasce como domínio próprio ou como sub-rota de outro.
- `DOMAIN_MODEL.md` §1.3 (OS) não menciona garantia de reparo (V1.5, `os_reparos`/garantia inline) nem
  o endpoint agregado `/garantias` — a tabela de dependências desse domínio está desatualizada em relação
  ao estado real do código.
- `ROUTE_PERMISSIONS` (dict de autorização por endpoint, `app.py` linha 1882) vive fora do blueprint —
  qualquer decomposição precisa decidir se esse dict acompanha os módulos novos, é fatiado por domínio,
  ou permanece centralizado em `app.py`. Não decidido nesta Phase 0, fica para Phase 1.
- Autenticação e Usuários hoje têm **duas implementações paralelas** (`fluxoly_blueprints_auth.py`
  legado + rotas dentro de `fluxoly_blueprints_api.py`), já registrado em `ARCHITECTURE.md` §3 e
  `DOMAIN_MODEL.md` §1.1 — a Phase 1 precisa decidir se `api_auth.py`/`api_users.py` absorvem também a
  superfície legada ou convivem com ela.

### 6. Único importador confirmado

`app.py` linha 2027 é o único ponto de chamada de `create_api_blueprint(deps)` — confirma `ADR-011`
(a linha mudou de 1911 para 2027 por edições posteriores não relacionadas, ex. `python-dotenv`). Qualquer
estratégia de migração incremental (Phase 2) precisa decidir como múltiplos blueprints coexistem nesse
único ponto de registro durante a transição (todos os domínios ainda não extraídos continuam saindo de
`create_api_blueprint`, os já extraídos registram blueprint próprio) — pergunta em aberto para Phase 1.

### 7. Perguntas em aberto para a Phase 1 (não respondidas aqui, propositalmente)

1. Qual domínio extrair primeiro? (Candidatos por menor acoplamento cruzado: Preços, Backup, Meta/Sistema,
   Custos — todos com "Depende de: nenhum outro domínio" ou próximo disso.)
2. `ROUTE_PERMISSIONS` acompanha os módulos ou permanece centralizado?
3. `api_os.py`/`api_stock.py` adotam a recomendação já existente do `ENGINEERING_GUIDE.md` de extrair
   `estoque_service.py` formal, ou a decomposição da API acontece primeiro e o service depois?
4. Layout físico: arquivo único `api_<dominio>.py` (mais próximo do texto de `ADR-002`) ou trio
   `fluxoly_<dominio>_controller.py`/`_service.py`/`_repository.py` (convenção de `ENGINEERING_GUIDE.md`
   §3.1, já aplicada em Clientes/Unidades Serializadas/Produtos/Vendas)?
5. Como preservar compatibilidade de rotas durante a migração incremental (Phase 2) sem registrar a
   mesma rota Flask duas vezes?
6. Estratégia de rollback por domínio extraído — reverter um commit de extração deveria ser suficiente,
   mas precisa validação explícita no plano de Phase 1.

---

## Phase 1 — Architecture Design

**Status:** CONCLUÍDA (2026-08-04). Nenhum código alterado — respostas às 6 perguntas da Phase 0,
validadas por leitura direta do código (mesmo método da Phase 0), mais um achado novo (helpers
compartilhados) que a Phase 0 não tinha mapeado.

### 0. Achado novo: helpers compartilhados (closures)

Os 70 endpoints não são a superfície inteira a migrar. `create_api_blueprint` define **~25 funções
auxiliares** antes da primeira rota, todas fechadas sobre o mesmo escopo (`deps` desestruturado). Duas
categorias, confirmadas por leitura:

- **Genéricas** (usadas por múltiplos domínios): `usuario_logado()`, `usuario_admin()`, `err(msg, code)`,
  `ok(data, **kwargs)`, `_texto_limpo_local()`, `_to_bool()`. Precisam de um lar compartilhado — nenhum
  dos 12 módulos novos é "dono" delas.
- **Específicas de um domínio**: ex. `_slug_estoque`/`_normalizar_tipo_estoque`/`_gerar_sku_estoque`/
  `_recalcular_custo_medio` (Estoque), `_parse_checklist_json`/`_checklist_status`/`_serialize_checklist`/
  `_buscar_checklist_por_os` (OS/checklist), `_snapshot_reprocessamento_mp`/
  `_executar_reprocessamento_mp_async` (MercadoPhone). Migram junto com as rotas do domínio dono.

**Decisão:** criar `fluxoly_api_helpers.py` (módulo novo, sem prefixo de domínio) só para as funções
genéricas. Cada `api_<dominio>.py` importa dele o que precisar. Inventário exaustivo das ~25 funções
(qual é genérica vs. específica de qual domínio) fica para o início da Phase 2, feito uma vez por domínio
extraído — não vale a pena enumerar as 25 aqui sem o contexto de qual domínio está sendo tocado no
momento.

**Regra de admissão (evita que `fluxoly_api_helpers.py` vire um mini-monólito novo):** nenhum helper
migra para lá "por conveniência". Só entra quando, na extração, ficar comprovado que **dois ou mais**
domínios já extraídos o usam de fato (mesmo teste do achado #2 da `API_DEPENDENCY_MATRIX.md`, que
encontrou `_carregar_config_mercadophone`/`_atualizar_runtime_mercadophone` compartilhados entre OS e
MercadoPhone). Um helper usado por um único domínio permanece nesse domínio, mesmo que pareça genérico
pelo nome.

### 1. Respostas às 6 perguntas da Phase 0

| # | Pergunta | Resposta | Evidência |
|---|---|---|---|
| 2 | `ROUTE_PERMISSIONS` acompanha os módulos? | **Não se aplica.** Confirmado por leitura de `app.py` linha 1882: o dict só tem entradas para `auth_views.*`/`main_views.*`/`static`/o webhook do MercadoPhone — nenhuma das 70 rotas `/api/*` está lá. A autorização de `/api/*` é feita **inline**, dentro de cada handler (`if session.get("usuario_perfil") not in (...)`), ~15 padrões ligeiramente diferentes espalhados pelo arquivo. Migra junto com o handler, sem mudança de comportamento — não é uma decisão a tomar, é um não-problema que a Phase 0 registrou por precaução antes de verificar. |
| 3 | `estoque_service.py` antes ou depois? | **Nem um nem outro — são independentes.** As funções de movimentação de estoque (`consumir_peca_da_os`, `devolver_pecas_da_os`, etc.) já vivem em `fluxoly_os.py`, não dentro do blueprint — extrair `api_os.py`/`api_stock.py` não exige mexer nelas primeiro. Formalizá-las em `estoque_service.py` (recomendação já registrada em `ENGINEERING_GUIDE.md`) é uma melhoria de camada de serviço, ortogonal a esta refatoração de blueprint. **Decisão:** fora do escopo de TD-01, registrar como item de dívida técnica separado (candidato a TD-16) para não misturar os dois tipos de refatoração no mesmo commit. |
| 4 | Layout físico: arquivo único ou trio controller/service/repository? | **Arquivo único `api_<dominio>.py`** (um `Blueprint` por domínio, sem repository/service novos). `ENGINEERING_GUIDE.md` §3 é explícito: a convenção de camadas obrigatória vale para "qualquer domínio de negócio novo… não se aplica retroativamente aos domínios existentes… esses seguem seu próprio plano de decomposição (`ADR-002`)". Adotar o trio completo para 12 domínios de uma vez seria reescrita, não decomposição — contradiz a razão de `ADR-002` ter vencido a Opção B (FastAPI) e a Opção A (manter tudo). Um domínio pode evoluir para o trio completo depois, individualmente (mesmo caminho que Vendas/Clientes/Produtos já percorreram), mas isso é decisão de cada domínio, não desta sprint. |
| 5 | Como coexistir rotas durante a migração incremental? | **Múltiplos `Blueprint` com o mesmo `url_prefix="/api"`, cada um com nome único.** Já é o padrão do projeto: `auth_views` e `main_views` coexistem no mesmo app Flask hoje. Mecânica por domínio extraído: (1) criar `api_<dominio>.py` com `create_api_<dominio>_blueprint(deps)` retornando `Blueprint("api_<dominio>", __name__, url_prefix="/api")`; (2) **remover** as rotas equivalentes de `fluxoly_blueprints_api.py` no mesmo commit (nunca duplicar — Flask rejeita duas regras idênticas); (3) registrar o blueprint novo em `app.py` ao lado do antigo. Testes não precisam mudar: os 6 arquivos de teste que citam `fluxoly_blueprints_api.py` fazem isso só em docstring/comentário — nenhum importa a função diretamente, todos batem em URLs via `Flask test client`. |
| 6 | Estratégia de rollback? | **Um commit por domínio extraído, `git revert` reverte sozinho.** Cada commit de extração: move rotas + helpers específicos, atualiza `app.py` (novo dict `deps` parcial + registro do blueprint), roda a suíte completa (682+ testes) antes do merge. Se um problema aparecer depois do merge, reverter o commit único restaura o domínio inteiro no arquivo monolítico sem afetar os domínios já extraídos antes dele (branches Blueprint independentes, sem dependência estrutural entre commits de domínios diferentes). |
| 1 | Qual domínio extrair primeiro? | Ver ordem recomendada abaixo — não é resposta única, é uma sequência. |

### 2. Ordem de extração recomendada

> **Superseded (2026-08-04, mesma sessão):** a versão original desta seção classificava `api_system.py`
> no Tier 1 ("zero acoplamento"), baseada em `DOMAIN_MODEL.md`. Construir
> `docs/engineering/API_DEPENDENCY_MATRIX.md` (a pedido do CTO, para servir de checklist objetivo da
> Phase 2) mediu o acoplamento real por contagem de `deps`/helpers/serviços tocados e mostrou que
> `/api/dashboard` agrega 22 dependências e 4 serviços — a suposição original estava errada. **A ordem
> vigente é a da seção "Ordem de extração revisada" em `API_DEPENDENCY_MATRIX.md`**, não a lista abaixo,
> mantida só para registro histórico da correção:

Ordem original (não vigente): Preços → Custos → Backup → Garantias → Sistema → Usuários → Estoque →
Shopping → Auth → MercadoPhone → Relatórios → OS. Ordem vigente (por complexidade real medida):
Shopping → Garantias → Custos → Preços → Usuários → Auth → Estoque → Relatórios → Backup →
MercadoPhone → **Sistema** (reclassificado) → OS. Ver `API_DEPENDENCY_MATRIX.md` para o diagrama
completo e a justificativa item a item.

> **Ajuste (2026-08-06, após extração de Preços):** Estoque e Backup trocaram de posição — Backup sobe
> (baixo acoplamento real, maioria das deps é config/string), Estoque desce para imediatamente antes de
> OS (o acoplamento real de Estoque é com OS, não com o restante dos domínios intermediários). **Ordem
> vigente atualizada:** Shopping → Garantias → Custos → Preços → Usuários → Auth → Backup → Relatórios →
> MercadoPhone → Sistema → Estoque → OS. Ver nota equivalente em `API_DEPENDENCY_MATRIX.md`.

### 3. Particionamento de `deps`

Hoje `app.py` monta **um único dict** com 87 chaves (79 realmente lidas pelo blueprint — ver Phase 0
seção 2 — as 8 restantes já são código morto, candidatas a limpeza na Phase 3) e passa para
`create_api_blueprint`. **Decisão:** cada `create_api_<dominio>_blueprint(deps)` novo recebe **só as
chaves que seu domínio usa** — não o dict inteiro. `app.py` monta um dict menor por chamada. Funções
usadas por mais de um domínio (ex. `conectar`, `registrar_log_auditoria`) são passadas para todos os
dicts que precisam — duplicar a passagem é aceitável (é só uma referência à mesma função), duplicar a
lógica não seria.

### 4. Diagrama — estado atual vs. estado-alvo

```mermaid
flowchart LR
    subgraph Hoje["Estado atual"]
        APP1["app.py<br/>(1 dict, 87 chaves)"] -->|"create_api_blueprint(deps)"| MONO["fluxoly_blueprints_api.py<br/>3.368 linhas, 70 rotas, 13 domínios"]
    end
    subgraph Alvo["Estado-alvo (fim da Phase 2)"]
        APP2["app.py<br/>(12 dicts parciais)"] --> M1["api_auth.py"]
        APP2 --> M2["api_os.py (+Reparos)"]
        APP2 --> M3["api_garantias.py"]
        APP2 --> M4["api_stock.py"]
        APP2 --> M5["api_shopping.py"]
        APP2 --> M6["api_reports.py"]
        APP2 --> M7["api_users.py"]
        APP2 --> M8["api_costs.py"]
        APP2 --> M9["api_prices.py"]
        APP2 --> M10["api_backup.py"]
        APP2 --> M11["api_mercadophone.py"]
        APP2 --> M12["api_system.py"]
        M1 -.-> H["fluxoly_api_helpers.py<br/>(usuario_logado, ok/err, etc.)"]
        M2 -.-> H
        M4 -.-> H
        M2 -->|"6 chamadas"| ESTOQUE["fluxoly_os.py<br/>(consumir_peca_da_os etc.)"]
    end
```

### 5. Riscos identificados nesta Phase (além dos já registrados na Phase 0)

| ID | Risco | Mitigação |
|----|-------|-----------|
| RS-01 | Helper genérico usado por um domínio sem ser percebido como genérico durante a extração (ex. um `_slug_estoque` sendo usado fora de Estoque sem estar mapeado) | Rodar suíte completa (682+ testes) a cada extração, não só os testes do domínio tocado |
| RS-02 | `deps` parcial esquecer uma chave que o domínio usa, causando `KeyError` só em runtime (não em import) | Testar boot local (`python app.py` ou suíte) sempre inclui exercitar as rotas do domínio extraído, não só importar o módulo |
| RS-03 | Extração de OS (Tier 3, por último) descobrir que o acoplamento com Estoque é mais profundo do que as 6 chamadas mapeadas | Se acontecer, é motivo para reabrir Phase 1 só para OS/Estoque, não para forçar a extração — critério de parada já coerente com a filosofia do projeto (ver `ENGINEERING_GUIDE.md` seção 11) |

---

## Phase 2 — Incremental Extraction

**Status:** EM ANDAMENTO — 4 de 12 domínios extraídos (Shopping List, 2026-08-04; Garantias, 2026-08-05; Custos Operacionais, 2026-08-06; Preços, 2026-08-06). Regras de execução
definidas na Phase 1, para não decidir mecânica no meio da extração:

**Unidade de trabalho = um domínio inteiro por commit, nunca uma rota isolada.** Cada commit de extração
segue sempre a mesma sequência interna: helpers do domínio → `deps` parcial → `Blueprint` novo → suíte
completa → Graphify (`graphify update .`) → commit. Extrair rota a rota quebraria a coesão do domínio e
multiplicaria o número de vezes que a suíte completa precisa rodar sem reduzir risco.

**Definition of Done por domínio extraído** — todos os 6 critérios, sem exceção, antes do commit:

- [ ] Rota(s) do domínio movidas para `api_<dominio>.py`, registrando `Blueprint("api_<dominio>", __name__, url_prefix="/api")`
- [ ] Helpers específicos do domínio (ver `API_DEPENDENCY_MATRIX.md`) migrados junto; helpers genéricos importados de `fluxoly_api_helpers.py`
- [ ] `deps` reduzido: `app.py` monta um dict só com as chaves daquele domínio (conferir contra a linha do domínio na matriz). Se uma chave for **removida** (não só particionada, como em Preços/`carregar_tabelas_preco`) por não ter mais consumidor no monólito, confirmar com `graphify affected "<funcao>"`/`graphify explain "<funcao>"` **antes** de remover — não só `grep` (achado do CTO após a extração de Preços, 2026-08-06: grep não pega injeção por `deps`/chamada indireta)
- [ ] Suíte completa passando (682+ testes, não só os testes do domínio tocado — ver RS-01)
- [ ] `graphify update .` rodado e validado com duas consultas: `graphify explain "api_<dominio>"` confirma que o módulo novo aparece no grafo com as arestas esperadas; `graphify affected "fluxoly_blueprints_api.py"` confirma que o arquivo monolítico não mantém nenhuma relação residual inesperada com o domínio recém-extraído
- [ ] Nenhuma referência residual ao domínio em `fluxoly_blueprints_api.py` (nem rota, nem helper específico, nem menção em comentário desatualizado)

Ordem de extração: ver `docs/engineering/API_DEPENDENCY_MATRIX.md`, seção "Ordem de extração revisada".

### Log de execução

**1. Shopping List (2026-08-04) — ✅ concluído, todos os 6 critérios do DoD.**
- `api_shopping.py` criado (9 rotas), `fluxoly_api_helpers.py` criado (primeiro uso — `err`/`ok`/
  `usuario_logado`, comprovadamente usados por múltiplos domínios já na matriz da Phase 1).
- **Achado durante a Discovery Local** (não estava na `API_DEPENDENCY_MATRIX.md` original): `_log_shopping()`
  é um helper específico do domínio definido na linha 707, fora do bloco de helpers mapeado na Phase 1
  (linhas 104-421). Motivou um re-scan completo do arquivo, que encontrou **33 helpers reais, não 25** —
  matriz corrigida com a lista completa e um aviso para as próximas extrações refazerem esse scan.
  `_ordem_lista_por_id_desc()` (linha 1182, logo após o bloco de Shopping) foi identificada como
  pertencente a OS, não a Shopping — não migrou.
- Suíte completa (682 testes) passando após a extração, sem alteração de nenhum teste.
- `graphify . --code-only` (primeira indexação real do repo, código apenas — sem custo de LLM) +
  `graphify explain "api_shopping"` (conexões esperadas: `fluxoly_api_helpers`, `fluxoly_validation`,
  importado por `app.py`) + `graphify affected "fluxoly_blueprints_api.py"` (nenhuma referência residual
  específica de Shopping — só consumidores legítimos do restante do arquivo, 61 rotas remanescentes).
- Zero referência residual a `shopping`/`SHOPPING_`/`_log_shopping` em `fluxoly_blueprints_api.py`
  (as únicas menções de `shopping_list` remanescentes são consultas SQL diretas do `/api/dashboard`,
  domínio Sistema — leitura de dado cross-domínio já esperada, não acoplamento de código).

**2. Garantias (2026-08-05) — ✅ concluído, todos os 6 critérios do DoD.**
- `api_garantias.py` criado (1 rota — `GET /garantias`, listagem agregada), reaproveitando
  `fluxoly_api_helpers.py` (nenhum helper novo compartilhado — só `_classificar_garantia`, específico
  do domínio, migrou junto).
- `deps` parcial confirmado exatamente como a matriz previa: `conectar`, `garantia_reparo_dias_padrao`,
  `parse_data_ymd` — os dois últimos permanecem também no dict de `create_api_blueprint` porque OS e
  Sistema (ainda não extraídos) continuam usando-os; duplicar a referência é aceitável (mesma decisão
  já registrada na Phase 1), duplicar a lógica não seria.
- Suíte completa (682 testes) passando após a extração, sem alteração de nenhum teste, incluindo
  `tests/test_listar_garantias.py` intacto. `ruff check .` limpo.
- `graphify update .` + `graphify explain "api_garantias"` (conexões esperadas: importado por `app.py`,
  importa de `fluxoly_api_helpers.py`) + `graphify affected "fluxoly_blueprints_api.py"` (nenhuma
  referência residual específica de Garantias — só consumidores legítimos do restante do arquivo).
- Zero referência residual a `_classificar_garantia`/à rota `/garantias` em `fluxoly_blueprints_api.py`
  — as únicas menções remanescentes de "garantias" são `resolver_garantias_reparo`/
  `gravar_garantias_reparo`, que pertencem ao domínio OS→Garantia de Reparo (escopo de `api_os.py`,
  último da fila de extração), não ao domínio Garantias (listagem agregada) recém-extraído.

**3. Custos Operacionais (2026-08-06) — ✅ concluído, todos os 6 critérios do DoD.**
- `api_costs.py` criado (4 rotas — `GET/POST /custos`, `PUT/DELETE /custos/<id>`), reaproveitando
  `fluxoly_api_helpers.py`. `usuario_admin()` promovido para `fluxoly_api_helpers.py` (já previsto na
  Phase 1, linha 177 — genérico, agora comprovadamente usado por 2+ domínios: o monólito e
  `api_costs.py`); a cópia local em `fluxoly_blueprints_api.py` permanece intacta (mesmo padrão já
  aplicado a `err`/`ok`/`usuario_logado` nas 2 extrações anteriores — remover a duplicação é Phase 3).
- `deps` parcial confirmado exatamente como a matriz previa: `conectar`, `listar_custos_operacionais` —
  este último permanece também no dict de `create_api_blueprint` porque `/dashboard` e
  `/relatorios/custos-operacionais` (Sistema/Relatórios, ainda não extraídos) continuam usando-o;
  duplicar a referência é aceitável, duplicar a lógica não.
- Suíte completa (683 testes) passando após a extração, sem alteração de nenhum teste, incluindo
  `tests/test_api_parsing.py` (bate em `/api/custos*` via Flask test client, não importa a função
  diretamente). `ruff check .` limpo.
- `graphify update .` + `graphify explain "api_costs"` (conexões esperadas: importado por `app.py`,
  importa de `fluxoly_api_helpers.py` e `fluxoly_validation.py`) + `graphify affected
  "fluxoly_blueprints_api.py"` (nenhuma referência residual específica de Custos — só consumidores
  legítimos do restante do arquivo).
- Zero referência residual às rotas `/custos*` (CRUD) em `fluxoly_blueprints_api.py` — as menções
  remanescentes de "custos" são `/relatorios/custos-operacionais` (domínio Relatórios), `custo_pecas`
  (custo de peças da OS) e `_recalcular_custo_medio` (Estoque), todas fora do escopo deste domínio.

**4. Preços (2026-08-06) — ✅ concluído, todos os 6 critérios do DoD.**
- `api_prices.py` criado (4 rotas — `GET/POST /precos`, `POST /precos/excluir`, `GET /precos/sugerir`),
  reaproveitando `fluxoly_api_helpers.py`. Assimetria de autorização original preservada verbatim:
  `sugerir_preco()` exige só `usuario_logado()`, as outras 3 exigem também `usuario_admin()`.
  `sugerir_preco_tabela` (de `fluxoly_price_tables`) migrou junto — só usada por essa rota.
- **Diferente das 3 extrações anteriores:** `carregar_tabelas_preco`/`salvar_tabelas_preco` não têm
  nenhum outro consumidor no monólito (confirmado por grep antes da extração) — as chaves saíram do
  dict de `create_api_blueprint` em `app.py`, em vez de ficarem duplicadas. Primeiro domínio da Phase 2
  a reduzir `deps` de fato, não só particioná-lo.
- Suíte completa (683 testes) passando sem alteração, `ruff check .` limpo, `graphify update .` +
  `graphify explain "api_prices"` confirmado (conexões esperadas: `app.py`, `fluxoly_api_helpers.py`,
  `fluxoly_validation.py`, `fluxoly_price_tables.py`).
- Zero referência residual a `/precos*`, `carregar_tabelas_preco`, `salvar_tabelas_preco` ou
  `sugerir_preco_tabela` em `fluxoly_blueprints_api.py` (grep vazio).

## Phase 3 — Cleanup

_A definir. Não iniciada._

---

## Documentos relacionados

- `docs/engineering/adr/ADR-002.md` — decisão de fundo + módulos planejados (atualizado na Phase 0 e Phase 1)
- `docs/engineering/adr/ADR-011.md` — levantamento original (70 rotas/78 deps/13 domínios), 2026-08-03
- `docs/engineering/API_DEPENDENCY_MATRIX.md` — matriz helpers/deps/serviços por módulo e ordem de extração revisada (Phase 1, ferramenta de checklist para a Phase 2)
- `docs/engineering/DOMAIN_MODEL.md` — inventário de domínios existentes
- `docs/engineering/ENGINEERING_GUIDE.md` §3 — convenção controller/service/repository para domínios
- `docs/engineering/audits/AUDIT_DEPENDENCIES.md` — lacuna de acoplamento por injeção de parâmetro
- `docs/operations/KNOWN_ISSUES.md` — KI-003
- `docs/operations/PROJECT_STATUS.md` — TD-01
