# SECURITY.md — Política de Segurança

Este documento define a política de segurança do Fluxoly Platform, com um checklist baseado no OWASP Top 10 adaptado à stack do projeto (Flask + SQLite + React).

**Última revisão:** 2026-07-25  
**Próxima auditoria:** Sprint Segurança 1.0 (proposta, não iniciada) — ver
`docs/security/SECURITY_AUDIT_2026-07.md` para a auditoria mais recente (scan Aikido, triagem completa
de P0/P1, cada item validado no código antes de classificar)

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
| Rate limiting em `/api/auth/login` | ✅ | KI-001 resolvido — 5 tentativas/minuto por identificador (`irflow_rate_limit.py`, tabela `login_attempts`, contador em SQLite em vez de memória — ver nota abaixo) |
| Bloqueio após tentativas excessivas | ✅ | Mesma implementação acima — 429 na 6ª tentativa dentro da janela |
| Timeout de sessão por inatividade | ✅ | Janela deslizante de 30 min (`IR_FLOW_SESSION_INACTIVITY_MINUTES`), `irflow_core.py::sessao_ainda_ativa` aplicada em `verificar_autenticacao()` — cobre `/api/*` e views legadas no mesmo ponto (ver nota abaixo) |

**Nota de implementação (rate limiting):** o Gunicorn de produção roda com `--workers 2` (`Dockerfile`) — um
contador em memória de processo (Flask-Limiter default) seria por worker, enfraquecendo o limite nominal
para ~10/min efetivos e permitindo contorno parcial via roteamento entre workers. Por isso o contador vive
em SQLite (`login_attempts`), já compartilhado entre os workers via WAL — limite realmente global, sem
dependência nova. O identificador do cliente é resolvido via `Fly-Client-IP` (header injetado quando
rodando atrás do proxy da Fly.io — não é o caso da produção atual, Render), com fallback para
`X-Forwarded-For` (o header que o proxy do Render de fato envia) e por fim `request.remote_addr` —
nenhum desses headers era lido antes desta mudança.

**Nota de implementação (timeout de inatividade):** existiam duas checagens de sessão paralelas antes
desta mudança — `verificar_autenticacao()` (`app.py`, `before_request` global, cobre views legadas) e
`usuario_logado()` (`irflow_blueprints_api.py`, chamada por toda rota `/api/*`). Como
`verificar_autenticacao()` dispara para **toda** requisição (inclusive `/api/*`) antes do bypass que a
função já tinha para endpoints `api.*`, a checagem de inatividade foi colocada logo antes desse bypass —
um único ponto cobre as duas superfícies sem duplicar a regra: ao expirar, `session.clear()` já limpa
`usuario_id` antes de `usuario_logado()` ser avaliado na view real. Sessões sem marca de atividade (por
exemplo, criadas antes desta mudança existir) não expiram na primeira requisição — evita derrubar sessões
em andamento no momento do deploy.

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
| Queries usam parâmetros `?` (nunca f-strings ou concatenação) | ✅ | Auditado 2026-07-25 — ver `docs/security/SECURITY_AUDIT_2026-07.md` |
| Nenhum input do usuário é interpolado diretamente em SQL | ✅ | Todas as 11 ocorrências de f-string em `.execute()` do backend inteiro (incluindo `irflow_blueprints_api.py`) verificadas linha a linha — só fragmentos fixos/whitelists são interpolados, valores do usuário sempre via `?` |

**Regra obrigatória:**
```python
# PROIBIDO
cursor.execute(f"SELECT * FROM os WHERE cliente = '{nome}'")

# OBRIGATÓRIO
cursor.execute("SELECT * FROM os WHERE cliente = ?", (nome,))
```

**Auditoria concluída em 2026-07-25** (disparada por scan Aikido do usuário/CTO), fechando esta ação
pendente desde 2026-07-06 — ver `docs/security/SECURITY_AUDIT_2026-07.md` para o detalhamento completo,
item a item, com o padrão seguro já em uso documentado.

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
| `SameSite=None; Secure` apenas quando necessário (deploy separado) | ⚠️ | Verificar se ainda necessário — produção atual já é deploy separado (Render + Vercel) |
| CSRF token em formulários críticos | N/A | API REST com JSON — CSRF via SameSite |

---

### 6. Configuração de Segurança HTTP

| Item | Status | Observação |
|------|--------|-----------|
| `X-Content-Type-Options: nosniff` | ❌ | Header ausente — confirmado de novo em 2026-07-25 (scan Aikido) |
| `X-Frame-Options: DENY` | ❌ | Header ausente — mesma confirmação |
| `Referrer-Policy: strict-origin-when-cross-origin` | ❌ | Header ausente |
| `Content-Security-Policy` | ❌ | Header ausente |
| CORS restrito a origens conhecidas (`IR_FLOW_CORS_ORIGINS`) | ✅ | Configurado via variável de ambiente |
| CORS nunca `*` em produção | ✅ | Documentado no ENGINEERING_GUIDE |

**Ação:** Adicionar headers de segurança via middleware Flask em `app.py` — item P1 confirmado em
`docs/security/SECURITY_AUDIT_2026-07.md`, candidato à Sprint Segurança 1.0.

---

### 7. Tokens e Links Públicos

| Item | Status | Observação |
|------|--------|-----------|
| Tokens de checklist são UUIDs aleatórios | ✅ | Não sequenciais, não previsíveis |
| Tokens de checklist expiram | ❌ | **KI-002 — sprint 3** |
| Tokens revogados ao fechar OS | ❌ | Não implementado |
| Checklist público não expõe dados sensíveis além do necessário | ⚠️ | Verificar campos retornados no endpoint |
| Token de reset de senha é aleatório e de uso único | ✅ | `secrets.token_urlsafe(24)`, mesma técnica de `gerar_token_checklist_os`; `usado_em` marca consumo |
| Token de reset de senha expira | ✅ | 24h por padrão (`IR_FLOW_PASSWORD_RESET_TOKEN_HOURS`) — curto porque é entregue manualmente pelo admin, não por e-mail com prazo longo |
| Gerar novo token invalida o anterior | ✅ | No máximo um token válido por usuário simultaneamente |
| Reset de senha é self-service por e-mail | N/A | Decisão explícita: não é — token gerado e entregue manualmente pelo admin, sem infraestrutura de e-mail transacional nova |

---

### 8. Gestão de Segredos

| Item | Status | Observação |
|------|--------|-----------|
| Credenciais removidas do repositório | ⚠️ | Commit `832945c` remove o arquivo do working tree, mas **o valor de `FLASK_SECRET_KEY` continua no histórico do Git** (3 commits, `eefcfd2`→`252815a`) — confirmado 2026-07-25, ver `docs/security/SECURITY_AUDIT_2026-07.md` item 2. Ação: rotacionar a chave em produção |
| `.env` no `.gitignore` | ✅ | Verificar |
| `.env.example` documenta todas as variáveis sem valores reais | ✅ | Criado em 2026-07-11 (T-10, fechado junto da Unidade 8 da Sprint 3) — 26 variáveis documentadas, nenhum valor real |
| `FLASK_SECRET_KEY` forte em produção | ❌ | **Escalado de `⚠️` para `❌` em 2026-07-25**: `app.py:229` usa `os.environ.get("FLASK_SECRET_KEY", "ir-flow-dev-key")` — fallback hardcoded e público se a variável não estiver setada, sem nenhum aviso no boot. Confirmar imediatamente se está configurada em produção (Render); correção de código recomendada: falhar no boot em vez de usar o fallback fora de dev local. Ver `docs/security/SECURITY_AUDIT_2026-07.md` item 3 |
| Tokens de integração (MercadoPhone) via variável de ambiente | ✅ | `MERCADO_PHONE_API_TOKEN` |
| Nenhum segredo em logs ou respostas de erro | ⚠️ | A verificar |

---

### 9. Rate Limiting e DoS

| Item | Status | Observação |
|------|--------|-----------|
| Rate limiting em rotas de autenticação | ✅ | KI-001 resolvido — ver seção 1 |
| Rate limiting em rotas públicas (checklist) | ❌ | Ausente |
| Proteção contra upload de arquivos excessivamente grandes | N/A | Sem upload de arquivos no fluxo principal |
| Paginação em listagens (proteção contra dump) | ❌ | **KI-005 — sprint 5** |

---

### 10. Logging e Auditoria

| Item | Status | Observação |
|------|--------|-----------|
| Logs de operações críticas (criação/edição/deleção de OS) | ❌ | Auditoria central (`audit_log`, ver abaixo) existe mas OS ainda não foi migrada para chamá-la — fora de escopo da Sprint 3 (mudaria domínio existente, não é feature nova) |
| Logs de tentativas de login falhas | ✅ | Tabela `login_attempts` (KI-001) grava toda tentativa (sucesso e falha) — não é logging estruturado em JSON, mas cobre a auditabilidade |
| Logs sem exposição de dados sensíveis | N/A | Sem logs de aplicação estruturados hoje |
| Logs consultáveis em produção | ❌ | Render tem logs básicos mas não estruturados |
| Auditoria central reutilizável entre domínios | ✅ | `audit_log` (`irflow_audit.py::registrar_log_auditoria`) — tabela genérica (entidade/entidade_id/ação/antes/depois), consumida pela primeira vez pelos domínios Clientes e `unidades_serializadas` (Sprint P0.1; evoluído de `estoque_unidades` na migração ADR-007) |

**Ação Sprint 3:** Implementar logging estruturado em JSON para operações críticas — auditoria em banco
(`audit_log`) resolvida; logging estruturado em arquivo/stdout para observabilidade (Sentry etc.) segue
pendente.

---

### 11. Dependências

| Item | Status | Observação |
|------|--------|-----------|
| Dependências de produção atualizadas | ❌ | Scan Aikido 2026-07-25 confirmou: `gunicorn` preso em `>=21,<22` (nunca pega a correção de CVE-2024-1135, contrabando de requisição HTTP — instalado 21.2.0); `react-router-dom`, `immer`, DOMPurify (transitiva) também flagados — ver `docs/security/SECURITY_AUDIT_2026-07.md` |
| Auditoria de vulnerabilidades conhecidas | ⚠️ | Ainda sem `safety check`/`npm audit` automatizado no CI, mas auditoria manual pontual feita via Aikido em 2026-07-25 |
| Sem dependências não utilizadas | ⚠️ | Verificar manualmente |

**Ação:** Adicionar `safety check` e `npm audit` ao pipeline de CI (pendente desde Sprint 2). Curto
prazo: atualizar `gunicorn` para `>=22` e rodar `npm update` nas dependências flagadas — candidatos à
Sprint Segurança 1.0.

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
