# SPRINT 00 — MVP em Produção

**Status:** CONCLUÍDA  
**Período:** Início do projeto – Maio/2026  
**Tipo:** Fundação

---

## Objetivo

Colocar o sistema funcional em produção com as operações essenciais de uma assistência técnica.

## Motivação

Substituir planilhas e processos manuais. O time precisava de uma ferramenta operacional imediatamente.
O foco foi na entrega rápida das funcionalidades core, com dívida técnica aceita conscientemente.

---

## Arquivos Envolvidos

| Arquivo | Papel |
|---------|-------|
| `app.py` | Inicialização, schema DB, blueprints |
| `irflow_blueprints_api.py` | Todos os endpoints REST |
| `irflow_os.py` | Lógica de negócio de OS |
| `irflow_blueprints_auth.py` | Autenticação |
| `irflow_storage.py` | Backup automático |
| `irflow_reports.py` | Relatórios e PDF |
| `irflow_mercadophone.py` | Integração MercadoPhone |
| `frontend/src/App.jsx` | Roteamento e guards |
| `frontend/src/pages/` | Login, Dashboard, Orders, NewOrder, EditOrder, Stock |
| `Dockerfile`, `fly.toml` | Infraestrutura de deploy |

---

## Entregas

| Feature | Status |
|---------|--------|
| Login e controle de sessão | Entregue |
| CRUD completo de Ordens de Serviço | Entregue |
| Controle de estoque com movimentações | Entregue |
| Tabela de preços por modelo/reparo | Entregue |
| Kanban board | Entregue |
| Checklist público de dispositivo (token) | Entregue |
| Garantias | Entregue |
| Relatórios (IR Phones, Técnicos, Custos) | Entregue |
| Exportação PDF | Entregue |
| Backup manual e automático | Entregue |
| Google Drive para backup | Entregue |
| Gestão de usuários (admin) | Entregue |
| Deploy Fly.io | Entregue |
| Integração MercadoPhone | Entregue |

---

## Critérios de Aceitação

- [x] Sistema acessível em produção via URL pública
- [x] Todas as rotas retornam respostas esperadas nos smoke tests
- [x] Operação real de OS funcionando end-to-end
- [x] Backup automático ativo

---

## Testes na Entrega

| Tipo | Ferramenta | Status |
|------|-----------|--------|
| Smoke tests de rotas | `smoke_test_full.py` | Executado manualmente |
| E2E básico | Playwright | Configurado, 4 testes |
| Testes unitários backend | — | Ausentes |
| Isolamento de testes | — | Ausente |

---

## Dívida Técnica Gerada

| ID | Dívida |
|----|--------|
| TD-01 | `irflow_blueprints_api.py` com ~130KB monolítico |
| TD-02 | `app.py` mistura inicialização, DB e lógica |
| TD-03 | Migrations via `ALTER TABLE` com `try/except` sem versionamento |
| TD-04 | Testes ad-hoc que tocam banco real |
| TD-05 | Sem CI/CD |
| TD-06 | Sem `.env.example` |
| TD-07 | Commits sem padrão |

---

## Riscos Aceitos

- SQLite em produção sem replicação (mitigado por backup automático)
- Sem rate limiting em autenticação
- Tokens de checklist sem expiração

---

## Definition of Done — Verificação

- [x] Sistema em produção no Fly.io
- [x] Fluxo de OS funcionando para o time operacional
- [x] Backup ativo e verificado
- [ ] Testes automatizados — **não atingido, aceito como dívida**
- [ ] CI/CD — **não atingido, aceito como dívida**
