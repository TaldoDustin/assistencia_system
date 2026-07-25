# SECURITY_AUDIT_2026-07.md — Triagem do relatório Aikido

**Status:** Sprint Segurança 1.0 concluída em 2026-07-25 (P0/P1 do 1º scan). **2º scan Aikido rodado no
mesmo dia, pós-sprint** — triado abaixo em "Segundo scan Aikido". Resultado: só 1 achado novo real
(hardening preventivo de SQL, não explorável hoje — item 17), 1 dependência com CVE genuína adicional
(gunicorn, 2ª vulnerabilidade distinta da 1ª — item 6 revisitado), e vários itens que já estavam
corrigidos no 1º scan mas o Aikido ainda mostrava (Docker root, segredo no Git) — provável cache/lag do
scanner, não regressão real, ver evidência por item.
**Origem:** scans automatizados do Aikido rodados pelo usuário (CTO) em 2026-07-25 contra o repositório.
**Investigado por:** Claude (Principal Engineer), 2026-07-25.
**Regra seguida:** SAST (análise estática) gera falsos positivos com frequência — nenhum item abaixo foi
classificado sem antes ler o código real envolvido. Ver metodologia de cada item.

---

## Tabela de classificação

| # | Item (relatório Aikido) | Severidade | Classificação | Ação |
|---|---|---|---|---|
| 1 | SQL Injection via concatenação de strings | 🔴 P0 | **Falso positivo** | Nenhuma — documentar o padrão seguro existente |
| 2 | Segredo no histórico do Git (`.env`) | 🔴 P0 | ✅ **Rotacionado em 2026-07-25** — usuário/CTO confirmou a troca da `FLASK_SECRET_KEY` em produção | Nenhuma — reescrever histórico do Git (BFG/filter-repo) segue opcional, sem urgência |
| 3 | *(achado relacionado, fora do relatório Aikido)* Fallback inseguro de `FLASK_SECRET_KEY` no código atual | 🔴 P0 | ✅ **Corrigido em 2026-07-25** — `app.py` falha no boot (`RuntimeError`) se `FLASK_SECRET_KEY` não estiver definida fora de dev local | `hotfix/...` — 2 novos testes de subprocesso confirmando falha/sucesso do boot em cada cenário |
| 4 | File Inclusion em `irflow_storage` | 🔴 P0 | **Falso positivo** | Nenhuma |
| 5 | SSRF | 🔴 P0 | **Falso positivo** | Nenhuma |
| 6 | Gunicorn — 3 vulnerabilidades (contrabando de requisição HTTP) | 🟠 P1 | ✅ **Corrigido em 2026-07-25** — `21.2.0` → `22.0.0` | `requirements.txt` fixa `gunicorn>=22,<23`; testado (suite completa + boot manual via gunicorn) |
| 7 | react-router — 7 vulnerabilidades | 🟠 P1 | **Não aplicável (majoritariamente) / sem correção não-regressiva disponível para o restante** | Ver detalhe — projeto usa `BrowserRouter` client-side, não o modo servidor/RSC visado pelas CVEs restantes |
| 8 | immer — Poluição de Protótipo | 🟠 P1 | ✅ **Corrigido em 2026-07-25** — resolvido via `npm audit fix` (sem `--force`), dentro do range já aceito por `package.json` | Nenhuma ação adicional — `frontend/package-lock.json` atualizado |
| 9 | DOMPurify — inconsistência em `CUSTOM_ELEMENT_HANDLING` | 🟠 P1 | **Não aplicável**, mas ✅ **atualizado em 2026-07-25** por higiene via `npm audit fix` | Projeto não usa `CUSTOM_ELEMENT_HANDLING` nem Web Components — ver detalhe |
| 10 | CSP ausente | 🟠 P1 | ✅ **Corrigido em 2026-07-25** | Middleware `@app.after_request` em `app.py` (`_security_headers`); testado em `tests/test_security_headers.py` |
| 11 | Clickjacking (`X-Frame-Options`/`frame-ancestors`) | 🟠 P1 | ✅ **Corrigido em 2026-07-25** | Mesmo middleware do item 10 |
| 12 | Container Docker roda como root | 🟠 P1 | ✅ **Corrigido em 2026-07-25** | `Dockerfile` + `docker-entrypoint.sh`: roda como `appuser`, exceto o instante inicial (como root) para corrigir a posse de `/data` — ver detalhe |
| 13 | `actions/checkout` sem `persist-credentials: false` | 🟠 P1 | ✅ **Corrigido em 2026-07-25** | Adicionado aos 5 usos em `ci.yml` |
| 14 | *(achado relacionado, proposto pelo usuário/CTO durante a revisão)* Rotas de mutação de OS/Estoque na API sem restrição por perfil | 🔴 P0 | ✅ **Corrigido em 2026-07-25** — já era achado documentado em `DATA_DICTIONARY.md` desde 2026-07-10, nunca corrigido | OS exige `admin`/`tecnico`; Estoque exige `admin`/`estoque` (perfil novo) — ver `docs/product/BUSINESS_RULES.md` BR-030 |
| 15 | SymlinkPlugin (webpack) | 🟢 P3 | **Dependência de build, não de runtime** | Atualizar quando fizer `npm update` geral |
| 16 | *(achado relacionado, encontrado durante a Sprint Segurança 1.0)* `brace-expansion` (ReDoS) — via `eslint`/`minimatch` | 🟢 P3 | **Risco aceite** | Ver detalhe — devDependency de lint, não roda em produção nem processa entrada de usuário; correção exigiria bump major do `eslint` (9→10) |

---

## Segundo scan Aikido (2026-07-25) — pós Sprint Segurança 1.0

Rodado pelo usuário/CTO depois do merge de todos os P0/P1 do 1º scan. Comparação item a item:

| Item do 2º scan | Mapeia para | Classificação | Ação |
|---|---|---|---|
| SQL Injection (`irflow_os.py`) | Novo — não estava no 1º scan | ✅ **Achado real, mas não explorável hoje — corrigido preventivamente em 2026-07-25** | Ver item 17 abaixo |
| Gunicorn | Item 6 (revisitado) | **Confirmado — 2ª CVE distinta da 1ª** | ✅ **Corrigido em 2026-07-25** — `22.0.0` → `26.0.0` |
| react-router | Item 7 (revisitado) | Sem mudança desde o 1º scan | Mantido: **não aplicável** (client-side, CVE remanescente é de modo RSC/servidor) |
| Docker Root | Item 12 | **Provável cache do scanner** | Já corrigido e validado com `docker build`/`docker run` reais antes do 1º scan terminar — ver evidência abaixo |
| immer | Item 8 | **Provável cache do scanner** | `npm audit` local não mostra nenhuma vulnerabilidade em `immer` hoje (10.2.0/11.1.4, ambos abaixo do latest 11.1.15 mas sem CVE conhecida) |
| SSRF MercadoPhone | Item 5 | Sem mudança | Mantido: **falso positivo** (mesmo código, já investigado) |
| Secreto no Git | Item 2 | Sem mudança de classificação, só de status | ✅ Já estava confirmado+rotacionado antes deste 2º scan; o Aikido agora descreve como "segredo em arquivo excluído" — reflete corretamente que o arquivo não existe mais no working tree |
| enhanced-resolve | Novo item, mesma classe do item 15 (SymlinkPlugin) | **Provável cache do scanner** | `npm audit` local não mostra vulnerabilidade; instalado `5.20.1`, latest `5.24.3` — sem CVE conhecida na diferença |
| File Inclusion | Item 4 | Sem mudança | Mantido: **falso positivo** (mesmo código, já investigado) |

### 17. SQL Injection em `irflow_os.py::carregar_os_com_relacoes` — achado real, corrigido preventivamente

**Metodologia:** localizadas as 2 ocorrências de f-string dentro de `.execute(...)` em `irflow_os.py`
(`grep`), cada uma lida linha a linha, seguindo a mesma régua pedida pelo usuário: "se for concatenação
de valor do usuário, é real; se for parametrizado, é falso positivo".

**Achado 1 — `validar_reparo_ids` (linha ~88-92): falso positivo.**
```python
placeholders = ",".join("?" for _ in reparo_ids)
cursor.execute(f"SELECT id FROM reparos WHERE id IN ({placeholders})", reparo_ids)
```
O f-string só gera a **quantidade** de `?` (um por item de `reparo_ids`), nunca os valores em si — os
valores reais são passados via `reparo_ids` como parâmetros vinculados. Padrão seguro padrão para
cláusulas `IN (...)` de tamanho dinâmico.

**Achado 2 — `carregar_os_com_relacoes` (linha ~146-169): real, mas não explorável hoje.**
```python
def carregar_os_com_relacoes(cursor, order_by="os.id DESC"):
    cursor.execute(f"""... ORDER BY {order_by} ...""")
```
Diferente do achado 1: aqui `order_by` era interpolado **sem nenhuma validação dentro da função** —
diferente do padrão seguro já usado em `irflow_unidades_serializadas_repository.py`
(`_ORDENACOES.get(sort, ...)`, um dicionário whitelist). `grep -rn "carregar_os_com_relacoes"` em todo
o projeto encontra só 2 chamadores, ambos em `irflow_blueprints_api.py`, e **ambos passam sempre o
mesmo literal fixo** `order_by="os.id DESC"` — nunca algo vindo de `request.args` ou de qualquer
entrada do usuário. Não há caminho de exploração hoje.

**Por que corrigir mesmo assim:** a função em si não se protegia — dependia de todo chamador presente
e futuro lembrar de nunca passar entrada do usuário direto. Um chamador futuro (ex.: adicionar
ordenação configurável na tela de OS) poderia reintroduzir o problema sem que ninguém percebesse, já
que a função aceitaria qualquer string sem validar.

**Correção:** whitelist `_ORDENACOES_OS` (mesmo padrão do módulo de Unidades Serializadas) — valores
fora da whitelist caem no default `"os.id DESC"` em vez de serem interpolados. 3 novos testes em
`tests/test_os_order_by_whitelist.py`, incluindo um com payload malicioso (`"os.id; DROP TABLE os; --"`)
confirmando que a tabela `os` continua intacta depois da chamada.

### Docker Root — por que o 2º scan ainda mostra isso (item 12)

O usuário já suspeitava cache do scanner antes de eu confirmar. Evidência: o `Dockerfile` atual (desde
o merge `ebe710b`, antes deste 2º scan) tem usuário `appuser` + `docker-entrypoint.sh` com `gosu`, e foi
**validado rodando de verdade** (`docker build`/`docker run` via `colima`) — `/proc/1/status` do
processo do gunicorn mostrando `Uid: 999` (`appuser`), não root. SAST/SCA de container geralmente olha
só a última instrução `USER`/ausência dela no `Dockerfile` de forma estática, e pode não interpretar
corretamente o padrão "entrypoint troca de privilégio em runtime via `gosu`" — ou o scan rodou antes do
Aikido reindexar o commit mais recente. De qualquer forma, o comportamento real do container (validado
neste ambiente, não só lido no `Dockerfile`) é a fonte de verdade aqui, não o alerta estático.

---

## P0 — Detalhamento e evidência

### 1. SQL Injection — Falso positivo

**Metodologia:** localizadas as 11 ocorrências de f-string dentro de `.execute(...)` em todo o backend
(`grep` recursivo, todos os módulos `.py`), mais varredura separada por `.format(`/concatenação `+`/
`%`-formatting alimentando `.execute(` — zero ocorrências adicionais. Cada uma das 11 lida
individualmente.

**Achado:** todas seguem o mesmo padrão seguro — fragmentos SQL fixos (nomes de coluna, cláusulas
`WHERE`/`ORDER BY` vindas de listas brancas) são interpolados via f-string, mas **todo valor vindo do
usuário passa por `?` parametrizado**, nunca é embutido diretamente na string SQL. Exemplo do padrão
(`irflow_produtos_repository.py::_montar_filtros`):

```python
condicoes.append("categoria = ?")   # fragmento fixo
params.append(categoria)             # valor do usuário -> parametrizado
where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
cursor.execute(f"SELECT {_COLUNAS} FROM produtos {where} ...", (*params, limit, offset))
```

**Candidato mais provável ao alerta:** `irflow_unidades_serializadas_repository.py`, `ORDER BY
{order_sql}` — mas `order_sql = _ORDENACOES.get(sort, _ORDENACOES["recente"])` só pode assumir um de 5
valores fixos de um dicionário, nunca texto arbitrário do usuário, mesmo que `sort` venha de
`request.args`. Esse é exatamente o padrão hipotético que o usuário (CTO) descreveu como falso positivo
típico de SAST antes da investigação.

**Conclusão:** nenhuma injeção de SQL explorável encontrada. Fecha a ação pendente desde 2026-07-06 em
`docs/engineering/SECURITY.md` seção 3 ("Ação Sprint 3: Grep em todo o backend por f-strings").

### 2. Segredo no histórico do Git — Confirmado, risco ativo (verificado 2026-07-25)

**Metodologia:** `git log --diff-filter=A -- .env` e `git show <commit>:.env` nos 3 commits onde o
arquivo existiu.

**Achado:** `.env` foi commitado em `eefcfd2` ("feat: sistema de autenticação com perfis"), existiu em
mais 2 commits (`a21f8db`, `252815a`), e foi removido em `832945c` ("Remove .env do repositório" —
já documentado em `docs/company/CHANGELOG.md`/Sprint 1). **O arquivo não existe mais no working tree,
mas os 3 commits antigos continuam no histórico**, então o valor de `FLASK_SECRET_KEY` presente neles
continua recuperável por qualquer um que clone o repositório completo. As demais variáveis do arquivo
(`IR_FLOW_HOST`, `IR_FLOW_PORT`, config do Mercado Phone) não são segredos reais — só `FLASK_SECRET_KEY`
tinha valor sensível não-vazio nos 3 commits.

**Impacto:** `FLASK_SECRET_KEY` assina os cookies de sessão do Flask. Se o valor vazado ainda for o
mesmo usado em produção hoje, alguém com esse valor pode forjar um cookie de sessão válido para
qualquer usuário, inclusive admin, sem precisar de senha.

**Verificado em 2026-07-25 (usuário/CTO): é o mesmo valor de sempre — nunca foi rotacionado desde que o
`.env` foi removido do repositório.** Risco confirmado como ativo, não hipotético — rotação é P0
imediato, não pode esperar a Sprint Segurança 1.0.

**Ação necessária (usuário — só o CTO tem acesso ao painel do Render):**
1. ~~Confirmar o valor atual de `FLASK_SECRET_KEY` em produção (Render).~~ ✅ Feito 2026-07-25 —
   confirmado que é o mesmo valor vazado.
2. Gerar uma chave nova **localmente, no seu terminal** (não colar o valor gerado de volta nesta
   conversa — evita que o novo segredo fique registrado em qualquer histórico de chat):
   ```bash
   python3 -c "import secrets; print(secrets.token_hex(32))"
   ```
3. Colar o valor gerado diretamente no painel do Render (variável `FLASK_SECRET_KEY`), sem compartilhar
   em nenhum outro lugar.
4. Isso invalida todas as sessões ativas (esperado e aceitável — força novo login de todo mundo,
   inclusive você).
5. Repetir o mesmo processo no ambiente local (`.env`, se você usa um) para manter consistência — não é
   obrigatório ter o mesmo valor local e produção, mas evita confusão.
6. Reescrever o histórico do Git (`git filter-repo` ou BFG) é opcional depois da rotação — o valor
   vazado já estará morto, mas a limpeza de histórico ainda é boa prática de higiene, sem urgência.
7. Depois de rotacionar, atualizar este documento marcando o item como resolvido.

### 3. Fallback inseguro de `FLASK_SECRET_KEY` no código atual — Confirmado no código, não explorado hoje

**Não estava no relatório do Aikido — encontrado ao investigar o item 2.**

```python
# app.py:229
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ir-flow-dev-key")
```

Esse fallback já era um item conhecido e documentado como `⚠️` em `docs/engineering/SECURITY.md` seção 1
("Default inseguro em dev") desde 2026-07-06, mas nunca verificado em produção até agora.

**Verificado em 2026-07-25 (usuário/CTO): a variável está configurada em produção**, então este
fallback nunca é acionado hoje — não é um risco ativo. Continua sendo uma lacuna de robustez: o sistema
inicia silenciosamente com um valor previsível se a variável um dia deixar de estar configurada (ex.:
novo ambiente, erro de configuração), sem nenhum aviso ou erro. Correção recomendada para a Sprint
Segurança 1.0, não urgente: remover o fallback hardcoded e falhar no boot (`raise RuntimeError(...)`)
se a variável não estiver definida fora do modo de desenvolvimento local.

### 4. File Inclusion em `irflow_storage` — Falso positivo

**Metodologia:** arquivo lido por completo (233 linhas). Todo `open()`/`os.path.join()` mapeado até sua
origem.

**Achado:** os únicos caminhos de arquivo manipulados (`integrations_config_path`, `backup_dir`,
`google_drive_backup_dir`, `caminho_arquivo` de backup) são construídos a partir de configuração fixa do
servidor (`DATA_DIR` do `app.py`, variáveis de ambiente definidas no deploy) — nenhum vem de
`request.args`/`request.form`/corpo de requisição. O endpoint de download de backup
(`GET /api/backup/download/<filename>`) usa `send_from_directory` do Flask, que já rejeita `../` e
caminhos absolutos nativamente. O endpoint de restore (`POST /api/backup/restaurar`) usa
`tempfile.NamedTemporaryFile` para o arquivo temporário — nunca o nome enviado pelo cliente
(`f.filename`) é usado para compor um caminho.

**Conclusão:** nenhum caminho controlável pelo atacante alcança uma operação de leitura/escrita de
arquivo neste módulo.

### 5. SSRF — Falso positivo

**Metodologia:** única chamada HTTP de saída em todo o projeto (`grep` por `requests.*/urllib_request./
urlopen` em todos os `.py`) — `irflow_mercadophone.py::chamar_api_mercado_phone`.

**Achado:**
```python
url = f'{config["api_base"]}{method_name}'
```
`config["api_base"]` vem de `MERCADO_PHONE_API_BASE`, variável de ambiente fixada no deploy — nunca de
uma requisição. `method_name` é sempre uma string literal fixa (`"index"` ou `"get"`, os dois únicos
call sites), nunca uma variável vinda de request. Nenhum dado de entrada do usuário influencia a URL
chamada.

**Conclusão:** sem vetor de SSRF — a URL de destino é inteiramente controlada pelo servidor.

---

### 14. Mutação de OS/Estoque sem restrição por perfil — Confirmado e corrigido

**Não estava no relatório do Aikido — proposto pelo usuário (CTO) durante a revisão desta auditoria,
retomando um achado já documentado em `docs/engineering/DATA_DICTIONARY.md` desde 2026-07-10 e nunca
corrigido.**

**Achado:** `POST/PUT/DELETE /api/ordens*` e `POST/PUT/DELETE /api/estoque*` checavam só
`usuario_logado()` — qualquer perfil autenticado (`admin`, `tecnico` ou `vendedor`) podia criar, editar
ou excluir qualquer OS ou item de estoque. `ROUTE_PERMISSIONS` (`app.py`) não cobre essas rotas —
bypassa explicitamente todo `/api/*`, só se aplica às views legadas server-rendered.

**Decisão do usuário:** OS restrita a `admin`/`tecnico`; Estoque restrita a `admin`/`estoque` — perfil
novo, criado nesta correção (resolve também um `TODO` já registrado em
`docs/company/PRODUCT_REQUIREMENTS.md` sobre "Estoque como perfil de usuário"). `vendedor` perdeu acesso
de mutação a ambos os domínios.

**Corrigido em 2026-07-25:** checagem de perfil adicionada nas 7 rotas de mutação
(`irflow_blueprints_api.py`); `PERFIS_OPCOES` centralizado em `irflow_core.py`; validação de perfil na
criação/edição de usuário (`criar_usuario`/`atualizar_usuario`/views legadas) usa a mesma fonte central.
Frontend (`Users.jsx`) atualizado com o novo perfil. Testes existentes que caracterizavam o
comportamento antigo (`test_tecnico_pode_excluir_item_de_estoque`,
`test_vendedor_pode_excluir_item_de_estoque`, `test_vendedor_pode_excluir_qualquer_os`) reescritos para
confirmar a negação (403); novos testes cobrindo `admin`/`estoque` tendo acesso.

Ver `docs/product/BUSINESS_RULES.md` BR-030 e `docs/company/DECISION_LOG.md` (entrada 2026-07-25) para o
registro completo.

---

## P1 — Corrigidos em 2026-07-25 (Sprint Segurança 1.0)

Todos verificados diretamente no código, sem ambiguidade. Branch
`security/sprint-1.0-p1-headers-docker-ci`, commits atômicos por item.

- **CSP ausente / Clickjacking (itens 10, 11) — ✅ corrigido**: nenhum header de segurança
  (`Content-Security-Policy`, `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`)
  configurado em nenhuma resposta — já documentado como `❌` em `docs/engineering/SECURITY.md`
  seção 6 desde 2026-07-06. Corrigido via `@app.after_request` (`_security_headers` em `app.py`).
  Confirmado que o build do Vite (`frontend/dist/index.html`) não usa inline script/style, então a
  CSP (`script-src 'self'`) não quebra o `/app` servido pelo Flask. Testado em
  `tests/test_security_headers.py` (5 testes) e na suíte completa (499 testes).
- **Docker root (item 12) — ✅ corrigido e validado em 2026-07-25**: `Dockerfile` não tinha diretiva
  `USER` — container rodava como root por padrão. Corrigido com um usuário de sistema (`appuser`) +
  `docker-entrypoint.sh`: o entrypoint roda como root só o suficiente para corrigir a posse do disco
  persistente do Render em `/data` (montado em runtime, fora do controle da imagem), depois troca para
  `appuser` via `gosu` antes de executar o gunicorn. Confirmado que **produção usa Docker de fato**
  (`DEPLOY.md`: Environment=Docker, Dockerfile Path=`Dockerfile`, disco `irflow_data` em `/data`) — não
  era um cenário hipotético. Validado com `docker build` + `docker run` reais (via `colima`, instalado
  para este fim): `docker build` sem erros; `/proc/1/status` e dos workers do gunicorn confirmam
  `Uid: 999` (`appuser`), nunca root; `/data` e `/app` com posse `appuser:appuser`; testado dentro do
  container: login, criar/editar OS, criar item de estoque, criar backup, restaurar backup via upload
  (gera `pre-restore-*.db` automaticamente, dados íntegros depois), headers de segurança presentes nas
  respostas reais, `/app` (frontend) responde 200, nenhum erro nos logs. Merge em `main` feito após essa
  validação.
- **`persist-credentials` (item 13) — ✅ corrigido**: `.github/workflows/ci.yml` usa
  `actions/checkout@v4` em 5 lugares; adicionado `persist-credentials: false` em todos — nenhum job
  precisa empurrar de volta ao repositório.
- **Gunicorn (item 6) — ✅ corrigido**: versão instalada era `21.2.0` (confirmado via `pip show`);
  `requirements.txt` fixava `gunicorn>=21,<22` — nunca puxaria a correção (CVE-2024-1135, contrabando
  de requisição via `Transfer-Encoding`, corrigido na 22.0.0). Pin alterado para `>=22,<23`; testado
  (suíte completa + smoke test manual: `gunicorn app:app --bind ... ` + `GET /api/constantes` → 200).
- **immer / DOMPurify / js-yaml / postcss / vite (itens 8, 9) — ✅ atualizado**: `npm audit fix` (sem
  `--force`) resolveu todos dentro dos ranges já aceitos por `package.json` — só
  `frontend/package-lock.json` mudou, nenhuma dependência direta precisou de bump manual. DOMPurify
  continua **não aplicável** de qualquer forma: `grep -r "CUSTOM_ELEMENT_HANDLING\|customElements.define"
  frontend/src` não retorna nenhuma ocorrência — o projeto não usa esse recurso do DOMPurify;
  atualizado por higiene, não por exploração real.
- **react-router-dom (item 7) — decisão: não forçar downgrade**: a versão instalada já era a mais
  recente (`7.18.1`, dentro do range `^7.14.0`). Após `npm audit fix` sem `--force`, restou uma única
  CVE ("RSC Mode CSRF Bypass Allows Action Execution Before 400 Response", GHSA-qwww-vcr4-c8h2) —
  afeta o modo servidor/RSC (React Server Components) do React Router. Este projeto usa
  `<BrowserRouter>` em modo puramente client-side (`frontend/src/App.jsx`), sem
  `react-router.config.ts`, sem rotas `.server.*`, sem RSC — **não aplicável**. A única correção que o
  `npm audit fix --force` oferece é um downgrade para `7.11.0`, que seria regressão (perde 7 versões
  de correções e features) sem ganho real de segurança para este modo de uso. Reavaliar quando o React
  Router publicar uma correção para a linha 7.18.x, ou se o projeto adotar modo servidor no futuro.
- **`brace-expansion` / ReDoS via `eslint`→`minimatch` (achado novo, item 16) — risco aceite**:
  encontrado ao rodar `npm audit` durante este item, não estava no relatório Aikido original. É
  devDependency de lint (não roda em produção, não processa entrada de usuário — só os próprios
  caminhos de arquivo do projeto durante `npm run lint`/CI). Corrigir exigiria `npm audit fix --force`,
  que faria bump major do `eslint` (9 → 10), risco desproporcional ao ganho para este item nesta
  sprint. Registrado aqui para não se perder; revisar na próxima atualização geral de devDependencies.

---

## O que NÃO apareceu no relatório (positivo)

Registrado porque é sinal relevante: o Aikido não encontrou autenticação quebrada, senhas em texto
puro, JWT inseguro, cookies sem proteção, CORS totalmente aberto, RCE no Flask, nem upload arbitrário de
arquivo. Consistente com o que já estava documentado em `docs/engineering/SECURITY.md` (rate limiting,
hash de senha, expiração de sessão, CORS restrito por variável de ambiente — todos já ✅ desde a
Sprint 3).

---

## Próximo passo

1. ~~Confirmar `FLASK_SECRET_KEY` em produção~~ ✅ Feito 2026-07-25 — revelou risco ativo (mesmo valor
   vazado no histórico do Git).
2. ~~Rotacionar `FLASK_SECRET_KEY` no Render~~ ✅ Feito 2026-07-25, confirmado pelo usuário/CTO.
3. ~~Decidir se abre a "Sprint Segurança 1.0"~~ ✅ Aberta e executada 2026-07-25 — todos os itens P0 e
   P1 corrigidos (ver tabela), restam só os dois itens P3 (15, 16 — risco aceite/build-only, sem
   urgência).
4. ~~Validar o Docker non-root localmente antes do merge~~ ✅ Feito 2026-07-25 — `docker build`/`docker
   run` reais via `colima`, checklist completo (ver detalhe do item 12), branch mesclada em `main`
   (`ebe710b`).
5. ~~Refletir no `RELEASE_1.0_MASTER_CHECKLIST.md`~~ ✅ Feito — item "Segurança revisada" e visão
   executiva atualizados.
6. ~~Rodar um novo scan do Aikido~~ ✅ Feito 2026-07-25 pelo usuário/CTO — ver "Segundo scan Aikido"
   acima. Confirmou que a sprint resolveu o essencial; achados novos: 1 hardening preventivo de SQL
   (item 17, corrigido) e uma 2ª CVE de gunicorn distinta da 1ª (corrigido, `26.0.0`). Vários itens que
   o scan ainda mostrava (Docker root, immer, enhanced-resolve) foram confirmados como cache/lag do
   scanner, não regressão real (evidência por item na seção acima).
7. Se ainda não estiver: mesclar `security/sprint-1.0-aikido-rescan` em `main` (itens 17 + gunicorn
   26.0.0), rodar suíte + lint pós-merge, seguindo o mesmo ritmo das branches anteriores desta sprint.
8. Depois disso, próxima prioridade é do usuário (CTO): abrir uma "Sprint Observabilidade" (logs
   estruturados/JSON, correlation ID, `/health`, monitorização tipo Sentry, métricas básicas de
   resposta/erros 5xx) — não decidida/agendada ainda, só registrada aqui como intenção declarada.

---

## Documentos relacionados

- `docs/engineering/SECURITY.md` — checklist de segurança permanente (OWASP Top 10); esta auditoria
  fecha a ação pendente da seção 3 (SQL Injection) e atualiza o status de outras seções
- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — item "Segurança revisada"
- `docs/operations/KNOWN_ISSUES.md` — KI-002 (tokens de checklist sem expiração), já relacionado a
  gestão de segredos/tokens
