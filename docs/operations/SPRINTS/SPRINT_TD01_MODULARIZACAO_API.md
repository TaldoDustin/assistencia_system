# SPRINT TD-01 — Modularização de `fluxoly_blueprints_api.py`

**Status:** EM ANDAMENTO (Phase 0)
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

_A definir. Não iniciada._

## Phase 2 — Incremental Extraction

_A definir. Não iniciada._

## Phase 3 — Cleanup

_A definir. Não iniciada._

---

## Documentos relacionados

- `docs/engineering/adr/ADR-002.md` — decisão de fundo + módulos planejados (atualizado nesta Phase 0)
- `docs/engineering/adr/ADR-011.md` — levantamento original (70 rotas/78 deps/13 domínios), 2026-08-03
- `docs/engineering/DOMAIN_MODEL.md` — inventário de domínios existentes
- `docs/engineering/ENGINEERING_GUIDE.md` §3 — convenção controller/service/repository para domínios
- `docs/engineering/audits/AUDIT_DEPENDENCIES.md` — lacuna de acoplamento por injeção de parâmetro
- `docs/operations/KNOWN_ISSUES.md` — KI-003
- `docs/operations/PROJECT_STATUS.md` — TD-01
