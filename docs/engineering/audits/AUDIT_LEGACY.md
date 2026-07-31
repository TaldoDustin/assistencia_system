# AUDIT_LEGACY — Nomenclatura Legada (TD-12 / Sprint Housekeeping)

**Data:** 2026-07-31
**Fase:** Sprint Housekeeping — Fase 1 (Auditoria), item 1 de 4
**Método:** Graphify (`graphify query`, descoberta arquitetural) + `git grep` sobre arquivos rastreados
(confirmação textual completa, evita falsos negativos do grafo). Nenhum arquivo foi alterado nesta etapa.

**Termos buscados:** `assistencia_system`, `assistencia-system`, `IRFlow`, `irflow`, `IR_FLOW`,
`nt-driver`, `nt_driver`, `NT Driver`.

---

## Resumo executivo

| Termo | Arquivos rastreados (git grep) | Achado principal |
|-------|-------------------------------|-------------------|
| `irflow` (case-insensitive) | 122 | 24 módulos `.py` reais + testes + docs + frontend |
| `IR_FLOW` | 32 | 14 variáveis de ambiente distintas, usadas em produção |
| `assistencia-system` | 10 | **Domínio de produção Vercel ainda ativo** (`assistencia-system.vercel.app`) |
| `assistencia_system` | 5 | Nome do repositório Git, caminhos de exemplo em docs |
| `IRFlow` (mixed-case, sem espaço) | 0 (fora da própria lista de busca) | Não encontrado no código/docs — não existe como grafia real |
| `nt-driver` / `nt_driver` / `NT Driver` | 0 (fora da própria lista de busca) | **Não encontrado em lugar nenhum do projeto** — termo não se aplica a este repositório |

O Graphify confirmou a arquitetura geral (módulos `irflow_*` interligados via `app.py`, comunidade de
sincronização Mercado Phone, etc.) mas a enumeração completa e confiável veio do `git grep` — a
travessia BFS do grafo é amostrada/truncada por orçamento de tokens e não substitui a busca textual
para fins de inventário exaustivo (confirma a expectativa: grafo para arquitetura, grep para
completude).

---

## Achado crítico fora de escopo (reportado, não é nomenclatura)

Durante a busca por `assistencia-system` como URL, dois arquivos de banco de dados foram encontrados
**versionados no git e presentes em `main` até hoje**:

- `backup-20260429-015724.db` (commit `8b69767`, 2026-04-28) — 74 linhas em `os`, 2 em `usuarios`
- `database-pre-cleanup-20260517-123834.db` (commit `252815a`, 2026-05-17)

Ambos parecem conter dados operacionais reais (a tabela `clientes` ainda não existia nesse snapshot,
então nomes de cliente ficavam em campo de texto livre dentro de `os`). Isso não é nomenclatura legada
— é dado potencialmente sensível dentro do histórico do repositório, contrariando a regra "Sempre
manter testes isolados" e o princípio "O banco é sagrado" do `CLAUDE.md`. **Nenhuma ação foi tomada.**
Recomendo tratar como item separado (provável entrada nova em `KNOWN_ISSUES.md` e/ou
`docs/engineering/SECURITY.md`), com decisão explícita sobre remover do working tree vs. reescrever
histórico (esta segunda opção é destrutiva e exigiria aprovação explícita à parte). Registrado aqui
apenas porque foi descoberto durante esta auditoria; será formalizado como achado independente de
TD-12/nomenclatura, não misturado com a Fase 3 (Limpeza) da Housekeeping sem decisão própria.

---

## 1. Código — módulos Python com prefixo `irflow_`

24 arquivos, todos ativos (nenhum morto/órfão — todos importados por `app.py` ou por outro módulo do
domínio):

| Arquivo | Categoria | Recomendação |
|---------|-----------|--------------|
| `irflow_audit.py` | código | Renomear |
| `irflow_blueprints_api.py` | código | Renomear (arquivo ~130KB, TD-01 — considerar se a quebra em módulos menores acontece antes ou depois do rename) |
| `irflow_blueprints_auth.py` | código | Renomear |
| `irflow_blueprints_main.py` | código | Renomear |
| `irflow_clientes_controller.py` | código | Renomear |
| `irflow_clientes_repository.py` | código | Renomear |
| `irflow_clientes_service.py` | código | Renomear |
| `irflow_core.py` | código | Renomear |
| `irflow_logging.py` | código | Renomear |
| `irflow_mercadophone.py` | código | Renomear |
| `irflow_os.py` | código | Renomear |
| `irflow_price_tables.py` | código | Renomear |
| `irflow_produtos_controller.py` | código | Renomear |
| `irflow_produtos_repository.py` | código | Renomear |
| `irflow_produtos_service.py` | código | Renomear |
| `irflow_rate_limit.py` | código | Renomear |
| `irflow_reference_data.py` | código | Renomear |
| `irflow_reports.py` | código | Renomear |
| `irflow_storage.py` | código | Renomear |
| `irflow_unidades_serializadas_controller.py` | código | Renomear |
| `irflow_unidades_serializadas_repository.py` | código | Renomear |
| `irflow_unidades_serializadas_service.py` | código | Renomear |
| `irflow_validation.py` | código | Renomear |
| `irflow_web.py` | código | Renomear |

Todos seguem o mesmo padrão de rename já usado com sucesso para os módulos `fluxoly_vendas_*` e
`fluxoly_tipos_garantia_*` (ADR-008) — renomear arquivo, atualizar imports, rodar testes.

### Achado — referências mortas em `pyproject.toml`

`known_first_party` (isort) e `source` (coverage) em `pyproject.toml` ainda listam **3 módulos que não
existem mais como arquivo**: `irflow_blueprints_admin`, `irflow_blueprints_inventory`,
`irflow_blueprints_orders`. Provavelmente consolidados em `irflow_blueprints_api.py` em algum momento
sem limpar a config. Não é nomenclatura — é dívida de configuração órfã.

| Item | Categoria | Recomendação |
|------|-----------|--------------|
| `irflow_blueprints_admin` em `pyproject.toml` | configuração | Investigar (confirmar consolidação) e remover |
| `irflow_blueprints_inventory` em `pyproject.toml` | configuração | Investigar e remover |
| `irflow_blueprints_orders` em `pyproject.toml` | configuração | Investigar e remover |

---

## 2. Configuração — variáveis de ambiente `IR_FLOW_*`

14 variáveis distintas, usadas em `app.py`, `irflow_blueprints_api.py`, `irflow_core.py`,
`.env.example`, `tests/conftest.py` e mais 4 arquivos de teste, `frontend/playwright.config.js`,
`DEPLOY.md`:

`IR_FLOW_DATA_DIR`, `IR_FLOW_HOST`, `IR_FLOW_PORT`, `IR_FLOW_PUBLIC_BASE_URL`,
`IR_FLOW_CORS_ORIGINS`, `IR_FLOW_NO_BROWSER`, `IR_FLOW_SESSION_INACTIVITY_MINUTES`,
`IR_FLOW_PASSWORD_RESET_TOKEN_HOURS`, `IR_FLOW_ENABLE_BACKGROUND_JOBS`,
`IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR`, `IR_FLOW_BACKUP_EMAIL`, `IR_FLOW_BACKUP_EMAIL_SENHA`,
`IR_FLOW_BACKUP_EMAIL_DESTINO`, `IR_FLOW_SQLITE_TIMEOUT_SECONDS`, `IR_FLOW_DEBUG_CONN_TRACE`.

| Categoria | Recomendação |
|-----------|--------------|
| Configuração / Infraestrutura | **Investigar antes de renomear.** `IR_FLOW_DATA_DIR` é a variável que ativa `IS_SERVER_RUNTIME` em `app.py` — provavelmente configurada hoje no Render em produção. Renomear a variável no código sem atualizar o dashboard do Render simultaneamente quebra a detecção de runtime silenciosamente (o mesmo tipo de causa-raiz do KI-027 registrado neste projeto). Não é um rename mecânico como os módulos `.py` — precisa de uma janela coordenada com o dashboard de produção (ver `AUDIT_INFRA.md`, ainda não feito). |

---

## 3. Infraestrutura — nomes de produção (fora do repositório, alto risco)

| Item | Onde aparece | Categoria | Recomendação |
|------|---------------|-----------|--------------|
| Nome do repositório GitHub (`TaldoDustin/assistencia_system`) | `git remote -v`, caminhos de exemplo em `docs/engineering/CONTRIBUTING.md`, `scripts/import_legacy_db.py` | infraestrutura | Investigar — já reconhecido conscientemente em ADR-006/ADR-008 como fora de escopo até janela de manutenção planejada |
| URL de produção Render (`irflow-backend.onrender.com`) | `docs/operations/PROJECT_STATUS.md` | infraestrutura | Investigar — mesma decisão consciente das ADRs acima |
| URL de produção Vercel (`assistencia-system.vercel.app`) | `README.md`, `DEPLOY.md`, `.TESTING_REPORT.md`, `app.py` (comentário), `docs/operations/PROJECT_STATUS.md` | infraestrutura | Investigar — idem; mudar a URL pública exige atualizar CORS, bookmarks, e qualquer integração externa que aponte para ela |
| `assets/ir_flow.ico` + `build_exe.ps1` + `build_setup.ps1` + `installer.iss` | raiz do repo | infraestrutura / repositório | Investigar — parecem ser scripts de empacotamento desktop (Windows/PyInstaller) de uma distribuição legada; não referenciados por CI, docs ativos, nem pelo fluxo atual (Render+Vercel). Candidato a `AUDIT_REPOSITORY.md` (possível remoção), não apenas rename |

**Nota:** ADR-006 e ADR-008 já documentam explicitamente que o rename de repositório/domínio de
produção foi uma decisão consciente de não fazer ainda, por exigir janela de manutenção. Esta
auditoria não contradiz essa decisão — apenas confirma que o item continua pendente e quantifica onde
aparece.

---

## 4. Documentação — referências históricas (deliberadas, não são bugs)

| Arquivo | Natureza | Recomendação |
|---------|----------|--------------|
| `docs/company/BRAND_IDENTITY.md`, `docs/engineering/adr/ADR-006.md`, `ADR-008.md`, `docs/operations/CHANGELOG.md` | Registro histórico explícito do processo de rebranding (V1.0/ADR-006, cronograma) | **Manter** — apagar isso destruiria o histórico de decisão, indo contra a regra "nunca apagar entradas" |
| `.TESTING_REPORT.md` | Relatório histórico de testes, já citado como "não tocado" no próprio CHANGELOG | Manter (registro histórico congelado) |
| `docs/engineering/CONTRIBUTING.md` (`cd assistencia_system`) | Caminho de exemplo que reflete o nome real atual da pasta | Manter até o repositório em si ser renomeado — depois, atualizar junto |
| `scripts/import_legacy_db.py` (comentário de exemplo de path) | Idem | Manter até rename do repositório |

---

## 5. Frontend — branding residual e testes

| Item | Local | Categoria | Recomendação |
|------|-------|-----------|--------------|
| `# Frontend IR Flow` | `frontend/README.md:1` | documentação | Renomear |
| `IR Flow API Client`, logs `[IR Flow] ...` (5 ocorrências) | `frontend/src/api/client.js` | código | Renomear |
| Comentário "IR Flow brand palette" | `frontend/src/index.css:4` | código (comentário) | Renomear |
| Comentários citando `irflow_core.py`/`irflow_reference_data.py`/`irflow_unidades_serializadas_service.py` como fonte de verdade | `frontend/src/lib/constants.js`, `Produtos.jsx`, `UnidadesSerializadas.jsx`, `Users.jsx` | código (comentário) | Atualizar quando os módulos backend forem renomeados (Fase 4, passo 4→depois do passo 1) |
| `ADMIN_PASS = "irflow@2024"` | `frontend/tests/e2e/app.spec.js:4` | testes | Renomear; confirmar antes que não é reaproveitada como senha real de nenhum ambiente (parece ser só seed local de E2E) |
| `<title>IR Flow — Assistência Técnica</title>` | `frontend/dist/index.html:7` | build (gerado) | **Não é rename** — o `frontend/index.html` fonte já foi corrigido para "Fluxoly" em 2026-07-17 (commit `83d8c29`); o `frontend/dist/` commitado está desatualizado (último touch 2026-06-09, antes do fix). Rebuildar (`npm run build`) e recommitar antes de fechar a sprint. Vale confirmar também se o deploy Vercel builda a partir do fonte ou serve o `dist/` committado — se for o segundo caso, produção pode estar servindo o título antigo agora |

---

## Termos não encontrados

- **`IRFlow`** (grafia mista, sem espaço) — não existe em nenhum arquivo do projeto além da própria
  lista de busca desta sprint. Provavelmente um alias mencionado de memória, não uma grafia real usada
  no código.
- **`nt-driver` / `nt_driver` / `NT Driver`** — não encontrado em nenhum lugar do projeto (código, docs,
  infra, testes). Não se aplica a este repositório; manter na lista de busca por precaução em futuras
  reindexações, mas não gerar nenhuma ação.

---

## Próximo passo

`AUDIT_DEPENDENCIES.md` — para cada módulo `.py` da seção 1, mapear via Graphify (`graphify path` /
`graphify explain`) quem importa e quem seria impactado pelo rename, para ordenar a Fase 4 do menor
para o maior risco.
