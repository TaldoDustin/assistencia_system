# ROTEIRO-homologacao-interna-controlada — Homologação Interna Controlada do Ambiente Demo

**Data:** 2026-08-15
**Feature:** Não é código — é o ciclo operacional que valida a experiência funcional do Ambiente Demo
(`ADR-012`, gate técnico 14/14 já fechado), incluindo controle de acesso por perfil, executado via Claude in
Chrome sob supervisão do CTO. Não há BR-NNN novo.
**Status:** 🟡 **Execução concluída (2026-08-15) — CONCLUÍDA COM PENDÊNCIAS.** Substitui, por decisão do
CTO, o gate atual da Homologação Externa (`PLAN-homologacao-externa-demo.md`) — ver "Relação com a
Homologação Externa" abaixo. Ver "Encerramento" para a decisão final e os achados (KI-041, KI-042).

> Este documento é efêmero (mesmo padrão de `docs/engineering/adr/ADR-010.md` e de
> `PLAN-homologacao-externa-demo.md`). Depois que o ciclo encerra, permanece só como histórico.

**Estado**

- [x] Roteiro definido e aprovado pelo CTO (2026-08-15)
- [x] Execução — Fluxo 1 (login/navegação, 3 perfis) (2026-08-15)
- [x] Execução — Fluxos 2/3/4 (Admin/Técnico/Vendedor) (2026-08-15)
- [x] Execução — Fluxo 5 (testes negativos de controle de acesso) (2026-08-15)
- [x] Coleta e classificação dos achados (2026-08-15) — ver KI-041, KI-042
- [x] Restore do Demo para `seed-inicial` pós-execução (2026-08-15) — ambiente limpo, produção confirmada
  saudável (`/health` → `{"status":"ok"}`)
- [ ] Correções (KI-041 — seed sem Tipo de Garantia — bloqueia reabertura do ciclo)
- [x] Encerramento — 🟡 **CONCLUÍDA COM PENDÊNCIAS** (nem HOMOLOGADO, nem REJEITADO — ver seção
  "Encerramento")

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

## Registro de evidências (execução real, 2026-08-15)

| Caso | Perfil | Resultado | Evidência |
|---|---|---|---|
| Login + dashboard | admin.demo | ✅ | Dashboard carregou, menu completo (19 itens) |
| Login + dashboard | tecnico.demo | ✅ | Dashboard carregou; menu mais restrito que o documentado no `ADR-012` (também sem Vendas/Relatórios/Tipos de Garantia) — observação, não bug |
| Login + dashboard | vendedor.demo | ⚠️ | Dashboard carregou; menu inclui Kanban e Garantias, contradizendo `ADR-012` — ver KI-042 |
| Logout | Todos os 3 perfis | ✅ | Retorno confirmado à tela de login em cada caso |
| Acesso negado a Usuários | tecnico.demo, vendedor.demo | ✅ | "Somente administradores podem gerenciar usuários." |
| Acesso negado a Financeiro | tecnico.demo, vendedor.demo | ✅ | "Somente perfis administrador ou financeiro podem acessar o Financeiro." |
| Acesso a `/vendas` | tecnico.demo | ⚠️ | UI expõe formulário completo; backend bloqueia escrita (403 confirmado no código, `fluxoly_vendas_controller.py:108-109`) — ver KI-042 |
| Acesso a Kanban/Garantias | vendedor.demo | ⚠️ | Leitura completa e funcional; escrita bloqueada no backend (`api_os.py:671,905`) — ver KI-042 |
| Alterar status de OS | tecnico.demo | ✅ | OS #12 → "Aguardando peça" salvo com sucesso ("Ordem atualizada!") |
| Registrar serviço/reparo | tecnico.demo | ✅ | Validação peça-modelo funcionando corretamente; 2 de 3 OS testadas tinham peça incompatível pré-existente no seed (dado inconsistente, não bug de lógica) |
| **Finalizar OS** | tecnico.demo | 🔴 **bloqueado** | "Nenhum Tipo de Garantia cadastrado" — seed sem dado — ver KI-041 |
| Cadastro de cliente | vendedor.demo | ✅ | "Cliente criado!" — cliente sintético de teste |
| **Registrar venda** | vendedor.demo | 🔴 **bloqueado** | Mesmo bloqueio do Tipo de Garantia — ver KI-041 |
| Reflexo no Dashboard | vendedor.demo | ⚠️ | Venda registrada corretamente em Vendas > Histórico; não reflete no card "Faturamento" do Dashboard (só receita de OS/serviço) — ver KI-042 |
| Acesso indevido a Usuários/Financeiro | vendedor.demo | ✅ | Bloqueado corretamente, mesma mensagem do admin/técnico |
| Acesso a Backups | vendedor.demo | ✅ | Redirecionamento silencioso para Dashboard, sem exposição de dado |
| MercadoPhone | Não testado nesta rodada | — | Já confirmado 403 nos 4 endpoints via `admin.demo` no gate técnico (`ADR-012` DoD); não repetido aqui |

**Após a mudança de decisão do CTO (correção controlada do KI-041 dentro desta mesma sessão):**

| Caso | Perfil | Resultado | Evidência |
|---|---|---|---|
| Criar Tipo de Garantia (`admin.demo`) | admin.demo | ✅ | "Tipo de Garantia criado!" — "Garantia Padrao 90 dias" (3 meses), usado só para confirmar o desbloqueio, não como correção definitiva |
| Finalizar OS (reexecução) | admin.demo (mesma OS #12) | ✅ | "Ordem finalizada!" — 12→13 finalizadas |
| Registrar venda (reexecução) | vendedor.demo | ✅ | "Venda concluída!" — Venda #9, R$ 4.900,00, confirmada em Vendas > Histórico |
| Restore `seed-inicial` (limpeza) | admin.demo | ✅ | 18 clientes (cliente de teste removido), Tipos de Garantia voltou a zero (confirma que o gap é do seed, reproduzível), produção confirmada saudável (`/health` → 200) |

Critério de classificação de achado: mesmo critério do `PLAN-homologacao-externa-demo.md` — avaliar contra
`ENGINEERING_GUIDE.md` §11. Nenhum achado desta execução atendeu critério objetivo de interrupção (C-01 a
C-03) — todos são C-04 isolado ou nenhum critério — por isso nenhum virou `hotfix/` imediato. Todos entraram
em `KNOWN_ISSUES.md` (KI-041, KI-042).

## Definition of Done deste ciclo

| Critério | Resultado |
|---|---|
| Login dos 3 perfis com menu correto | ⚠️ Login ✅; menu diverge do `ADR-012` em 2 perfis (KI-042) |
| Fluxos positivos (Admin/Técnico/Vendedor) executados | ✅ (Finalizar OS e Registrar Venda só após correção pontual do Tipo de Garantia) |
| Testes negativos de controle de acesso executados | ✅ |
| Nenhum guardrail violado | ✅ |
| Achados registrados e classificados | ✅ KI-041 (crítico, bloqueante), KI-042 (médio/baixo, não bloqueante) |
| Incidentes críticos (P0) | zero |

---

## Encerramento

**Decisão do CTO (2026-08-15): 🟡 CONCLUÍDA COM PENDÊNCIAS.**

Não é HOMOLOGADO nem REJEITADO — categoria intermediária, mais precisa para o resultado real:

- Os fluxos principais foram exercitados nos 3 perfis.
- O ambiente se mostrou funcional e os guardrails foram respeitados integralmente (nenhum dado real, nenhuma
  chamada MercadoPhone, nenhum acesso à produção, produção confirmada saudável ao final).
- Não foi encontrada nenhuma falha estrutural grave de segurança ou lógica de negócio — os achados de
  autorização/UX (KI-042) são inconsistências de exposição de tela, não bypass confirmado (backend valida
  corretamente em ambos os casos verificados).
- Mas o **seed inicial estava incompleto** (KI-041): sem nenhum Tipo de Garantia cadastrado, os dois fluxos
  centrais do sistema — Finalizar OS e Registrar Venda — ficam bloqueados para qualquer perfil. Isso não é
  aceitável para uma homologação (interna ou externa) ser considerada concluída.

**Correção aplicada durante a execução, só para validar o desbloqueio — não é a correção definitiva:** um
Tipo de Garantia foi criado manualmente via `admin.demo` para confirmar que os fluxos de Finalizar OS e
Registrar Venda funcionam corretamente quando o dado existe (ambos passaram). Em seguida o Demo foi
restaurado ao backup `seed-inicial`, removendo esse dado manual (junto com o cliente e a venda de teste
criados durante a execução) — o Demo está limpo novamente, e o gap do seed volta a existir até a correção
formal entrar via `scripts/seed_demo.py` (ver KI-041).

**Regra mantida:** nenhum achado desta homologação foi corrigido diretamente no código ou no Demo de forma
permanente. A correção do KI-041 segue o fluxo normal — Git → CI → deploy → nova homologação — não uma
correção ad-hoc contra o ambiente vivo.

```
Homologação Interna Controlada — EXECUTADA (2026-08-15)
       ↓
🟡 CONCLUÍDA COM PENDÊNCIAS (não HOMOLOGADO, não REJEITADO)
       ↓
Restore seed-inicial (limpeza) ✅
       ↓
KI-041 registrado (seed sem Tipo de Garantia) — bloqueante
KI-042 registrado (menu/autorização, Dashboard) — não bloqueante
       ↓
Correção do seed (scripts/seed_demo.py) — aguardando aprovação do Plano Técnico (KI-041)
       ↓
Testes + CI + reset do Demo com seed corrigido
       ↓
Reexecução dos fluxos afetados (Finalizar OS, Registrar Venda, Caixa)
       ↓
Nova decisão: 🟢 HOMOLOGADO INTERNAMENTE ou novas pendências
       ↓
Só então: apresentação a prospect / retomada da Homologação Externa (TBD)
```

## Próximo passo

Aguardando o CTO aprovar o Plano Técnico do KI-041 (quantos/quais Tipos de Garantia sintéticos) para então
implementar a correção em `scripts/seed_demo.py` — fora do escopo deste documento, segue o ciclo normal de
código (branch → PR → CI → merge → deploy). KI-042 fica registrado, sem sprint definida, não bloqueia a
retomada.
