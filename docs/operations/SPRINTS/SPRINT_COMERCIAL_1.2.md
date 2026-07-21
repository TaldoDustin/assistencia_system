# SPRINT COMERCIAL 1.2 — Tela Clientes

**Status:** CONCLUÍDA
**Período:** 2026-07-21 (dia único)
**Tipo:** Feature (frontend)

---

## Objetivo

Segunda tela do Épico Vendas — dar visibilidade ao domínio Clientes (backend pronto desde a Sprint 3
Unidade 5) e demonstrar o potencial de perfil unificado do cliente, mesmo com módulos ainda não
implementados (Vendas) aparecendo como placeholder vazio.

## Motivação

Sequência definida pelo usuário (CTO) após a Tela Produtos: Clientes é o segundo item por ter backend
pronto e por reforçar a percepção de produto completo ("Clientes → João → Compras/Garantias/OS").

---

## Arquivos Envolvidos

| Arquivo | Mudança |
|---------|---------|
| `frontend/src/pages/Clientes.jsx` | Novo — listagem, busca, cards, CRUD e painel de perfil |
| `frontend/src/api/client.js` | Novo objeto `clientes` (get/list/create/update/delete); `garantias.list` passou a aceitar parâmetros (`q`) |
| `frontend/src/App.jsx` | Nova rota `/clientes` |
| `frontend/src/components/Layout.jsx` | Novo item de menu "Clientes" (ícone `UserCircle`, distinto de "Usuários") |

---

## Entregas

| Entrega | Tipo | Status |
|---------|------|--------|
| Listagem, busca única e cards de resumo (Clientes/Com telefone/Com e-mail) | feat | Concluído |
| Modal de cadastro/edição (qualquer perfil autenticado, igual ao backend) | feat | Concluído |
| Exclusão restrita a `admin` (backend já bloqueia cliente com OS vinculada) | feat | Concluído |
| Painel de Perfil do Cliente (dados, observações, histórico de OS, garantias, compras) | feat | Concluído |
| Validação manual end-to-end (app rodando localmente, banco isolado) | test | Concluído |

---

## Achados durante a investigação (antes de codar)

- `os.cliente_id` existe no schema (`app.py`, Sprint P0.1) mas **nenhum fluxo real hoje o preenche** —
  só testes escrevem nele diretamente no banco. Não é utilizável para montar o histórico de OS de um
  cliente.
- O caminho real e já em uso é o endpoint legado `GET /api/ordens/historico-cliente?cliente=<nome>`,
  que casa pelo campo texto `os.cliente` (case-insensitive, últimas 10). Reaproveitado para a aba de
  Histórico de OS do perfil — nenhum endpoint novo.
- `GET /api/garantias?q=<termo>` já aceita filtro de texto (cliente/modelo/imei) — reaproveitado para a
  aba de Garantias do perfil. `garantias.list` no client.js só aceitava chamada sem parâmetros;
  estendida para aceitar `params` (mudança de frontend, endpoint já suportava o parâmetro).
- "Compras" fica como placeholder vazio ("módulo de Vendas em construção") — decisão já antecipada pelo
  usuário.

---

## Critérios de Aceitação

- [x] Consome integralmente `/api/clientes*`, `/api/ordens/historico-cliente` e `/api/garantias`
      existentes, sem alterar backend/schema/regra de negócio
- [x] Busca única cobre nome, telefone, e-mail e CPF/CNPJ (client-side — o parâmetro `q` do backend só
      cobre nome/telefone/cpf_cnpj)
- [x] Criar/editar visível para qualquer perfil autenticado; excluir restrito a `admin`, espelhando o
      backend (`irflow_clientes_controller.py`)
- [x] Perfil do cliente mostra histórico de OS e garantias reais; compras aparece como placeholder
      claro, não como erro ou tela quebrada

---

## Testes Obrigatórios

Mesma situação da Sprint Comercial 1.1: sem framework de teste de componente/unitário no frontend.

| Verificação | Método | O que validou |
|-------------|--------|----------------|
| Lint (`eslint .`) | Automatizado | Nenhum erro novo (1 erro de `set-state-in-effect` corrigido durante o desenvolvimento, removendo um `setLoading(true)` redundante — estado inicial já era `true`) |
| Build (`vite build`) | Automatizado | Compila sem erros |
| Fluxo completo (login → listar → buscar → criar → editar → excluir) | Manual, Playwright dirigido via script | Cards, busca combinada, toasts e contadores corretos em cada etapa |
| Perfil do cliente | Manual, Playwright dirigido via script + API direta | Cliente e OS de teste seedados via API (mesmo nome), histórico de OS e garantia real exibidos corretamente; compras mostrando placeholder |

---

## Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| RS-01 | Histórico de OS depende de correspondência exata de nome (`os.cliente` texto livre) — cliente cadastrado com nome diferente do usado nas OS antigas não mostra histórico | Média | Baixo | Mesma limitação já existente no sistema (endpoint legado); resolver de vez exige popular `os.cliente_id` de verdade, fora de escopo desta tela |
| RS-02 | Busca client-side carrega até 500 clientes de uma vez (`per_page: 500`), mesma decisão da Tela Produtos | Baixa | Baixo | Base de clientes ainda pequena; revisitar se crescer |

---

## Dependências

- Depende de: domínio Clientes (Sprint 3 Unidade 5) e Sprint Comercial 1.1 (padrão visual de
  cards/busca/permissão) — ambos concluídos.
- Bloqueia: nada diretamente; é referência de padrão para C1.3 (IMEI).

---

## Definition of Done

- [x] Todos os critérios de aceitação atingidos
- [x] Lint e build sem erros novos
- [x] `CHANGELOG.md` atualizado
- [x] `PROJECT_STATUS.md` atualizado
- [x] `KNOWN_ISSUES.md` — nenhum bug novo encontrado, nada a registrar
- [x] Commits seguem Conventional Commits

---

## Retrospectiva

### O que funcionou bem

Reaproveitar os dois endpoints já existentes (`historico-cliente`, `garantias?q=`) evitou qualquer
necessidade de tocar o backend — o perfil do cliente ficou rico (histórico real, não só cadastro) sem
sair do escopo "consumir API existente".

### O que poderia ter sido melhor

O histórico de OS por nome-texto é uma limitação conhecida e antiga do sistema, não desta sprint — mas
agora fica mais visível na UI (um cliente cadastrado com nome levemente diferente do usado nas OS não
vê o próprio histórico). Vale um KI se isso incomodar na prática.

### Lições aprendidas para a próxima sprint

Para C1.3 (IMEI), verificar antes de codar se existe caminho equivalente de correlação (produto ↔
unidade) — mesmo tipo de investigação que evitou retrabalho aqui.

### Dívida técnica gerada

Nenhuma nova.
