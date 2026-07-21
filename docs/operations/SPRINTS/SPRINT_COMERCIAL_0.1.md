# SPRINT COMERCIAL 0.1 — Catálogo de Produtos

**Status:** CONCLUÍDA
**Período:** 2026-07-20 (dia único)
**Tipo:** Feature

---

## Objetivo

Criar o catálogo comercial de venda (`produtos`) — categoria, marca, modelo, cor, capacidade, condição,
preço de custo/venda, margem — como primeiro passo do Épico Vendas. Backend apenas (schema + CRUD +
testes); tela fica para o próximo PR.

## Motivação

Divisão de trabalho acordada com o usuário (CTO): Frente A (relacionamento com cliente/requisitos),
Frente B (Claude, implementação em tarefas pequenas e fechadas). Vendas é o módulo prioritário do
produto, mas "faça o módulo de vendas" é grande demais para uma tarefa fechada — o catálogo comercial é
o primeiro pré-requisito estrutural, na mesma lógica já usada em Clientes/IMEI na Sprint P0.1.

---

## Arquivos Envolvidos

| Arquivo | Mudança prevista |
|---------|-----------------|
| `app.py` | `CREATE TABLE produtos` + índices; registro do blueprint |
| `irflow_produtos_repository.py` | Novo — SQL parametrizado |
| `irflow_produtos_service.py` | Novo — validação, cálculo de margem, auditoria |
| `irflow_produtos_controller.py` | Novo — blueprint `/api/produtos` |
| `irflow_reference_data.py` | `PRODUTOS_CATEGORIAS`, `PRODUTOS_CONDICOES` |
| `tests/test_produtos.py` | Novo — cobertura de `/api/produtos*` |

---

## Entregas

| Entrega | Tipo | Status |
|---------|------|--------|
| Schema `produtos` (domínio novo, separado de `estoque`) | feat | Concluído |
| CRUD `/api/produtos*` (controller/service/repository) | feat | Concluído |
| Testes (27 casos) | test | Concluído |
| Documentação (`DATABASE.md`, `BUSINESS_RULES.md`, `VENDAS.md`, `PRODUCT_BACKLOG.md`) | docs | Concluído |

---

## Critérios de Aceitação

- [x] `produtos` existe com categoria/condição validadas contra lista fechada, sem coerção silenciosa
- [x] CRUD completo via `/api/produtos*`, permissão leitura-autenticada/escrita-admin
- [x] Margem calculada no service, nunca persistida
- [x] `estoque`/`estoque_unidades`/`Stock.jsx` (peças de reparo) intocados

---

## Testes Obrigatórios

| Teste | Arquivo | O que valida |
|-------|---------|-------------|
| CRUD feliz + auditoria | `tests/test_produtos.py` | Criar/listar/obter/atualizar/excluir, log de auditoria na criação |
| Categoria/condição inválida | `tests/test_produtos.py` | Rejeitada com 400, não normalizada (BR-027) |
| Preço de venda ausente/zero/negativo, custo negativo | `tests/test_produtos.py` | Rejeitados com 400 |
| Margem calculada | `tests/test_produtos.py` | `preco_venda - preco_custo`; `None` sem `preco_custo` |
| Permissão | `tests/test_produtos.py` | 401/403 conforme perfil em cada rota |

---

## Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| RS-01 | `VENDAS.md` documenta `vendas.estoque_unidade_id` apontando para `estoque_unidades`, que não serve mais para produto comercial | Alta | Médio | Nota adicionada em `VENDAS.md` sinalizando revisão necessária no Sprint Comercial 0.2 — sem código de Vendas ainda, custo de correção é baixo |

---

## Dependências

- Depende de: nada — domínio novo, standalone.
- Bloqueia: Sprint Comercial 0.2 (rastreamento por unidade/IMEI de produtos) e 0.3 (Tela de Venda MVP).

---

## Definition of Done

- [x] Todos os critérios de aceitação atingidos
- [x] Testes obrigatórios passando (434 no total, 407 + 27 novos)
- [x] `ruff check .` — 0 erros
- [x] Cobertura não regrediu (48%)
- [x] `CHANGELOG.md` atualizado
- [x] `PROJECT_STATUS.md` atualizado
- [x] `KNOWN_ISSUES.md` — nenhum bug novo identificado nesta sprint
- [ ] `ROADMAP.md` — não atualizado nesta sprint (ainda estruturado por Fase/Sprint técnica, não por
      Release/Épico comercial; reorganização é decisão em aberto, não decidida nesta tarefa)
- [x] Commits em Conventional Commits

---

## Retrospectiva

### O que funcionou bem

Investigar antes de implementar (2 agentes de pesquisa em paralelo, docs + código real) evitou estender
`estoque` de forma que misturaria peça de reparo com produto comercial na mesma tabela — decisão
confirmada com o usuário antes de qualquer linha de schema.

### O que poderia ter sido melhor

`VENDAS.md` foi escrito antes de existir um catálogo comercial desenhado — o schema proposto lá
(`estoque_unidade_id`) ficou desatualizado assim que este domínio nasceu. Não é um erro de processo (o
gap era real e só ficou visível investigando), mas reforça que specs escritas sem implementação por perto
divergem rápido.

### Lições aprendidas para a próxima sprint

Sprint Comercial 0.2 (rastreamento por unidade/IMEI de produtos) precisa decidir a tabela filha
(`produtos_unidades`, candidata) **e** atualizar `VENDAS.md` na mesma tarefa — não depois.

### Dívida técnica gerada

Nenhuma nova. `requer_rastreio_unidade` existe no schema desde já para não exigir outro `ALTER TABLE`
quando o Sprint Comercial 0.2 chegar.
