# PLAN-ki038-admin-senha-configuravel — Senha do admin padrão via variável de ambiente

**Data:** 2026-08-13
**Feature:** `docs/operations/KNOWN_ISSUES.md` KI-038
**Status:** Aprovado pelo CTO

> Este documento é efêmero (ver `docs/engineering/adr/ADR-010.md`). Depois que a sprint encerra, ele
> permanece só como histórico da decisão de implementação — não é mantido atualizado como `ARCHITECTURE.md`
> ou `DATABASE.md`. Se algo aqui continuar relevante depois, promova para o documento vivo correspondente.

**Estado**

- [x] Discovery — concluída em modo leitura (achado: `criar_admin_padrao()` roda incondicionalmente desde
      a implementação original de autenticação; senha `irflow@2024` hardcoded; é a conta real de produção
      do CTO até 2026-08-13)
- [x] Plano Técnico — aprovado pelo CTO (escopo amplo: remover o fallback hardcoded em qualquer ambiente
      que não seja dev local)
- [ ] Implementação
- [ ] Testes
- [ ] QA Manual
- [ ] Revisão Arquitetural
- [ ] Encerramento

---

## Objetivo

`criar_admin_padrao()` (`app.py`) para de criar o usuário `admin` com a senha fixa `"irflow@2024"` em
qualquer ambiente que se pareça com um servidor real (produção, Demo, qualquer deploy Render/Fly futuro).
A senha do admin inicial passa a vir de uma variável de ambiente obrigatória fora de dev local — mesmo
padrão já adotado para `FLASK_SECRET_KEY` (`SECURITY_AUDIT_2026-07.md` item 3).

---

## Escopo

- Reestruturar `criar_admin_padrao()` para ler `IR_FLOW_ADMIN_PASSWORD` do ambiente.
- Fora de dev local (`IS_SERVER_RUNTIME=True`) e com a tabela `usuarios` vazia (nenhum `admin` existente):
  variável ausente derruba o boot com `RuntimeError` — mesmo texto/estilo do erro de `FLASK_SECRET_KEY`.
- Em dev local (`IS_SERVER_RUNTIME=False`): mantém o fallback atual (`"irflow@2024"`), documentado em
  `.env.example`, sem mudança de comportamento.
- Atualizar `tests/conftest.py` (a suíte automatizada roda com `IS_SERVER_RUNTIME=True` via
  `IR_FLOW_DATA_DIR`) para não quebrar na coleta.
- Atualizar `.env.example` e a documentação de segurança (`SECURITY.md`).

---

## Fora de Escopo

- Migrar/invalidar a senha antiga já exposta no histórico do git — risco residual aceito, fora deste
  plano (a senha de produção já foi trocada manualmente pelo CTO em 2026-08-13, fora deste ciclo).
- `scripts/smoke_test_full.py`, `frontend/tests/e2e/app.spec.js`, `docs/engineering/TESTING.md` — todos
  rodam contra `python app.py` local sem `IR_FLOW_DATA_DIR`/`RENDER`/`FLY_DATA_DIR`, então
  `IS_SERVER_RUNTIME` fica falso e o fallback de dev continua valendo. Confirmado por leitura, nenhuma
  mudança necessária.
- Qualquer alteração ao fluxo de troca de senha (`PUT /api/usuarios/<id>`) — já corrigido separadamente
  (KI-039, hotfix `ba2d6294`, fora deste plano).
- Provisionamento do Demo, PR/merge desta branch, homologação externa — gates seguintes, fora deste plano.

---

## Impacto no Banco

Nenhum. Nenhuma tabela/coluna nova, nenhuma migração. Mesmo `INSERT INTO usuarios` de sempre, só a origem
da senha muda.

---

## Impacto no Backend

- `app.py::criar_admin_padrao()` — reestruturada em duas fases:
  1. Conexão própria, só para checar se `admin` já existe; fecha a conexão.
  2. Se não existe: resolve `admin_senha` (variável de ambiente ou fallback de dev local) **fora** de
     qualquer `try/except` que capture exceções amplas — o `RuntimeError` de configuração ausente deve
     propagar e derrubar o boot, nunca ser engolido pelo `logger.warning` que hoje protege só contra erro
     inesperado de banco na inserção.
  3. Nova conexão, insere o usuário; erros de banco na inserção continuam só logados (comportamento atual
     preservado para esse caso específico).
- Nenhum endpoint HTTP novo ou alterado.

---

## Impacto no Frontend

Nenhum.

---

## Estratégia de Migração

Não há migração de schema. Para o deploy real (fora deste plano, gate futuro): a variável
`IR_FLOW_ADMIN_PASSWORD` só precisa existir no momento em que um ambiente novo (Render/Fly) sobe com banco
vazio — produção atual não é afetada porque `admin` já existe lá. Necessário para o **próximo** Demo
provisionado do zero.

---

## Testes

- Teste novo (mesmo padrão de `tests/test_security_flask_secret_key_fallback.py`): boot falha com
  `RuntimeError` quando `IS_SERVER_RUNTIME=True`, tabela `usuarios` vazia e `IR_FLOW_ADMIN_PASSWORD`
  ausente.
- Teste novo: com `IR_FLOW_ADMIN_PASSWORD` definida, o admin é criado com a senha da variável (não mais
  `irflow@2024`).
- Teste novo: com `admin` já existente, a função não faz nada, independente da variável — sem regressão.
- `tests/conftest.py`: `os.environ.setdefault("IR_FLOW_ADMIN_PASSWORD", "<valor-de-teste>")`, ao lado do
  `FLASK_SECRET_KEY` já existente — sem isso, a suíte inteira quebra na coleta.
- Suíte completa local + CI (Linux) confirmando zero regressão.

---

## Critérios de Aceite

- [ ] `IR_FLOW_ADMIN_PASSWORD` ausente + `IS_SERVER_RUNTIME=True` + banco vazio → boot falha com erro
      claro (não silencioso).
- [ ] `IR_FLOW_ADMIN_PASSWORD` definida + banco vazio → admin criado com a senha da variável.
- [ ] Dev local sem a variável → comportamento idêntico ao atual (fallback `irflow@2024`, sem quebrar
      onboarding de novos colaboradores).
- [ ] Produção atual não afetada (admin já existe, função é no-op independente da variável).
- [ ] `smoke_test_full.py`/E2E/`TESTING.md` continuam funcionando sem alteração.
- [ ] Suíte completa + CI verdes.

---

## Riscos

| Risco | Mitigação |
|---|---|
| `RuntimeError` engolido pelo `try/except` genérico existente, perdendo o "fail-loud" | Checagem da variável fica fora do bloco `try/except` que envolve só a inserção — critério obrigatório do CTO na aprovação deste plano |
| Suíte de testes quebra na coleta por falta da variável | `tests/conftest.py` recebe `setdefault` mirrando o padrão já usado para `FLASK_SECRET_KEY` |
| Confusão entre este `IR_FLOW_ADMIN_PASSWORD` e `DEMO_SEED_ADMIN_PASSWORD` (`scripts/seed_demo.py`) — nomes parecidos, propósitos diferentes | Documentar a distinção em `SECURITY.md`: um é bootstrap de qualquer ambiente vazio, o outro é dado sintético específico do Demo |

---

## Rollback

Reverter o commit — `criar_admin_padrao()` volta ao comportamento atual (fallback incondicional). Sem
mudança de schema, sem dado a reverter.

---

## Questões em Aberto

Nenhuma — escopo e comportamento já decididos na etapa de decisão arquitetural (variável
`IR_FLOW_ADMIN_PASSWORD`, fail-loud fora de dev local, sem migração de credencial de produção necessária).
