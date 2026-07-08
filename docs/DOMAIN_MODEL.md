# DOMAIN_MODEL.md — Mapa de Domínios

Este documento mapeia os domínios de negócio do Assistência System **como eles existem hoje no código**.
Não descreve estado desejado nem features futuras em detalhe — para isso, ver `PRODUCT_ROADMAP.md` (quando existir)
e os ADRs relevantes. Divergências entre este documento e o código devem ser corrigidas aqui (o código é a fonte
da verdade — mesma regra de `ARCHITECTURE.md`).

**Última revisão:** 2026-07-08
**Fonte:** `app.py` (schema), `docs/ARCHITECTURE.md` (camadas), leitura direta dos módulos `irflow_*.py`.

---

## 1. Domínios existentes

Cada domínio abaixo é descrito por: responsabilidade, tabela(s) de banco, módulo(s) de lógica, blueprint(s) HTTP
e página(s) de frontend. Um domínio sem serviço/repositório separado hoje está registrado como está — ver seção 3.

### 1.1 Autenticação

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Login, logout, sessão |
| Tabela(s) | `usuarios` (senha com hash Werkzeug) |
| Lógica | Embutida em `irflow_blueprints_auth.py` (rotas legadas) e em `irflow_blueprints_api.py` (`/api/auth/*`) — duas implementações paralelas, ver `ARCHITECTURE.md` seção 3 |
| HTTP | `irflow_blueprints_auth.py` (form `/login`, `/logout`); `/api/auth/*` dentro de `irflow_blueprints_api.py` |
| Frontend | `AuthContext.jsx`, `pages/Login.jsx` |
| Observação | Nenhuma camada de serviço isolada — lógica de autenticação vive direto no blueprint em ambas as superfícies (legada e API) |

### 1.2 Usuários

| Aspecto | Hoje |
|---|---|
| Responsabilidade | CRUD de usuários do sistema, perfis (`admin`, `tecnico`, `vendedor`) |
| Tabela(s) | `usuarios` |
| Lógica | Embutida em `irflow_blueprints_auth.py` (views legadas) e `irflow_blueprints_api.py` (`/api/usuarios`) |
| HTTP | Ambas as superfícies, sem serviço compartilhado |
| Frontend | Tela de administração de usuários (dentro do fluxo admin) |
| Observação | Perfis são checados por lista explícita em `ROUTE_PERMISSIONS` (`app.py`) — não há hierarquia nem permissão por tela (ver `PRODUCT_REQUIREMENTS.md` para a ambição de permissão granular) |

### 1.3 Ordens de Serviço (OS)

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Ciclo de vida completo de uma ordem de serviço: abertura, status, peças, reparos, finalização |
| Tabela(s) | `os`, `os_pecas`, `os_reparos`, `os_checklists`, `reparos` |
| Lógica | `irflow_os.py` — consumo/devolução de peças, FIFO de lotes, validação de reparos |
| HTTP | `irflow_blueprints_orders.py` (views legadas `/ordens*`); `/api/ordens/*` em `irflow_blueprints_api.py` |
| Frontend | `pages/NewOrder.jsx`, `pages/EditOrder.jsx`, `pages/Orders.jsx` |
| Observação | **`cliente` não é uma entidade própria** — é uma coluna `TEXT` solta na tabela `os` (`app.py`, `CREATE TABLE os`). Não há tabela `clientes`, não há histórico relacional além dos registros de OS com o mesmo texto em `cliente`. Isso é o ponto de partida real para qualquer futuro domínio de CRM |

### 1.4 Estoque

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Cadastro de peças/itens, controle de quantidade, custo médio, lotes |
| Tabela(s) | `estoque`, `estoque_lotes`, `movimentacoes` |
| Lógica | CRUD e consulta em `irflow_blueprints_api.py` (`criar_estoque`, `atualizar_estoque`, `listar_estoque`); **movimentação/consumo já vive separada em `irflow_os.py`** (`registrar_movimentacao`, `consumir_peca_da_os`, `_consumir_lotes_fifo`, `devolver_pecas_da_os`) |
| HTTP | `irflow_blueprints_inventory.py` (views legadas `/estoque*`); `/api/estoque/*` em `irflow_blueprints_api.py` |
| Frontend | Páginas de estoque (dentro do fluxo principal) |
| Observação | Este é o domínio mais próximo de já ter uma "camada de serviço": a lógica de movimentação em `irflow_os.py` é reutilizável e já tem 69 testes cobrindo-a (Sprint 2.5 — `test_stock_movement.py`, `test_stock_os_integration.py`). É o candidato natural a virar `estoque_service.py` formal quando um novo domínio (ex.: Vendas) precisar consumir a mesma lógica |

### 1.5 Compras / Lista de Compras (Shopping List)

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Rastrear necessidade de reposição de peças, workflow de status |
| Tabela(s) | `shopping_list`, `shopping_list_logs` |
| Tabela legada morta | `compras` — criada em `app.py`, mas sem rota ativa apontando para ela (ver KI-012, KI-014); candidata a remoção formal na Sprint 4 |
| Lógica | Embutida em `irflow_blueprints_api.py` |
| HTTP | `/api/shopping-list/*` |
| Frontend | `pages/Compras.jsx`, `EditShoppingItemModal.jsx`, `ShoppingModal.jsx` |

### 1.6 Tabela de Preços

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Preço sugerido por modelo + reparo |
| Tabela(s) | Sem tabela SQL dedicada — estrutura normalizada em memória/config via `irflow_price_tables.py` (`tabelas_preco_vazias`, `_normalizar_tabela_preco`) |
| Lógica | `irflow_price_tables.py` |
| HTTP | `GET /api/precos/sugerir` em `irflow_blueprints_api.py` |
| Frontend | Consumido via `useEffect` em `NewOrder.jsx`/`EditOrder.jsx` para auto-preencher `valor_cobrado` |

### 1.7 Dados de Referência

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Listas de apoio: modelos, cores, técnicos, vendedores |
| Lógica | `irflow_reference_data.py` |
| HTTP | Endpoints de listagem simples em `irflow_blueprints_api.py` |

### 1.8 Relatórios

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Agregações e exportação em PDF (IR Phones, Técnicos) |
| Lógica | `irflow_reports.py` |
| HTTP | `irflow_blueprints_main.py` (views legadas `/relatorios`); rotas de PDF em `irflow_blueprints_api.py` |
| Frontend | Tela de relatórios |

### 1.9 Backup / Persistência

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Backup local, e-mail, Google Drive |
| Lógica | `irflow_storage.py` |
| Observação | Falhas de envio apenas logadas, sem alerta visível (KI-006) |

### 1.10 Integrações — MercadoPhone

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Importação de OS e sincronização com sistema externo MercadoPhone |
| Tabela(s) | `integracao_sync_estado`, `integracao_os_vistas` |
| Lógica | `irflow_mercadophone.py` (~1200 linhas) |
| HTTP | Rotas de webhook com autenticação própria por token, fora de `ROUTE_PERMISSIONS` (ver R-07) |

### 1.11 Núcleo Compartilhado

| Aspecto | Hoje |
|---|---|
| Responsabilidade | Constantes de status de OS, normalização de texto, cálculo de faturamento/lucro |
| Lógica | `irflow_core.py` |
| Observação | Único módulo com 78%+ de cobertura de testes hoje — ponto de referência de qualidade para os demais |

---

## 2. O que ainda não é um domínio isolado

- **Clientes** — não existe como entidade. É um campo texto solto em `os`. Qualquer domínio de CRM ou de Vendas
  que precise de histórico de cliente por identidade (não por string) precisa resolver isso primeiro — é
  pré-requisito estrutural, não detalhe de implementação.
- **Financeiro / Caixa** — não existe hoje. Custos operacionais (`custos_operacionais`) e valores de OS existem,
  mas não há conceito de caixa, sangria, suprimento ou fluxo de caixa consolidado.

---

## 3. Convenção para novos domínios

A partir de agora, todo domínio novo (ex.: Vendas) segue a convenção formalizada em
`docs/ENGINEERING_GUIDE.md` seção 3.1 — camadas `controller → service → repository → tests → README`,
mesmo que o domínio inicialmente viva no mesmo diretório dos módulos existentes.

Este mapa deve ser atualizado a cada novo domínio adicionado ou reestruturado — é o inventário vivo,
não um documento estático.

---

## Documentos relacionados

- `docs/ARCHITECTURE.md` — visão arquitetural completa (camadas, fluxos)
- `docs/DATABASE.md` — schema completo
- ADR-002 — decomposição da API por domínio (camada HTTP)
- ADR-005 — estratégia de multiempresa (afeta todos os domínios listados acima)
- `docs/ENGINEERING_GUIDE.md` seção 3.1 — convenção de camadas para domínio novo
