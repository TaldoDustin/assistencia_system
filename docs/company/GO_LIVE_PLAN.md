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

- [ ] Critério de decisão: que tipo de falha aciona rollback (ex.: bug crítico impedindo operação,
      perda de dados, indisponibilidade prolongada) — **ainda não definido**, decidir antes do primeiro
      go-live real
- [ ] Como reverter o deploy (branch/tag da versão anterior, processo de deploy do Render)
- [ ] Como restaurar o backup pré-implantação (mesmo processo do item "Restore validado" do master
      checklist)
- [ ] Comunicação ao cliente em caso de rollback

---

## O que este documento ainda não tem (gaps conhecidos)

- Nenhuma das checkboxes acima foi exercitada de ponta a ponta — é um rascunho baseado no que faz
  sentido, não um processo testado. Vale um "dry run" completo (implantação simulada, sem cliente real)
  antes do primeiro go-live de verdade.
- Critério de decisão de rollback não definido.
- Número de dias de acompanhamento pós-lançamento é um palpite (7 dias), não uma decisão validada.

---

## Documentos relacionados

- `docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` — pré-requisito deste plano
- `docs/company/RELEASE_STRATEGY.md` — Fase 3 (Multiempresa) muda o significado de "provisionar um
  cliente" quando for entregue
- `docs/engineering/adr/ADR-005.md` — decisão pendente que define como multiempresa vai funcionar
