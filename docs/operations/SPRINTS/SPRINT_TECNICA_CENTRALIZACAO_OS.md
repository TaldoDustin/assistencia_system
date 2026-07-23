# SPRINT TÉCNICA — Centralização de Referências de OS

**Status:** CONCLUÍDA
**Período:** 2026-07-23 (dia único)
**Tipo:** Chore (centralização de referências)

---

## Objetivo

Segunda parte da centralização de referências pedida pelo usuário (CTO) — a primeira (2026-07-22)
cobriu categorias/condições de Produtos. Esta cobre o domínio de OS: tipos, status e prazo de garantia.

## Motivação

Pedido explícito do usuário após a Sprint Comercial 1.3.4, citando o próprio Hotfix H-002 (catálogo
iPhone 17) como exemplo do risco de listas duplicadas divergirem silenciosamente.

---

## Investigação (antes de codar)

Mapeamento completo de listas/constantes de referência no sistema, feito antes de qualquer mudança:

| Item | Situação encontrada | Ação |
|---|---|---|
| **Tipos de OS** (Assistencia/Garantia/Upgrade) | Literal inline em 2 lugares no backend (nem uma constante nomeada); **3 cópias no frontend** (`lib/constants.js`, fallback em `NewOrder.jsx`, fallback em `EditOrder.jsx`); `OrderFilters.jsx` **nunca buscava da API**, só usava a cópia estática | ✅ Centralizado |
| **Status de OS** | Backend já centralizado (`STATUS_OS_OPCOES`, `irflow_core.py`) e exposto; mesma falha do item acima em `OrderFilters.jsx` | ✅ Centralizado |
| **Prazo de garantia (90 dias)** | Literal `90` hardcoded **2x no mesmo arquivo** backend (nem uma constante); `GARANTIA_DIAS` exportado no frontend mas **nunca importado em lugar nenhum** — código morto | ✅ Centralizado + código morto removido |
| **Perfis** (admin/tecnico/vendedor) | Espalhado como string literal em 11 arquivos backend, sem lista central | ❌ Fora de escopo — categoria diferente (lógica de autorização, não lista de referência para UI); tocar 11 arquivos de permissão é risco alto e desproporcional. Registrado como achado separado, não uma tarefa desta sprint |
| **Estoque tipos/qualidades** | Já funcional (fonte única, exposta, consumida com fallback defensivo) — só definida dentro de `irflow_blueprints_api.py` em vez de `irflow_reference_data.py` | Não tocado — inconsistência cosmética de localização, sem risco funcional, fora do escopo desta sprint |
| **Produtos categorias/condições, Modelos/cores de iPhone** | Já centralizados em sprints anteriores | Confirmado, nenhuma ação |

---

## Arquivos Envolvidos

| Arquivo | Mudança |
|---------|---------|
| `irflow_core.py` | `OS_TIPOS_OPCOES`, `GARANTIA_REPARO_DIAS_PADRAO` (novas constantes nomeadas) |
| `app.py` | Import das novas constantes; adicionadas ao deps dict de `create_api_blueprint` |
| `irflow_blueprints_api.py` | Rota `/constantes` e `listar_garantias` passam a usar as constantes em vez de literais soltos |
| `frontend/src/lib/constants.js` | `STATUS_OPTIONS`/`OS_TYPES` renomeados para `*_FALLBACK` (só fallback defensivo, não fonte primária); `GARANTIA_DIAS` (código morto) removido |
| `frontend/src/pages/Orders.jsx` | Passa a buscar `/api/constantes` e repassar para `OrderFilters` |
| `frontend/src/components/orders/OrderFilters.jsx` | Passa a consumir `constants.status_opcoes`/`constants.os_tipos` da API, com fallback |
| `frontend/src/pages/NewOrder.jsx`, `EditOrder.jsx` | Fallback inline duplicado substituído pela constante compartilhada de `lib/constants.js` |
| `tests/test_constantes_os.py` | 2 novos testes |

---

## Entregas

| Entrega | Status |
|---------|--------|
| `OS_TIPOS_OPCOES`/`GARANTIA_REPARO_DIAS_PADRAO` centralizados em `irflow_core.py` | Concluído |
| `/api/constantes` e `/api/garantias` consomem as constantes nomeadas, não literais soltos | Concluído |
| `OrderFilters.jsx` passa a consumir a API (antes nunca buscava) | Concluído |
| 5 cópias frontend (3 de tipos/status + 1 código morto) reduzidas a 1 fallback compartilhado | Concluído |
| Validação manual end-to-end | Concluído |

---

## Testes

| Teste | O que valida |
|-------|--------------|
| `test_constantes_inclui_os_tipos_e_garantia_dias` | `/api/constantes` retorna exatamente `OS_TIPOS_OPCOES`/`GARANTIA_REPARO_DIAS_PADRAO` |
| `test_garantias_usa_o_mesmo_prazo_padrao` | `/api/garantias` calcula `dias_restantes` com o mesmo prazo padrão centralizado |

478 testes no total (476 + 2 novos), `ruff check .` limpo, `eslint .`/`vite build` sem erros novos.
Validado manualmente: dropdowns de Status e Tipo em `/ordens` populados a partir de `GET /api/constantes`
real, confirmados nos valores exatos (`Em andamento`, `Aguardando peca`, `Finalizado`, `Cancelado`,
`Assistencia`, `Garantia`, `Upgrade`).

---

## Achado registrado, não corrigido

**Perfis (`admin`/`tecnico`/`vendedor`) sem lista central** — 11 arquivos backend comparam perfil contra
string literal diretamente (`session.get("usuario_perfil") == "admin"`), sem nenhuma
`PERFIS_VALIDOS`/`PERFIS_OPCOES` central. Diferente das outras centralizações desta sprint, isso é lógica
de autorização espalhada, não uma lista de referência para popular dropdown — formalizar um "único lugar"
aqui provavelmente significa um helper de permissão central, não só uma constante, e tocar 11 arquivos
de controle de acesso de uma vez é risco desproporcional para um "chore". Candidato a uma sprint própria,
com escopo e plano de teste dedicados — não decidido nem iniciado aqui.

---

## Definition of Done

- [x] Todos os pontos investigados, decisão registrada para cada um
- [x] Testes obrigatórios passando, sem regressão
- [x] `CHANGELOG.md` e `PROJECT_STATUS.md` atualizados
- [x] Commits seguem Conventional Commits
