# GO_LIVE_PLAN.md — Plano de implantação do primeiro cliente pagante

**Status:** 🔵 Rascunho — criado em 2026-07-25, nunca executado (nenhum cliente pagante ainda)
**Última revisão:** 2026-07-25

---

## Por que este documento é separado do RELEASE_1.0_MASTER_CHECKLIST.md

Sugestão do usuário (CTO), 2026-07-25 — são duas perguntas diferentes:

| Documento | Pergunta que responde |
|---|---|
| `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` | "O produto está pronto?" — certificação, itens binários (atende / não atende) |
| `GO_LIVE_PLAN.md` (este documento) | "Como colocamos um cliente em produção com segurança?" — plano de execução, com tarefas reais |

**Pré-requisito:** todos os itens do `RELEASE_1.0_MASTER_CHECKLIST.md` concluídos antes de iniciar este
plano. Diferente daquele documento, aqui **é esperado ter tarefas, subtarefas e sequência de execução**
— este é um runbook operacional, não um checklist de certificação.

---

## Contexto importante: não existe multiempresa ainda

Hoje (2026-07-25) o schema não tem conceito de `empresa` — nenhuma tabela, nenhuma coluna `empresa_id`
(confirmado por busca direta no schema, `app.py`). Multiempresa é a Fase 3 do roadmap
(`docs/company/RELEASE_STRATEGY.md`), ainda bloqueada por decisão pendente em `ADR-005.md`. **Isso
significa que, para o primeiro cliente pagante nos moldes de hoje, "colocar um cliente em produção" não
é "criar um registro de empresa dentro do sistema atual" — é provisionar um deployment próprio**
(instância separada: Render + banco + domínio), o mesmo modelo do cliente atual. Os itens abaixo
refletem essa realidade; vários precisarão ser reescritos quando a Fase 3 (Multiempresa) existir.

---

## Fase 1 — Preparação (antes da semana de implantação)

- [ ] Confirmar `RELEASE_1.0_MASTER_CHECKLIST.md` 100% concluído
- [ ] Backup completo do ambiente de referência (template de onde o novo deployment vai partir)
- [ ] Restore testado num ambiente isolado, não em produção (deveria já estar validado pelo item
      "Restore validado" do master checklist — este passo é a repetição operacional, não o primeiro teste)
- [ ] Ambiente de demonstração/homologação preparado para o cliente conhecer o sistema antes do go-live
- [ ] Contrato/dados do cliente confirmados: nome da empresa, domínio desejado, usuários iniciais
- [ ] Time de suporte alinhado sobre o cronograma de implantação

## Fase 2 — Dia da implantação

- [ ] Provisionar o deployment do cliente (Render + banco + domínio — ou empresa isolada, se a Fase 3
      já tiver sido entregue até lá)
- [ ] Deploy da versão 1.0 (ou a versão vigente) neste ambiente
- [ ] Smoke test completo: login, criar OS, criar item de estoque, criar venda, criar movimentação de
      caixa (financeiro mínimo), gerar relatório
- [ ] Criar usuário administrador do cliente
- [ ] Importar dados existentes do cliente, se houver migração de outro sistema: clientes, estoque, OS
      históricas
- [ ] Validar integrações que o cliente vai usar (ex.: Mercado Phone) — configuração e teste de ponta a
      ponta
- [ ] Confirmar backup automático rodando no ambiente do cliente
- [ ] Treinamento da equipe do cliente (perfis admin/técnico/vendedor)

## Fase 3 — Acompanhamento pós-lançamento

- [ ] Acompanhamento diário nos primeiros 7 dias (ajustar o número conforme a experiência do primeiro
      cliente real — não validado ainda)
- [ ] Canal de suporte direto definido e comunicado ao cliente
- [ ] Revisão de logs/erros diária na primeira semana (depende do item "Logs estruturados" e
      "Monitorização" do master checklist estarem prontos — hoje não estão)
- [ ] Checkpoint com o cliente ao final da primeira semana: o que funcionou, o que não funcionou

---

## Plano de rollback

**Política definida em 2026-08-10** (Discovery da Operação Release 1.0 — Parte B, decisão do CTO, uma
pergunta de cada vez, seguindo a separação técnico/política/autoridade/procedimento do `CLAUDE.md`. Ver
também `DEPLOY.md` seção "Rollback" para o procedimento técnico espelhado):

- **Escopo:** rollback coordenado — backend (Render) e frontend (Vercel) são sempre revertidos juntos,
  nunca de forma independente.
- **Critério de acionamento:** bug crítico impedindo operação, perda/corrupção de dados, ou
  indisponibilidade prolongada.
- **Autoridade:** só o CTO autoriza um rollback. Claude nunca executa um rollback sem aprovação explícita
  a cada ocorrência real — esta política não é uma autorização permanente.
- **Interação com migrations (TD-03 — roll-forward only):** rollback de código **nunca cruza uma
  migration já aplicada** em produção. Se o deploy problemático incluiu uma migration nova, a correção é
  sempre um hotfix roll-forward — nunca reverter para um commit anterior à migration.
- **Mecanismo técnico:** `git revert` do(s) commit(s) problemático(s) em `main` + `git push` — dispara
  redeploy normal em Render e Vercel a partir do código revertido. Deliberadamente não usa o "redeploy de
  versão anterior" nativo de cada plataforma, que deixaria `main` divergente do que está rodando.
- **Verificação:** smoke test manual mínimo (login + uma operação real por módulo crítico — criar OS,
  criar venda, ver dashboard) contra produção logo após o redeploy.
- **Restauração de dado**, se o gatilho envolveu perda/corrupção: mesmo processo já validado do item
  "Restore validado" do master checklist (`api_backup.py::restaurar_backup_upload`).
- **Conflito durante o revert** (decidido em 2026-08-10, após o Dry-Run 1B — ver
  `docs/operations/PROJECT_STATUS.md`): qualquer conflito em `git revert` durante um rollback de produção
  é **condição de parada** — cobre qualquer tipo de arquivo (código, documentação, testes, configuração,
  migrations, ou qualquer outro). O Dry-Run 1B usou um commit real (`609619f`) e gerou conflito real em
  `docs/operations/KNOWN_ISSUES.md` (arquivo append-only, evoluído por commits posteriores); resolvê-lo
  exigiria decisão de conteúdo (reabrir vs. remover a entrada do KI-028, e propagar a consistência para
  outros documentos que a referenciam) — não é uma operação puramente mecânica de Git.
  - **Não fazer automaticamente:** `git revert --continue`, `git revert --abort`, `git revert --skip`,
    escolher `ours`/`theirs`, apagar documentação para o revert passar, `git reset`, force-push.
  - **Fazer:** parar, preservar a evidência do conflito, informar o CTO, aguardar decisão explícita antes
    de qualquer resolução ou continuação.
  - **Decisões possíveis do CTO:** resolver o conflito de forma controlada; hotfix roll-forward; rollback
    alternativo; abortar o rollback.
- [ ] Comunicação ao cliente em caso de rollback — ainda não definida; só relevante quando houver um
      cliente real em produção, fora do escopo desta decisão

---

## O que este documento ainda não tem (gaps conhecidos)

- A política de rollback está definida e aprovada (2026-08-10). Dois exercícios locais foram conduzidos
  no mesmo dia (Dry-Run 1A e 1B, branch `dry-run/rollback-f5fdb23`, preservada): o 1A validou o mecanismo
  de `git revert` isolado, sem conflito (commit `f5fdb23`, só testes). O 1B, com um commit real de
  produção (`609619f`), encontrou um conflito real em documentação — o que levou à regra "Conflito
  durante o revert" acima. `git revert --abort` executado com sucesso, `main`/`origin/main` nunca
  tocadas. Ainda faltam: repetir o Dry-Run 1B sob a nova regra, um dry-run local completo sem interrupção,
  e um dry-run de infraestrutura (Render/Vercel) antes do primeiro go-live de verdade.
- Comunicação ao cliente em caso de rollback ainda não definida.
- Número de dias de acompanhamento pós-lançamento é um palpite (7 dias), não uma decisão validada.

---

## Documentos relacionados

- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — pré-requisito deste plano
- `docs/company/RELEASE_STRATEGY.md` — Fase 3 (Multiempresa) muda o significado de "provisionar um
  cliente" quando for entregue
- `docs/engineering/adr/ADR-005.md` — decisão pendente que define como multiempresa vai funcionar
