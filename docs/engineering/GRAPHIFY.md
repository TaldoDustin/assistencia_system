# Graphify — Grafo de Conhecimento do Repositório

## Objetivo

O Graphify indexa todo o repositório (backend, frontend, documentação) e constrói um grafo de
conhecimento persistente: nós para arquivos/módulos/classes/funções/conceitos, arestas para as
relações entre eles (imports, chamadas, citações, relações semânticas inferidas). O objetivo é
permitir responder perguntas sobre a arquitetura do projeto (dependências, impacto de uma mudança,
onde um conceito é citado) sem depender do contexto de uma conversa específica — a documentação e o
grafo são a fonte de verdade, não a memória acumulada de uma sessão.

Não modifica código nem adiciona dependência ao projeto (`requirements.txt`/`package.json`). É uma
ferramenta de análise, local ao ambiente de quem a executa.

Configurado inicialmente em 2026-07-31 para apoiar a Sprint Housekeeping (rebranding técnico, TD-12)
— ver `docs/operations/SPRINTS/SPRINT_HOUSEKEEPING.md`.

## Instalação

Pacote `graphifyy` (PyPI), instalado via `uv tool install graphifyy` (ou `pip install graphifyy` como
fallback). Skill do Claude Code em `~/.claude/skills/graphify/`. Nada disso é dependência do projeto —
é uma ferramenta de linha de comando, análoga a um linter, que roda fora do runtime da aplicação.

## Como atualizar o grafo

```bash
graphify . --update       # incremental — só re-extrai arquivos novos/alterados
graphify .                # rebuild completo (ignora o cache incremental)
graphify . --cluster-only # só re-executa a clusterização sobre o grafo já existente
```

Regenerar sempre que:
- Uma sprint grande terminar (ex.: fim da Sprint Housekeeping, para validar a nomenclatura migrada)
- Uma reestruturação de pastas/módulos acontecer
- O grafo estiver sendo usado para responder uma pergunta arquitetural importante e a última
  indexação for antiga

Não precisa ser regenerado a cada commit trivial.

## O que é indexado

Todo o repositório a partir da raiz, exceto:
- Diretórios sempre ignorados: `venv/`, `.venv/`, `node_modules/`, `__pycache__/`, `.git/`, `.tox/`,
  `.nox/`, `.eggs/`, `*.egg-info/`
- Tudo que estiver coberto por `.gitignore` (respeitado nativamente) ou por um `.graphifyignore`
  opcional (ainda não criado neste projeto)
- Arquivos potencialmente sensíveis, pulados silenciosamente: `.env`/`.envrc` (exceto
  `.env.example`/templates), chaves/certificados (`.pem`, `.key`, `.p12`, `.crt`, `id_rsa` etc.),
  arquivos de credenciais nomeados (`.netrc`, `.npmrc`, `.git-credentials` etc.), e arquivos cujo
  nome ou conteúdo bate em padrões de segredo/token/senha

Na indexação de 2026-07-31: 249 arquivos (159 código, 88 documentação, 2 imagens), 258.942 palavras.
`skipped_sensitive` veio vazio — nenhum arquivo sensível foi encontrado sob esses critérios.

## Extração: código vs. documentação

- **Código**: extração estrutural via AST, determinística, sem custo de LLM e sem precisar de
  chave de API.
- **Documentação/imagens**: extração semântica via subagentes (Claude, dentro desta sessão) ou via
  Gemini se `GEMINI_API_KEY`/`GOOGLE_API_KEY` estiver configurada. Custo em tokens do host (não do
  Graphify). Na indexação inicial: ~934k tokens de input, 0 de output reportado pelos subagentes.

## Onde ficam os artefatos

Tudo em `graphify-out/` na raiz do projeto — **não versionado** (adicionado ao `.gitignore` em
2026-07-31):

| Arquivo | Conteúdo |
|---------|----------|
| `graph.html` | Visualização interativa, abre em qualquer navegador |
| `graph.json` | Grafo bruto (nós/arestas), formato GraphRAG-ready |
| `GRAPH_REPORT.md` | Relatório em linguagem simples: God Nodes, Surprising Connections, Hyperedges, comunidades, perguntas sugeridas |
| `.graphify_labels.json` | Rótulos das comunidades detectadas |
| `manifest.json` | Manifesto de arquivos processados, usado por `--update` |
| `cost.json` | Histórico cumulativo de custo em tokens por execução |
| `cache/` | Cache semântico por arquivo (evita reprocessar docs não alterados) |
| `.graphify_python`, `.graphify_root` | Metadados internos (interpretador Python resolvido, raiz do scan) |

## Consultar o grafo

```bash
graphify query "<pergunta>"                 # busca BFS — contexto amplo
graphify path "ConceitoA" "ConceitoB"       # caminho mais curto entre dois conceitos
graphify explain "NomeDoNó"                 # explicação em linguagem simples de um nó
```

Útil para a Sprint Housekeeping: perguntas como "quais módulos ainda usam `irflow_*`", "quais
documentos citam `assistencia_system`", "o que seria impactado por renomear X" — em vez de grep
manual arquivo por arquivo.

## Limitações conhecidas

- **Arestas "dangling"** (502 na indexação inicial de 2026-07-31): subagentes de chunks diferentes,
  rodando em paralelo, geram stub-nodes para arquivos citados fora do seu próprio chunk, e às vezes
  esses IDs não batem exatamente com o ID determinístico que o AST/outro subagente gerou para o
  mesmo arquivo. Não corrompe o grafo (é um diagnóstico honesto, não um erro fatal), mas significa
  que algumas conexões inferidas entre docs e código citados por nome podem estar "soltas". Tende a
  diminuir com `--update` (o merge incremental reconcilia contra o grafo já existente).
- Sem chave de API configurada, a extração semântica de documentação depende de subagentes
  dispatchados pelo host (Claude Code) — isto é, rodar `graphify .` num terminal puro (sem um agente
  para dispatchar) não teria como processar `docs/**` sozinho; só a parte de código (AST) funcionaria
  sem qualquer LLM.
- Extração semântica é não-determinística (LLM) — duas indexações do mesmo conteúdo podem produzir
  nós/arestas ligeiramente diferentes na camada semântica. A camada de código (AST) é sempre
  determinística.
- Ferramenta local, não faz parte do CI nem do runtime da aplicação — não afeta produção.
