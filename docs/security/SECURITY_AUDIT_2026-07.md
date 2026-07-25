# SECURITY_AUDIT_2026-07.md — Triagem do relatório Aikido

**Status:** Investigado — cada alerta validado no código (não corrigido às cegas). Correção ainda não
iniciada, aguardando decisão do usuário (CTO) sobre a Sprint Segurança 1.0.
**Origem:** scan automatizado do Aikido rodado pelo usuário (CTO) em 2026-07-25 contra o repositório.
**Investigado por:** Claude (Principal Engineer), 2026-07-25.
**Regra seguida:** SAST (análise estática) gera falsos positivos com frequência — nenhum item abaixo foi
classificado sem antes ler o código real envolvido. Ver metodologia de cada item.

---

## Tabela de classificação

| # | Item (relatório Aikido) | Severidade | Classificação | Ação |
|---|---|---|---|---|
| 1 | SQL Injection via concatenação de strings | 🔴 P0 | **Falso positivo** | Nenhuma — documentar o padrão seguro existente |
| 2 | Segredo no histórico do Git (`.env`) | 🔴 P0 | **Confirmado** | Rotacionar `FLASK_SECRET_KEY` |
| 3 | *(achado relacionado, fora do relatório Aikido)* Fallback inseguro de `FLASK_SECRET_KEY` no código atual | 🔴 P0 | **Confirmado** | Remover fallback hardcoded; falhar no boot se ausente |
| 4 | File Inclusion em `irflow_storage` | 🔴 P0 | **Falso positivo** | Nenhuma |
| 5 | SSRF | 🔴 P0 | **Falso positivo** | Nenhuma |
| 6 | Gunicorn — 3 vulnerabilidades (contrabando de requisição HTTP) | 🟠 P1 | **Confirmado** | Atualizar para `>=22` |
| 7 | react-router — 7 vulnerabilidades | 🟠 P1 | **Dependência vulnerável, exploração não confirmada** | Atualizar via `npm update`/`npm audit fix` |
| 8 | immer — Poluição de Protótipo | 🟠 P1 | **Dependência vulnerável, exploração não confirmada** | Atualizar (dependência transitiva) |
| 9 | DOMPurify — inconsistência em `CUSTOM_ELEMENT_HANDLING` | 🟠 P1 | **Não aplicável** | Projeto não usa `CUSTOM_ELEMENT_HANDLING` nem Web Components — ver detalhe |
| 10 | CSP ausente | 🟠 P1 | **Confirmado** | Adicionar middleware de headers |
| 11 | Clickjacking (`X-Frame-Options`/`frame-ancestors`) | 🟠 P1 | **Confirmado** | Mesmo middleware do item 10 |
| 12 | Container Docker roda como root | 🟠 P1 | **Confirmado** | Adicionar `USER` não-root no `Dockerfile` |
| 13 | `actions/checkout` sem `persist-credentials: false` | 🟠 P1 | **Confirmado** | Adicionar aos 5 usos em `ci.yml` |
| 14 | SymlinkPlugin (webpack) | 🟢 P3 | **Dependência de build, não de runtime** | Atualizar quando fizer `npm update` geral |

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

### 2. Segredo no histórico do Git — Confirmado

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

**Ação necessária (usuário — só o CTO tem acesso ao painel do Render):**
1. Confirmar o valor atual de `FLASK_SECRET_KEY` em produção (Render).
2. Gerar uma chave nova (`python -c "import secrets; print(secrets.token_hex(32))"`, já documentado em
   `.env.example`).
3. Atualizar a variável de ambiente no Render.
4. Isso invalida todas as sessões ativas (esperado e aceitável — força novo login).
5. Reescrever o histórico do Git (`git filter-repo` ou BFG) é opcional depois da rotação — o valor
   vazado já estará morto, mas a limpeza de histórico ainda é boa prática de higiene, sem urgência.

### 3. Fallback inseguro de `FLASK_SECRET_KEY` no código atual — Confirmado (achado independente)

**Não estava no relatório do Aikido — encontrado ao investigar o item 2.**

```python
# app.py:229
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "ir-flow-dev-key")
```

Esse fallback já era um item conhecido e documentado como `⚠️` em `docs/engineering/SECURITY.md` seção 1
("Default inseguro em dev") desde 2026-07-06, mas nunca verificado em produção. **É mais grave que o
vazamento histórico do item 2**: não depende de ninguém vasculhar commits antigos — o valor
`"ir-flow-dev-key"` está visível agora mesmo no código-fonte público do repositório. Se
`FLASK_SECRET_KEY` não estiver configurada em produção, o Flask usa esse valor previsível para assinar
sessões.

**Ação necessária:**
1. Confirmar (usuário, painel do Render) que `FLASK_SECRET_KEY` está de fato configurada em produção —
   prioridade imediata, independente do resto desta auditoria.
2. Correção de código recomendada (Sprint Segurança 1.0, não feita nesta investigação): remover o
   fallback hardcoded e falhar no boot (`raise RuntimeError(...)`) se a variável não estiver definida
   fora do modo de desenvolvimento local — hoje o sistema inicia silenciosamente com o valor inseguro,
   sem nenhum aviso.

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

## P1 — Confirmados, correção simples (Sprint Segurança 1.0)

Todos verificados diretamente no código, sem ambiguidade:

- **CSP ausente / Clickjacking**: nenhum header de segurança (`Content-Security-Policy`,
  `X-Frame-Options`, `X-Content-Type-Options`, `Referrer-Policy`) configurado em nenhuma resposta —
  já documentado como `❌` em `docs/engineering/SECURITY.md` seção 6 desde 2026-07-06, nunca corrigido.
- **Docker root**: `Dockerfile` não tem diretiva `USER` — container roda como root por padrão.
- **`persist-credentials`**: `.github/workflows/ci.yml` usa `actions/checkout@v4` em 5 lugares, nenhum
  com `persist-credentials: false`.
- **Gunicorn**: versão instalada `21.2.0` (confirmado via `pip show`); `requirements.txt` fixa
  `gunicorn>=21,<22` — nunca vai puxar a correção (CVE-2024-1135, contrabando de requisição via
  `Transfer-Encoding`, corrigido na 22.0.0). Precisa mudar o pin, não só rodar `pip install -U`.
- **react-router-dom** (`^7.14.0`) e **immer** (dependência transitiva, `^10.1.1`/`^11.0.0` conforme o
  pacote que a puxa): não investigado CVE-a-CVE nesta sessão (sem acesso a base de CVE ao vivo neste
  ambiente) — tratar como "atualizar e rodar a suíte de testes", não como confirmação de exploração real.
- **DOMPurify — não aplicável**: o achado é específico de projetos que usam
  `CUSTOM_ELEMENT_HANDLING`/Web Components customizados combinados com o hook `afterSanitizeElements`
  como camada de segurança. Verificado: `grep -r "CUSTOM_ELEMENT_HANDLING\|customElements.define"
  frontend/src` não retornou nenhuma ocorrência — o projeto não usa esse recurso do DOMPurify.
  Atualizar mesmo assim por higiene (é dependência transitiva do `html2canvas` ou similar), mas sem
  urgência de exploração.

---

## O que NÃO apareceu no relatório (positivo)

Registrado porque é sinal relevante: o Aikido não encontrou autenticação quebrada, senhas em texto
puro, JWT inseguro, cookies sem proteção, CORS totalmente aberto, RCE no Flask, nem upload arbitrário de
arquivo. Consistente com o que já estava documentado em `docs/engineering/SECURITY.md` (rate limiting,
hash de senha, expiração de sessão, CORS restrito por variável de ambiente — todos já ✅ desde a
Sprint 3).

---

## Próximo passo (aguardando decisão do usuário)

1. **Imediato, independente do resto:** confirmar `FLASK_SECRET_KEY` em produção (item 3 acima).
2. Decidir se abre a "Sprint Segurança 1.0" sugerida (zerar P0 confirmados + todos os P1) antes de
   continuar o Épico Vendas/Fase 1.
3. Este documento deveria refletir no `RELEASE_1.0_MASTER_CHECKLIST.md` (item "Segurança revisada") —
   feito nesta sessão, ver commit correspondente.

---

## Documentos relacionados

- `docs/engineering/SECURITY.md` — checklist de segurança permanente (OWASP Top 10); esta auditoria
  fecha a ação pendente da seção 3 (SQL Injection) e atualiza o status de outras seções
- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — item "Segurança revisada"
- `docs/operations/KNOWN_ISSUES.md` — KI-002 (tokens de checklist sem expiração), já relacionado a
  gestão de segredos/tokens
