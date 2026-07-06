# CONTRIBUTING.md — Como Contribuir

Este documento descreve o processo completo para contribuir com o Assistência System.
Leia antes de criar qualquer branch ou abrir qualquer PR.

---

## Antes de tudo

Leia os documentos fundacionais:

1. [`CLAUDE.md`](../CLAUDE.md) — protocolo de trabalho e regras
2. [`docs/ENGINEERING_GUIDE.md`](ENGINEERING_GUIDE.md) — padrões técnicos
3. [`docs/PROJECT_STATUS.md`](PROJECT_STATUS.md) — estado atual e sprint ativa
4. [`docs/KNOWN_ISSUES.md`](KNOWN_ISSUES.md) — bugs conhecidos (não repita trabalho)

---

## 1. Setup Local

### Pré-requisitos

- Python 3.11+
- Node.js 20+
- Git

### Clone e configuração

```bash
# Clone
git clone <url-do-repositório>
cd assistencia_system

# Variáveis de ambiente
cp .env.example .env
# Edite .env — os valores padrão funcionam para desenvolvimento local

# Backend — dependências de produção + desenvolvimento
pip install -r requirements-dev.txt

# Frontend
cd frontend && npm install
```

### Iniciar em desenvolvimento

```bash
# Terminal 1 — backend
python app.py
# API em http://localhost:5080

# Terminal 2 — frontend
cd frontend && npm run dev
# UI em http://localhost:5173
```

### Verificar que tudo funciona

```bash
# Rodar todos os testes
pytest tests/

# Lint backend
ruff check .

# Lint frontend
cd frontend && npm run lint
```

---

## 2. Fluxo de Desenvolvimento

### Criando uma branch

Sempre crie uma branch antes de qualquer mudança. Nunca trabalhe diretamente em `main`.

```bash
# Sincronize com main antes de criar a branch
git checkout main
git pull origin main

# Crie a branch com o prefixo correto
git checkout -b feat/nome-da-feature      # nova feature
git checkout -b fix/nome-do-bug           # correção de bug
git checkout -b refactor/nome             # refatoração
git checkout -b test/nome                 # adição de testes
git checkout -b docs/nome                 # documentação
git checkout -b chore/nome                # manutenção (deps, config)
```

### Nomenclatura de branches

| Prefixo | Quando usar |
|---------|-------------|
| `feat/` | Nova funcionalidade de negócio |
| `fix/` | Correção de bug |
| `refactor/` | Mudança de código sem mudança de comportamento |
| `test/` | Adição ou ajuste de testes |
| `docs/` | Documentação apenas |
| `chore/` | Configurações, dependências, CI/CD |

---

## 3. Ciclo de Desenvolvimento

Para cada tarefa, siga este ciclo em ordem:

### 3.1 Analisar

Antes de escrever código:
- [ ] Li o código que será modificado
- [ ] Entendi o impacto da mudança
- [ ] Verifiquei se há issue relacionado em `KNOWN_ISSUES.md`
- [ ] Verifiquei se há ADR que governa esta área em `docs/adr/`

### 3.2 Implementar

- Edite um arquivo por vez
- Não misture bug fix + feature no mesmo commit
- Não misture refatoração + feature no mesmo commit

### 3.3 Testar

Para qualquer mudança de código:
- [ ] Escrevi teste(s) para a mudança
- [ ] Todos os testes existentes continuam passando: `pytest tests/`
- [ ] Cobertura não regrediu: `pytest tests/ --cov`
- [ ] Lint backend passa: `ruff check .`
- [ ] Lint frontend passa (se mudança no frontend): `cd frontend && npm run lint`

**Regra:** se corrigiu um bug, escreva primeiro o teste que falha, depois corrija o código.

### 3.4 Documentar

Atualize os documentos que sua mudança afeta:

| Se você... | Atualize... |
|------------|-------------|
| Corrigiu um bug | `KNOWN_ISSUES.md` (mover para Resolvidos) + `CHANGELOG.md` |
| Adicionou feature | `CHANGELOG.md` + sprint ativa em `SPRINTS/` |
| Tomou decisão arquitetural | Novo arquivo em `docs/adr/` + `ARCHITECTURE_DECISIONS.md` |
| Mudou o schema do banco | `DATABASE.md` |
| Identificou vulnerabilidade | `KNOWN_ISSUES.md` + `SECURITY.md` |

### 3.5 Commitar

Use Conventional Commits:

```
<tipo>(<escopo>): <descrição em minúsculas>
```

**Tipos:** `feat`, `fix`, `refactor`, `test`, `docs`, `chore`, `perf`, `style`

```bash
# Exemplos corretos
git commit -m "feat(shopping): adicionar agrupamento por fornecedor"
git commit -m "fix(auth): corrigir sessão não invalidada após logout"
git commit -m "test(os): adicionar cobertura para deleção de OS inexistente"
git commit -m "docs(contributing): adicionar seção de setup local"
git commit -m "chore(deps): atualizar pytest-flask para 1.3"

# Proibido
git commit -m "att"
git commit -m "fix bug"
git commit -m "S"
```

---

## 4. Atualizando `CHANGELOG.md`

Toda mudança que impacta o usuário deve ser registrada no `CHANGELOG.md`.

Adicione sua mudança na seção `[Não lançado]` com o tipo correto:

```markdown
## [Não lançado]

### Adicionado
- Agrupamento por fornecedor na lista de compras

### Corrigido
- Sessão não era invalidada corretamente após logout

### Segurança
- Adicionado rate limiting em /api/auth/login
```

**Tipos de mudança (Keep a Changelog):**

| Tipo | Quando usar |
|------|-------------|
| **Adicionado** | Novas features |
| **Modificado** | Mudanças em features existentes |
| **Descontinuado** | Features que serão removidas em breve |
| **Removido** | Features removidas |
| **Corrigido** | Bug fixes |
| **Segurança** | Correções de vulnerabilidades |

---

## 5. Abrindo um Pull Request

### Antes de abrir

- [ ] Branch atualizada com `main`: `git rebase main` ou `git merge main`
- [ ] CI local passando (testes, lint)
- [ ] `CHANGELOG.md` atualizado
- [ ] Documentação relevante atualizada
- [ ] Nenhum arquivo de debug (`.env`, arquivos temporários, `console.log`)

### Criando o PR

Use o template abaixo como descrição:

```markdown
## O que muda

Descrição clara do que foi implementado ou corrigido.

## Por que muda

Motivação ou issue relacionado (ex: "Corrige KI-001 — rate limiting ausente").

## Como testar

1. Passo 1
2. Passo 2
3. Resultado esperado: ...

## Checklist

- [ ] Testes escritos para a mudança
- [ ] Todos os testes passando
- [ ] Lint passando
- [ ] CHANGELOG.md atualizado
- [ ] Documentação relevante atualizada
- [ ] Nenhum segredo ou dado sensível commitado
```

### Revisão

- Responda todos os comentários antes de solicitar re-revisão
- Não faça force push em branches com PR aberto (perde histórico de revisão)
- Após aprovação, merge via squash ou merge commit (não rebase em PRs públicos)

---

## 6. Criando uma Nova Sprint

Ao iniciar uma nova sprint:

```bash
# 1. Crie o arquivo da sprint a partir do template
cp docs/templates/SPRINT_TEMPLATE.md docs/SPRINTS/SPRINT_NN.md

# 2. Preencha objetivo, motivação, arquivos envolvidos, critérios de aceitação

# 3. Atualize PROJECT_STATUS.md: seção "Próxima Sprint"

# 4. Commit
git add docs/SPRINTS/SPRINT_NN.md docs/PROJECT_STATUS.md
git commit -m "docs(sprints): iniciar planejamento da sprint NN"
```

---

## 7. Adicionando um ADR

Quando uma decisão arquitetural importante for tomada:

```bash
# 1. Copie o template
cp docs/templates/ADR_TEMPLATE.md docs/adr/ADR-NNN.md

# 2. Preencha contexto, alternativas, decisão, consequências

# 3. Adicione a entrada no índice
# Edite docs/ARCHITECTURE_DECISIONS.md

# 4. Commit
git commit -m "docs(adr): ADR-NNN decisão sobre X"
```

---

## 8. Perguntas Frequentes

**Posso commitar direto em `main`?**
Não. Todo código passa por branch + PR, mesmo que seja uma mudança pequena.

**Posso pular os testes se for só documentação?**
Para mudanças apenas em `.md`, sim. Para qualquer `.py` ou `.jsx`, não.

**O que faço se o CI falhar no meu PR?**
Investigue a falha, corrija, faça push. Não peça merge com CI vermelho.

**Como descubro qual sprint está ativa?**
Leia `docs/PROJECT_STATUS.md` — seção "Próxima Sprint" ou "Sprint Atual".

**Encontrei um bug mas não tenho tempo de corrigir agora. O que faço?**
Documente em `KNOWN_ISSUES.md` usando `docs/templates/ISSUE_TEMPLATE.md`. Não ignore.
