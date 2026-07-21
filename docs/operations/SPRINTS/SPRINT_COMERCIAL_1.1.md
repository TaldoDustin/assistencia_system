# SPRINT COMERCIAL 1.1 — Tela Produtos

**Status:** CONCLUÍDA
**Período:** 2026-07-21 (dia único)
**Tipo:** Feature (frontend)

---

## Objetivo

Permitir que um vendedor visualize rapidamente o catálogo comercial da empresa. Priorizar clareza
visual e velocidade de consulta, não apenas reproduzir um CRUD administrativo — primeira tela do
Épico Vendas, consumindo integralmente o backend já entregue na Sprint Comercial 0.1.

## Motivação

Sequenciamento decidido pelo usuário (CTO) pela ótica de impacto na próxima reunião com cliente, não
pela ótica de implementação: Produtos primeiro porque backend/testes já prontos, zero mudança de
banco, e demonstra imediatamente que a Fluxoly vende produtos, não só presta assistência. Ajuste de
produto pedido antes da aprovação: não reproduzir apenas linhas de tabela — um lojista pensa em
perguntas ("quantos iPhones eu tenho?"), não em campos de formulário.

---

## Arquivos Envolvidos

| Arquivo | Mudança |
|---------|---------|
| `frontend/src/pages/Produtos.jsx` | Novo — página completa (cards, busca, filtros, tabela, modais) |
| `frontend/src/api/client.js` | Novo objeto `produtos` (get/create/update/delete), mesmo padrão de `estoque` |
| `frontend/src/App.jsx` | Nova rota `/produtos` |
| `frontend/src/components/Layout.jsx` | Novo item de menu "Produtos" (ícone `ShoppingBag`, sem `adminOnly`) |

---

## Entregas

| Entrega | Tipo | Status |
|---------|------|--------|
| Listagem, busca e filtros (categoria/condição/status) | feat | Concluído |
| Cards de resumo (Produtos/Seminovos/Vitrine, calculados no frontend) | feat | Concluído |
| Badges de categoria com emoji | feat | Concluído |
| Modal de cadastro/edição, exclusão com confirmação | feat | Concluído |
| Permissão: leitura para qualquer perfil autenticado, escrita restrita a `admin` | feat | Concluído |
| Coluna "Unidades" (placeholder `—`, reserva de layout para IMEI futuro) | feat | Concluído |
| Validação manual end-to-end (app rodando localmente, banco isolado) | test | Concluído |

---

## Critérios de Aceitação

- [x] Consome integralmente `/api/produtos*` existente, sem alterar backend/schema/regra de negócio
- [x] Busca única cobre descrição, categoria, marca, modelo, cor, capacidade, SKU e condição (client-side —
      o parâmetro `q` do backend só cobre descrição/modelo/SKU)
- [x] Cards de resumo refletem o catálogo completo, não a lista filtrada
- [x] Criar/editar/excluir visível e funcional apenas para perfil `admin`; leitura visível para
      qualquer perfil autenticado (ex.: `vendedor`)
- [x] Layout reserva espaço para quantidade/unidades por IMEI sem precisar redesenhar depois

---

## Testes Obrigatórios

Não há framework de teste de componente/unitário para páginas no frontend hoje (`PROJECT_STATUS.md`:
0% de cobertura unitária de frontend) — só E2E Playwright para fluxos principais
(`frontend/tests/e2e/app.spec.js`), não expandido nesta sprint por decisão de manter o escopo pequeno.

| Verificação | Método | O que validou |
|-------------|--------|----------------|
| Lint (`eslint .`) | Automatizado | Nenhum erro novo introduzido (5 erros/2 warnings pré-existentes, fora dos arquivos tocados) |
| Build (`vite build`) | Automatizado | Compila sem erros, chunk próprio gerado (`Produtos-*.js`) |
| Fluxo completo (login → listar → buscar → criar → editar → excluir) | Manual, Playwright dirigido via script | Cards, badges, busca combinada, toasts, contadores e status (Disponível/Esgotado) corretos em cada etapa |
| Visão do perfil `vendedor` | Manual, Playwright dirigido via script | Catálogo visível, sem botão "Novo Produto" nem ícones de editar/excluir |

---

## Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| RS-01 | Busca client-side carrega até 500 produtos de uma vez (`per_page: 500`) em vez de paginar | Baixa | Baixo | Catálogo ainda pequeno; se crescer, revisitar com paginação real ou busca server-side ampliada (fora de escopo desta sprint, que não altera backend) |

---

## Dependências

- Depende de: Sprint Comercial 0.1 (backend `produtos`) — concluída.
- Bloqueia: nada diretamente, mas é o modelo de referência visual (cards, busca combinada, coluna
  placeholder) para C1.2 (Clientes) e C1.3 (IMEI).

---

## Definition of Done

- [x] Todos os critérios de aceitação atingidos
- [x] Lint e build sem erros novos
- [x] `CHANGELOG.md` atualizado
- [x] `PROJECT_STATUS.md` atualizado
- [x] `KNOWN_ISSUES.md` — nenhum bug novo encontrado nesta sprint, nada a registrar
- [x] `ROADMAP.md` — não altera fase/sprint numerada do roadmap técnico (é sequência do Épico Vendas
      combinada à parte com o usuário)
- [x] Commits seguem Conventional Commits

---

## Retrospectiva

### O que funcionou bem

Backend pronto e testado (Sprint Comercial 0.1) tornou esta sprint zero-risco de regressão — nenhuma
linha de `app.py`/`irflow_blueprints_api.py` tocada. Validação manual ponta a ponta (servidor real +
banco isolado + navegador dirigido) pegou o comportamento real de permissão (vendedor vs. admin) que
nenhum teste automatizado cobre ainda no frontend.

### O que poderia ter sido melhor

Ausência de framework de teste de frontend (unitário/componente) significa que esta validação não é
repetível automaticamente — qualquer regressão futura na tela só aparece em teste manual ou E2E
Playwright, se expandido.

### Lições aprendidas para a próxima sprint

Para C1.2 (Clientes), o mesmo padrão de cards de resumo + busca combinada client-side deve servir de
referência direta, evitando redecidir esses detalhes de UX do zero.

### Dívida técnica gerada

Nenhuma nova. `frontend/tests/e2e/app.spec.js` não foi expandido para cobrir Produtos — candidato a
uma sprint de testes de frontend dedicada, não esta.
