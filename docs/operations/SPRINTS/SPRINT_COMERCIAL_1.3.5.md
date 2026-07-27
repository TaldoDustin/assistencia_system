# SPRINT COMERCIAL 1.3.5 — Rastreabilidade Individual de Itens de Estoque

**Status:** CONCLUÍDA
**Período:** 2026-07-27 (dia único)
**Tipo:** Bug fix + feature (backend + frontend)

---

## Objetivo

Fechar o KI-020: permitir marcar um item de `estoque` como exigindo rastreabilidade individual
(hoje via IMEI/serial) através da UI/API, em vez de exigir escrita direta no banco. O nome da coluna
(`requer_imei`) é histórico — o conceito que a sprint resolve é mais amplo: **rastreabilidade
individual do item**, não apenas IMEI. À medida que o sistema deixar de ser Apple-centric, o mesmo
campo pode passar a cobrir número de série, MAC address ou outro identificador único — o nome técnico
é mantido por compatibilidade, a documentação e a UX já refletem o conceito mais amplo.

## Motivação

Sequência definida pelo usuário (CTO) após INC-001 (Branch A + Branch C mergeadas e enviadas em
2026-07-27): próximo item antes de retomar o Épico Vendas. Investigação confirmou que o KI-020,
identificado em 2026-07-21 durante a Sprint C1.3.1, bloqueava de fato o fluxo comercial: o domínio
`unidades_serializadas` já lê `estoque.requer_imei` para decidir se uma unidade pode ser criada a
partir de um item de estoque (`irflow_unidades_serializadas_service.py:175`), mas nenhuma rota
permitia gravar esse valor como `1` — todo item nascia com o default `0` e nunca podia mudar. Só o
caminho via `produtos.requer_rastreio_unidade` (já totalmente cabeado) funcionava de ponta a ponta.

---

## Investigação e decisões de escopo (antes de codar)

| Ponto | Situação real | Decisão |
|---|---|---|
| Onde vive a lógica de Estoque hoje | Direto em `irflow_blueprints_api.py`, domínio legado, sem controller/service/repository | Não migrar para a convenção de `ENGINEERING_GUIDE.md` §3.1 nesta sprint — misturaria refactor com feature |
| Nome do campo | `requer_imei`, já existente no schema desde a Sprint P0.1 | Mantido por compatibilidade; conceito documentado como "rastreabilidade individual" nesta sprint e no comentário de código |
| Indicador na listagem (tabela) | `produtos.requer_rastreio_unidade` não tem indicador na listagem, só no form | Mesmo padrão aplicado a Estoque — só checkbox no form, sem coluna nova na tabela |

---

## Critérios de Aceitação

| # | Critério |
|---|---|
| CA-1 | `POST /api/estoque` grava `requer_imei` quando enviado no corpo |
| CA-2 | `PUT /api/estoque/<id>` grava `requer_imei` quando enviado no corpo (liga e desliga) |
| CA-3 | `GET /api/estoque` expõe `requer_imei` como booleano por item |
| CA-4 | Omitir o campo em qualquer uma das rotas acima preserva o comportamento anterior (default `0`/`false`) — sem regressão |
| **CA-5** | **Fluxo completo, ponta a ponta:** criar item → marcar "requer rastreabilidade" → salvar → criar unidade serializada selecionando esse item → sucesso. Este é o verdadeiro objetivo da sprint |

---

## Arquivos Envolvidos

| Arquivo | Mudança |
|---------|---------|
| `irflow_blueprints_api.py` | `listar_estoque()` expõe `requer_imei`; `criar_estoque()`/`atualizar_estoque()` leem e gravam `requer_imei` |
| `frontend/src/pages/Stock.jsx` | Checkbox "Requer rastreabilidade (IMEI / Nº de série)" no form de criar/editar |
| `tests/test_stock_creation_query.py` | `TestRastreabilidadeIndividualEstoque` (3 casos — criar true/false, listar) |
| `tests/test_stock_movement.py` | `TestAtualizarRastreabilidadeIndividual` (3 casos — ligar, desligar, omitir) |
| `tests/test_unidades_serializadas.py` | `TestIntegracaoEstoqueViaApiC135` (2 casos — CA-5 completo via API real, e regressão sem a flag) |

---

## Entregas

| Entrega | Tipo | Status |
|---------|------|--------|
| `requer_imei` gravável via `POST`/`PUT /api/estoque` | feat | Concluído |
| `requer_imei` exposto em `GET /api/estoque` | feat | Concluído |
| Checkbox no form de Estoque (frontend) | feat | Concluído |
| KI-020 movido para Resolvidos | docs | Concluído |
| Fluxo completo validado por teste (CA-5) | test | Concluído |

---

## Testes

8 novos casos (549 no total), `ruff check .` limpo, `npm run build`/`npm run lint` sem erros novos
introduzidos por esta sprint (erros pré-existentes em outros arquivos não tocados aqui).

O teste mais importante (`TestIntegracaoEstoqueViaApiC135`) exercita o fluxo real via HTTP, não via
seed direto no banco: `POST /api/estoque` (perfil `estoque`) com `requer_imei: true` → `POST
/api/unidades-serializadas` (perfil `tecnico`) com o `estoque_id` retornado → sucesso. Um segundo
teste confirma que o mesmo fluxo, sem marcar a flag, continua rejeitado — mesmo comportamento de antes
da sprint, agora provado via API real em vez de só via fixture de banco.

---

## Riscos

Nenhum novo. Coluna já existia (`DEFAULT 0`), mudança é aditiva na leitura/escrita, sem alteração de
schema.

---

## Dependências

- Depende de: C1.3.1–C1.3.4 (concluídas), domínio `unidades_serializadas` (ADR-007).
- Desbloqueia: uso real do caminho "unidade serializada com origem em Estoque" — pré-requisito para
  cenários de Vendas que envolvam aparelhos rastreados via Estoque, não só via `produtos`.

---

## Definition of Done

- [x] Todos os critérios (CA-1 a CA-5) atingidos
- [x] Testes obrigatórios passando, sem regressão (549 testes)
- [x] `CHANGELOG.md`, `PROJECT_STATUS.md` e `KNOWN_ISSUES.md` atualizados
- [x] Commits seguem Conventional Commits

---

## Retrospectiva

### O que funcionou bem

Reaproveitar o padrão já validado em `produtos.requer_rastreio_unidade` (mesmo nome de conceito,
mesma forma de coerção `1 if body.get(...) else 0`, mesmo estilo de checkbox) manteve a mudança pequena
e previsível — sem decisões de design novas a tomar.

### O que poderia ter sido melhor

Nada a registrar nesta sprint.

### Dívida técnica gerada

Nenhuma nova.
