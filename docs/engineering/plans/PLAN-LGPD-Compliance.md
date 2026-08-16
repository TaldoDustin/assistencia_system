# PLAN-LGPD-Compliance — Contenção de exposição de dado pessoal (KI-029 + KI-043 + KI-044 + KI-045)

**Data:** 2026-08-16
**Feature:** `docs/product/research/DISCOVERY_LGPD.md` (Discovery + seção "Decisões do CTO", baseline
aprovada 2026-08-16). Referências de fato: `docs/operations/KNOWN_ISSUES.md` (KI-029, KI-043, KI-044,
KI-045).
**Status:** Aprovado pelo CTO em 2026-08-16 (Fase 1 do KI-029 + KI-043 + KI-044 + KI-045 + mecanismo
parametrizável do `audit_log`, inativo em produção até prazo definido). KI-029 Fase 2 (reescrita de
histórico) segue como gate separado, não incluído nesta aprovação.

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação — não é mantido atualizado como `ARCHITECTURE.md`
> ou `DATABASE.md`. Se algo aqui continuar relevante depois, promova para o documento vivo correspondente.

**Estado**

- [x] Discovery — aprovada (`DISCOVERY_LGPD.md`, decisões do CTO em 2026-08-16: escopo intermediário,
      KI-029 obrigatório antes do piloto, KI-043 com contenção de destinos externos, KI-044 com
      anonimização, KI-045 com restrição de campos sensíveis, `audit_log` com política de
      mascaramento/expurgo a definir, posição jurídica conservadora provisória)
- [x] Plano Técnico — aprovado pelo CTO em 2026-08-16 (as 4 questões em aberto da revisão fechadas: Fase 2
      do KI-029 confirmada como gate separado; produção não ativa expurgo/mascaramento do `audit_log` sem
      prazo definido; KI-045 restringe só leitura de CPF, escrita permanece liberada; `DELETE` de cliente
      órfão mantém-se separado da anonimização)
- [ ] Implementação
- [ ] Testes
- [ ] QA Manual
- [ ] Revisão Arquitetural — obrigatória (toca >3 arquivos e mais de um domínio: Clientes, Backup, Auditoria)
- [ ] Encerramento

---

## Objetivo

Fechar a lacuna técnica que a `DISCOVERY_LGPD.md` identificou como bloqueadora do primeiro cliente
pagante: dado pessoal exposto no histórico git (KI-029), backup sem proteção em destinos externos
(KI-043), ausência de qualquer mecanismo de apagamento/anonimização (KI-044) e controle de acesso mais
amplo que o necessário a CPF/telefone/e-mail (KI-045) — num único ciclo, em vez de quatro sprints
isoladas tratando sintomas do mesmo problema. Este plano decide **como implementar** a baseline já
aprovada pelo CTO; não reabre nenhuma decisão de negócio já fechada na Discovery.

---

## Escopo

### 1. KI-029 — dado real no histórico git

**Fase 1 (não-destrutiva, incluída neste plano):**
- Reforçar `.gitignore` para cobrir de forma inequívoca qualquer `*.db`/`*.db-shm`/`*.db-wal` na raiz do
  repositório (auditar o padrão atual, que já cobre `database.db*`/`backup-*.db` mas não impediu os dois
  arquivos hoje presentes).
- `git rm --cached` dos dois arquivos ainda rastreados hoje
  (`backup-20260429-015724.db`, `database-pre-cleanup-20260517-123834.db`) — remove do estado atual/HEAD,
  **não** do histórico. Ação reversível, baixo risco.
- Auditoria de confirmação: `git ls-files | grep -i "\.db"` deve retornar vazio após a Fase 1.
- Levantar (sem decidir) os fatores que informam a Fase 2: idade do dado (abril/maio de 2026), se o
  repositório já foi clonado externamente, quantos colaboradores tiveram acesso — para o CTO avaliar o
  risco residual real do histórico.

**Fase 2 (destrutiva, fora do gate de aprovação deste plano) — confirmado pelo CTO em 2026-08-16:**
reescrita de histórico (`git filter-repo`/BFG) + force-push. **Permanece explicitamente fora da
implementação inicial**, mesmo depois deste Plano Técnico ser aprovado como um todo — a aprovação geral do
plano **não** autoriza a Fase 2. Ela exige uma segunda confirmação explícita e específica do CTO no
momento da execução, dado que é irreversível na prática assim que qualquer outro clone puxar o histórico
reescrito (`CLAUDE.md`, regra de operação destrutiva). Este plano só prepara a decisão (Fase 1 +
levantamento de risco); a Fase 2 é um gate à parte, com aprovação própria, não incluída em nenhum
"implementar tudo que foi aprovado".

### 2. KI-043 — contenção de destinos externos de backup

- Nova constante central em `fluxoly_config.py`, ex. `EXTERNAL_BACKUP_DESTINATIONS_ENABLED` (hardcoded
  `False` nesta fase, não configurável por env var — decisão de produto, não operacional) — força
  `GOOGLE_DRIVE_BACKUP_DIR`/`BACKUP_EMAIL_SENHA_APP` efetivos a vazio nas camadas de uso
  (`fluxoly_blueprint_registry.py`, `api_backup.py`, `app.py`), **independente** do que estiver configurado
  no ambiente — mesmo padrão de "único ponto de verdade" já usado para `IS_PULL_REQUEST`/
  `IS_DEMO_ENVIRONMENT`.
- Log estruturado de aviso no boot se `IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR`/`IR_FLOW_BACKUP_EMAIL_SENHA`
  estiverem configuradas mas ignoradas pela contenção — visibilidade em vez de silêncio (evita alguém
  assumir que o destino externo está ativo quando não está).
- Backup local (`backups/`, disco do Render) continua funcionando normalmente — não é o item contido.
- Criptografia do backup **fica fora deste plano** (🟡 pós-cliente, decisão já registrada na Discovery).

### 3. KI-044 — anonimização de cliente

- Nova função central `anonimizar_cliente(cursor, cliente_id)` em `fluxoly_clientes_service.py`: mantém
  `clientes.id` intacto (preserva toda FK em `os.cliente_id`/`vendas.cliente_id` — histórico de OS/vendas
  continua íntegro), sobrescreve `nome` por um placeholder padrão (ex. `"Cliente Anonimizado #<id>"`),
  `telefone`/`email`/`cpf_cnpj` por `NULL`. Registra a própria ação em `audit_log` (`acao` distinta, ex.
  `"anonymize"`, para diferenciar de uma edição comum).
- Novo endpoint `POST /api/clientes/<id>/anonimizar` (admin-only, mesmo padrão de `DELETE`) —
  **confirmado pelo CTO em 2026-08-16: complementa, não substitui**, o `DELETE` já existente. Cliente
  órfão (sem OS/venda vinculada) continua usando hard-delete normalmente — decisão explícita de manter
  dois comportamentos de privacidade diferentes, cada um coerente com sua própria situação (sem histórico
  vs. com histórico vinculado), em vez de unificar tudo em anonimização.
- **Limitação conhecida, não resolvida por este plano:** `os.cliente` (campo texto livre, legado,
  desnormalizado do cadastro estruturado) não é tocado pela anonimização de `clientes` — OS antigas
  continuam com o nome em texto puro gravado na própria linha de `os`. Corrigir esse desenho é fora de
  escopo (mudança estrutural maior, registrada como observação na Discovery, não como KI novo).

### 4. Decisão 6 — retenção/mascaramento do `audit_log`

- Nova função `mascarar_audit_log_pii_expirado(cursor)`, reaproveitando o mesmo padrão de job periódico já
  usado para backup automático (`fluxoly_storage.py`): varre `audit_log` onde `entidade = 'cliente'` e
  `criado_em` mais antigo que `AUDIT_LOG_PII_MASK_APOS_DIAS` (nova env var, **sem default** — mesma
  filosofia fail-safe já usada em `IR_FLOW_ADMIN_PASSWORD`/`FLASK_SECRET_KEY`: sem configuração explícita,
  a rotina não roda e loga aviso, não assume um número). Substitui os campos PII dentro do JSON de
  `valor_anterior`/`valor_novo` por placeholder, preservando `acao`/`entidade_id`/`usuario_id`/`criado_em`
  intactos — a trilha de auditoria ("o que aconteceu, quando, quem fez") continua íntegra, só o conteúdo
  pessoal é mascarado.
- Expurgo total (exclusão da linha) após `AUDIT_LOG_EXPURGO_APOS_DIAS` (também sem default), mesmo
  mecanismo.
- **Os dois prazos não são decididos por este plano** — ver "Questões em Aberto".
- **Confirmado pelo CTO em 2026-08-16, requisito explícito de produção:** enquanto
  `AUDIT_LOG_PII_MASK_APOS_DIAS`/`AUDIT_LOG_EXPURGO_APOS_DIAS` não estiverem definidas por decisão
  jurídica/operacional (não pela engenharia), **nenhuma política automática de expurgo/mascaramento roda
  em produção** — o mecanismo pode ser implementado e testado (comportamento fail-safe: ausência da env
  var = rotina inativa, sem exceção, sem valor arbitrário para "ativar"), mas o deploy em produção não deve
  setar essas variáveis com um número inventado só para a rotina sair do estado inativo. Isso vira item
  explícito nos Critérios de Aceite abaixo.

### 5. KI-045 — controle de acesso a campos sensíveis

Mapeamento de consumidores de `cpf_cnpj` feito nesta etapa do Plano Técnico (grep completo no
repositório): **único** domínio que referencia o campo é Clientes —
`fluxoly_clientes_controller.py`/`_service.py`/`_repository.py` (backend) e
`frontend/src/pages/Clientes.jsx` (frontend). Nenhum comprovante, PDF, relatório, venda, OS ou garantia
referencia CPF em nenhum ponto do código — o escopo da mudança é pequeno e contido.

- `fluxoly_clientes_controller.py` (rotas `listar_clientes`/`obter_cliente`): remove `cpf_cnpj` do dict de
  resposta quando `session.get("usuario_perfil") not in ("admin", "financeiro")` — mesmo padrão de
  filtragem condicional por perfil já usado em outros pontos da API.
  `frontend/src/pages/Clientes.jsx`: oculta a coluna/campo CPF quando o perfil da sessão não é
  admin/financeiro (mesmo padrão já usado para esconder itens de menu por perfil).
- Escrita (`POST`/`PUT /api/clientes`): **confirmado pelo CTO em 2026-08-16 — não restringida por este
  plano.** Permanece liberada a todo perfil operacional autenticado (cadastro acontece no balcão por
  qualquer atendente). Decisão explícita, não implícita: a restrição do KI-045 cobre só **leitura**
  (consulta posterior de um CPF já salvo) — quem digita o CPF no momento do cadastro não precisa ser
  admin/financeiro, só quem consulta depois.

---

## Fora de Escopo

- KI-029 Fase 2 (reescrita de histórico) — gate de aprovação separado, ver seção 1 acima.
- Criptografia de backup em repouso (solução completa, com gestão de chave/rotação/recuperação) — 🟡
  pós-cliente, já decidido na Discovery.
- Redação do documento de privacidade/termo de uso — conteúdo jurídico, não é entregável de Plano Técnico
  de engenharia.
- Definição contratual/operacional Fluxoly × loja-cliente (decisão 7 da Discovery) — depende de validação
  jurídica, corre em paralelo, fora do escopo técnico deste plano.
- Correção do desenho de `os.cliente` (texto livre desnormalizado) — observação registrada, não um KI
  aberto, fora de escopo.
- Qualquer melhoria de auditoria/controle de acesso além do que KI-045 exige (ex.: log de quem visualizou
  CPF) — não fazia parte da baseline aprovada.

---

## Impacto no Banco

Nenhuma tabela nova. Nenhuma coluna nova em `clientes`/`audit_log` — a anonimização e o mascaramento
sobrescrevem valores existentes, não mudam schema. Migração: nenhuma (`ALTER TABLE` não é necessário).

---

## Impacto no Backend

- `fluxoly_config.py`: nova constante `EXTERNAL_BACKUP_DESTINATIONS_ENABLED` (hardcoded `False`); duas
  novas env vars sem default (`AUDIT_LOG_PII_MASK_APOS_DIAS`, `AUDIT_LOG_EXPURGO_APOS_DIAS`).
- `fluxoly_clientes_service.py`: nova função `anonimizar_cliente`.
- `fluxoly_clientes_controller.py`: novo endpoint `POST /api/clientes/<id>/anonimizar` (admin-only);
  filtragem de `cpf_cnpj` na resposta por perfil em `listar_clientes`/`obter_cliente`.
- `fluxoly_storage.py`/`fluxoly_blueprint_registry.py`/`app.py`/`api_backup.py`: leitura de
  `GOOGLE_DRIVE_BACKUP_DIR`/`BACKUP_EMAIL_SENHA_APP` passa a respeitar
  `EXTERNAL_BACKUP_DESTINATIONS_ENABLED` como guard central.
- Novo módulo/função de rotina periódica para mascaramento/expurgo do `audit_log` (local exato a decidir
  na implementação — provável reaproveitamento da thread já existente de manutenção periódica).
- `.gitignore`: ajuste de padrão para `*.db`/`*.db-shm`/`*.db-wal` na raiz.

---

## Impacto no Frontend

- `frontend/src/pages/Clientes.jsx`: oculta campo/coluna CPF condicionalmente por perfil; novo botão de
  ação "Anonimizar" (admin-only) ao lado do "Excluir" já existente, para clientes com histórico vinculado.

---

## Estratégia de Migração

Não há migração de schema. Sequência operacional (não destrutiva) no deploy: `.gitignore` +
`git rm --cached` dos dois arquivos do KI-029 podem ser feitos em qualquer momento, independente do resto.
As demais mudanças (contenção de backup, anonimização, mascaramento de `audit_log`, filtragem de CPF) são
aditivas — sem janela de manutenção necessária.

---

## Testes

- `tests/test_clientes_anonimizacao.py` (novo): anonimizar cliente com OS/venda vinculada preserva o `id`
  e o histórico; campos PII viram `NULL`/placeholder; `audit_log` registra a ação; só `admin` acessa o
  endpoint.
- `tests/test_clientes_pii_acesso.py` (novo): `cpf_cnpj` presente na resposta para `admin`/`financeiro`,
  ausente para `tecnico`/`vendedor`/`estoque`; escrita continua liberada a todo perfil autenticado
  (confirma que a restrição é só de leitura, conforme decidido).
- `tests/test_backup_contencao_externa.py` (novo): com `IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR`/
  `IR_FLOW_BACKUP_EMAIL_SENHA` configuradas, `criar_backup()`/`enviar_backup_email()` não são efetivamente
  chamadas com destino externo — só o backup local ocorre; log de aviso confirmado.
- `tests/test_audit_log_retencao.py` (novo): sem `AUDIT_LOG_PII_MASK_APOS_DIAS` configurada, a rotina não
  roda (fail-safe); com a variável configurada, registro mais antigo que o prazo tem PII mascarada,
  `acao`/`entidade_id`/`usuario_id`/`criado_em` preservados; registro mais recente que o prazo não é
  tocado.
- KI-029: não é testável via pytest — validado via `git ls-files`/`git log` antes/depois da Fase 1, fora
  da suíte automatizada.

---

## Critérios de Aceite

- [ ] `git ls-files` não retorna nenhum `.db`/`.db-shm`/`.db-wal` em `main`.
- [ ] Backup com destino externo configurado não envia/copia o arquivo para fora do disco local, com log
      de aviso confirmado.
- [ ] `POST /api/clientes/<id>/anonimizar` funciona para cliente com histórico, preserva `id`/FKs, mascara
      PII, só `admin` acessa.
- [ ] `GET /api/clientes`/`GET /api/clientes/<id>` omitem `cpf_cnpj` para perfis fora de
      `admin`/`financeiro`.
- [ ] Rotina de mascaramento/expurgo do `audit_log` não roda sem as env vars explícitas configuradas; roda
      corretamente quando configuradas.
- [ ] Deploy de produção **não** define `AUDIT_LOG_PII_MASK_APOS_DIAS`/`AUDIT_LOG_EXPURGO_APOS_DIAS` até
      existir decisão jurídica/operacional sobre o prazo — confirmado antes do Encerramento deste ciclo,
      não só no código.
- [ ] Fase 2 do KI-029 (reescrita de histórico) **não** foi executada como parte deste ciclo — confirmado
      no Encerramento que só a Fase 1 foi implementada.
- [ ] Suíte completa de testes passando, `ruff check .` limpo, CI 6/6 verde.
- [ ] Nenhuma regressão nos fluxos existentes de Clientes/Backup/Auditoria.

---

## Riscos

- **Anonimização quebrar algo que dependa do nome do cliente em relatório/tela histórica** — mitigado por
  manter `clientes.id` estável; qualquer join por `id` continua funcionando, só o valor exibido muda.
- **Contenção de backup externo surpreender quem já depende do Google Drive/e-mail hoje** — mitigado pelo
  log de aviso explícito no boot; comunicar a mudança operacionalmente antes do deploy (fora do escopo
  técnico, mas relevante para o Encerramento).
- **Mascaramento do `audit_log` sem prazo configurado dar a falsa sensação de que o problema já está
  resolvido** — mitigado pelo comportamento fail-safe (rotina não roda sem env var) e por manter KI-044/
  decisão 6 como "em andamento" até o prazo real ser definido.

---

## Rollback

Mudanças de código (contenção de backup, anonimização, filtragem de CPF, mascaramento de `audit_log`) são
reversíveis pelo fluxo normal de `git revert` + deploy, mesma política já registrada em `GO_LIVE_PLAN.md`.
KI-029 Fase 1 (`git rm --cached`) é reversível (`git revert`). KI-029 Fase 2, se e quando autorizada, **não
tem rollback real** — é o motivo do gate de aprovação separado.

---

## Questões em Aberto

As 4 questões que bloqueavam a aprovação foram fechadas pelo CTO em 2026-08-16:

- ~~KI-029 Fase 2~~ — **resolvida:** permanece gate separado, fora da implementação inicial (ver seção 1).
- ~~Escrita de CPF~~ — **resolvida:** só a leitura é restrita; escrita permanece liberada a todo perfil
  (ver seção 5).
- ~~Hard-delete de cliente órfão~~ — **resolvida:** mantém-se separado da anonimização (ver seção 3).
- ~~Ativação do expurgo/mascaramento do `audit_log`~~ — **resolvida:** nenhuma ativação em produção sem
  prazo definido (ver seção 4 e Critérios de Aceite).

Perguntas de **negócio/jurídico** que seguem em aberto, não bloqueiam a implementação da Fase 1 deste
plano, mas este Plano Técnico não as responde:

- Prazos exatos de `AUDIT_LOG_PII_MASK_APOS_DIAS`/`AUDIT_LOG_EXPURGO_APOS_DIAS` — aguardando orientação
  jurídica/operacional (decisão 6 da Discovery); até lá, o mecanismo fica implementado mas inativo.
- KI-029 Fase 2: reescrever o histórico ou aceitar o risco residual documentado, depois de avaliar
  exposição real (idade do dado, clones externos, colaboradores com acesso) — decisão separada, própria
  autorização.
- Redação do documento mínimo de privacidade — quem escreve, e quando entra no ciclo (antes ou depois da
  implementação técnica)?

---

## Documentos relacionados

- `docs/product/research/DISCOVERY_LGPD.md` — Discovery e decisões do CTO que originam este plano
- `docs/product/research/DISCOVERY_RELEASE_1.0_RESTANTE.md` — Discovery que colocou LGPD como prioridade
- `docs/operations/KNOWN_ISSUES.md` — KI-029, KI-043, KI-044, KI-045
- `docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md` — precedente de plano consolidando múltiplos
  KIs relacionados num único ciclo
