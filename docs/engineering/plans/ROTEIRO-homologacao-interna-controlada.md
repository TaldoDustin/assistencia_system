# ROTEIRO-homologacao-interna-controlada — Homologação Interna Controlada do Ambiente Demo

**Data:** 2026-08-15
**Feature:** Não é código — é o ciclo operacional que valida a experiência funcional do Ambiente Demo
(`ADR-012`, gate técnico 14/14 já fechado), incluindo controle de acesso por perfil, executado via Claude in
Chrome sob supervisão do CTO. Não há BR-NNN novo.
**Status:** Rascunho aprovado pelo CTO (2026-08-15). Substitui, por decisão do CTO, o gate atual da
Homologação Externa (`PLAN-homologacao-externa-demo.md`) — ver "Relação com a Homologação Externa" abaixo.

> Este documento é efêmero (mesmo padrão de `docs/engineering/adr/ADR-010.md` e de
> `PLAN-homologacao-externa-demo.md`). Depois que o ciclo encerra, permanece só como histórico.

**Estado**

- [x] Roteiro definido e aprovado pelo CTO (2026-08-15)
- [ ] Execução — Fluxo 1 (login/navegação, 3 perfis)
- [ ] Execução — Fluxos 2/3/4 (Admin/Técnico/Vendedor)
- [ ] Execução — Fluxo 5 (testes negativos de controle de acesso)
- [ ] Coleta e classificação dos achados
- [ ] Correções (se houver achados que se qualifiquem — ver critérios objetivos de interrupção)
- [ ] Encerramento — HOMOLOGADO INTERNAMENTE / REJEITADO

---

## Relação com a Homologação Externa

Decisão do CTO (2026-08-15): este ciclo **substitui, por agora**, o gate da Homologação Externa descrito em
`docs/engineering/plans/PLAN-homologacao-externa-demo.md`. Aquele documento permanece no repositório como
histórico do Discovery e do Plano já aprovados (PR #34/#35) — não é apagado nem revertido — mas sua etapa de
Preparação (data + homologador humano `TBD`) fica **adiada**, sem data para retomar, até decisão futura do
CTO. A sequência revisada é:

```
Discovery externa (histórico, PR #34)
       ↓
Plano de Homologação Externa (histórico, PR #35)
       ↓
┌───────────────────────────────┐
│ Homologação Interna Controlada│  ← este documento, gate atual
│ Claude in Chrome + roteiro    │
└───────────────┬───────────────┘
                ↓
          Achados / Bugs
                ↓
        Correções necessárias
                ↓
        Reexecução (se preciso)
                ↓
    HOMOLOGADO INTERNAMENTE
                ↓
   Apresentação a prospect (futuro)
                ↓
   Homologação Externa real (retomada futura, TBD)
```

## Objetivo

Validar a experiência funcional do Ambiente Demo — incluindo que cada perfil só acessa o que deveria — antes
de qualquer apresentação a prospect ou retomada da homologação externa com humano.

## Executor e camadas

- **Camada A (este roteiro):** Claude in Chrome, executando os fluxos abaixo como um usuário real faria,
  sob supervisão do CTO nesta sessão — confirmação antes de avançar de um perfil/fluxo para o próximo.
- **Camada B (posterior, fora deste documento):** Claude Code cruza os resultados observados com logs,
  banco do Demo, Sentry e backup/reset, para diferenciar "funcionou visualmente" de "funcionou corretamente
  no backend".

## Ambiente e regras invioláveis

- **Frontend:** `https://assistencia-system-do1h.vercel.app`
- **Backend:** `https://fluxoly-demo.onrender.com`
- **Perfis:** `admin.demo`, `tecnico.demo`, `vendedor.demo`
- Executar exatamente os passos deste roteiro. Nenhum passo fora dele.
- Não alterar código, configuração ou schema.
- Não acessar produção (`irflow-backend.onrender.com` / `assistencia-system.vercel.app`) em nenhum momento.
- Não usar/reabrir PR #22 (`test/render-preview-isolation`) nem PR #24.
- Não inserir dados reais de cliente.
- Guardrails do `PLAN-homologacao-externa-demo.md` (seção "O que NÃO pode acontecer") continuam valendo
  integralmente: qualquer violação (MercadoPhone real, e-mail real, backup externo, acesso à produção) para
  a execução imediatamente e vira P0, não item de roteiro.
- Achado de bug **não é corrigido no ato** — é registrado, evidenciado, classificado; o fluxo afetado para,
  os fluxos independentes continuam.

---

## Fluxo 1 — Login e navegação (todos os perfis)

Para cada perfil, nesta ordem (`admin.demo` → `tecnico.demo` → `vendedor.demo`), com confirmação do CTO
antes de passar ao próximo perfil:

1. Abrir o Demo (aba nova, sem sessão anterior).
2. Login com o perfil.
3. Confirmar que o dashboard carrega.
4. Confirmar que o menu lateral bate com o esperado:
   - **Admin:** menu completo.
   - **Técnico:** sem Financeiro / Custos Operacionais / Tabelas de Preço / Backups / Usuários.
   - **Vendedor:** com Vendas, sem Kanban / Garantias.
5. Logout.

**Evidência esperada:** screenshot do dashboard + screenshot do menu lateral, por perfil.

---

## Fluxo 2 — Admin

| Caso | Passos | Resultado esperado |
|---|---|---|
| Gestão de usuários | Acessar tela de Usuários, abrir um usuário existente | Lista carrega, dados corretos |
| Configurações | Acessar Configurações | Tela carrega sem erro |
| Estoque | Consultar lista de estoque, abrir um item | Dados sintéticos visíveis |
| Ordens de Serviço | Listar OS, abrir uma OS existente | Detalhe da OS carrega |
| Vendas | Listar vendas | Lista carrega |
| Financeiro | Acessar Financeiro/Custos Operacionais | Tela carrega |
| Relatórios | Abrir um relatório | Dados sintéticos, sem erro |

## Fluxo 3 — Técnico

| Caso | Passos | Resultado esperado |
|---|---|---|
| Receber OS | Abrir uma OS pendente, assumir | OS passa a "em andamento" |
| Alterar status | Mudar status da OS assumida | Status refletido na lista |
| Registrar serviço/reparo | Adicionar registro de serviço à OS | Registro aparece no histórico da OS |
| Finalizar OS | Concluir a OS | OS sai da fila ativa / status "concluída" |

## Fluxo 4 — Vendedor

| Caso | Passos | Resultado esperado |
|---|---|---|
| Cadastro de cliente | Criar cliente sintético novo | Cliente aparece na lista |
| Consulta de produto/estoque | Buscar produto existente | Dado correto retornado |
| Registrar venda | Criar venda com produto + cliente | Venda registrada |
| Caixa | Conferir reflexo da venda no caixa | Valor bate com a venda registrada |

---

## Fluxo 5 — Testes negativos (controle de acesso)

Executar depois dos fluxos positivos. Este bloco diferencia "funciona" de "está seguro".

| Caso | Perfil | Ação | Resultado esperado |
|---|---|---|---|
| Acesso indevido a Usuários | `tecnico.demo` | Tentar navegar direto para a URL de Gestão de Usuários | Bloqueado (redirect ou 403) |
| Acesso indevido a Financeiro | `tecnico.demo` | Tentar acessar Financeiro/Custos Operacionais/Backups | Bloqueado |
| Acesso indevido a funções admin | `vendedor.demo` | Tentar acessar Usuários/Configurações/Backups | Bloqueado |
| Acesso indevido a Kanban/Garantias | `vendedor.demo` | Tentar navegar direto para essas URLs | Bloqueado |
| MercadoPhone | Qualquer perfil | Tentar disparar sincronização/reprocessamento manual, se houver botão exposto na UI | Bloqueado (já confirmado 403 no backend via KI-037; este teste valida que a UI também não permite/oculta corretamente) |

---

## Registro de evidências

| Caso | Perfil | Resultado | Evidência |
|---|---|---|---|
| (preenchido durante a execução) | | ✅ / ⚠️ / ❌ | screenshot / trecho de console / URL testada |

Critério de classificação de achado: mesmo critério do `PLAN-homologacao-externa-demo.md` — avaliar contra
`ENGINEERING_GUIDE.md` §11. O que se qualificar vira `hotfix/` a partir de `main`; o resto vira entrada em
`KNOWN_ISSUES.md`.

## Definition of Done deste ciclo

| Critério | Resultado esperado |
|---|---|
| Login dos 3 perfis com menu correto | ✅ |
| Fluxos positivos (Admin/Técnico/Vendedor) executados | a confirmar na execução |
| Testes negativos de controle de acesso executados | a confirmar na execução |
| Nenhum guardrail violado | ✅ obrigatório |
| Achados registrados e classificados | a confirmar na execução |
| Incidentes críticos (P0) | zero |

---

## Encerramento

Decisão final — **HOMOLOGADO INTERNAMENTE** ou **REJEITADO** — permanece exclusiva do CTO, mesmo padrão já
estabelecido para a Homologação Externa. Achados que se qualificarem pelos critérios objetivos de
interrupção seguem o fluxo `hotfix/` do `CLAUDE.md`; os demais entram em `KNOWN_ISSUES.md` sem bloquear o
encerramento deste ciclo.

## Próximo passo

Execução do Fluxo 1 (login/navegação) via Claude in Chrome, com confirmação do CTO a cada perfil, nesta
sessão.
