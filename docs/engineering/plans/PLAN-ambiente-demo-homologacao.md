# PLAN-ambiente-demo-homologacao — Ambiente de Demonstração/Homologação

**Data:** 2026-08-11
**Feature:** `docs/engineering/adr/ADR-012.md` (arquitetura aprovada) + duas Discoveries somente-leitura de 2026-08-11 (Parte C da Release 1.0; Discovery dedicada do Ambiente de Demonstração). Não há BR-NNN novo — este plano implementa uma decisão arquitetural e operacional, não uma regra de negócio nova.
**Status:** Aprovado (CTO, 2026-08-11 — com 3 ajustes de escopo, ver "Decisões de Escopo Confirmadas" ao final)

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação — não é mantido atualizado como `ARCHITECTURE.md`
> ou `DATABASE.md`. Se algo aqui continuar relevante depois, promova para o documento vivo correspondente.

**Estado**

- [x] Discovery — aprovada (Discovery da Parte C + Discovery dedicada do Ambiente de Demo, 2026-08-11)
- [x] ADR — `ADR-012` aceita (2026-08-11): Render+Vercel dedicados, `IR_FLOW_ENVIRONMENT=demo`, KI-037 bloqueante, isolamento de credenciais por design
- [x] Plano Técnico — aprovado pelo CTO (2026-08-11), com 3 ajustes de escopo
- [x] Implementação — concluída (2026-08-12), branch `feat/ambiente-demo-homologacao`, commit `59597bd8`. Escopo exatamente igual ao aprovado: `fluxoly_config.py` (`IR_FLOW_ENVIRONMENT`/`IS_DEMO_ENVIRONMENT`/`integracao_externa_bloqueada_neste_ambiente()`), `api_mercadophone.py` (guard KI-037 nos 4 endpoints), `app.py` (log de boot + precedência do Sentry), `scripts/seed_demo.py`, `tests/test_ambiente_demo.py`, `tests/test_ki037_guard_integracoes.py`
- [x] Testes — CI 6/6 verde no Linux (commit `59597bd8`: Lint, Docker Build, Frontend Quality, Backend Tests, Frontend Build, Coverage Report). 20 testes novos, todos passando no CI. Suíte completa local: 764 passed / 5 failed — as 5 falhas (2 já existentes de Preview + `test_sentry_init.py` + 2 novas equivalentes de Demo) são limitação de ambiente Windows local (subprocess + `sentry_sdk`/`_overlapped`, `WinError 10106`), confirmada pré-existente via `git stash` antes desta mudança — não é regressão, e o CI Linux já confirma verde
- [x] QA Manual — concluída (2026-08-12) contra backend Flask real e descartável (`IR_FLOW_DATA_DIR` isolado, nunca `database.db`). Evidências: log `demo_background_jobs_desativados` e ausência de log de sync mesmo com token/sync herdados simulando o cenário INC-003; `sentry_inicializado environment=demo`; os 4 endpoints do KI-037 retornam 403 para `admin.demo`/`tecnico.demo`, `/config` confirmado sem persistir token (`integrations.json` com `api_token: ""`); `vendedor.demo` barrado por permissão antes do guard; `status_mercadophone` continua 200; regressão produção/dev confirmada (2º servidor descartável sem flags, endpoints voltam ao 400 "não configurado" de antes); as 3 contas de demo autenticam com os perfis corretos via `POST /api/auth/login` real; proteção contra segunda execução do seed testada 2x; reset/restore validado (backup `seed-inicial` → OS extra → restore → contagem revertida de 25 para 24); CORS explícito confirmado (origem do Demo permitida, origem `*.vercel.app` arbitrária rejeitada, sem fallback permissivo). Achado registrado como `KI-038` (conta `admin`/`irflow@2024` padrão, fora de escopo deste plano) — não bloqueia este gate
- [x] Revisão Arquitetural — 2026-08-12, 4 eixos do `ADR-010` (Etapa 6). **Coerência do domínio** ✅ (mudança
      puramente aditiva, nada foi revogado/descontinuado — não se aplica). **Autorização centralizada** ✅
      (`integracao_externa_bloqueada_neste_ambiente()` é o único ponto de verdade do guard; grep completo por
      `IS_PULL_REQUEST` em todo o repositório confirma só 3 pontos de uso reais — `fluxoly_config.py`
      (definição + `BACKGROUND_JOBS_ENABLED` + guard), `app.py` boot log, `app.py` Sentry — e os 3 têm o
      correspondente `IS_DEMO_ENVIRONMENT` aplicado, nenhum ficou de fora, nenhuma checagem duplicada
      inline). **Risco de vazamento de dado** ✅ (rastreados todos os call sites de
      `chamar_api_mercado_phone()`: só alcançável via `sincronizar_mercado_phone()`/
      `reprocessar_todas_os_mercado_phone()`/`reimportar_todas_os_mercado_phone()` — cobertos pelo guard
      novo via os 3 endpoints manuais e por `BACKGROUND_JOBS_ENABLED` via a thread de sync — e via o
      webhook `receber_os_mercado_phone`, já fail-secure por design quando `MERCADO_PHONE_WEBHOOK_TOKEN`
      não está configurado, KI-023). **Achado documentado (não é bug, não exige código novo):** o Runbook
      de Provisionamento não listava `MERCADO_PHONE_WEBHOOK_TOKEN` explicitamente — adicionado à tabela
      acima, documentando que a variável já fica fechada por padrão quando ausente, e que o Demo nunca deve
      configurá-la. **Consistência da máquina de estados** ✅ (Preview mantém precedência sobre Demo em
      toda a cadeia — provado por teste automatizado e por QA manual; comportamento de produção/dev
      confirmado idêntico ao anterior, sem regressão). **KI-038** considerado nesta revisão: comportamento
      pré-existente (não introduzido por este plano), fora do escopo aprovado, corretamente registrado
      como KI separado — não bloqueia este gate, mas é pendência real antes da homologação externa do
      Demo (acesso de alguém fora da equipe), conforme já registrado no próprio KI-038.
- [ ] Encerramento

---

## Objetivo

Implementar a arquitetura já aprovada em `ADR-012`: um ambiente Render+Vercel dedicado, identificado por `IR_FLOW_ENVIRONMENT=demo`, com o KI-037 corrigido antes de qualquer exposição externa, seed de dados 100% sintético, contas de demonstração fixas, e um mecanismo de reset — cobrindo os 14 critérios do Definition of Done do ADR-012.

---

## Escopo

1. Nova constante de ambiente `IR_FLOW_ENVIRONMENT`/`IS_DEMO_ENVIRONMENT` em `fluxoly_config.py`, coexistindo com `IS_PULL_REQUEST` (nenhum dos dois substitui o outro).
2. Guard de KI-037 nos 4 endpoints de escrita/ação de `api_mercadophone.py` (`sincronizar`, `reprocessar`, `reimportar`, e a gravação de configuração em `/config`), bloqueando em Preview **e** em Demo — cobre a integração inteira, não só os pontos que fazem a chamada externa.
3. Script de seed sintético (`scripts/seed_demo.py`) — clientes, aparelhos/unidades, OS, peças/estoque, vendas, caixa, e as 3 contas de demonstração.
4. Extensão do guard de background jobs (`BACKGROUND_JOBS_ENABLED`) e do `environment` do Sentry para reconhecer Demo, seguindo exatamente o padrão já usado para Preview.
5. Runbook de provisionamento Render/Vercel (documentação operacional, não código) com checklist de isolamento de credenciais.
6. Mecanismo de reset via backup/restore já existente (`api_backup.py`), usando o seed como "restore point" fixo.
7. Testes automatizados novos cobrindo os itens 1, 2 e 4 acima.
8. Levantamento (sem decisão) das opções de camada de acesso adicional, para o CTO decidir — item deliberadamente deferido pelo `ADR-012`.

---

## Fora de Escopo

- Escolher/implementar a camada de acesso adicional (Basic Auth, allowlist de IP, token de convite) — só a análise de opções entra aqui; a escolha é do CTO, fora deste plano.
- Provisionar de fato o serviço Render/Vercel — o runbook é escrito aqui, executado na etapa de Implementação.
- Domínio próprio (branding) — `ADR-012` já fixou subdomínio padrão Vercel/Render para esta primeira versão.
- Automação de reset (Render Cron) — `ADR-012` já fixou reset manual sob demanda para esta primeira versão.
- Qualquer mudança em produção ou preview — este plano só adiciona comportamento condicional a um terceiro estado de ambiente; `IS_PULL_REQUEST`/produção continuam com o comportamento de hoje, coberto por teste de regressão.
- Projeto Sentry dedicado para o Demo — decidido reaproveitar o projeto atual com `environment=demo` (ver "Decisões de Escopo Confirmadas").

---

## Impacto no Banco

Nenhuma tabela ou coluna nova, nenhuma migration nova. O seed sintético (item 3) escreve nas tabelas de negócio já existentes (`clientes`, `os`, `os_reparos`, `os_pecas`, `estoque`, `unidades_serializadas`, `produtos`, `vendas`, `vendas_itens`, `movimentacoes_caixa`, `usuarios`) usando o schema atual, sem alterá-lo — roda depois que `migrations/runner.py` já aplicou o schema normalmente no primeiro boot do serviço demo.

---

## Impacto no Backend

### `fluxoly_config.py`

```python
# IR_FLOW_ENVIRONMENT=demo: sinal manual de ambiente (ADR-012), distinto de
# IS_PULL_REQUEST (que o Render seta sozinho em todo PR Preview). Os dois
# coexistem -- nenhum substitui o outro. Só o valor "demo" tem efeito; qualquer
# outro valor (incluindo ausente/vazio) é tratado como produção/desenvolvimento.
IR_FLOW_ENVIRONMENT = os.environ.get("IR_FLOW_ENVIRONMENT", "").strip().lower()
IS_DEMO_ENVIRONMENT = IR_FLOW_ENVIRONMENT == "demo"

BACKGROUND_JOBS_ENABLED = (
    os.environ.get("IR_FLOW_ENABLE_BACKGROUND_JOBS", "1").strip().lower()
    not in {"0", "false", "nao", "off"}
    and not IS_PULL_REQUEST
    and not IS_DEMO_ENVIRONMENT
)
```

- Reaproveita a mesma constante `BACKGROUND_JOBS_ENABLED` que já governa a thread de sync do MercadoPhone (`app.py:1013`) e a de backup automático (`app.py:485-486`) — nenhuma mudança nesses dois pontos de consumo, exatamente como aconteceu com `IS_PULL_REQUEST` no plano anterior.
- Nova função `integracao_externa_bloqueada_neste_ambiente()` (mesmo arquivo, ao lado das outras constantes de ambiente): `return IS_PULL_REQUEST or IS_DEMO_ENVIRONMENT`. Ponto único de verdade para o guard do KI-037 (item seguinte) — evita duplicar `IS_PULL_REQUEST or IS_DEMO_ENVIRONMENT` em 3 lugares diferentes de `api_mercadophone.py`.

### `api_mercadophone.py` — correção do KI-037

Nos 4 endpoints de escrita/ação (linhas atuais: `sincronizar_mercadophone` 120-134, `reprocessar_mercadophone` 137-167, `reimportar_mercadophone` 176-206, `salvar_config_mercadophone` 230-254+), adicionar a checagem logo após a checagem de permissão já existente em cada um:

```python
from fluxoly_config import integracao_externa_bloqueada_neste_ambiente
...
    @api_mercadophone.route("/integracoes/mercadophone/sincronizar", methods=["POST"])
    def sincronizar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)
        if integracao_externa_bloqueada_neste_ambiente():
            return err("Integração externa desabilitada neste ambiente (preview/demo).", 403)
        ...
```

Mesmo padrão nos outros três (`reprocessar_mercadophone`, `reimportar_mercadophone`, e `salvar_config_mercadophone` — `POST /config`, que grava `api_token`/`sync_enabled` na configuração persistida). Nota de implementação: `salvar_config_mercadophone` usa hoje uma checagem de permissão diferente das outras três (`usuario_admin()`, só admin — as outras três aceitam `admin` ou `tecnico`); a nova checagem entra logo depois dessa checagem existente, sem alterar quem tem permissão de acesso, só bloqueando adicionalmente em Preview/Demo. Incluir `/config` evita que o ambiente Demo armazene uma credencial real de uma integração que ele não pode usar, mesmo que os 3 pontos de disparo já estejam bloqueados — decisão do CTO (2026-08-11): o guard cobre a integração inteira, não só os endpoints que fazem a chamada externa. A checagem **não** entra em `status_mercadophone` (só leitura de status, sem gravação nem chamada externa).

### `app.py`

- Boot log (ao lado do bloco `if IS_PULL_REQUEST:` já existente, linha ~140):
```python
if IS_DEMO_ENVIRONMENT:
    logger.warning(
        "demo_background_jobs_desativados",
        extra={"motivo": "IR_FLOW_ENVIRONMENT=demo", "referencia": "ADR-012"},
    )
```
- Sentry `environment` (linha ~165), estendendo a cadeia já existente:
```python
if IS_PULL_REQUEST:
    _sentry_environment = "preview"
elif IS_DEMO_ENVIRONMENT:
    _sentry_environment = "demo"
elif IS_SERVER_RUNTIME:
    _sentry_environment = "production"
else:
    _sentry_environment = "development"
```
- Import de `IS_DEMO_ENVIRONMENT` junto dos demais símbolos já importados de `fluxoly_config` (linha ~74).

---

## Impacto no Frontend

Nenhum. Mudança inteiramente de backend/bootstrap/scripts — nenhum endpoint novo consumido pelo frontend, nenhuma página nova.

---

## Runbook de Provisionamento (Render/Vercel)

Documentação operacional — não é código, mas fica registrada aqui por ser parte da implementação deste plano (o CTO ou quem provisionar segue este checklist na etapa de Implementação):

1. **Nunca usar "Duplicate Service" a partir do serviço de produção no painel Render** — causa raiz do INC-003. Criar um Web Service novo do zero, mesmo repositório/branch, mesmo Dockerfile.
2. Nome do serviço: `fluxoly-demo` (confirmado pelo CTO, 2026-08-11).
3. Disco próprio (1GB, mesmo tamanho da produção hoje) montado em `/data`, nunca compartilhado com o disco de produção.
4. Variáveis de ambiente a configurar manualmente, uma a uma (nenhuma herdada):

| Variável | Valor no Demo | Observação |
|---|---|---|
| `IR_FLOW_ENVIRONMENT` | `demo` | Nova, este plano |
| `FLASK_SECRET_KEY` | gerada nova (`python -c "import secrets; print(secrets.token_hex(32))"`) | Nunca a mesma de produção |
| `IR_FLOW_DATA_DIR` | `/data` | Padrão já usado em produção |
| `IR_FLOW_CORS_ORIGINS` | `https://fluxoly-demo.vercel.app` (ou domínio Vercel real do projeto demo) | Explícito — **não** deixar em branco. Deixar em branco ativa o fallback de regex `https://.*\.vercel\.app` com `supports_credentials=True` (`fluxoly_app_security.py:47-50`), que aceitaria cookies de sessão de **qualquer** site `*.vercel.app`, não só o do Demo — risco desnecessário no primeiro ambiente exposto a alguém fora da equipe |
| `MERCADO_PHONE_SYNC_ENABLED` | `0` | Explícito, mesma defesa em profundidade já usada em Preview — redundante com o guard de código, mas mantém o padrão de duas camadas do INC-003 |
| `MERCADO_PHONE_API_TOKEN` | *(vazio)* | Nunca copiar de produção |
| `MERCADO_PHONE_WEBHOOK_TOKEN` | *(vazio, nunca configurar)* | Achado da Revisão Arquitetural (Eixo 3): sem esta variável, `autenticar_integracao_mercado_phone()` já é fail-secure por design (KI-023) — nenhum candidato de token corresponde a uma string vazia, então `POST /integracoes/mercadophone/os` fica fechado por padrão. Nunca copiar de produção; se um dia o Demo precisar do webhook, isso é uma decisão nova, não uma herança |
| `IR_FLOW_ENABLE_BACKGROUND_JOBS` | `0` | Explícito, mesma defesa em profundidade |
| `SENTRY_DSN` | mesmo DSN do projeto Sentry já usado por produção/preview | Confirmado pelo CTO (2026-08-11): reaproveitar o projeto atual — `environment=demo` já separa os eventos, sem necessidade de projeto dedicado |
| `METRICS_TOKEN` | gerado novo, se `/metrics` for exposto | Mesmo padrão de produção |

5. Vercel: novo projeto apontando para `frontend/`, variável de build apontando para a URL do backend demo (mesmo padrão do projeto de produção, `VITE_API_URL` ou equivalente — confirmar nome exato da variável no projeto Vercel de produção existente antes de replicar).
6. Após o primeiro boot bem-sucedido: confirmar nos logs a presença de `demo_background_jobs_desativados` e a ausência de qualquer log de sync do MercadoPhone — mesma verificação já usada no Dry-Run 2B.

---

## Seed Sintético e Contas de Demonstração

- Novo script `scripts/seed_demo.py`, standalone (mesmo padrão de `scripts/import_legacy_db.py` — conecta direto ao banco via `conectar()` de `app.py`, sem subir o servidor Flask).
- Roda uma única vez, contra um banco já com schema aplicado (depois do primeiro boot do serviço demo) e vazio de dados de negócio.
- Popula uma "loja modelo" fictícia: ~15-20 clientes, ~10 produtos/peças em `produtos`/`estoque`, algumas `unidades_serializadas`, ~20-30 OS em diferentes status (`os`, `os_reparos`, `os_pecas`), algumas vendas (`vendas`, `vendas_itens`) e lançamentos de caixa (`movimentacoes_caixa`) coerentes com as vendas — volume suficiente para o dashboard e os relatórios não aparecerem vazios numa demonstração, sem tentar ser realista ao ponto de parecer dado real.
- Contas de demonstração: `admin.demo`, `tecnico.demo`, `vendedor.demo` — inseridas em `usuarios` com `generate_password_hash()`, mesmo padrão de `api_users.py:65-66`. Senhas lidas de variáveis de ambiente no momento da execução do script (`DEMO_SEED_ADMIN_PASSWORD` etc.), nunca hardcoded no script nem commitadas — evita reintroduzir credencial em texto plano no repositório (mesma lição do KI-029).
- Depois do seed rodar uma vez: criar um backup via `POST /api/backup/criar` (endpoint já existente, `api_backup.py:31`) com um nome identificável (ex. `versao=seed-inicial`) — esse arquivo `.db` vira o "estado inicial" de referência para o reset.

---

## Reset Manual

- Reaproveita `POST /api/backup/restaurar` (`api_backup.py:98-`), já validado no item "Restore" do checklist de Release 1.0 — nenhum código novo.
- Operador (equipe interna, sessão `admin.demo` ou conta interna) faz upload do arquivo `seed-inicial` salvo na etapa anterior sempre que quiser voltar ao estado zero.
- Nenhum agendamento automático nesta fase (decisão já fixada no `ADR-012`, item #6).

---

## Testes

- `tests/test_ambiente_demo.py` (novo, mesmo padrão de `tests/test_ambiente_preview.py` — cada cenário roda `import fluxoly_config`/`import app` em subprocesso isolado, porque as constantes são decididas no momento do import):
  - `IR_FLOW_ENVIRONMENT=demo` → `BACKGROUND_JOBS_ENABLED is False`, mesmo com `IR_FLOW_ENABLE_BACKGROUND_JOBS=1` setado.
  - `IR_FLOW_ENVIRONMENT` ausente/outro valor → comportamento idêntico ao de hoje (sem regressão).
  - `IR_FLOW_ENVIRONMENT=demo` e `IS_PULL_REQUEST` ausente → log `demo_background_jobs_desativados` aparece; `IS_PULL_REQUEST=true` e `IR_FLOW_ENVIRONMENT` ausente → só `preview_background_jobs_desativados` aparece (os dois logs não se confundem).
  - Sentry: `environment == "demo"` quando `IR_FLOW_ENVIRONMENT=demo` e `IS_PULL_REQUEST` ausente; `environment == "preview"` continua vencendo se, por engano, os dois estiverem setados juntos (prova da ordem de precedência).
- `tests/test_ki037_guard_integracoes.py` (novo, usando o client de teste Flask já usado em `tests/test_permissions.py`):
  - Sessão `admin` + `IS_PULL_REQUEST=true` → `POST /integracoes/mercadophone/sincronizar` retorna 403 antes de qualquer chamada externa.
  - Sessão `admin` + `IR_FLOW_ENVIRONMENT=demo` → mesmo resultado para os 4 endpoints (`sincronizar`, `reprocessar`, `reimportar`, `config`) — incluindo confirmar que `/config` retorna 403 sem gravar nenhum valor novo em `mercadophone_config` (não só bloquear a resposta, mas provar que o `UPDATE`/`INSERT` nunca roda).
  - Sessão `admin`, sem `IS_PULL_REQUEST` nem `IR_FLOW_ENVIRONMENT=demo` → `status_mercadophone` (leitura) continua acessível normalmente nos 3 ambientes — só as 4 rotas de escrita/ação são bloqueadas em Preview/Demo.
  - Sessão `admin`, sem `IS_PULL_REQUEST` nem `IR_FLOW_ENVIRONMENT=demo` (produção/dev) → comportamento idêntico ao de hoje, sem regressão (teste de regressão explícito, igual ao já feito para KI-035).
  - Sessão sem perfil `admin`/`tecnico` continua barrada por 403 antes mesmo de chegar no novo guard (ordem das checagens preservada).
- `scripts/seed_demo.py`: não precisa de teste automatizado formal (é um script operacional, não parte da aplicação em runtime), mas a QA Manual deve rodá-lo uma vez contra um banco descartável e confirmar que não lança exceção e produz os volumes esperados.
- Suíte completa (`pytest tests/`) e `ruff check .` sem regressão antes do merge — mesmo gate já usado no plano de Preview Seguro.

Mapeamento para os 14 itens do Definition of Done do `ADR-012` (execução concreta na etapa de QA Manual):

| # DoD (ADR-012) | Como verificar |
|---|---|
| Admin/Técnico/Vendedor conseguem entrar | Login manual com as 3 contas de demo no ambiente provisionado |
| Dados 100% sintéticos | Conferência visual dos registros criados pelo seed — nenhum nome/telefone real |
| Nenhuma credencial de produção presente | Checklist do Runbook de Provisionamento (seção acima), conferido item a item |
| MercadoPhone não é acessível | Logs de boot mostram `demo_background_jobs_desativados`; nenhum log de sync aparece durante uma sessão de uso completa |
| Endpoints do KI-037 não atingem a integração real | `curl`/chamada manual aos 4 endpoints (incluindo `/config`) logado como `admin.demo` → 403 |
| Backup não envia dado para destino real | Inspeção do endpoint `/api/backup/criar` — grava só no disco local do serviço demo, mesmo comportamento de produção, sem destino externo |
| Sentry identifica `environment=demo` | Forçar um erro controlado no ambiente demo e conferir no painel Sentry |
| CORS funciona com o domínio Vercel do Demo | Login real a partir do frontend Vercel do Demo, sem erro de CORS no console do navegador |
| Sessão cross-site funciona | Mesmo teste acima — cookie de sessão precisa sobreviver ao fluxo `SameSite=None; Secure` (`app.py:200-201`, já ativo automaticamente porque o Demo roda com `IS_SERVER_RUNTIME=True`) |
| Reset restaura o estado inicial | Alterar um dado via UI, restaurar o backup `seed-inicial`, confirmar que o dado voltou ao original |
| Demo não compartilha banco/disco com produção | Confirmado por construção (Runbook, serviço/disco dedicados) — checagem visual no painel Render |
| Produção permanece intocada | Nenhuma etapa deste plano toca infraestrutura de produção — confirmar ausência de qualquer log/erro novo em produção durante a QA do Demo |

---

## Critérios de Aceite

- [ ] `IR_FLOW_ENVIRONMENT=demo` desliga `BACKGROUND_JOBS_ENABLED`, coexistindo sem conflito com `IS_PULL_REQUEST` — provado por teste automatizado.
- [ ] Os 4 endpoints de escrita/ação do KI-037 (`sincronizar`/`reprocessar`/`reimportar`/`config`) retornam 403 tanto em Preview quanto em Demo, com sessão admin/técnico real — provado por teste automatizado (não só leitura de código).
- [ ] Nenhuma regressão de comportamento em produção/desenvolvimento local (nenhuma das duas flags nunca é setada nesses ambientes).
- [ ] Sentry reporta `environment="demo"` corretamente, sem colidir com `"preview"` ou `"production"`.
- [ ] `scripts/seed_demo.py` executa sem erro contra um banco vazio e produz os volumes de dados esperados.
- [ ] As 3 contas de demonstração autenticam corretamente com os perfis certos (`admin`, `tecnico`, `vendedor`).
- [ ] Runbook de provisionamento seguido item a item na criação real do serviço Render/Vercel (Implementação).
- [ ] Reset (backup `seed-inicial` → restore) testado de ponta a ponta pelo menos uma vez.
- [ ] Os 14 itens do Definition of Done do `ADR-012` verificados e marcados na QA Manual.
- [ ] Suíte completa + `ruff check .` sem regressão.
- [ ] `KI-037` movido para "Resolvidos" em `KNOWN_ISSUES.md`, com data e commit.

---

## Riscos

- **Dependência de nomenclatura de variável não documentada formalmente por nenhuma plataforma** — ao contrário de `IS_PULL_REQUEST` (setada automaticamente pelo Render), `IR_FLOW_ENVIRONMENT=demo` depende 100% de alguém configurar manualmente no provisionamento. Mitigação: Runbook de Provisionamento explícito + log de boot (`demo_background_jobs_desativados`) torna a ausência da flag visível (nenhum log = nenhuma proteção ativa) em vez de silenciosa.
- **Seed sintético desatualiza com o tempo** — conforme o schema evoluir (novos campos obrigatórios, novas tabelas), `scripts/seed_demo.py` pode quebrar silenciosamente ou gerar dado incompleto. Sem mitigação automática neste plano (fora de escopo criar teste de regressão do seed); recomendação operacional: reexecutar e validar o seed antes de cada demonstração importante, não só na primeira vez.
- **Senhas de demo em variável de ambiente do processo de seed** — se alguém rodar `scripts/seed_demo.py` localmente sem cuidado, pode deixar a senha real de demo no histórico do shell local. Mitigação: documentar no próprio script um aviso equivalente ao já usado em `fluxoly_config.py` para `FLASK_SECRET_KEY`.

---

## Rollback

Mudança de bootstrap/config (`fluxoly_config.py`, `app.py`) segue o mesmo padrão do plano de Preview Seguro: aditiva/condicional, sem migration, `git revert` padrão sem risco de cruzar schema. O guard novo em `api_mercadophone.py` também é aditivo (um `if` a mais antes da lógica existente) — revertível da mesma forma. Nenhuma mudança em produção real: `IR_FLOW_ENVIRONMENT` nunca é setada lá, então o rollback do código, se necessário, não teria efeito observável em produção mesmo antes de ser aplicado.

---

## Decisões de Escopo Confirmadas (CTO, 2026-08-11)

A primeira versão deste plano levantou 3 pequenas decisões de escopo sem tomá-las. O CTO resolveu as três antes de aprovar o plano como baseline:

| # | Questão | Decisão | Motivo (CTO) |
|---|---|---|---|
| 1 | `POST /api/integracoes/mercadophone/config` | **Incluído no guard do KI-037** — o guard passa a cobrir 4 endpoints (`sincronizar`, `reprocessar`, `reimportar`, `config`), não só os 3 pontos de disparo | Evita que o Demo armazene credencial real de uma integração que o próprio ambiente não pode utilizar, mesmo que essa credencial nunca chegue a ser usada pelos endpoints já bloqueados |
| 2 | Projeto Sentry | **Reaproveitar o projeto atual**, distinguindo por `environment=demo` | Menor complexidade; separa produção/preview/demo dentro do mesmo projeto |
| 3 | Nome do serviço | **`fluxoly-demo`** | Simples, explícito, consistente com a finalidade |

Nenhuma questão em aberto remanescente. Nenhuma dessas 3 decisões reabre o `ADR-012` — são detalhes de escopo de implementação, não decisões arquiteturais novas.
