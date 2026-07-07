# CHANGELOG

Todas as mudanças notáveis neste projeto serão documentadas aqui.

Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/).
Versionamento segue [Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Não lançado]

### Adicionado
- `docs/ARCHITECTURE.md` e `docs/DATABASE.md` — documentação obrigatória ausente, extraída do estado real do código
- `tests/test_auth.py` — primeira suíte pytest do projeto (Sprint 2.2): login, logout, sessão e controle de acesso por perfil, isolada via `IR_FLOW_DATA_DIR`
- `tests/test_users.py` — cobertura de CRUD de usuários via `/api/usuarios` (Sprint 2.3): listar, criar, editar, excluir; duplicado, campos obrigatórios, perfil desconhecido, auto-desativação/auto-exclusão bloqueadas
- `tests/test_permissions.py` — matriz de acesso por perfil (admin/tecnico/vendedor) em rotas admin-only legadas e API, cobrindo 200/401/403/404 (Sprint 2.3)
- `tests/test_session.py` — cobertura de sessão: expiração (cookie forjado), cookie adulterado/não assinado, logout múltiplo, acesso após logout (Sprint 2.3)
- `tests/test_security.py` — cobertura de resiliência de entrada em `/api/auth/login`: SQL injection, campos obrigatórios, payload vazio, JSON malformado, Content-Type incorreto (Sprint 2.3)

### Corrigido
- Removido endpoint duplicado `GET/POST/PUT/DELETE /api/shopping-list` legado (baseado na tabela `compras`) em `irflow_blueprints_api.py` — colidia com a implementação atual (tabela `shopping_list`) e causava `AssertionError` do Flask na inicialização, impedindo a aplicação e a suíte de testes de rodar (KI-012)

### Em progresso
- Infraestrutura de CI/CD com GitHub Actions
- Testes backend com pytest e banco in-memory
- Configuração de Ruff para lint do backend
- Documentação de engenharia de nível profissional

---

## [1.1.0] — 2026-06-21

### Adicionado
- Módulo de lista de compras (`shopping_list`): tabela no banco, API REST completa com workflow de status (PENDENTE → EM_COTACAO → EM_COMPRA → COMPRADO → RECEBIDO)
- Endpoint `GET /api/precos/sugerir`: retorna preço total sugerido com base em modelo + reparos selecionados
- Página `Compras.jsx` no frontend com listagem e gestão da lista de compras
- `EditShoppingItemModal`: modal de edição de itens da lista de compras
- `ShoppingModal`: modal de adição de novos itens
- Client dedicado `shoppingList` em `frontend/src/api/client.js`
- Logs de atividade por item de shopping list com exportação

### Corrigido
- `valor_cobrado` agora é auto-preenchido ao selecionar modelo + reparo em nova OS
- `valor_cobrado` não sobrescreve valor existente ao abrir OS para edição (flag `initialized.current`)
- URL do endpoint de PDF IR Phones corrigida (`/irphones` → `/ir-phones`)
- Rota `historico-cliente` apontava para endpoint inexistente em `client.js`
- Campo `cor` agora é limpo ao trocar modelo em `EditOrder.jsx`
- Pipeline de build/dist do frontend corrigido

### Segurança
- Arquivo `.env` removido do repositório (credenciais não mais expostas no histórico git)

---

## [1.0.0] — 2026-05-01

### Adicionado
- Sistema completo de gestão de Ordens de Serviço (OS): criação, edição, exclusão, histórico
- Controle de estoque com movimentações por lotes e SKU
- Tabela de preços por modelo e tipo de reparo
- Kanban board para visualização de OS por status
- Checklist público de dispositivo com token (sem autenticação)
- Rastreamento de garantias com contagem de dias restantes
- Relatórios: IR Phones, Técnicos, Custos Operacionais
- Exportação de relatórios em PDF
- Backup manual e automático com notificação por e-mail
- Integração Google Drive para armazenamento de backups
- Integração MercadoPhone para importação de OS externas
- Gestão de usuários com perfis: admin, vendedor, técnico
- Autenticação via sessão com hash de senha (Werkzeug)
- Deploy em Fly.io com Dockerfile e configuração de produção
- Suporte a build para executável Windows (PyInstaller + InnoSetup)
- CORS configurado para deploy separado frontend/backend

---

## Guia de Versões

| Versão | Sprint | Status |
|--------|--------|--------|
| 1.2.0 (futura) | Sprint 2 | Infraestrutura de qualidade |
| 1.3.0 (futura) | Sprint 3 | Segurança e observabilidade |
| 2.0.0 (futura) | Sprint 4-5 | Refatoração arquitetural |
| 1.1.0 | Sprint 1 | Lançado |
| 1.0.0 | Sprint 0 | Lançado |

---

*Para mudanças em andamento, consulte [`docs/SPRINTS/`](SPRINTS/) e [`docs/PROJECT_STATUS.md`](PROJECT_STATUS.md).*
