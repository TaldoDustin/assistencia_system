# CHANGELOG

Todas as mudanças notáveis neste projeto serão documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).
Versionamento segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

### Adicionado
- `docs/company/BRAND_IDENTITY.md` — Constituição da Marca Fluxoly V1.0 (Product Owner): nome, 6 pilares macrossistêmicos, escopo negativo, promessa de mercado, visão 2030, cronograma de transição técnica de marca. Registra gap conhecido: promessa de rastreamento por IMEI sem suporte na tabela `estoque` hoje
- `docs/engineering/adr/ADR-006.md` — decisão de reorganizar `docs/` em `company/`, `engineering/`, `product/`, `operations/` por audiência, com mapeamento completo arquivo-a-arquivo e cronograma de rename
- Preenchidos a partir de `BRAND_IDENTITY.md`: `docs/company/VISION.md` (Missão, Visão, Valores, Objetivo de Longo Prazo, Critérios de Sucesso) e `docs/company/PRODUCT_REQUIREMENTS.md` (Mercado-alvo, O que NÃO faz, Diferenciais, parte de Problemas Resolvidos) — Persona, Quem Decide a Compra e Modelo de Monetização seguem `TODO`, não respondidos pelo documento de marca
- `docs/product/FEATURE_MATRIX_TEMPLATE.md` seção 1 atualizada com os seis pilares e o gap de rastreamento por IMEI

### Adicionado (cont.)
- `docs/company/PRODUCT_REQUIREMENTS.md` — Persona Primária (Cliente: Dono de Loja de Dispositivos Móveis Premium) preenchida com input direto do Product Owner: perfil, como trabalha hoje, dores, objetivos, o que compra, critérios de compra, objeções, e por que escolhe a Fluxoly. Confirma na prática o gap de rastreamento por IMEI já registrado (dor "IMEIs perdidos ou difíceis de localizar")
- `docs/company/PRODUCT_REQUIREMENTS.md` — "Quem Decide a Compra" respondido (dono da loja); "Modelo de Monetização" parcialmente respondido (assinatura mensal confirmada, estrutura de precificação segue `TODO`); "Problemas Resolvidos" e "Diferenciais" complementados com dados reais de objeção de venda
- `docs/company/PRODUCT_REQUIREMENTS.md` — substituída a ideia de uma única "Persona Secundária" por seção própria "Personas Operacionais" (Usuários, distintos do Cliente que compra): Vendedor preenchido com objetivo/responsabilidades/dores/expectativas; Técnico, Financeiro, Estoque e Administrador registrados como `TODO`, com nota sobre quais já existem como perfil no código hoje (`admin`, `tecnico`, `vendedor`) e quais não existem ainda (Financeiro, Estoque como perfil de usuário). Tabela "Perfil → Interface" registrada como visão de produto, não feature implementada
- `docs/company/VISION.md` — novo valor: "cada profissional deve enxergar apenas o que precisa para executar seu trabalho com máxima eficiência" (princípio de UX derivado do diferencial de interfaces por perfil)
- `docs/engineering/ENGINEERING_GUIDE.md` — critério de UX correspondente adicionado às decisões de frontend (interface por perfil, não tela única para todos)
- `docs/product/BUSINESS_RULES.md` — livro de regras de negócio (BR-001 a BR-022): regras implementadas extraídas linha a linha do código (Autenticação, Estoque, OS, Compras — 16 regras, todas com fonte no arquivo/função) e regras especificadas de Vendas extraídas de `VENDAS.md` (6 regras). Registra achado: `data_finalizado` é limpo ao reabrir uma OS (BR-013), comportamento observado mas não confirmado como decisão deliberada. Registra 3 regras candidatas citadas em conversa, ainda não formalizadas em `VENDAS.md`
- `docs/engineering/DATA_DICTIONARY.md` — governança de dados campo a campo, complementar a `DATABASE.md`: quem cria/altera/exclui/vê cada tabela. Achado: rotas de mutação de OS e Estoque na API aceitam qualquer perfil autenticado, sem restrição — diferente de Usuários (admin-only) e Shopping List (`admin`/`tecnico`/`comprador`). Achado adicional: perfil `"comprador"` checado no código de Shopping List não é um valor de `perfil` documentado no schema (`admin`\|`tecnico`\|`vendedor`) — candidato a esclarecimento com o Product Owner
- `docs/company/OPERATION_SYSTEM.md` — ciclo completo da loja (Fornecedor → Pós-venda). Blocos fundamentados no código/spec existente: Venda, Entrada de Estoque, Assistência, Reserva, Troca (parcial), Garantia (parcial), Compra (parcial). Blocos deixados `TODO` por ausência total de informação: Fornecedor, Cadastro, Anúncio, Entrega, Motoboy, Pós-venda, Financeiro e Caixa (estes dois últimos por decisão explícita de adiamento já registrada em `VENDAS.md`, não por lacuna de documentação)
- `docs/company/DECISION_LOG.md` — histórico executivo de decisões de produto, distinto de ADR (arquitetural). Populado com 10 decisões já tomadas e catalogadas de suas fontes originais (7 de `VENDAS.md`, 2026-07-09; 3 de marca/documentação/UX, 2026-07-10) — nenhuma decisão nova, só indexação cronológica
- `docs/company/NON_FUNCTIONAL_REQUIREMENTS.md` — formulário de requisitos não-funcionais (capacidade, desempenho, timeout de reserva de IMEI, disponibilidade, RTO/RPO de backup, upload, offline, navegadores) — majoritariamente `TODO`, com referências existentes citadas como contexto (gatilhos de revisão de `ADR-003.md`, meta de latência pontual da Sprint 5), nunca como resposta
- Regra de governança de documentação registrada em `docs/README.md`: nenhum documento novo sem responder "que decisão ele ajuda a tomar?"; backlog de documentação futura identificada (`UX_GUIDELINES.md`, `FEATURE_SPEC_FINANCEIRO.md`, `FEATURE_SPEC_ESTOQUE.md`)
- `docs/product/PRODUCT_BACKLOG.md` — fila priorizada de épicos (P0 a P3): Vendas/Clientes/IMEI Individual (P0), Financeiro/Caixa/Dashboard Executivo (P1), WhatsApp/CRM (P2), Multiempresa (P3). Status de cada épico verificado contra o código real antes de publicar (ex.: Dashboard já existe parcialmente — distinção feita entre o básico atual e o "Dashboard Executivo" completo)
- `docs/company/RELEASE_STRATEGY.md` — proposta de versionamento (1.0 já em produção, 1.1 a 2.0 propostas), reconciliando o esboço original desta conversa com as decisões já tomadas desde então (Vendas desacoplado de Caixa/Financeiro). Marcado como proposta técnica — decisão final de nomes/escopo por versão é do Product Owner, mesmo padrão do ADR-005

### Modificado
- Toda a árvore `docs/` reorganizada por audiência (ver `docs/engineering/adr/ADR-006.md` para o mapeamento completo e critério de cada pasta); todos os links relativos entre documentos corrigidos
- `CLAUDE.md`: árvore de "Estrutura de Documentos" e tabela "Leitura Obrigatória" atualizadas para os novos caminhos; `BRAND_IDENTITY.md` adicionado como leitura fundacional
- Rename "Assistência System" → "Fluxoly" (camada de negócio: `README.md`, `CLAUDE.md`, `docs/product/FEATURE_MATRIX_TEMPLATE.md`) e → "Fluxoly Platform" (camada técnica: `docs/engineering/*.md`, `docs/operations/PROJECT_STATUS.md`, `docs/operations/ROADMAP.md`), conforme cronograma de `BRAND_IDENTITY.md` seção 9. Repositório Git, domínio de produção (`assistencia-system.fly.dev`), módulos `irflow_*.py` e `database.db` não foram alterados nesta etapa — fora de escopo até janela de manutenção planejada. `.TESTING_REPORT.md` (registro histórico) não foi tocado
- `docs/engineering/DOMAIN_MODEL.md` — mapa dos domínios de negócio existentes, extraído do código (schema `app.py` + `ARCHITECTURE.md` + `tests/` reais em `main`); cada domínio inclui testes existentes e dependências com outros domínios; registra que "Clientes" não é uma entidade própria hoje (campo texto solto em `os`)
- `docs/engineering/adr/ADR-005.md` — estratégia de multiempresa: alternativas técnicas avaliadas (banco por empresa / `empresa_id` / schema por empresa), decisão pendente do Product Owner
- `docs/engineering/ENGINEERING_GUIDE.md` seção 3.1 — convenção obrigatória de camadas (`controller → service → repository → tests → README`) para domínios de negócio novos, com regra de reuso entre domínios (ex.: `irflow_estoque_service.py` como candidato a serviço compartilhado) e regra inegociável de que um domínio nunca acessa o repository de outro diretamente (só o service do dono)
- `docs/company/PRODUCT_REQUIREMENTS.md` — formulário de requisitos de produto (persona, dores, diferenciais, quem decide a compra, escopo negativo, monetização, mercado-alvo) com perguntas-guia objetivas por seção, seções marcadas `TODO` até decisão do Product Owner
- `docs/company/VISION.md` — formulário de missão, visão, valores e critérios de sucesso do produto, seções marcadas `TODO`
- `docs/product/FEATURE_MATRIX_TEMPLATE.md` — seção 1 (funcionalidades atuais do sistema) completa e extraída do código; seção 2 (comparação com concorrentes) vazia, a preencher após pesquisa de mercado real
- `docs/engineering/ARCHITECTURE.md` e `docs/engineering/DATABASE.md` — documentação obrigatória ausente, extraída do estado real do código
- `tests/test_auth.py` — primeira suíte pytest do projeto (Sprint 2.2): login, logout, sessão e controle de acesso por perfil, isolada via `IR_FLOW_DATA_DIR`
- `irflow_validation.py` (Sprint 2.6): camada compartilhada de parsing de entrada — `parse_int`, `parse_float`, `safe_json`, `validate_positive_number` — usada pelos endpoints JSON de `irflow_blueprints_api.py`
- `tests/test_users.py` — cobertura de CRUD de usuários via `/api/usuarios` (Sprint 2.3): listar, criar, editar, excluir; duplicado, campos obrigatórios, perfil desconhecido, auto-desativação/auto-exclusão bloqueadas
- `tests/test_os_creation_query.py` — cobertura de criação e consulta de Ordens de Serviço via `/api/ordens` (Sprint 2.4): criação válida, campos obrigatórios, dependências (reparo, vendedor, peça), status/valores/data padrão, listagem com filtros, obter por id, histórico de cliente
- `tests/test_os_update_status.py` — cobertura de atualização (`PUT /api/ordens/<id>`) e transição de status (`PATCH /api/ordens/<id>/status`) de OS (Sprint 2.4): matriz completa de transições entre os 4 status válidos, troca de peças
- `tests/test_os_deletion_security.py` — cobertura de exclusão (`DELETE /api/ordens/<id>`) e resiliência de entrada em rotas de OS (Sprint 2.4): SQL injection, payload vazio, JSON malformado
- `tests/test_permissions.py` — matriz de acesso por perfil (admin/tecnico/vendedor) em rotas admin-only legadas e API, cobrindo 200/401/403/404 (Sprint 2.3)
- `tests/test_session.py` — cobertura de sessão: expiração (cookie forjado), cookie adulterado/não assinado, logout múltiplo, acesso após logout (Sprint 2.3)
- `tests/test_security.py` — cobertura de resiliência de entrada em `/api/auth/login`: SQL injection, campos obrigatórios, payload vazio, JSON malformado, Content-Type incorreto (Sprint 2.3)
- `tests/test_stock_creation_query.py` — cobertura de cadastro e consulta de itens de estoque via `/api/estoque` (Sprint 2.5): criação, campos obrigatórios, normalização de tipo/qualidade/modelo, filtros de listagem
- `tests/test_stock_movement.py` — cobertura de movimentação de estoque (Sprint 2.5): entrada/saída via ajuste, saldo final, consumo FIFO de lotes
- `tests/test_stock_os_integration.py` — cobertura de integração estoque × Ordem de Serviço (Sprint 2.5): consumo automático, múltiplas peças, mesma peça em mais de uma OS, devolução (cancelamento/exclusão), alteração/remoção/substituição de peças, compatibilidade por modelo
- `tests/test_stock_security.py` — cobertura de segurança e exclusão de estoque (Sprint 2.5): sem sessão, SQL injection, payload inválido, exclusão bloqueada quando peça em uso em OS aberta
- `tests/test_pricing.py` — cobertura de tabela de preços (restante da Sprint 2): testes unitários de `irflow_price_tables.py` (normalização de modelo/serviço, `sugerir_preco_tabela`, `encontrar_servico_tabela` com correspondência fuzzy) e testes de integração de `GET/POST /api/precos`, `GET /api/precos/sugerir`, `POST /api/precos/excluir`
- `tests/test_shopping.py` — cobertura completa de `/api/shopping-list` (restante da Sprint 2): CRUD, paginação/filtros, workflow de transição de status (matriz de transições válidas/inválidas, idempotência, estado terminal `CANCELADO`), bloqueio de compra simultânea, cancelamento (soft delete), agrupamento (`/grouped`) e auditoria (`/logs`, BR-016)
- `docs/product/features/CLIENTES.md` — spec do épico P0 Clientes: fluxo, modelo de dados (`clientes` + migração aditiva `os.cliente_id`), wireframes conceituais, casos de erro, critérios de aceite. Decisões de negócio pendentes (deduplicação, campos adicionais) marcadas `TODO`, sem validação do Product Owner ainda
- `docs/product/features/IMEI.md` — spec do épico P0 IMEI Individual: fluxo, modelo de dados (`estoque_unidades` + `estoque.requer_imei`), wireframes conceituais, casos de erro, critérios de aceite. Mesma ressalva de `CLIENTES.md` sobre decisões pendentes
- `irflow_rate_limit.py` (Sprint 3, Unidade 1): rate limiting de login via tabela SQLite `login_attempts` (KI-001) — 5 tentativas/minuto por identificador em `POST /api/auth/login` e `POST /login`. Contador em SQLite em vez de memória de processo porque o Gunicorn de produção roda com `--workers 2`; identificador resolvido via `Fly-Client-IP`/`X-Forwarded-For`/`remote_addr` (nenhum desses headers era lido antes). `tests/test_rate_limit_login.py` (7 casos) e fixture autouse `_limpar_login_attempts` em `tests/conftest.py`
- `irflow_core.py::sessao_ainda_ativa` (Sprint 3, Unidade 2): expiração de sessão por inatividade — janela deslizante de 30 min (`IR_FLOW_SESSION_INACTIVITY_MINUTES`), aplicada uma única vez em `verificar_autenticacao()` (`app.py`) e cobrindo tanto views legadas quanto `/api/*` (achado: as duas superfícies passavam pelo mesmo `before_request` global antes de qualquer bypass de endpoint). `tests/test_session_inactivity.py` (11 casos)
- `irflow_audit.py::registrar_log_auditoria` + tabela `audit_log` (Sprint 3, Unidade 3): auditoria central reutilizável (entidade/entidade_id/ação/antes/depois) para novos domínios, em vez de replicar o padrão `shopping_list_logs` por domínio a cada feature nova — esse padrão existente não foi tocado/migrado. Primeiros consumidores: Clientes e `estoque_unidades` (Sprint P0.1, ainda a implementar). `tests/test_audit_log.py` (5 casos, nível de service)
- `POST /api/usuarios/<id>/reset-token` e `POST /api/password-reset/<token>` (Sprint 3, Unidade 4): recuperação de senha via token de uso único gerado pelo admin — mecanismo escolhido no lugar de self-service por e-mail (menor escopo, sem infraestrutura de e-mail transacional nova). Token expira em 24h (`IR_FLOW_PASSWORD_RESET_TOKEN_HOURS`), gerar um novo invalida o anterior, mesmo padrão de `secrets.token_urlsafe` já usado em `gerar_token_checklist_os`. `tests/test_password_reset.py` (10 casos)
- Domínio Clientes completo (Sprint P0.1, Unidade 5): `irflow_clientes_controller.py`/`irflow_clientes_service.py`/`irflow_clientes_repository.py` — primeira aplicação real da convenção controller/service/repository de `ENGINEERING_GUIDE.md` §3.1. `GET/POST/PUT/DELETE /api/clientes*` (busca por nome/telefone/CPF, paginação, exclusão bloqueada com OS vinculada — BR-023/BR-024), tabela `clientes` + `os.cliente_id` (aditivo, sem backfill). Sem tela — fundação de backend para o futuro módulo de Vendas. `tests/test_clientes.py` (23 casos). Achado corrigido no processo: `verificar_autenticacao()` (`app.py`) só reconhecia o bypass de `/api/*` pelo nome do blueprint (`api.*`), então um segundo blueprint sob `/api/*` (como `clientes_api`) caía na checagem de sessão legada em vez de deixar o próprio blueprint responder 401 — trocado para checar por `request.path`, cobre qualquer blueprint futuro sob `/api/*` sem precisar atualizar essa lista a cada domínio novo
- Domínio `estoque_unidades` — rastreamento individual por IMEI (Sprint P0.1, Unidade 6): `irflow_estoque_unidades_controller.py`/`_service.py`/`_repository.py`, segunda aplicação da convenção de `ENGINEERING_GUIDE.md` §3.1. `GET/POST /api/estoque-unidades*` e `PATCH /api/estoque-unidades/<id>/status` (transições manuais `disponivel ↔ em_reparo`, `em_reparo/devolvido → disponivel` — BR-025/BR-026), tabela `estoque_unidades` + `estoque.requer_imei`. `reservado`/`vendido` existem no schema mas nenhum endpoint desta sprint os produz/aceita — reservados para o futuro módulo de Vendas. Fecha o gap de marca de rastreamento por IMEI (`BRAND_IDENTITY.md` seção 2). `tests/test_estoque_unidades.py` (20 casos)
- `irflow_vendas_service.py` (Sprint P0.1, Unidade 7): stub vazio (só docstring), placeholder explícito para o futuro domínio Vendas — sem rota, sem tabela, sem wiring em `app.py`, pedido explícito do usuário
- `.env.example` (Sprint 3, Unidade 8): pendente desde a Sprint 2 (T-10) — 26 variáveis documentadas com comentários e defaults seguros, incluindo as 2 novas desta sprint (`IR_FLOW_SESSION_INACTIVITY_MINUTES`, `IR_FLOW_PASSWORD_RESET_TOKEN_HOURS`) e 6 injetadas automaticamente pela plataforma de deploy (Fly.io/Render/Vercel), documentadas como referência
- `docs/engineering/ENGINEERING_GUIDE.md` §3.1 (Sprint P0.1, Unidade 9): adendo registrando a interpretação de "README de domínio = docstring no topo do `_service.py`" quando não há pasta própria — já aplicada em Clientes e `estoque_unidades`, formalizada como precedente para os próximos domínios (Financeiro, Vendas)
- Domínio Produtos — catálogo comercial de venda (Sprint Comercial 0.1, 2026-07-20): `irflow_produtos_controller.py`/`_service.py`/`_repository.py`, terceira aplicação da convenção controller/service/repository de `ENGINEERING_GUIDE.md` §3.1. `GET/POST/PUT/DELETE /api/produtos*` (categoria — iPhone/Apple Watch/AirPods/Acessório —, marca, modelo, cor, capacidade, condição — Novo/Seminovo/Vitrine —, preço de custo/venda, margem calculada, quantidade agregada), tabela `produtos`, domínio **novo e separado** de Estoque (peças de reparo) — decisão investigada e confirmada com o usuário antes de implementar. `categoria`/`condicao` rejeitadas com 400 quando fora da lista fechada, nunca normalizadas silenciosamente (BR-027). Margem nunca persistida (BR-028). Criar/editar/excluir restrito a `admin` (BR-029). Sem tela — fundação de backend para o Épico Vendas. `tests/test_produtos.py` (27 casos)
- `frontend/src/pages/Produtos.jsx` — tela do catálogo comercial (Sprint Comercial 1.1, 2026-07-21): primeira tela do Épico Vendas, consome integralmente `/api/produtos*` sem alterar backend/schema. Cards de resumo (Produtos/Seminovos/Vitrine), badges por categoria com emoji (🟦 iPhone, ⌚ Apple Watch, 🎧 AirPods, 🔌 Acessório), busca client-side combinando descrição/categoria/marca/modelo/cor/capacidade/SKU/condição em uma única caixa (o filtro `q` do backend só cobre descrição/modelo/SKU), coluna "Unidades" com placeholder `—` reservando espaço para o rastreamento por IMEI de uma sprint futura sem precisar mudar o layout depois, status derivado (Disponível/Esgotado/Inativo) a partir de `ativo`+`quantidade`. Escrita (criar/editar/excluir) restrita a `admin` no frontend, espelhando a permissão já existente no backend — leitura liberada para qualquer perfil autenticado (ex.: vendedor). Nova rota `/produtos` e item de menu em `Layout.jsx`. Validado manualmente end-to-end (login, listagem, busca, criar/editar/excluir, visão restrita do perfil vendedor) via app rodando localmente com banco isolado — sem suíte de teste de frontend automatizada (convenção do projeto ainda é só E2E Playwright para fluxos principais, não expandida nesta sprint)
- `frontend/src/pages/Clientes.jsx` — tela de Clientes (Sprint Comercial 1.2, 2026-07-21): segunda tela do Épico Vendas, consome integralmente `/api/clientes*` já existente (Sprint 3 Unidade 5), sem alterar backend/schema. Listagem, busca única (nome/telefone/e-mail/CPF-CNPJ, client-side — o `q` do backend só cobre nome/telefone/cpf_cnpj), cards de resumo, CRUD (criar/editar para qualquer perfil autenticado, excluir restrito a `admin`, espelhando `irflow_clientes_controller.py`). Painel de Perfil do Cliente ao clicar numa linha: dados cadastrais e observações, Histórico de OS via `GET /api/ordens/historico-cliente` (endpoint legado por nome — `os.cliente_id` existe no schema mas nenhum fluxo real o preenche hoje, achado durante a investigação), Garantias via `GET /api/garantias?q=` (parâmetro já suportado pelo backend, só não exposto antes no client `garantias.list`, agora aceita `params`), e Compras como placeholder vazio ("módulo de Vendas em construção") — nenhum endpoint novo criado. Nova rota `/clientes` e item de menu em `Layout.jsx`. Validado manualmente end-to-end (login, listagem, busca, criar/editar/excluir, perfil com histórico de OS e garantia reais a partir de dados semeados via API)

<!-- Sprint 2.4 (testes de OS) segue em branch própria aguardando revisão de
     merge — a entrada de "Adicionado" só entra aqui quando a branch for de
     fato mergeada em main. -->

### Corrigido
- Removido endpoint duplicado `GET/POST/PUT/DELETE /api/shopping-list` legado (baseado na tabela `compras`) em `irflow_blueprints_api.py` — colidia com a implementação atual (tabela `shopping_list`) e causava `AssertionError` do Flask na inicialização, impedindo a aplicação e a suíte de testes de rodar (KI-012)
- Nove rotas de `irflow_blueprints_api.py` (`shopping_list`, `reposicao_sugerida_estoque`, `criar_ordem`, `atualizar_ordem`, `criar_estoque`, `atualizar_estoque`, `criar_custo`, `atualizar_custo`, `salvar_preco`) retornavam 500 não tratado ao receber um valor não numérico em campos parseados com `int()`/`float()`; agora retornam 400 com mensagem de validação (KI-013)
- `PUT /api/estoque/<id>` calculava o diff de movimentação com a quantidade não limitada a zero — enviar quantidade negativa gerava um registro de saída maior que o saldo real no histórico de movimentações (Sprint 2.5, achado durante investigação de testes, hotfix)
- `GET /api/estoque` com qualquer filtro (modelo, tipo ou qualidade) sempre retornava lista vazia, por ordem errada de parâmetros SQL (Sprint 2.5, achado durante investigação de testes, hotfix)
- `PATCH /api/ordens/<id>/status` e `PUT /api/ordens/<id>` aceitavam `status` ausente ou desconhecido e o normalizavam silenciosamente para "Em andamento" em vez de rejeitar — em `PUT`, isso reabria uma OS Finalizada e zerava `data_finalizado` sem erro; ambas as rotas agora exigem `status` explícito e válido (KI-015, hotfix `2defd17`, achado ao retomar o Sprint 2 e revisar a branch `test/sprint-2-4-regras-negocio-os` para merge)
- `POST /api/shopping-list` calculava `quantidade` com `body.get("quantidade_solicitada") or body.get("quantidade")` — como `0` é falsy em Python, enviar `quantidade_solicitada: 0` caía no `or` e virava o default `1` do `parse_int`, antes mesmo de chegar na validação `quantidade <= 0`; o item era criado silenciosamente com quantidade `1` em vez de ser rejeitado (KI-016, hotfix `quantidade-zero-shopping-list`, achado durante a escrita de `test_shopping.py`, C-01+C-04 — ver `ENGINEERING_GUIDE.md` §11)
- `IPHONE_MODELS`/`IPHONE_COLORS` (`irflow_reference_data.py`) desatualizados até iPhone 16e — não permitiam abrir OS para iPhone 17/17 Air/17 Pro/17 Pro Max, únicos dispositivos usados nessa tela (fonte única, sem duplicação, confirmada antes da mudança). Adicionados os 4 modelos; cores usam lista genérica (`Preto`/`Branco`/`Azul`/`Verde`/`Rosa`) em vez de nomes específicos do catálogo oficial Apple — decisão deliberada em revisão para não arriscar nome de cor incorreto sem necessidade comercial ainda (campo não bloqueia a criação da OS; trocar pelos nomes oficiais quando houver essa demanda). Regex de extração de modelo por descrição livre (`extrair_modelo_da_descricao_aparelho`) ajustado para reconhecer o sufixo "air", nunca usado antes nesta lista — sem o ajuste, uma descrição livre como "iPhone 17 Air" seria extraída incorretamente como "iPhone 17" (Hotfix H-002, `fix/catalogo-iphone-17`, branch a partir de `main`). Comentário adicionado acima de `IPHONE_MODELS` documentando os 5 consumidores da lista (Nova OS, Editar OS, Estoque, Tabela de Preços, `API /api/constantes`), para reduzir o risco de desatualização silenciosa no futuro. Nenhuma mudança de schema/endpoint/regra de negócio. Validado com a suíte completa (407 testes, sem regressão) e manualmente: criação real de OS com modelo "iPhone 17 Pro Max" via API e via tela `NewOrder.jsx`
- `ruff check .` estava vermelho em `main` com 175 erros, bloqueando o job `Lint` do CI e, por `needs: lint`, os jobs `backend`/`frontend` para qualquer PR (KI-017). Resolvido em 6 commits atômicos na branch `chore/fix-ruff-lint-ki-017`: 11 scripts de debug/smoke pré-pytest movidos da raiz para `scripts/` (95 erros, zero mudança de conteúdo), auto-fixes seguros do ruff nos módulos de produção, 28 idiomas `try/except/pass` convertidos para `contextlib.suppress` (mesmo comportamento), remoção de bindings `deps[...]` não usados, e 17 correções pontuais (loop vars não usadas, `raise ... from`, simplificações de `if`/builtin). `ruff check .` → 0 erros. 407 testes, 100% passando, cobertura 48%. Esta branch só chegou a `origin/main` em 2026-07-21, junto do merge da Sprint Comercial 1.1 (Tela Produtos) — apesar de já registrada aqui como concluída em 2026-07-20, o merge efetivo em `origin/main` não havia acontecido até então
- Removido bloco morto duplicado de `criar_estoque()` em `irflow_blueprints_api.py` (linhas ~224–272, sem `@api.route`, nunca roteado, sobrescrito pela versão real mais abaixo) — resíduo do mesmo merge que originou KI-012 (KI-014, achado durante a correção de KI-017). Nenhum efeito em runtime
- `getOrderDisplayNumber` (`frontend/src/lib/constants.js`) sempre exibia o `id` interno da OS, mesmo para Ordens de Serviço importadas do MercadoPhone — deveriam mostrar `os.id_externo_integracao` (número real da integração), já existente no schema e já retornado por `GET /api/ordens`, só nunca usado pela função de exibição. Regressão de 2026-06-09 (commit `fda0929`, "fix shopping list mismatch") que removeu a preferência pelo número externo inteira ao corrigir um truncamento (`.slice(-5)`) que era o bug real da época. Restaurada a preferência pelo número externo quando `origem_integracao === "mercado_phone"`, sem reintroduzir o truncamento (KI-021, Hotfix H-003, pedido do usuário — CTO). Nenhuma mudança de schema/backend. Validado manualmente: OS nativa exibe id interno, OS de origem MercadoPhone exibe o número externo

### Modificado
- `irflow_blueprints_api.py` (Sprint 2.6): ~30 pontos de parsing/validação já protegidos (20x `request.get_json(silent=True) or {}`, checagens de valor positivo em estoque/custos, parsing de quantidade em shopping-list e config do MercadoPhone) substituídos pela camada compartilhada de `irflow_validation.py` — sem mudança de comportamento observável
- `pyproject.toml`/`.github/workflows/ci.yml` — cobertura tornada bloqueante no CI (`fail_under = 40`, removido `continue-on-error`), antecipando o cronograma original que só previa bloqueio a partir da Sprint 3 (20%) — cobertura real medida (43%) já passava da meta de 40% da Sprint 2, decisão explícita do usuário de não segurar o gate abaixo do que a suíte já garante
- `docs/product/features/VENDAS.md` — adicionadas as seções "Modelo de dados", "Wireframes conceituais" e "Dependências" (faltantes desde a criação em 2026-07-09); nenhuma decisão já tomada foi alterada
- `docs/product/PRODUCT_BACKLOG.md` — Clientes e IMEI Individual atualizados de "Não iniciado" para "Especificação", apontando para `CLIENTES.md`/`IMEI.md`
- Removidas referências operacionais ao Fly.io (`CLAUDE.md`, `README.md`, `DEPLOY.md`, `docs/engineering/ARCHITECTURE.md`, `ENGINEERING_GUIDE.md`, `SECURITY.md`, `docs/operations/PROJECT_STATUS.md`, `ROADMAP.md`, `docs/company/BRAND_IDENTITY.md`, `.env.example`, `.gitignore`) e removido `fly.toml` — produção já migrada para Render (backend) + Vercel (frontend) desde antes desta sprint; achado ao investigar erro real de webhook do Mercado Phone apontando para o domínio antigo do Fly. Comentários em `irflow_rate_limit.py` e `Dockerfile` atualizados (sem mudança de comportamento). Documentos históricos (`.TESTING_REPORT.md`, entradas antigas deste changelog, `KNOWN_ISSUES.md`, sprints já fechadas, ADRs aceitos) preservados sem alteração de propósito

### Adicionado (2026-07-21 — migração ADR-007)
- `docs/engineering/adr/ADR-007.md` — decisão de arquitetura (Aceita): consolidação de rastreamento por IMEI entre Estoque e Produtos. `estoque_unidades` evolui para `unidades_serializadas`, fonte única de verdade para qualquer unidade física da empresa, com origem em Estoque OU Produtos (nunca os dois — Regra de Ouro). Formaliza também o Princípio da Responsabilidade de Transição (cada domínio futuro só transiciona os estados que lhe pertencem)
- `docs/engineering/migrations/MIGRATION_unidades_serializadas.md` — plano técnico de execução da migração (objetivo, impacto arquitetural, estratégia SQLite de recriação de tabela, rollback, checklist de integridade, testes obrigatórios, critérios de aceite, checklist de deploy, riscos, fora de escopo), aprovado pelo usuário (CTO)
- `scripts/migrate_unidades_serializadas.py` — script idempotente de migração (recria a tabela dentro de uma única transação, valida contagem antes de remover a tabela antiga, corrige `sqlite_sequence`); testado contra bancos SQLite descartáveis, nunca executado contra `database.db` real nesta sessão
- `tests/test_migration_unidades_serializadas.py` — suíte dedicada à migração: preservação de dados linha a linha, remoção da tabela antiga, recriação de índices, `sqlite_sequence` sem colisão de PK, idempotência (rodar duas vezes é no-op seguro)

### Modificado (2026-07-21 — migração ADR-007)
- `estoque_unidades` → `unidades_serializadas`: schema em `app.py::criar_tabelas()` (novas colunas `produto_id`, `saude_bateria`, `localizacao`; `estoque_id` relaxado para nullable); `irflow_estoque_unidades_{repository,service,controller}.py` renomeados para `irflow_unidades_serializadas_{repository,service,controller}.py`; rota `/api/estoque-unidades` → `/api/unidades-serializadas`; `tests/test_estoque_unidades.py` → `tests/test_unidades_serializadas.py` (~27 casos, incluindo os novos cenários de origem por `produto_id`). Sem alias de compatibilidade — decisão deliberada do CTO (zero consumidores hoje). Migração implementada e testada apenas contra bancos de teste/locais nesta sessão — a migração do `database.db` de produção é um passo de deploy separado, ainda pendente, seguindo o checklist do plano técnico
- `docs/engineering/DATABASE.md`, `DOMAIN_MODEL.md`, `ENGINEERING_GUIDE.md`, `SECURITY.md` e `docs/product/BUSINESS_RULES.md` (BR-025/BR-026), `docs/product/features/IMEI.md`/`VENDAS.md` (nota pendente da Sprint Comercial 0.1 resolvida) e `docs/product/PRODUCT_BACKLOG.md` — atualizados para refletir o novo nome de tabela/arquivos/rota

### Adicionado (2026-07-22 — Sprint Comercial 1.3.1)
- `frontend/src/pages/UnidadesSerializadas.jsx` — tela de listagem de Unidades Serializadas (busca única por IMEI/modelo/produto, cards de resumo — Unidades/Disponíveis/Em Reparo —, badges de origem Estoque/Produto e de status). Consome `GET /api/unidades-serializadas`, enriquecido com `LEFT JOIN` em `estoque`/`produtos` só para exibição (label de origem, categoria/marca do produto quando aplicável) — nenhuma mudança de filtro ou regra de negócio. Implementada em sessão anterior (branch `feat/tela-unidades-serializadas`), revisada e mergeada nesta sessão: 449 testes (29 em `test_unidades_serializadas.py`) passando, `ruff check .` limpo, lint/build do frontend sem erros novos, validado manualmente rodando o app com unidades seedadas via API a partir de `estoque` e de `produtos` — busca cruzada e badges de origem confirmadas corretas para os dois casos

### Em progresso
- Infraestrutura de CI/CD com GitHub Actions
- Testes backend com pytest e banco in-memory
- Configuração de Ruff para lint do backend
- Documentação de engenharia de nível profissional

---

## [1.1.0] — 2026-06-21

### Adicionado
- Módulo de lista de compras (`shopping_list`): tabela no banco, API REST completa com workflow de status (PENDENTE → EM_COTACAO → EM_COMPRA → COMPRADO → RECEBIDO)
- Endpoint `GET /api/precos/sugerir`: retorna preço total sugerido com base em modelo + reparos selecionados
- Página `Compras.jsx` no frontend com listagem e gestão da lista de compras
- `EditShoppingItemModal`: modal de edição de itens da lista de compras
- `ShoppingModal`: modal de adição de novos itens
- Client dedicado `shoppingList` em `frontend/src/api/client.js`
- Logs de atividade por item de shopping list com exportação

### Corrigido
- `valor_cobrado` agora é auto-preenchido ao selecionar modelo + reparo em nova OS
- `valor_cobrado` não sobrescreve valor existente ao abrir OS para edição (flag `initialized.current`)
- URL do endpoint de PDF IR Phones corrigida (`/irphones` → `/ir-phones`)
- Rota `historico-cliente` apontava para endpoint inexistente em `client.js`
- Campo `cor` agora é limpo ao trocar modelo em `EditOrder.jsx`
- Pipeline de build/dist do frontend corrigido

### Segurança
- Arquivo `.env` removido do repositório (credenciais não mais expostas no histórico git)

---

## [1.0.0] — 2026-05-01

### Adicionado
- Sistema completo de gestão de Ordens de Serviço (OS): criação, edição, exclusão, histórico
- Controle de estoque com movimentações por lotes e SKU
- Tabela de preços por modelo e tipo de reparo
- Kanban board para visualização de OS por status
- Checklist público de dispositivo com token (sem autenticação)
- Rastreamento de garantias com contagem de dias restantes
- Relatórios: IR Phones, Técnicos, Custos Operacionais
- Exportação de relatórios em PDF
- Backup manual e automático com notificação por e-mail
- Integração Google Drive para armazenamento de backups
- Integração MercadoPhone para importação de OS externas
- Gestão de usuários com perfis: admin, vendedor, técnico
- Autenticação via sessão com hash de senha (Werkzeug)
- Deploy em Fly.io com Dockerfile e configuração de produção
- Suporte a build para executável Windows (PyInstaller + InnoSetup)
- CORS configurado para deploy separado frontend/backend

---

## Guia de Versões

| Versão | Sprint | Status |
|--------|--------|--------|
| 1.2.0 (futura) | Sprint 2 | Infraestrutura de qualidade |
| 1.3.0 (futura) | Sprint 3 | Segurança e observabilidade |
| 2.0.0 (futura) | Sprint 4-5 | Refatoração arquitetural |
| 1.1.0 | Sprint 1 | Lançado |
| 1.0.0 | Sprint 0 | Lançado |

---

*Para mudanças em andamento, consulte [`docs/operations/SPRINTS/`](SPRINTS/) e [`docs/operations/PROJECT_STATUS.md`](PROJECT_STATUS.md).*
