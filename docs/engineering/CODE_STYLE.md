# CODE_STYLE.md — Guia de Estilo

Este documento define as convenções de código do Fluxoly Platform.
Seu objetivo é eliminar decisões subjetivas e garantir que qualquer colaborador — humano ou IA — produza código consistente com o que já existe.

Quando houver dúvida sobre estilo, este documento é a resposta. Não a opinião de ninguém.

**Última revisão:** 2026-07-06

---

## Python

### Tamanho máximo

| Unidade | Limite | O que fazer quando ultrapassar |
|---------|--------|-------------------------------|
| Função / método | 40 linhas | Extraia para funções auxiliares com nome descritivo |
| Módulo (`irflow_*.py`) | 500 linhas | Decomponha em submódulos por responsabilidade |
| Blueprint de rota | 80 linhas por rota | Extraia lógica para módulo de serviço |

Linhas em branco, comentários e docstrings contam no limite.
Se uma função está beirando 40 linhas, ela provavelmente faz duas coisas.

---

### Nomenclatura

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Variáveis | `snake_case` | `valor_cobrado`, `reparo_id` |
| Funções | `snake_case` | `calcular_total_reparos()` |
| Constantes | `UPPER_SNAKE_CASE` | `STATUS_FINALIZADO`, `DB_PATH` |
| Classes | `PascalCase` | `BackupManager` |
| Funções privadas | `_leading_underscore` | `_validar_campos_obrigatorios()` |
| Módulos | `snake_case` | `irflow_os.py`, `irflow_storage.py` |

**Idioma dos identificadores:**

| Contexto | Idioma | Exemplos |
|----------|--------|---------|
| Domínio de negócio | Português | `os`, `reparo`, `valor_cobrado`, `criar_ordem` |
| Infraestrutura técnica | Inglês | `get`, `post`, `handle`, `client`, `config` |
| Rotas HTTP | Português com hífen | `/api/ordens`, `/api/precos/sugerir` |
| Nomes de tabelas | Português snake_case | `os`, `estoque`, `shopping_list` |

Não misture idiomas na mesma função. Uma função `criar_ordem` não chama `getRepairById`.

---

### Docstrings

Docstrings são obrigatórias **apenas** quando o comportamento não é óbvio pelo nome da função.
Não documente o óbvio.

```python
# DESNECESSÁRIO — o nome já diz tudo
def calcular_total(valores):
    """Calcula o total dos valores."""  # ← apague isso
    return sum(valores)

# NECESSÁRIO — a razão não é óbvia pelo nome
def sugerir_preco(modelo, reparo_ids, tabela="clientes"):
    """
    Retorna a soma dos preços da tabela para o modelo + reparos informados.
    Retorna 0.0 se nenhum preço for encontrado (não levanta exceção).
    O parâmetro 'tabela' define qual conjunto de preços usar — padrão 'clientes'.
    """
```

Docstrings de uma linha: use apenas aspas duplas simples, na mesma linha.
```python
def formatar_moeda(valor):
    """Retorna valor formatado como 'R$ 1.234,56'."""
```

Docstrings de múltiplas linhas: abertura e fechamento em linhas próprias.
```python
def criar_os(dados, usuario_id):
    """
    Cria uma nova Ordem de Serviço no banco.

    Levanta ValueError se campos obrigatórios estiverem ausentes.
    Não faz commit — o caller é responsável pelo commit.
    """
```

---

### Tipagem

Tipagem estática é **opcional** no código legado, **recomendada** em código novo.
Não adicione type hints retroativamente sem testes cobrindo.

```python
# Código novo — com tipagem
def calcular_total_reparos(reparo_ids: list[int], tabela: str = "clientes") -> float:
    ...

# Código legado — sem tipagem é aceitável
def criar_os(dados, usuario_id):
    ...
```

Imports de tipagem:
```python
from __future__ import annotations  # para Python 3.10 e anteriores
from typing import Optional         # use apenas quando necessário
```

Nunca use `Any` como saída de uma função de negócio — indica falta de clareza sobre o que a função retorna.

---

### Logging

O projeto usa o módulo `logging` padrão do Python.
Logging estruturado em JSON será implementado na Sprint 3 — até lá, use o padrão abaixo.

```python
import logging
logger = logging.getLogger(__name__)

# Nível correto para cada situação
logger.debug("Buscando OS id=%s", os_id)              # dev, rastreamento detalhado
logger.info("OS %s criada por usuário %s", os_id, user_id)   # evento de negócio
logger.warning("Backup falhou, tentativa %d", tentativa)      # situação anormal mas recuperável
logger.error("Falha ao criar OS: %s", str(e))                 # erro que o usuário vai sentir
logger.critical("Banco inacessível: %s", str(e))              # sistema inoperante

# PROIBIDO — interpolação de string em log (performance e segurança)
logger.info(f"OS {os_id} criada")     # ← errado: avalia mesmo sem log ativo
logger.info("OS %s criada" % os_id)   # ← errado: concatenação manual

# OBRIGATÓRIO
logger.info("OS %s criada", os_id)    # ← correto: lazy evaluation
```

**O que nunca logar:**
- Senhas, tokens, chaves de API
- Dados pessoais completos de clientes (nome pode, CPF/telefone não)
- Stack traces em ambiente de produção na resposta HTTP (só no log)

---

### Tratamento de Exceções

```python
# PROIBIDO — captura tudo e engole o erro
try:
    processar_os(dados)
except:
    pass

# PROIBIDO — captura genérica sem log
try:
    processar_os(dados)
except Exception:
    return jsonify({"error": "Erro interno"}), 500

# CORRETO — específico, logado, relançado ou convertido
try:
    processar_os(dados)
except ValueError as e:
    logger.warning("Dados inválidos para criar OS: %s", str(e))
    return jsonify({"error": str(e)}), 400
except sqlite3.IntegrityError as e:
    logger.error("Violação de integridade ao criar OS: %s", str(e))
    return jsonify({"error": "Conflito de dados"}), 409
except Exception as e:
    logger.exception("Erro inesperado ao criar OS")  # logger.exception inclui stack trace
    return jsonify({"error": "Erro interno"}), 500
```

**Regras:**
1. Capture a exceção mais específica possível
2. Sempre logue antes de retornar ao usuário
3. Use `logger.exception()` (não `logger.error`) quando quiser incluir stack trace no log
4. Nunca exponha stack trace ao usuário em produção
5. Não re-levante com `raise Exception(str(e))` — use `raise` puro para preservar o stack

---

### SQL e Acesso ao Banco

```python
# PROIBIDO — SQL injection
cursor.execute(f"SELECT * FROM os WHERE cliente = '{nome}'")
cursor.execute("SELECT * FROM os WHERE id = " + str(os_id))

# OBRIGATÓRIO — parâmetros posicionais
cursor.execute("SELECT * FROM os WHERE cliente = ?", (nome,))
cursor.execute("SELECT * FROM os WHERE id = ?", (os_id,))
cursor.execute(
    "SELECT * FROM os WHERE modelo = ? AND status = ?",
    (modelo, status)
)

# Fechar conexão no finally
conn = get_db_connection()
try:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO os ...", (...))
    conn.commit()
    return cursor.lastrowid
finally:
    conn.close()
```

---

## React / JavaScript

### Tamanho máximo

| Unidade | Limite | O que fazer quando ultrapassar |
|---------|--------|-------------------------------|
| Componente (`.jsx`) | 200 linhas | Extraia sub-componentes ou hooks |
| Hook customizado | 80 linhas | Separe responsabilidades em hooks menores |
| Função dentro de componente | 20 linhas | Extraia para função nomeada externa ou hook |

---

### Nomenclatura

| Elemento | Convenção | Exemplo |
|----------|-----------|---------|
| Componentes | `PascalCase` | `OrderTable.jsx`, `KpiCard.jsx` |
| Hooks customizados | `camelCase` com prefixo `use` | `useOrders.js`, `useShopping.js` |
| Arquivos de page | `PascalCase` | `Orders.jsx`, `NewOrder.jsx` |
| Funções de handler | `handle` + ação | `handleSubmit`, `handleDelete` |
| Variáveis de estado | substantivo + `set` | `[ordens, setOrdens]` |
| Constantes de módulo | `UPPER_SNAKE_CASE` | `STATUS_LABELS`, `PRIORITY_COLORS` |
| Funções utilitárias | `camelCase` | `formatarMoeda`, `calcularDias` |

---

### Estrutura de Componente

Ordem obrigatória dentro de um componente:

```jsx
function OrderTable({ ordens, onDelete }) {
  // 1. Props desestruturadas na assinatura (não dentro do corpo)

  // 2. Hooks de estado
  const [loading, setLoading] = useState(false);
  const [selecionado, setSelecionado] = useState(null);

  // 3. Hooks de contexto
  const { usuario } = useAuth();

  // 4. useEffect (na ordem de importância)
  useEffect(() => {
    // efeito de montagem
  }, []);

  useEffect(() => {
    // efeito reativo
  }, [ordens]);

  // 5. Handlers de evento
  function handleDelete(id) { ... }
  function handleStatusChange(id, status) { ... }

  // 6. Valores derivados (sem estado)
  const ordensAtivas = ordens.filter(o => o.status !== "CANCELADO");

  // 7. Render
  return (
    <div>...</div>
  );
}
```

---

### Chamadas à API

**Regra:** toda chamada à API usa `frontend/src/api/client.js`. Zero `fetch()` inline em componentes.

```jsx
// PROIBIDO — fetch direto em componente
useEffect(() => {
  fetch("/api/ordens")
    .then(r => r.json())
    .then(setOrdens);
}, []);

// OBRIGATÓRIO — via client.js
import { os } from "../api/client";

useEffect(() => {
  async function carregar() {
    try {
      const { data } = await os.listar();
      setOrdens(data.data);
    } catch (err) {
      setErro(err.message);
    }
  }
  carregar();
}, []);
```

Adicionando endpoint novo: sempre em `client.js`, no grupo correto, com nomenclatura consistente.

```javascript
// client.js — padrão de adição
const shopping = {
  listar: (params = {}) => api.get("/shopping-list", { params }),
  criar: (data) => api.post("/shopping-list", data),
  atualizar: (id, data) => api.put(`/shopping-list/${id}`, data),
  atualizarStatus: (id, status) => api.patch(`/shopping-list/${id}/status`, { status }),
  deletar: (id) => api.delete(`/shopping-list/${id}`),
};
```

---

### Hooks Customizados

Use hooks quando a lógica de estado é compartilhada entre dois ou mais componentes, ou quando o componente ultrapassa 200 linhas devido a lógica de dados.

```javascript
// src/hooks/useOrdens.js
export function useOrdens(filtros = {}) {
  const [ordens, setOrdens] = useState([]);
  const [loading, setLoading] = useState(false);
  const [erro, setErro] = useState(null);

  async function recarregar() {
    setLoading(true);
    try {
      const { data } = await os.listar(filtros);
      setOrdens(data.data);
    } catch (e) {
      setErro(e.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { recarregar(); }, []);

  return { ordens, loading, erro, recarregar };
}
```

Hooks não fazem render — retornam dados e funções. Não retornem JSX de um hook.

---

### Organização de Pastas

```
frontend/src/
├── api/
│   └── client.js          ← único ponto de acesso à API
├── components/
│   ├── ui/                ← componentes atômicos reutilizáveis (Button, Input, Badge)
│   ├── dashboard/         ← widgets do dashboard
│   ├── orders/            ← componentes específicos de OS
│   └── shopping/          ← componentes específicos de compras
├── contexts/
│   └── AuthContext.jsx    ← estado global de autenticação
├── hooks/                 ← hooks customizados (a partir da Sprint 5)
├── lib/
│   ├── constants.js       ← constantes de UI (labels, cores, formatação)
│   └── utils.js           ← funções utilitárias puras (sem estado, sem efeitos)
└── pages/                 ← uma page por rota, orquestra dados e layout
```

**Regras de onde colocar o quê:**

- Lógica que usa `fetch` ou estado global → `hooks/` ou direto na `page/`
- Componente usado em 2+ páginas → `components/`
- Componente usado em apenas 1 página → pode ficar no próprio arquivo da page se < 50 linhas, ou em `components/<domínio>/` se maior
- Função sem estado, sem efeitos → `lib/utils.js`
- Label, cor, constante de UI → `lib/constants.js`

---

## Git

### Nomes de Branch

```
<prefixo>/<descrição-em-kebab-case>
```

| Prefixo | Quando usar |
|---------|-------------|
| `feat/` | Nova funcionalidade |
| `fix/` | Correção de bug |
| `hotfix/` | Correção mínima para um bug que interrompeu uma sprint de teste/QA/validação (critérios em `ENGINEERING_GUIDE.md` §11) — sempre a partir de `main` |
| `refactor/` | Mudança de código sem mudança de comportamento |
| `test/` | Adição ou ajuste de testes |
| `docs/` | Documentação apenas |
| `chore/` | Configurações, dependências, CI/CD |
| `perf/` | Melhoria de performance |

```bash
# Corretos
feat/paginacao-listagem-os
fix/sessao-nao-invalidada-logout
refactor/decompor-blueprints-api
test/cobertura-endpoint-sugerir
docs/architecture-adr-002
chore/adicionar-ruff-ao-ci

# Proibidos
minha-branch
fix
novo
isaque/feature
```

---

### Commits — Conventional Commits

```
<tipo>(<escopo>): <descrição em minúsculas, imperativo>
```

**Tipos:**

| Tipo | Quando usar | Aparece no CHANGELOG? |
|------|-------------|----------------------|
| `feat` | Nova funcionalidade | Sim — Adicionado |
| `fix` | Correção de bug | Sim — Corrigido |
| `refactor` | Refatoração sem mudança de comportamento | Não |
| `test` | Adição ou correção de testes | Não |
| `docs` | Documentação apenas | Não |
| `chore` | Manutenção (deps, config, CI) | Não |
| `perf` | Melhoria de performance | Sim — Modificado |
| `style` | Formatação, espaços, lint | Não |
| `revert` | Revertendo um commit anterior | Sim — se reverter feat/fix |

**Escopo:** opcional, deve ser o domínio afetado (`os`, `auth`, `estoque`, `shopping`, `ci`, `docs`).

```bash
# Corretos — imperativo, minúsculas, sem ponto final
feat(os): adicionar paginação na listagem de ordens
fix(auth): corrigir sessão não invalidada após logout
refactor(api): mover endpoints de shopping list para módulo separado
test(pricing): adicionar cobertura para sugerir com múltiplos reparos
docs(adr): documentar decisão sobre separação da API
chore(ci): configurar GitHub Actions com lint e testes
perf(estoque): adicionar índice em estoque(modelo, tipo, qualidade)

# Proibidos
att
fix bug
S
att 09/06 5
wip
commit
```

**Breaking changes:** adicione `!` após o tipo e descreva no rodapé:
```
feat!: remover endpoint legado /api/v1/ordens

BREAKING CHANGE: clientes que usavam /api/v1/ordens devem migrar para /api/ordens
```

---

### Pull Requests

**Título do PR:** mesmo formato de Conventional Commits.
```
feat(shopping): adicionar agrupamento por fornecedor na lista de compras
fix(auth): corrigir rate limiting não aplicado em /api/auth/login
```

**Tamanho recomendado:** <= 400 linhas alteradas por PR.
PRs maiores devem ser divididos em PRs menores com dependência explícita.

**Um PR = uma intenção.**
Nunca misture feature + bug fix em um PR, mesmo que pequenos.

**Revisão:** todo PR requer pelo menos uma revisão antes do merge quando houver mais de um colaborador.
Em projeto solo: self-review via checklist de `QUALITY_GATES.md`.
