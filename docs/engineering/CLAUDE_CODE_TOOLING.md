# CLAUDE_CODE_TOOLING.md — Ferramentas do Ambiente Claude Code

Este documento descreve **como** o protocolo definido em [`AI_WORKFLOW.md`](AI_WORKFLOW.md) é executado
especificamente no ambiente Claude Code deste projeto — quais plugins/skills/MCPs estão instalados, para
que serve cada um, e quando usar cada um.

`AI_WORKFLOW.md` é o contrato agnóstico de ferramenta ("o que é o processo"). Este documento é a
implementação desse contrato para o Claude Code ("como isso é executado aqui"). Não duplique o conteúdo
de `AI_WORKFLOW.md` aqui — só referencie.

**Regra de manutenção:** este documento descreve capacidades e ferramentas disponíveis no ambiente Claude
Code *no momento em que foi escrito*. Instalar, remover ou trocar um plugin/MCP que altere o workflow
recomendado exige atualizar este documento no mesmo commit/PR — do contrário ele passa a descrever uma
ferramenta que não existe mais, ou deixa de registrar uma que passou a existir. Se este documento e a
lista real de plugins instalados (`claude plugin list`) divergirem, o real prevalece — reporte a
divergência e corrija o documento antes de seguir.

---

## Camadas

```
                    FLUXOLY
                       │
          ┌────────────┼────────────┐
          │             │            │
       PENSAR        CONSTRUIR     VALIDAR
          │             │            │
   Superpowers     frontend-      Playwright
   ├─ debugging    design         └─ E2E
   ├─ planning     └─ UI
   └─ verification
                       │
                       ▼
                    DEPURAR
                       │
              ┌────────┴────────┐
              │                 │
        ECC Chrome DevTools  Claude-in-Chrome
              │                 │
          técnico          interação real
          console          navegador
          network          sessão/login
          performance      fluxo manual
          lighthouse
```

| Camada | Ferramenta | Papel |
|--------|-----------|-------|
| Pensar | `superpowers` (plugin, já instalado) | Processo de engenharia: debugging sistemático, planejamento, verificação antes de dar tarefa por concluída. |
| Construir | `frontend-design` (plugin, skill) | Orientação de design ao mexer em UI: identidade visual, composição, tipografia, responsividade, estados de interface. Não adiciona ferramenta nova — é uma camada de raciocínio de design. |
| Validar | `playwright` (plugin, MCP) | Testes E2E persistentes e versionados no repositório (`tests/e2e/*.spec.ts`), executáveis em CI. |
| Depurar | ECC Chrome DevTools (MCP, dentro do plugin `ecc`) | Introspecção técnica: console, network, DOM, performance trace, Lighthouse audit. |
| Depurar | Claude-in-Chrome (MCP) | Interação exploratória no navegador real do usuário — sessão/login já autenticados, fluxo manual. |

Nenhuma ferramenta de navegador substitui a outra — respondem perguntas diferentes (ver Matriz de Uso).

---

## Fluxo de Feature

```
REQUISITO
   │
   ▼
Superpowers
Planejar / investigar
   │
   ▼
Implementação
   │
   ├───────────────┐
   ▼               ▼
Frontend         Backend
Design
   │               │
   └───────┬───────┘
           ▼
      Testes existentes
           │
           ▼
       Playwright
       E2E/regressão
           │
           ▼
     Falhou?
      │      │
     SIM    NÃO
      │      │
      ▼      ▼
ECC DevTools  Verification
debug         Before Completion
      │             │
      └──────┬──────┘
             ▼
            CI
             │
             ▼
           MERGE
```

Este fluxo é uma instância do Protocolo 2–4 de `AI_WORKFLOW.md` — não substitui aqueles protocolos, só
mostra onde cada ferramenta do Claude Code entra em cada etapa.

---

## Definição de Concluído

Uma tarefa não está concluída porque o código foi escrito. Está concluída quando:

```
Implementado + Testado + Verificado + Evidenciado
```

- **Implementado** — o código existe e resolve o requisito.
- **Testado** — testes relevantes (unitários e, quando aplicável, E2E via Playwright) passam.
- **Verificado** — a skill `verification-before-completion` (Superpowers) foi aplicada: releitura do que
  foi escrito, confronto com `ENGINEERING_GUIDE.md`, confirmação de que nenhuma regra de negócio foi
  violada.
- **Evidenciado** — há prova concreta (output de teste, screenshot, log) de que o comportamento esperado
  ocorre — não apenas a afirmação de que ocorre.

"Código escrito" nunca é sinônimo de "feature concluída" neste projeto.

---

## Matriz de Uso das Ferramentas

| Ferramenta | Usar quando | Não usar quando |
|-----------|-------------|------------------|
| **Superpowers** (`systematic-debugging`, `verification-before-completion`, etc.) | Antes de qualquer mudança de código; ao investigar um bug; antes de declarar uma tarefa concluída. | — é processo, sempre aplicável quando a tarefa envolve código. |
| **frontend-design** | A tarefa cria ou reformula UI: landing, dashboard, componente, identidade visual. | Mudança de lógica de backend sem impacto visual; ajuste de UI trivial (ex.: corrigir 1 padding) não precisa do processo completo de brainstorm/crítica. |
| **Playwright** | Fluxo de usuário precisa virar teste de regressão persistente (`tests/e2e/`), rodável em CI. | Verificação pontual e exploratória de "isso funciona?" — nesse caso, Claude-in-Chrome ou ECC DevTools são mais rápidos e não exigem manter um arquivo de teste. |
| **ECC Chrome DevTools** | Investigação técnica: "por que está lento", erro no console, requisição de rede falhando, auditoria Lighthouse. | Interação que depende de sessão/login já autenticados no navegador real do usuário — nesse caso é Claude-in-Chrome. |
| **Claude-in-Chrome** | Precisa da sessão real do navegador do usuário (login, cookies, extensões); exploração manual de um fluxo. | Teste que deve ficar no repositório e rodar em CI — nesse caso é Playwright; depuração técnica de performance/rede — nesse caso é ECC DevTools. |

**Regra geral:** nenhuma ferramenta é obrigatória por padrão. Use a que responde à pergunta que a tarefa
está fazendo. Não adicione Playwright, DevTools ou Claude-in-Chrome a uma tarefa que não precisa de
navegador só porque a ferramenta está disponível.

---

## Fora do Fluxo Principal

- **Firecrawl** (plugin instalado no marketplace, não instalado neste ambiente por padrão) — entra apenas
  quando houver necessidade concreta de pesquisa/extração de conteúdo externo. Não faz parte do ciclo
  obrigatório de desenvolvimento.

---

## Ver Também

- [`AI_WORKFLOW.md`](AI_WORKFLOW.md) — protocolo de trabalho agnóstico de ferramenta (o contrato que este
  documento implementa).
- [`ENGINEERING_GUIDE.md`](ENGINEERING_GUIDE.md) — padrões técnicos e convenções.
- [`TESTING.md`](TESTING.md) — estratégia oficial de testes (pirâmide, ferramentas, quando usar cada
  tipo) — Playwright complementa essa pirâmide na camada E2E, não a substitui.
