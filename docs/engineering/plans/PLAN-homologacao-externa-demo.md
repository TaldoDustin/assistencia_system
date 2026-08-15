# PLAN-homologacao-externa-demo — Homologação Externa do Ambiente de Demonstração

**Data:** 2026-08-15
**Feature:** Não é código — é o ciclo operacional que decide se o Ambiente Demo (`ADR-012`, gate técnico
14/14 já fechado) está pronto para ser usado por alguém de fora da equipe. Não há BR-NNN novo.
**Status:** Discovery concluída (decisões do CTO abaixo), aguardando aprovação para avançar ao Plano de
Homologação formal.

> Este documento é efêmero (mesmo padrão de `docs/engineering/adr/ADR-010.md`). Depois que o ciclo de
> homologação encerra, ele permanece só como histórico — não é mantido atualizado como `ARCHITECTURE.md` ou
> `DATABASE.md`.

**Estado**

- [x] Discovery — decisões abaixo (CTO, 2026-08-15)
- [ ] Plano de Homologação — preparação, roteiro de execução, formulário de coleta de feedback
- [ ] Preparação — conferir Demo/seed/backup ainda íntegros, preparar credenciais de acesso
- [ ] Execução — homologador percorre os cenários
- [ ] Coleta e classificação do feedback
- [ ] Correções (se houver achados que se qualifiquem — ver critérios objetivos de interrupção)
- [ ] Encerramento — ACEITO / REJEITADO

---

## Contexto

O gate técnico do Ambiente de Demonstração (`ADR-012`) está fechado: 14/14 critérios do Definition of Done
confirmados em 2026-08-15 (ver `docs/engineering/plans/PLAN-ambiente-demo-homologacao.md`, seção
"Verificação final dos 14 critérios do DoD"). Isso prova que o sistema **funciona** no ambiente Demo — não
prova que o ambiente está pronto para alguém de fora da equipe **usar e validar**. São dois gates
diferentes:

- **Homologação técnica** (concluída): o ambiente existe, está isolado, os guards funcionam.
- **Homologação de produto** (este documento): uma pessoa que não construiu o sistema consegue operá-lo
  pelos fluxos reais, sem incidentes, e o feedback dela vira evidência formal.

Decisão do CTO (2026-08-15): não abrir mais nenhuma sprint técnica agora. O próximo movimento é este ciclo
de homologação — LGPD roda em paralelo como trilha de Discovery separada (ver "Trilhas paralelas" abaixo),
sem se misturar a este ciclo.

---

## Decisões da Discovery (CTO, 2026-08-15)

| Pergunta | Decisão |
|---|---|
| Quem é o primeiro homologador? | Pessoa interna simulando usuário externo — menor exposição antes da primeira rodada real |
| Quantos usuários/perfis na primeira rodada? | 1 pessoa testando os 3 perfis (`admin.demo`/`tecnico.demo`/`vendedor.demo`) |
| Período da homologação | Sessão única (1 dia) |
| Quem decide ACEITO/REJEITADO ao final? | Só o CTO |

**Nota sobre o escopo do período:** sessão única de 1 dia não cobre cenários de uso contínuo (ex.: uma OS
que muda de status ao longo de vários dias, um ciclo completo de compra→estoque→venda espalhado no tempo).
Isso é uma limitação aceita conscientemente desta primeira rodada — se o feedback mostrar que esse tipo de
cenário importa, uma rodada seguinte com período maior fica em aberto, não decidida agora.

---

## O que será homologado — cenários por perfil

Lista de partida (a confirmar/ajustar na Preparação, antes da execução):

**Admin**
- Login
- Gestão de usuários
- Configurações
- Estoque
- Ordens de Serviço
- Vendas
- Financeiro
- Relatórios

**Técnico**
- Login
- Receber OS
- Alterar status da OS
- Registrar serviço/reparo
- Finalizar OS

**Vendedor**
- Login
- Cadastro de cliente
- Registrar venda
- Caixa
- Consulta de produtos/estoque

---

## O que NÃO pode acontecer durante a homologação

Direto da lição do INC-003 — todos já cobertos pelo gate técnico (`ADR-012` DoD), mas listados aqui como
guardrails explícitos da execução, não só como itens já verificados uma vez:

- Nenhum dado real de cliente/produção
- Nenhuma chamada real ao MercadoPhone (guard KI-037, confirmado 403 nos 4 endpoints)
- Nenhum e-mail real disparado
- Nenhum backup indo para destino externo (confirmado: sem `GOOGLE_DRIVE_*`/`BACKUP_EMAIL_*` no Demo)
- Nenhum acesso à produção
- Nenhuma credencial de produção usada ou exposta
- Nenhuma alteração no ambiente produtivo

Se qualquer um desses ocorrer durante a homologação, é incidente — trata-se como P0, não como "achado de
homologação".

---

## Definition of Done da Homologação (distinto do DoD técnico do `ADR-012`)

| Critério | Resultado esperado |
|---|---|
| URL Demo acessível | ✅ |
| Login admin | ✅ |
| Login técnico | ✅ |
| Login vendedor | ✅ |
| Dados sintéticos presentes | ✅ |
| MercadoPhone bloqueado | ✅ |
| Backup externo bloqueado | ✅ |
| Sentry `environment=demo` | ✅ |
| CORS restrito ao frontend Demo | ✅ |
| Reset funcionando | ✅ |
| Produção intocada | ✅ |
| Fluxos principais executados (lista de cenários acima) | a confirmar na execução |
| Feedback registrado | a confirmar na execução |
| Incidentes críticos | zero |

Os 11 primeiros critérios já têm evidência do gate técnico do `ADR-012` — citados aqui para reafirmar
durante a execução, não para reverificar do zero. Os 3 últimos são o que esta homologação efetivamente
mede.

---

## Ciclo formal

```
Discovery (este documento)
   ↓
Plano de Homologação — roteiro de execução + formulário de feedback
   ↓
Preparação — conferir Demo íntegro, credenciais prontas
   ↓
Homologador recebe acesso
   ↓
Execução dos cenários
   ↓
Coleta de feedback
   ↓
Classificação: bug crítico | bug alto | bug médio | melhoria | dúvida/usabilidade
   ↓
Correções (só o que se qualificar pelos critérios objetivos de interrupção do
ENGINEERING_GUIDE.md §11 — o resto vira KNOWN_ISSUES.md, sem bloquear o encerramento)
   ↓
Nova rodada (se necessário)
   ↓
ACEITO / REJEITADO (decisão do CTO)
```

---

## Trilhas paralelas (não misturar com este ciclo)

- **KI-040** (race condition em `criar_admin_padrao()`): permanece separado, não bloqueante. Só entra em
  sprint própria se o CTO decidir corrigi-lo — não é reaberto por causa desta homologação.
- **LGPD**: Discovery formal própria, recomendada pelo CTO para rodar em paralelo (trilha de compliance,
  não de código) — não decidida/iniciada neste documento.
- **PR #24**/**PR #22** (disposição pendente): decisão separada do CTO, sem relação com este ciclo.

---

## Próximo passo

Aguardando aprovação do CTO para avançar ao **Plano de Homologação** — que define o roteiro de execução
passo a passo, o formulário/formato de coleta de feedback, e a logística de acesso (link, credenciais,
janela de tempo exata do dia escolhido).
