# SECURITY.md — Política de Segurança

Este documento define a política de segurança do Assistência System, com um checklist baseado no OWASP Top 10 adaptado à stack do projeto (Flask + SQLite + React).

**Última revisão:** 2026-07-06  
**Próxima auditoria:** Início da Sprint 3

---

## Checklist de Segurança

### Legenda
- ✅ Implementado e validado
- ⚠️ Parcialmente implementado ou não auditado formalmente
- ❌ Ausente — issue aberto
- N/A Não aplicável a este projeto

---

### 1. Autenticação

| Item | Status | Observação |
|------|--------|-----------|
| Senhas armazenadas com hash seguro (Werkzeug) | ✅ | `generate_password_hash` / `check_password_hash` |
| Salt único por senha | ✅ | Werkzeug gera automaticamente |
| `FLASK_SECRET_KEY` forte e única por ambiente | ⚠️ | Default inseguro em dev — documentado no `.env.example` |
| Sessão invalidada completamente no logout | ⚠️ | `session.clear()` — validar que não há cookie residual |
| Rate limiting em `/api/auth/login` | ❌ | **KI-001 — sprint 3** |
| Bloqueio após tentativas excessivas | ❌ | Dependente do rate limiting |
| Timeout de sessão por inatividade | ❌ | Não configurado |

---

### 2. Autorização (Controle de Acesso)

| Item | Status | Observação |
|------|--------|-----------|
| Toda rota protegida verifica `session.get("usuario_id")` | ⚠️ | Verificar cobertura total das rotas |
| Rotas admin verificam `perfil == "admin"` | ⚠️ | Verificar cobertura |
| Usuário só acessa seus próprios dados quando aplicável | ⚠️ | Modelo multi-usuário sem isolamento por conta |
| Endpoints de escrita exigem autenticação | ⚠️ | Smoke test cobre apenas GET |

**Ação Sprint 3:** Auditoria de todas as rotas — verificar que 100% exigem autenticação e que as admin-only exigem perfil.

---

### 3. Injeção (SQL Injection)

| Item | Status | Observação |
|------|--------|-----------|
| Queries usam parâmetros `?` (nunca f-strings ou concatenação) | ⚠️ | Padrão seguido nos módulos recentes — auditoria do legado pendente |
| Nenhum input do usuário é interpolado diretamente em SQL | ⚠️ | A auditar em `irflow_blueprints_api.py` (130KB) |

**Regra obrigatória:**
```python
# PROIBIDO
cursor.execute(f"SELECT * FROM os WHERE cliente = '{nome}'")

# OBRIGATÓRIO
cursor.execute("SELECT * FROM os WHERE cliente = ?", (nome,))
```

**Ação Sprint 3:** Grep em todo o backend por f-strings em `cursor.execute`.

---

### 4. Cross-Site Scripting (XSS)

| Item | Status | Observação |
|------|--------|-----------|
| React escapa conteúdo por padrão | ✅ | JSX não renderiza HTML raw |
| `dangerouslySetInnerHTML` não utilizado | ⚠️ | Verificar no frontend |
| Inputs de texto não executam scripts | ✅ | React previne por design |
| PDF gerado via jsPDF sem HTML injection | ⚠️ | Validar inputs em campos que alimentam PDF |

---

### 5. CSRF (Cross-Site Request Forgery)

| Item | Status | Observação |
|------|--------|-----------|
| Sessões com `SameSite=Lax` ou `Strict` (deploy unificado) | ⚠️ | Verificar configuração de cookie |
| `SameSite=None; Secure` apenas quando necessário (deploy separado) | ⚠️ | Verificar se ainda necessário no Fly.io |
| CSRF token em formulários críticos | N/A | API REST com JSON — CSRF via SameSite |

---

### 6. Configuração de Segurança HTTP

| Item | Status | Observação |
|------|--------|-----------|
| `X-Content-Type-Options: nosniff` | ❌ | Header ausente |
| `X-Frame-Options: DENY` | ❌ | Header ausente |
| `Referrer-Policy: strict-origin-when-cross-origin` | ❌ | Header ausente |
| `Content-Security-Policy` | ❌ | Header ausente |
| CORS restrito a origens conhecidas (`IR_FLOW_CORS_ORIGINS`) | ✅ | Configurado via variável de ambiente |
| CORS nunca `*` em produção | ✅ | Documentado no ENGINEERING_GUIDE |

**Ação Sprint 3:** Adicionar headers de segurança via middleware Flask em `app.py`.

---

### 7. Tokens e Links Públicos

| Item | Status | Observação |
|------|--------|-----------|
| Tokens de checklist são UUIDs aleatórios | ✅ | Não sequenciais, não previsíveis |
| Tokens de checklist expiram | ❌ | **KI-002 — sprint 3** |
| Tokens revogados ao fechar OS | ❌ | Não implementado |
| Checklist público não expõe dados sensíveis além do necessário | ⚠️ | Verificar campos retornados no endpoint |

---

### 8. Gestão de Segredos

| Item | Status | Observação |
|------|--------|-----------|
| Credenciais removidas do repositório | ✅ | Commit `832945c` |
| `.env` no `.gitignore` | ✅ | Verificar |
| `.env.example` documenta todas as variáveis sem valores reais | ❌ | **Sprint 2 — T-10** |
| `FLASK_SECRET_KEY` forte em produção | ⚠️ | Responsabilidade do operador — documentar |
| Tokens de integração (MercadoPhone) via variável de ambiente | ✅ | `MERCADO_PHONE_API_TOKEN` |
| Nenhum segredo em logs ou respostas de erro | ⚠️ | A verificar |

---

### 9. Rate Limiting e DoS

| Item | Status | Observação |
|------|--------|-----------|
| Rate limiting em rotas de autenticação | ❌ | **KI-001 — sprint 3** |
| Rate limiting em rotas públicas (checklist) | ❌ | Ausente |
| Proteção contra upload de arquivos excessivamente grandes | N/A | Sem upload de arquivos no fluxo principal |
| Paginação em listagens (proteção contra dump) | ❌ | **KI-005 — sprint 5** |

---

### 10. Logging e Auditoria

| Item | Status | Observação |
|------|--------|-----------|
| Logs de operações críticas (criação/edição/deleção de OS) | ❌ | Não implementado |
| Logs de tentativas de login falhas | ❌ | Não implementado |
| Logs sem exposição de dados sensíveis | N/A | Sem logs hoje |
| Logs consultáveis em produção | ❌ | Fly.io tem logs básicos mas não estruturados |

**Ação Sprint 3:** Implementar logging estruturado em JSON para operações críticas.

---

### 11. Dependências

| Item | Status | Observação |
|------|--------|-----------|
| Dependências de produção atualizadas | ⚠️ | Sem processo automatizado de verificação |
| Auditoria de vulnerabilidades conhecidas | ❌ | Sem `safety check` ou `npm audit` no CI |
| Sem dependências não utilizadas | ⚠️ | Verificar manualmente |

**Ação Sprint 2:** Adicionar `safety check` e `npm audit` ao pipeline de CI.

---

## Resumo por Sprint

| Sprint | Itens de Segurança |
|--------|-------------------|
| Sprint 2 | `.env.example`, `safety check` no CI, `npm audit` no CI |
| Sprint 3 | Rate limiting, expiração de tokens, headers HTTP, logging de auditoria, CSRF audit |
| Sprint 4+ | Paginação (proteção dump), revisão completa de autorização |

---

## Reportando Vulnerabilidades

Se você identificou uma vulnerabilidade de segurança:

1. **Não abra um issue público.**
2. Documente em `KNOWN_ISSUES.md` com status "Confidencial" se estiver trabalhando internamente.
3. Corrija antes do próximo deploy em produção se a severidade for Alta ou Crítica.
4. Adicione ao `CHANGELOG.md` na seção `Security` após a correção.
