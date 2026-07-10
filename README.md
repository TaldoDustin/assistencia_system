# Fluxoly

Plataforma de gestão para lojas especializadas em dispositivos móveis premium — vendas, estoque, tabela
de preços, lista de compras, assistência técnica, garantias, relatórios e backup em um único fluxo.
Nome legado no repositório e infraestrutura: Assistência System (ver `docs/company/BRAND_IDENTITY.md`
seção 9 para o cronograma de transição de marca).

**Produção:** [assistencia-system.fly.dev](https://assistencia-system.fly.dev)

---

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Backend | Python 3.11 · Flask 3 · SQLite (WAL) |
| Frontend | React 19 · Vite · Radix UI · Tailwind CSS |
| Deploy | Fly.io |
| Testes | pytest · Playwright |

---

## Execução Local

### Pré-requisitos

- Python 3.11+
- Node.js 20+

### Backend

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar variáveis de ambiente
cp .env.example .env
# Edite .env com suas configurações locais

# 3. Iniciar servidor
python app.py
# Backend disponível em http://localhost:5080
```

### Frontend

```bash
cd frontend

# 1. Instalar dependências
npm install

# 2. Iniciar dev server
npm run dev
# Frontend disponível em http://localhost:5173
```

### Em produção (via Fly.io)

O frontend é compilado e servido pelo próprio Flask:

```bash
cd frontend && npm run build   # gera frontend/dist/
python app.py                  # serve o dist/ + API em uma porta
```

---

## Testes

```bash
# Backend (pytest)
pip install -r requirements-dev.txt
pytest tests/ --cov

# Frontend (lint)
cd frontend && npm run lint

# E2E (Playwright)
cd frontend && npm run test:e2e
```

---

## Documentação

A documentação completa está em [`docs/`](docs/README.md).

| Documento | Descrição |
|-----------|-----------|
| [`docs/README.md`](docs/README.md) | Índice de toda a documentação |
| [`CLAUDE.md`](CLAUDE.md) | Manual operacional para IA |
| [`docs/company/BRAND_IDENTITY.md`](docs/company/BRAND_IDENTITY.md) | Identidade de marca Fluxoly |
| [`docs/engineering/ENGINEERING_GUIDE.md`](docs/engineering/ENGINEERING_GUIDE.md) | Padrões técnicos e convenções |
| [`docs/engineering/ARCHITECTURE.md`](docs/engineering/ARCHITECTURE.md) | Arquitetura do sistema |
| [`docs/operations/ROADMAP.md`](docs/operations/ROADMAP.md) | Evolução planejada |
| [`docs/engineering/CONTRIBUTING.md`](docs/engineering/CONTRIBUTING.md) | Como contribuir |

---

## Contribuindo

Leia [`docs/engineering/CONTRIBUTING.md`](docs/engineering/CONTRIBUTING.md) antes de abrir um PR.

Resumo rápido:
1. Crie uma branch: `git checkout -b feat/nome-da-feature`
2. Instale dependências de dev: `pip install -r requirements-dev.txt`
3. Escreva testes para sua mudança
4. Garanta que CI local passa: `pytest tests/ && ruff check . && cd frontend && npm run lint`
5. Use Conventional Commits: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`
6. Abra o PR com descrição clara

---

## Licença

Uso interno. Todos os direitos reservados.
