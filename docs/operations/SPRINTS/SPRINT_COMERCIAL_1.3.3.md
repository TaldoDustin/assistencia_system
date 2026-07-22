# SPRINT COMERCIAL 1.3.3 — Filtros Avançados

**Status:** CONCLUÍDA
**Período:** 2026-07-22 (dia único)
**Tipo:** Feature (backend + frontend)

---

## Objetivo

Permitir que o técnico ou vendedor encontre qualquer aparelho em poucos segundos: busca combinada
(IMEI/serial, modelo, marca, localização), filtros por origem/status/faixa de saúde da
bateria/localização, ordenação, e persistência de busca/filtros/paginação ao abrir e fechar o detalhe.

## Motivação

Terceira e última etapa de usabilidade da listagem de Unidades Serializadas, na sequência definida pelo
usuário (CTO) após C1.3.1 (listagem) e C1.3.2 (detalhes).

---

## Investigação e decisões de escopo (antes de codar)

Três pontos do pedido original não tinham suporte real no sistema — reportados ao usuário antes de
implementar, com opções e recomendação técnica em cada um:

| Ponto pedido | Decisão do usuário (CTO) |
|---|---|
| Filtro por Cliente | **Removido desta sprint.** Nenhuma unidade tem relação com cliente hoje (depende do Épico Vendas) — um filtro sempre vazio geraria expectativa falsa. Volta quando `cliente_atual` existir de verdade. |
| Status "Em Garantia" / "Inativo" | **Não incluídos.** Não existem em lugar nenhum do sistema — criá-los seria definir regra de negócio nova (quando uma unidade entra em garantia/fica inativa), não um filtro. Filtro cobre os status que existem hoje: Disponível, Em Reparo, Devolvido, Reservado, Vendido (os 2 últimos no schema desde o ADR-007, reservados para Vendas). |
| Filtro por Saúde da bateria / Localização | **Construídos mesmo assim.** As colunas existem mas nenhum endpoint as grava ainda (mesmo padrão do KI-020) — os filtros funcionam corretamente hoje (inclusive "Não informado", que sempre bate com tudo), e passam a ter dado real assim que C1.3.4 (Edição) existir, sem retrabalho. |

Achado adicional: "IMEI/Serial" já é o mesmo campo (`unidades_serializadas.imei`, `TEXT UNIQUE`) — não
existe uma coluna "serial" separada, e não precisa existir (o campo já aceita qualquer identificador).
"Marca" só existe para unidades de origem `produto` (`produtos.marca`) — `estoque` não tem essa coluna,
assimetria real do domínio, não bug.

---

## Arquivos Envolvidos

| Arquivo | Mudança |
|---------|---------|
| `irflow_unidades_serializadas_repository.py` | `_montar_filtros_avancados` (busca combinada multi-coluna via `LEFT JOIN`, origem, status, faixa de bateria via `CAST`, localização); `buscar_paginado`/`contar` reescritos para os novos parâmetros + `sort` (whitelist SQL, nunca interpolado direto) |
| `irflow_unidades_serializadas_service.py` | `listar_unidades` com novos parâmetros; `FAIXAS_SAUDE_BATERIA` traduz a faixa escolhida em min/max/"não informado" antes de chegar no repository |
| `irflow_unidades_serializadas_controller.py` | Novos query params (`q`, `origem`, `saude_bateria_faixa`, `localizacao`, `sort`); `imei` mantido por compatibilidade, alimenta a mesma busca combinada |
| `frontend/src/pages/UnidadesSerializadas.jsx` | Reescrita: busca com debounce, 5 filtros, ordenação, paginação real (sem mais `per_page: 500` + filtro local) |
| `tests/test_unidades_serializadas.py` | 12 novos casos; helper `_criar_produto` corrigido para gravar `marca` (não gravava antes) |

---

## Entregas

| Entrega | Tipo | Status |
|---------|------|--------|
| Busca combinada (IMEI/serial, modelo, descrição, marca, localização) resolvida no backend | feat | Concluído |
| Filtro por Origem (Estoque/Produto) | feat | Concluído |
| Filtro por Status (todos os alcançáveis hoje) | feat | Concluído |
| Filtro por faixa de Saúde da bateria (5 faixas, incluindo "Não informado") | feat | Concluído |
| Filtro por Localização (texto livre) | feat | Concluído |
| Ordenação (recente/antigo/IMEI/modelo/status) | feat | Concluído |
| Paginação real (server-side, 20/página) | feat | Concluído |
| Persistência de busca/filtros/paginação ao abrir/fechar detalhe | feat | Já funcionava (arquitetura de modal, confirmado nesta sprint) |
| Validação manual end-to-end | test | Concluído |

---

## Critério de Aceite (conforme pedido)

- [x] Todos os filtros funcionam combinados (`test_filtros_combinados`, mais validado manualmente)
- [x] Nenhum filtro é feito só no frontend quando a API pode filtrar — busca, origem, status, faixa de
      bateria, localização e ordenação são todos resolvidos via query params no backend
- [x] Paginação real (20/página) evita carregar milhares de unidades de uma vez — antes a tela buscava
      `per_page: 500` uma vez e filtrava tudo em memória no navegador
- [x] Todos os testes passam (455 → 467, incluindo 12 novos deste domínio)
- [x] Build e lint permanecem verdes (`ruff check .` limpo, `eslint .` sem erros novos)

---

## Testes Obrigatórios

| Teste | Arquivo | O que validou |
|-------|---------|----------------|
| Suíte completa do domínio | `tests/test_unidades_serializadas.py` | 34 → 46 casos: busca por modelo/marca/localização, parâmetro `imei` legado ainda funciona, filtro de origem (2 variações), filtro de faixa de bateria (incluindo "não informado"), filtro de localização, ordenação por IMEI e por status, filtros combinados |
| Lint (`ruff check .`) | Automatizado | 0 erros no repositório inteiro |
| Lint frontend (`eslint .`) / Build (`vite build`) | Automatizado | Nenhum erro novo — corrigido durante o desenvolvimento um padrão de `setState` síncrono em efeito (mesma correção já aplicada em `Clientes.jsx`) |
| Fluxo completo (busca por marca, filtro de origem, filtro de bateria, abrir/fechar detalhe) | Manual, Playwright dirigido via script + dados semeados via API | Todos os filtros retornaram exatamente o subconjunto esperado; busca/filtro confirmados persistentes ao fechar o painel de detalhe |

---

## Riscos

| ID | Risco | Probabilidade | Impacto | Mitigação |
|----|-------|---------------|---------|-----------|
| RS-01 | Filtros de saúde de bateria/localização não retornam nada até C1.3.4 gravar esses campos | Alta (hoje) | Baixo | Decisão deliberada do usuário — filtro correto, só falta o lado de escrita, que já está no roadmap |
| RS-02 | `CAST(saude_bateria AS INTEGER)` em coluna `TEXT` pode se comportar de forma inesperada se algum dia o campo receber texto não numérico | Baixa | Baixo | SQLite `CAST` para texto não numérico resulta em `0`, não erro — comportamento testado e aceitável para o caso de uso (percentual) |

---

## Dependências

- Depende de: C1.3.1, C1.3.2 — concluídas.
- Bloqueia: nada diretamente. C1.3.4 (Edição) é o próximo passo natural para dar dado real aos filtros
  de bateria/localização.

---

## Definition of Done

- [x] Todos os critérios de aceite atingidos
- [x] Testes obrigatórios passando, sem regressão
- [x] `CHANGELOG.md` e `PROJECT_STATUS.md` atualizados
- [x] `KNOWN_ISSUES.md` — nenhum bug novo encontrado
- [x] Commits seguem Conventional Commits

---

## Retrospectiva

### O que funcionou bem

Reportar os três gaps de escopo (Cliente, novos status, dados vazios) antes de codar evitou construir
UI para conceitos que não existem — e a decisão de "construir mesmo sem dado" para bateria/localização
já deixa o terreno pronto para C1.3.4 sem retrabalho.

### O que poderia ter sido melhor

O card de resumo perdeu a granularidade por status (antes mostrava Disponíveis/Em Reparo) — trocado por
um único "total encontrado" para não sacrificar performance com consultas extras a cada filtro. Vale
reavaliar se o usuário sentir falta na prática.

### Dívida técnica gerada

Nenhuma nova.
