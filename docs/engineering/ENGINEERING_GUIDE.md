# ENGINEERING_GUIDE.md — Constituição Técnica

Este documento define os padrões, princípios e convenções que governam o desenvolvimento do Fluxoly Platform.
Ele muda raramente — apenas quando uma decisão arquitetural fundamental é revisada.
Quando houver conflito entre este documento e qualquer outro, este prevalece.

**Última revisão:** 2026-07-08

---

## 1. Princípios Gerais

### SOLID aplicado a este projeto

**S — Single Responsibility**
Cada módulo Flask (`irflow_*.py`) tem um domínio. Nenhuma função de negócio deve vazar entre módulos.
`irflow_os.py` cuida de OS. `irflow_storage.py` cuida de backup. Não misture.

**O — Open/Closed**
Novos tipos de reparo, novos modelos, novos status: adicione via dados (banco), não via código novo.
Evite `if modelo == "X"` espalhados. Use tabelas de configuração.

**L — Liskov Substitution**
Não aplicável diretamente — sem hierarquia de classes. O equivalente aqui: qualquer endpoint que receba
`os_id` deve funcionar com qualquer OS válida, sem casos especiais por tipo ou status.

**I — Interface Segregation**
No frontend: componentes recebem apenas as props que usam. Não passe objetos inteiros quando apenas um campo é necessário.

**D — Dependency Inversion**
Backend: lógica de negócio (`irflow_os.py`) não deve importar diretamente o banco — acessa via funções utilitárias.
Meta para Sprint 4: separar a camada de acesso a dados.

### DRY — Don't Repeat Yourself

- Constantes de status (`EM_ANDAMENTO`, `FINALIZADO`, etc.) vivem em `irflow_core.py`. Nunca redefina em outro lugar.
- Lógica de auto-preenchimento de preço tem um único ponto de verdade: `GET /api/precos/sugerir`.
- No frontend: lógica de negócio repetida em duas páginas → extrair para hook em `src/hooks/`.

### KISS — Keep It Simple, Stupid

- Se uma função tem mais de 40 linhas, pergunte se ela faz duas coisas.
- Se um componente React tem mais de 200 linhas, provavelmente deve ser decomposto.
- Prefira SQL direto com `sqlite3` a ORMs para este projeto — a camada de banco é simples e legível.
- Prefira `if/else` explícito a lógica condicional comprimida em uma linha quando o código é de negócio crítico.

---

## 2. Stack Tecnológica

| Camada | Tecnologia | Versão | Decisão |
|--------|-----------|--------|---------|
| Backend | Flask | >=3.0,<4 | — |
| Servidor WSGI | Gunicorn | >=21,<22 | — |
| Banco de dados | SQLite (WAL mode) | — | ADR-003 |
| Frontend framework | React | ^19 | ADR-001 |
| Build tool | Vite | ^8 | ADR-001 |
| UI components | Radix UI | ^1 | ADR-001 |
| Estilização | Tailwind CSS | ^4 | — |
| Gráficos | Recharts | ^3 | — |
| Testes E2E | Playwright | ^1.55 | — |
| Testes backend | pytest | >=8.0 | — |
| Lint backend | Ruff | >=0.5 | Sprint 2 |
| Lint frontend | ESLint | ^9 | — |
| Deploy | Render (backend) + Vercel (frontend) | — | — |

**Antes de adicionar qualquer nova dependência:**
1. Verifique se o problema não pode ser resolvido com o que já existe.
2. Avalie tamanho, manutenção e licença.
3. Adicione ao `requirements-dev.txt` se for dev-only, `requirements.txt` se for produção.
4. Documente a razão no PR.

---

## 3. Padrões Backend (Flask / Python)

### Estrutura de módulos

```
app.py                       — inicialização, schema DB, registro de blueprints
irflow_core.py               — constantes, utilitários compartilhados
irflow_blueprints_api.py     — endpoints REST (a ser decomposto na Sprint 4)
irflow_blueprints_auth.py    — autenticação
irflow_os.py                 — lógica de negócio de OS
irflow_reports.py            — geração de relatórios e PDF
irflow_storage.py            — backup e Google Drive
irflow_mercadophone.py       — integração externa MercadoPhone
irflow_price_tables.py       — lógica de tabela de preços
irflow_reference_data.py     — dados de referência (modelos, cores, técnicos)
```

**Regra:** não crie um novo arquivo `irflow_*.py` sem decisão explícita. Se a lógica é pequena, adicione ao módulo de domínio existente.

### 3.1 Convenção para domínios novos

Esta seção define a estrutura obrigatória para **qualquer domínio de negócio novo** adicionado ao sistema
a partir desta revisão (ex.: Vendas, Caixa, Financeiro). Não se aplica retroativamente aos domínios
existentes listados em `docs/engineering/DOMAIN_MODEL.md` — esses seguem seu próprio plano de decomposição (ADR-002,
Sprint 4).

**Motivação:** sem uma convenção fixada antes da primeira linha de código, cada domínio novo inventa sua
própria organização de pastas durante a sprint em que nasce — o que gera divergência silenciosa entre
módulos e o mesmo tipo de dívida técnica já registrada em TD-01/KI-003 (mas dessa vez em código novo,
sem justificativa de "legado").

**Camadas obrigatórias, nesta ordem de dependência:**

```
controller   — camada HTTP (blueprint Flask). Recebe request, valida entrada, chama service, formata resposta.
                Nunca contém regra de negócio nem acessa o banco diretamente.

service      — regra de negócio pura do domínio. Não conhece Flask, request ou jsonify.
                É o que se testa com testes unitários rápidos, sem subir um servidor.

repository   — único ponto de acesso ao banco para o domínio (queries SQL parametrizadas,
                seguindo o padrão da seção "Acesso ao banco" abaixo). Service nunca executa SQL direto.

tests        — um arquivo de teste por camada relevante (ex.: test_vendas_service.py,
                test_vendas_api.py), seguindo `docs/engineering/TESTING.md`.

README        — um README.md curto (10-20 linhas) na pasta do domínio: o que o domínio faz,
                quais tabelas usa, quais domínios ele depende/é dependido por.
```

**Onde isso vive fisicamente:** enquanto o projeto não migrar para uma pasta por domínio (`domains/vendas/`,
`domains/estoque/`, etc. — fora de escopo desta revisão), a convenção de nomes de arquivo é:

```
fluxoly_<dominio>_controller.py    (ou blueprint dentro de fluxoly_blueprints_<dominio>.py)
fluxoly_<dominio>_service.py
fluxoly_<dominio>_repository.py
```

**Prefixo `fluxoly_` vs. `irflow_` (ADR-008, 2026-07-27):** todo domínio **novo** a partir desta decisão
nasce com o prefixo `fluxoly_` (nome da marca), não `irflow_` (nome legado). Domínios já existentes
(`irflow_clientes_*.py`, `irflow_produtos_*.py`, `irflow_unidades_serializadas_*.py`, `irflow_os.py`,
`irflow_blueprints_api.py`, etc.) **não são renomeados** por esta decisão — permanecem `irflow_*` até
um futuro Épico de Rebranding Técnico (não escopado). A convenção de camadas acima (controller → service
→ repository → tests → README) é a mesma para os dois prefixos — só o nome muda, nunca a estrutura.

**Primeira aplicação real (2026-07-27):** Vendas MVP (`fluxoly_vendas_controller.py`/`_service.py`/
`_repository.py`, `docs/product/features/VENDAS.md`) é o primeiro domínio a nascer com o prefixo novo.

**Adendo — README de domínio sem pasta própria (registrado em 2026-07-11, primeira aplicação real desta
seção):** o item "README" das camadas obrigatórias acima pressupõe uma pasta de domínio (`domains/vendas/README.md`),
que não existe neste layout flat-file. Interpretação aplicada em Clientes (`irflow_clientes_service.py`)
e `estoque_unidades` (`irflow_estoque_unidades_service.py`, renomeado para
`irflow_unidades_serializadas_service.py` na migração ADR-007), primeiros domínios a seguir esta convenção
de fato: o "README curto" vira um **bloco de docstring no topo do arquivo `_service.py`** — mesma
informação (responsabilidade, tabelas usadas, dependências), sem arquivo separado. Usar este padrão para
qualquer domínio novo enquanto o projeto não migrar para pasta por domínio.

**Regra de reuso entre domínios:** se um domínio novo precisa de uma regra que já existe em outro
domínio (ex.: Vendas precisa dar baixa em estoque), ele **importa o service do domínio dono**, nunca
duplica a lógica nem acessa a tabela do outro domínio diretamente. Exemplo concreto já identificado:
a lógica de movimentação de estoque (`registrar_movimentacao`, `consumir_peca_da_os`, `_consumir_lotes_fifo`
em `irflow_os.py`) é a candidata natural a virar `irflow_estoque_service.py` — OS, Vendas e Compras
devem consumir esse mesmo service, nunca reimplementar a baixa de estoque cada um à sua maneira.

**Regra de dependência entre camadas de domínios diferentes (inegociável):** um domínio nunca importa
ou chama o `repository` de outro domínio, mesmo que pareça mais rápido no momento. A única porta de
entrada para o dado de outro domínio é o `service` dele.

```
❌ ERRADO
VendaRepository  ──▶  EstoqueRepository     (acesso direto a dado de outro domínio, sem passar pela regra de negócio dona)

✔ CORRETO
VendaService  ──▶  EstoqueService  ──▶  EstoqueRepository
```

**Por que isso importa:** se `repository` de um domínio pode ser chamado por qualquer outro, a regra
de negócio de quem é dono do dado (ex.: validação de saldo antes de dar baixa, atualização de custo
médio) passa a poder ser contornada por quem chamou direto o banco — o mesmo tipo de acoplamento oculto
que hoje já existe entre `irflow_os.py` e `irflow_blueprints_api.py` (TD-01) e que a convenção de
domínios existe justamente para não repetir em código novo.

Ver `docs/engineering/DOMAIN_MODEL.md` para o inventário de domínios existentes e seu estado atual de camadas.

### Padrão de endpoint REST

Todos os endpoints seguem este padrão de resposta:

```python
# Sucesso
return jsonify({"data": ..., "message": "..."}), 200

# Recurso criado
return jsonify({"data": ..., "id": novo_id}), 201

# Erro de validação (input inválido)
return jsonify({"error": "Descrição do problema"}), 400

# Não autenticado
return jsonify({"error": "Não autenticado"}), 401

# Sem permissão
return jsonify({"error": "Sem permissão"}), 403

# Recurso não encontrado
return jsonify({"error": "OS não encontrada"}), 404

# Erro interno
return jsonify({"error": "Erro interno"}), 500
```

**Nunca retornar stack traces em produção.** Sempre logar o erro e retornar mensagem genérica.

### Acesso ao banco

```python
# Padrão obrigatório para conexão
conn = get_db_connection()   # função em app.py ou irflow_core.py
cursor = conn.cursor()
try:
    cursor.execute("SELECT ...", (param,))
    conn.commit()
finally:
    conn.close()

# Nunca construir SQL com f-string ou concatenação de strings
# ERRADO:
cursor.execute(f"SELECT * FROM os WHERE cliente = '{nome}'")  # SQL injection

# CORRETO:
cursor.execute("SELECT * FROM os WHERE cliente = ?", (nome,))
```

### Variáveis de ambiente

- Sempre ler via `os.environ.get("VAR", "default")` — nunca hardcodar valores de produção.
- Todos os defaults devem ser seguros para desenvolvimento local.
- Toda nova variável deve ser adicionada imediatamente ao `.env.example` com comentário.
- Segredos (`FLASK_SECRET_KEY`, tokens, senhas) **nunca** têm valor padrão real — apenas placeholder `change-me`.

### Autenticação e sessão

- Sessões via Flask session (cookie assinado com `FLASK_SECRET_KEY`).
- Toda rota protegida verifica `session.get("usuario_id")` antes de qualquer operação.
- Rotas admin verificam `session.get("perfil") == "admin"`.
- A verificação de autenticação é feita no início da função, antes de qualquer acesso ao banco.

---

## 4. Padrões Frontend (React / Vite)

### 4.0 Princípio de UX: interface por perfil

**Cada profissional deve enxergar apenas o que precisa para executar seu trabalho com máxima eficiência.**
*(Fonte: Product Owner, 2026-07-10 — ver `docs/company/VISION.md` Valores e
`docs/company/PRODUCT_REQUIREMENTS.md` seção "Personas Operacionais".)*

Este é um critério de decisão, não só uma aspiração: ao desenhar uma tela nova ou decidir o que uma tela
existente exibe, prefira sempre a opção que restringe a visão ao necessário para o perfil de sessão ativo
(`admin`/`tecnico`/`vendedor` hoje — ver `docs/engineering/DOMAIN_MODEL.md` 1.2), em vez de uma tela única
com tudo visível para todos os perfis e apenas alguns campos desabilitados por permissão. Concretamente:

- Um Vendedor não precisa ver configuração de custos operacionais ou administração de usuários.
- Um Técnico não precisa do fluxo de checkout de venda.
- Quando um domínio novo nascer com perfil próprio (ex.: Financeiro, Estoque — hoje sem perfil de login
  distinto, ver `docs/company/PRODUCT_REQUIREMENTS.md` "Personas Operacionais"), sua tela deve ser
  desenhada para esse perfil desde o início, não como uma aba a mais dentro de uma tela genérica.

Isso não substitui a checagem de permissão no backend (`ROUTE_PERMISSIONS`, `usuario_logado()` — seção 3
acima) — é um critério de design de interface, complementar à autorização real, que continua sendo sempre
no servidor.

### Estrutura de arquivos

```
frontend/src/
├── api/
│   └── client.js          — único ponto de acesso à API (nunca fazer fetch direto nas pages)
├── components/
│   ├── ui/                — componentes atômicos (button, input, etc.)
│   ├── dashboard/         — widgets do dashboard
│   ├── orders/            — componentes de OS
│   └── shopping/          — componentes de lista de compras
├── contexts/
│   └── AuthContext.jsx    — estado global de autenticação
├── hooks/                 — hooks customizados (criar a partir da Sprint 5)
├── lib/
│   ├── constants.js       — constantes UI e formatação
│   └── utils.js           — utilitários puros
└── pages/                 — páginas (uma por rota)
```

### Regras de componentes

- **Pages** (`src/pages/`) contêm o layout e orquestram dados. Não contêm lógica de negócio direta.
- **Components** (`src/components/`) são reutilizáveis e não fazem chamadas à API diretamente.
- **Chamadas à API** são feitas exclusivamente via `src/api/client.js` — nunca `fetch()` inline numa page.
- Props tipadas com JSDoc quando o componente é compartilhado.

### Padrão de chamada à API

```javascript
// client.js — padrão de definição
const os = {
  listar: (params = {}) => api.get("/ordens", { params }),
  criar: (data) => api.post("/ordens", data),
  atualizar: (id, data) => api.put(`/ordens/${id}`, data),
  deletar: (id) => api.delete(`/ordens/${id}`),
};

// page — padrão de uso
const [loading, setLoading] = useState(false);
const [erro, setErro] = useState(null);

async function carregarOrdens() {
  setLoading(true);
  try {
    const { data } = await os.listar({ status: filtro });
    setOrdens(data.data);
  } catch (err) {
    setErro(err.message);
  } finally {
    setLoading(false);
  }
}
```

### Estado e efeitos

- `useEffect` com array de dependências explícito e correto — sem dependências omitidas.
- Estado derivado (calculado de outro estado) nunca vive em `useState` — calcule inline ou use `useMemo`.
- Cleanup em `useEffect` quando cria subscriptions, timers ou listeners.
- Nunca atualizar estado de componente desmontado — verificar com flags de cleanup.

### Roteamento e proteção

- Rotas privadas verificam autenticação via `AuthContext` em `App.jsx`.
- Rota pública única: `/checklist/:token` (sem autenticação).
- Redirecionamento para `/login` em qualquer rota sem sessão válida.

---

## 5. Banco de Dados

Detalhes completos em `docs/engineering/DATABASE.md`. Regras essenciais:

### Migrations

- **Nunca** executar `ALTER TABLE` ad-hoc sem documentação correspondente.
- Toda alteração de schema deve ter: arquivo de migration versionado + atualização de `DATABASE.md`.
- Migrations são sempre aditivas (adicionar coluna, tabela, índice) — nunca destrutivas em produção sem janela de manutenção.
- Antes de qualquer migration em produção: **backup verificado**.

### Consultas

- Parâmetros sempre por placeholder `?` — nunca por concatenação.
- Queries de listagem com potencial de retornar muitos resultados devem ter `LIMIT`.
- Índices documentados e justificados em `DATABASE.md`.
- `EXPLAIN QUERY PLAN` antes de adicionar índice novo.

### Nomenclatura

- Tabelas: `snake_case` no plural (`os`, `estoque`, `usuarios`, `shopping_list`).
- Colunas: `snake_case` (`criado_em`, `valor_cobrado`, `reparo_id`).
- Foreign keys: `<tabela_singular>_id` (`os_id`, `estoque_id`).
- Índices: `idx_<tabela>_<coluna>` (`idx_estoque_sku`).

---

## 6. Testes

Detalhes completos em `docs/engineering/TESTING.md`. Regras essenciais:

### Hierarquia de testes

| Tipo | Ferramenta | Escopo | Isolamento |
|------|-----------|--------|-----------|
| Unitário / Integração | pytest | Endpoints, lógica de negócio | SQLite in-memory |
| E2E | Playwright | Fluxos completos do usuário | Servidor Flask real |

### Regras inegociáveis

1. **Nenhum teste toca `database.db`** — banco de produção/desenvolvimento é intocável em testes.
2. **Cada teste é independente** — não depende de estado deixado por teste anterior.
3. **Testes falhos bloqueiam o merge** — CI vermelho = PR não entra.
4. **Cobertura não cai** — threshold definido em `pyproject.toml`. Se cair, o CI falha.
5. **Novo bug = novo teste** — ao corrigir um bug, escreva o teste que o teria detectado.

### O que deve ser testado

- Toda rota REST: casos felizes + casos de erro (401, 403, 404, 400).
- Toda transição de status (OS, shopping list).
- Toda regra de negócio crítica (cálculo de preço, validação de campos obrigatórios).
- Fluxos E2E: login, criar OS, editar OS, criar item de estoque.

---

## 7. Segurança

Detalhes completos em `docs/engineering/SECURITY.md`. Regras essenciais:

### SQL Injection
- **Proibido:** `f"SELECT * FROM os WHERE id = {id}"` ou qualquer interpolação em SQL.
- **Obrigatório:** `cursor.execute("SELECT * FROM os WHERE id = ?", (id,))`

### Autenticação
- Senhas armazenadas com hash via Werkzeug (`generate_password_hash` / `check_password_hash`).
- `FLASK_SECRET_KEY` forte e única por ambiente — nunca o valor default em produção.
- Sessões invalidadas no logout via `session.clear()`.

### CORS
- `IR_FLOW_CORS_ORIGINS` define origens permitidas — nunca `*` em produção.
- Cookies com `SameSite=None; Secure` apenas quando necessário para cross-origin (deploy separado).

### Exposição de dados
- Respostas de erro nunca incluem stack traces, paths de arquivo ou detalhes internos.
- Listagens paginadas quando o volume pode ser alto (protege contra dump de dados).

---

## 8. Qualidade de Código

### Lint backend (Ruff)

```bash
ruff check .
```

Regras habilitadas: `E` (pycodestyle), `F` (pyflakes), `W` (warnings), `I` (isort).
Configuração em `pyproject.toml`. Executado no CI — falha bloqueia o merge.

### Lint frontend (ESLint)

```bash
cd frontend && npm run lint
```

Configuração em `frontend/eslint.config.js`. Executado no CI — falha bloqueia o merge.

### Complexidade e legibilidade

- Funções com mais de 40 linhas: candidatas a decomposição.
- Componentes React com mais de 200 linhas: candidatos a decomposição.
- Comentários explicam o **porquê**, não o **o quê**. Código bem escrito não precisa de comentário para dizer o que faz.
- Nomes de variáveis e funções em português para domínio de negócio (`valor_cobrado`, `criarOrdem`), inglês para infraestrutura (`useEffect`, `useState`, `handleSubmit`).

---

## 9. Commits — Conventional Commits

**Formato obrigatório a partir da Sprint 2:**

```
<tipo>(<escopo opcional>): <descrição em minúsculas>

[corpo opcional]

[rodapé opcional]
```

### Tipos permitidos

| Tipo | Quando usar |
|------|-------------|
| `feat` | Nova funcionalidade |
| `fix` | Correção de bug |
| `refactor` | Refatoração sem mudança de comportamento |
| `test` | Adição ou correção de testes |
| `docs` | Documentação apenas |
| `chore` | Manutenção (deps, config, CI) |
| `perf` | Melhoria de performance |
| `style` | Formatação, espaços, ponto-e-vírgula |

### Exemplos corretos

```
feat(os): adicionar auto-preenchimento de valor_cobrado via tabela de preços
fix(auth): corrigir redirecionamento após logout em sessão expirada
refactor(api): mover endpoints de shopping list para módulo separado
test(pricing): adicionar cobertura para endpoint sugerir com múltiplos reparos
docs(claude): adicionar protocolo de trabalho obrigatório
chore(ci): configurar GitHub Actions com lint e testes
```

### Exemplos proibidos

```
att                     ← sem tipo, sem descrição
fix bug                 ← sem escopo, sem contexto
S                       ← incompreensível
att 09/06 5             ← data não pertence ao commit message
```

**Breaking changes** são indicados com `!` após o tipo: `feat!: remover endpoint legado`.

---

## 10. Fluxo de PR e Revisão

### Criando uma branch

```bash
git checkout -b feat/nome-da-feature
git checkout -b fix/nome-do-bug
git checkout -b refactor/nome-da-refatoracao
git checkout -b docs/nome-da-documentacao
```

### Antes de abrir o PR

- [ ] CI local passando (`pytest tests/`, `ruff check .`, `npm run lint`)
- [ ] Testes novos escritos para a mudança
- [ ] `KNOWN_ISSUES.md` atualizado se bug foi corrigido
- [ ] `CHANGELOG.md` atualizado
- [ ] Nenhum arquivo de debug ou temporário commitado
- [ ] Nenhum `console.log` ou `print()` de debug no código

### Template de PR

Use `docs/engineering/templates/PR_TEMPLATE.md` como base. Inclua obrigatoriamente:
- **O que muda:** descrição clara do que foi implementado
- **Por que muda:** motivação, contexto ou issue relacionado
- **Como testar:** passos para validar a mudança
- **Checklist:** itens de qualidade verificados

### Critérios de merge

- CI verde (todos os jobs bloqueantes passando)
- Revisão aprovada (quando houver mais de um colaborador)
- Nenhum comentário de revisão aberto
- Documentação atualizada

---

## 11. Bugs Encontrados Durante Sprints de Teste, QA ou Validação

Escrever testes, validar comportamento ou rodar QA frequentemente revela bugs reais no código de produção — não só lacunas de cobertura. Esta seção define quando um achado desses **interrompe a sprint** e exige um `hotfix/` imediato (ver `CLAUDE.md` para o fluxo completo e `docs/engineering/QUALITY_GATES.md` — G-18), e quando ele deve apenas ser **caracterizado por teste e reportado** para decisão posterior, sem parar o trabalho planejado.

Não há espaço para julgamento subjetivo aqui — mesmo espírito de `QUALITY_GATES.md`: cada critério é verdadeiro ou falso.

### Critérios objetivos de interrupção

Pare a sprint e abra um `hotfix/` se **qualquer um** dos critérios abaixo for verdadeiro:

| # | Critério | Pergunta objetiva |
|---|----------|---------------------|
| C-01 | Mutação silenciosa de dado persistido | O comportamento grava, apaga ou altera uma linha no banco **sem retornar erro** e sem que o chamador tenha pedido essa mudança? |
| C-02 | Perda de dado irreversível | Uma operação normal (não destrutiva por design) causa perda de dado que não pode ser recuperada a partir do próprio sistema? |
| C-03 | Bypass de autenticação/autorização | O achado permite acessar, alterar ou excluir dado de outro usuário, ou executar uma ação sem a permissão exigida pela regra de negócio? |
| C-04 | Caminho real de produção | O comportamento está na rota/função que o frontend em produção efetivamente usa (não uma rota legada morta ou código não referenciado)? |

Se **nenhum** critério for verdadeiro — por exemplo, uma exceção não tratada que resulta em `500` mas não escreve nenhum dado incorreto, ou um comportamento equivalente numa rota legada sem uso real — **não interrompa**: escreva o teste que caracteriza o comportamento atual, não o commite como falha, e reporte o achado ao final da sprint para decisão (registrar em `KNOWN_ISSUES.md`, corrigir depois, ou aceitar como está).

### Exemplos já observados no projeto

- **Interrompeu (C-01 + C-04):** `PATCH /api/ordens/<id>/status` aceitava um status desconhecido e o normalizava silenciosamente para "Em andamento" em vez de rejeitar — grava estado errado sem erro, na rota que o frontend usa. Corrigido via commit direto na sprint (antes desta política existir — ver ADR-004 sobre não-retroatividade).
- **Interrompeu (C-01 + C-02 + C-04):** `PUT /api/ordens/<id>` sem `status` reabria uma OS Finalizada e apagava `data_finalizado` silenciosamente — perda do dado de finalização sem qualquer erro.
- **Não interrompeu (nenhum critério):** `POST /api/auth/login` com um array JSON no lugar de um objeto derrubava a rota com `AttributeError` (500). Falha alto e visível, não persiste nenhum dado incorreto — caracterizado como comportamento a evitar no teste (removido da suíte, não commitado como falha) e reportado separadamente.
- **Não interrompeu (C-04 falso):** divergência entre `POST /atualizar_status` (rota legada) e `PATCH /api/ordens/<id>/status` (API) na reativação de OS Cancelada — a rota legada não é a que o frontend em produção usa; caracterizado por teste e reportado, sem hotfix.
