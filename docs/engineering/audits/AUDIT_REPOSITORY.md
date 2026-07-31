# AUDIT_REPOSITORY — Estrutura, Arquivos Órfãos e Build (Sprint Housekeeping)

**Data:** 2026-07-31
**Fase:** Sprint Housekeeping — Fase 1 (Auditoria), item 4 de 4 (última auditoria de conteúdo antes de
`AUDIT_BRANCHES.md`/`AUDIT_INFRA.md`)
**Método:** `git ls-files` por categoria + `git log` por arquivo para origem/contexto + inspeção de
conteúdo dos candidatos a remoção. Nenhum arquivo foi alterado, movido ou removido nesta etapa —
apenas levantamento, como nas auditorias anteriores.

**Insumos:** `AUDIT_LEGACY.md`, `AUDIT_DEPENDENCIES.md` (seção 4 já apontava `assets/ir_flow.ico` +
scripts de build desktop como candidatos a investigar).

---

## 1. Arquivos órfãos

| Arquivo | Situação | Recomendação |
|---------|----------|--------------|
| `cleanup_db.py` (raiz) | Script de 9 linhas, sem shebang/docstring, com `DELETE`s hardcoded (`shopping_list` com `produto_nome LIKE 'Peca Teste%'`, usuário `buyer_test`) direto via `from app import conectar`. Não referenciado em nenhum doc, CI ou outro script. Claramente um script de limpeza pontual de dados de teste manual, esquecido na raiz | Investigar com o usuário se ainda é necessário; se não, remover (candidato forte — risco de ser rodado por engano contra um banco real) |

---

## 2. Scripts (`scripts/`, 14 arquivos)

Todos os 14 foram movidos da raiz para `scripts/` num único commit de limpeza anterior
(`94cfdb2`, 2026-07-20, `"chore(cleanup): mover scripts de debug/smoke da raiz para scripts/"`) — ou
seja, já houve uma tentativa de organização, mas sem remoção do que parece morto.

| Script | Referenciado em docs/CI? | Natureza (pelo conteúdo) | Recomendação |
|--------|:--:|---------------------------|--------------|
| `import_legacy_db.py` | Sim (`AUDIT_LEGACY.md`, `AUDIT_DOCUMENTATION.md`) | Ferramenta real de migração, com `--legacy`/`--target` via `argparse` | Manter |
| `migrate_unidades_serializadas.py` | Sim (`MIGRATION_unidades_serializadas.md`, `CHANGELOG.md`) | Migração formal, documentada | Manter |
| `diagnose_mercadophone.py` | Não | CLI de diagnóstico real (`diagnostico_banco_dados`, `diagnostico_configuracoes`, `diagnostico_variaveis_ambiente` — usa `print_ok`/`print_warn`/`print_err`), parece ferramenta operacional útil para produção, não descartável | Manter, mas documentar (nenhum doc menciona como/quando usar) |
| `test_routes.py` | Não | Script de smoke test manual (`BASE_DIR`/`sys.path` boilerplate) pré-pytest | Investigar — provável obsoleto, ver nota abaixo |
| `test_shopping_list.py` | Não | Idem — nome quase idêntico a `tests/test_shopping.py` (suite pytest real, 15 testes) | Investigar — provável obsoleto |
| `test_solution.py` | Não | Docstring "Teste da solução do filtro de data" — script pontual de uma correção específica já em produção | Investigar — provável obsoleto |
| `test_update_os.py` | Não | Docstring "Script para testar atualização manual de uma OS no banco" — usa `sqlite3.connect('database.db')` direto, sem isolamento | Investigar — provável obsoleto, e arriscado se rodado por engano (toca banco real) |
| `test_dashboard_filter.py` | Não | Docstring "Simula diferentes cenários de filtragem" — idem `test_solution.py` | Investigar — provável obsoleto |
| `validate_changes.py` | Não | Docstring "Script de validação das mudanças de sincronização" — idem | Investigar — provável obsoleto |
| `check_old_orders.py` | Não | `sqlite3.connect('database.db')` direto, sem isolamento, verificação pontual de OSs do MercadoPhone | Investigar — provável obsoleto |
| `debug_shopping.py` | Não | Usa `app.test_client()`, login hardcoded com `senha: "irflow@2024"` (mesma senha do `frontend/tests/e2e/app.spec.js` — reforça que é uma senha de seed conhecida, não incidental) | Investigar — provável obsoleto; **a senha reaparecendo aqui é outra ocorrência a atualizar junto do achado já registrado em `AUDIT_DEPENDENCIES.md` seção 5** |
| `smoke_test_full.py` | Não | Boilerplate `BASE_DIR`/`sys.path`, nome genérico "smoke test full" | Investigar — pode ser o mais recente/abrangente dos smoke scripts manuais; comparar com a suíte pytest atual antes de decidir |

**Nota importante:** nenhum destes 8 scripts "Investigar" foi removido aqui — a suíte pytest atual
(682 testes) muito provavelmente já cobre o que eles testavam manualmente, mas isso precisa ser
confirmado item a item (ex.: `test_update_os.py` testa algo que `tests/test_os_update_status.py` não
cobre?) antes de qualquer remoção, seguindo a mesma disciplina de "investigar por conteúdo antes de
remover" já aplicada a branches nesta sprint.

---

## 3. Assets

| Item | Situação | Recomendação |
|------|----------|--------------|
| `assets/ir_flow.ico` | Único arquivo em `assets/`. Usado só por `build_exe.ps1`/`build_setup.ps1`/`installer.iss` (empacotamento desktop legado — ver seção 5) | Decisão amarrada à dos scripts de build desktop: se eles saem, o ícone sai junto |

Nenhum outro asset (logo, imagem de marca) versionado no repositório — a marca Fluxoly hoje existe só
como texto/CSS (`frontend/src/index.css`, `frontend/public/favicon.svg`, `frontend/public/icons.svg` —
esses dois últimos já fazem parte do build do frontend, fora do escopo desta seção).

---

## 4. Pastas

Nenhum diretório vazio ou claramente legado encontrado no conteúdo rastreado pelo git (git não versiona
diretórios vazios, então qualquer pasta remanescente do tipo já teria sido descartada naturalmente).
`.venv/`/`.venv-1/` existem localmente neste ambiente de trabalho, mas são cobertos por
`.gitignore` (`​.venv/`) — não fazem parte do repositório, não é um achado.

---

## 5. Arquivos gerados (`dist/`, caches, artefatos de build)

### `frontend/dist/` — investigação: a Vercel builda do fonte ou serve o `dist/` commitado?

Pergunta levantada nesta sessão: se a Vercel serve o `frontend/dist/` committado (desatualizado, ainda
diz "IR Flow" — achado de `AUDIT_LEGACY.md`), isso seria um problema de produção, não só de repositório.

**Evidência encontrada (sem acesso ao dashboard da Vercel, inferida da configuração versionada):**
- `frontend/vercel.json` não define `buildCommand`/`outputDirectory` — só `rewrites` (fallback de SPA).
  Sem essas chaves, a Vercel usa **detecção automática de framework**: reconhece Vite via
  `frontend/package.json` (`"build": "vite build"`) e roda o build a partir do código-fonte a cada
  deploy, publicando o `dist/` que ela mesma gera — não o commitado.
- `.gitignore` (raiz) já lista `dist/` na seção "Build / dist desktop" — confirma que a **intenção**
  sempre foi não versionar `dist/`. O fato de `frontend/dist/` ainda ter 4 arquivos rastreados é porque
  eles foram commitados antes dessa regra existir (ou antes de cobrir esse caminho específico) e nunca
  foram destrackeados depois — `.gitignore` não afeta arquivos já rastreados.

**Conclusão com confiança alta, não 100% certeza (não tenho acesso ao dashboard Vercel para confirmar
`Output Directory`/`Build Command` configurados manualmente lá, o que sobrescreveria `vercel.json`):**
provavelmente produção está segura — a Vercel builda do fonte, então o `frontend/dist/` commitado e
desatualizado não é servido aos usuários. Mas é uma inferência de configuração, não uma confirmação
direta do dashboard.

| Item | Recomendação |
|------|--------------|
| `frontend/dist/` (4 arquivos rastreados) | **Destrackear** (`git rm -r --cached frontend/dist/`) — já está no `.gitignore`, só nunca foi removido do índice. Resolve o achado de `AUDIT_LEGACY.md` (branding desatualizado) pela raiz, em vez de só regenerar o build |
| Confirmação do dashboard Vercel | Adicionar como item de `AUDIT_INFRA.md` (próxima auditoria) — confirmar/registrar que "Build Command"/"Output Directory" no dashboard não sobrescrevem o comportamento inferido aqui |

---

## 6. Bancos locais (`.db`, backups, arquivos de runtime do SQLite)

| Arquivo | Situação | Recomendação |
|---------|----------|--------------|
| `backup-20260429-015724.db`, `database-pre-cleanup-20260517-123834.db` | Já registrados em **KI-029** — dados operacionais reais versionados no git | Ver KI-029 (decisão pendente do usuário, fora desta sprint) |
| `database.db-shm` (32KB), `database.db-wal` (0 bytes atualmente) | **Achado novo.** Arquivos auxiliares do modo WAL do SQLite — `database.db` em si já está no `.gitignore`, mas os sidecars `-shm`/`-wal` **não** batem no padrão exato `database.db` e ficaram versionados, ainda presentes em `main` hoje. `-shm` é um índice de memória compartilhada que pode conter fragmentos de dados de transações recentes | Mesma natureza do KI-029 — **adicionar a ele**, não abrir um KI novo (é o mesmo padrão: artefato de banco vazando para o git). Ação recomendada de baixo risco, diferente do KI-029 original: `.gitignore` deveria cobrir `database.db-*` explicitamente para não repetir |

---

## 7. Configuração

| Item | Achado | Recomendação |
|------|--------|--------------|
| `FLY_DATA_DIR` (referenciado em `app.py` linhas 164/189) | Variável de detecção de runtime para hospedagem Fly.io — **hospedagem já migrou para Render/Vercel** (confirmado em `DEPLOY.md`/`BRAND_IDENTITY.md`). Código morto de compatibilidade, não afeta nomenclatura (`FLY_*`, não `IR_FLOW_*`), mas é a mesma categoria de dívida (referência a infraestrutura descontinuada) | Investigar se pode ser removido com segurança — fora do escopo de TD-12 (não é nomenclatura legada), mas descoberto na mesma varredura; registrar como achado separado, não misturar com a Fase 4 |
| `.env.example` vs. variáveis lidas em `app.py` | Cobertura boa — únicas ausências (`IR_FLOW_DEBUG_CONN_TRACE`) já são intencionalmente não documentadas por padrão (flag de debug interno, comentada inline no código) | Nenhuma ação |
| `.vscode/settings.json` | Versionado — settings de editor compartilhados. Não inspecionado a fundo o conteúdo | Investigar rapidamente se contém algo específico de uma máquina/pessoa antes de assumir que é intencional |
| `.pre-commit-config.yaml` | Presente e coerente com o CI (`ruff`, etc. — já validado nas sprints de CI/CD) | Nenhuma ação |

---

## 8. Build — arquivos que não deveriam estar versionados

| Item | Situação | Recomendação |
|------|----------|--------------|
| `frontend/dist/*` (4 arquivos) | Ver seção 5 — já coberto por `.gitignore`, nunca destrackeado | Destrackear |
| `database.db-shm`, `database.db-wal` | Ver seção 6 — artefato de runtime, não devia estar no git | Adicionar a KI-029, ajustar `.gitignore` |
| `assets/ir_flow.ico` + `build_exe.ps1` + `build_setup.ps1` + `installer.iss` | Pipeline de build desktop (PyInstaller/Inno Setup) sem nenhuma referência ativa em CI/docs — projeto hoje é 100% web (Render+Vercel) | Investigar com o usuário se a distribuição desktop ainda é um canal usado; se não, remover como bloco único (scripts + ícone, mesma decisão) |

---

## Resumo — itens que precisam de decisão do usuário antes da Fase 3 (Limpeza)

1. `cleanup_db.py` — remover?
2. 8 scripts de `scripts/` marcados "Investigar" — comparar cobertura com a suíte pytest atual antes de decidir remoção
3. `assets/ir_flow.ico` + 3 scripts de build desktop — ainda é um canal de distribuição usado?
4. `frontend/dist/` — destrackear (baixo risco, recomendação clara, não really precisa de debate)
5. `database.db-shm`/`database.db-wal` — adicionar a KI-029 e ajustar `.gitignore` (baixo risco, recomendação clara)
6. `FLY_DATA_DIR` em `app.py` — remover código morto de detecção de runtime Fly.io? (fora do escopo de TD-12, achado incidental)

Nada disso foi executado — todos os itens ficam para a Fase 2 (Planejamento) decidir prioridade e ação,
junto com os achados de `AUDIT_LEGACY.md`/`AUDIT_DEPENDENCIES.md`/`AUDIT_DOCUMENTATION.md`.

## Próximo passo

`AUDIT_BRANCHES.md` — analisar por conteúdo as 30+ branches locais e as branches remotas sem
equivalente local, preservando `demo/commercial-preview` conforme já definido na sprint.
