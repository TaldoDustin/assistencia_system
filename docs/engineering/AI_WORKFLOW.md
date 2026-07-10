# AI_WORKFLOW.md — Fluxo de Trabalho com Inteligência Artificial

Este documento define o protocolo de trabalho para qualquer IA (Claude, GitHub Copilot, Gemini CLI, Codex, ou outro agente) que contribua com este projeto.

Não é específico para nenhuma ferramenta — é o contrato entre o humano e a IA.

---

## Por que este documento existe

IAs são ferramentas poderosas, mas cometem erros previsíveis:
- Implementam sem entender o contexto completo
- Ignoram documentação existente e repetem decisões já tomadas
- Fazem mudanças em cascata sem perceber o impacto
- Assumem estado do banco de dados sem verificar
- Perdem contexto entre sessões e contradizem decisões anteriores

Este documento elimina esses erros definindo um protocolo claro.

---

## Protocolo 1 — Início de Sessão

Toda sessão começa com leitura obrigatória. Sem exceções.

```
PASSO 1: Ler CLAUDE.md (ou este documento, se a IA não carregar CLAUDE.md)
         → Entender: protocolo, regras, filosofia

PASSO 2: Ler docs/operations/PROJECT_STATUS.md
         → Entender: sprint atual, score, bugs abertos, arquivos críticos

PASSO 3: Ler docs/operations/ROADMAP.md
         → Entender: fase atual, objetivo estratégico da sprint, o que vem depois

PASSO 4: Ler docs/operations/KNOWN_ISSUES.md
         → Entender: o que está aberto, o que já foi resolvido, o que foi aceito como risco

PASSO 5: Comunicar entendimento ao humano
         → Formato obrigatório (5 linhas):

         Sistema: <descrição em uma linha>
         Sprint atual: <sprint> — <status>
         Bugs abertos: <N> críticos, <N> altos, <N> médios
         Objetivo da sprint: <objetivo>
         Minha compreensão da tarefa: <o que entendi que devo fazer>

PASSO 6: Aguardar confirmação antes de prosseguir
```

**Se algum documento estiver ausente:** pare, informe, pergunte se deve criá-lo. Não continue sem.

---

## Protocolo 2 — Antes de Alterar Código

Nunca implemente sem análise prévia aprovada pelo humano.

```
PASSO 1: ANALISAR
         - Quais arquivos serão afetados?
         - Existe algum issue aberto em KNOWN_ISSUES.md relacionado?
         - Existe algum ADR em docs/engineering/adr/ que governa esta área?
         - Quais testes existem para o código que será modificado?
         - Qual é o risco de regressão?

PASSO 2: PLANEJAR
         - Liste os arquivos que serão modificados (com razão)
         - Liste os arquivos que serão criados (com razão)
         - Identifique riscos e efeitos colaterais
         - Defina como o resultado será testado

PASSO 3: APRESENTAR PLANO
         Formato sugerido:

         ## Plano para: <descrição da tarefa>

         ### Arquivos que serão modificados
         - `arquivo.py` — razão

         ### Arquivos que serão criados
         - `novo_arquivo.py` — razão

         ### Riscos identificados
         - Risco 1: descrição → mitigação

         ### Como vou validar
         - Teste X valida Y

         Posso prosseguir?

PASSO 4: AGUARDAR APROVAÇÃO
         Não implemente até o humano confirmar.
         Se o humano aprovar parcialmente ou solicitar ajuste: revise o plano e apresente novamente.
```

**Tarefas simples** (correção de typo, atualização de doc, adição de teste isolado) podem pular o plano formal, mas o humano deve ter contexto do que será feito.

**Tarefas complexas** (qualquer mudança em `app.py`, mudança de schema, nova feature) exigem plano escrito antes de qualquer linha de código.

---

## Protocolo 3 — Durante a Implementação

```
REGRA 1: Um arquivo por vez
         Não abra, modifique e feche 5 arquivos de uma vez.
         Finalize um arquivo, confirme que está correto, avance para o próximo.

REGRA 2: Um commit por intenção
         Nunca misture feature + bug fix no mesmo commit.
         Nunca misture refatoração + feature no mesmo commit.
         Formato obrigatório: Conventional Commits (feat:, fix:, refactor:, test:, docs:, chore:)

REGRA 3: Leia antes de editar
         Sempre leia o arquivo completo antes de editar.
         Edits baseados em memória ou suposição são proibidos.

REGRA 4: Nunca apague sem confirmar
         Se precisar remover código, função, arquivo ou tabela:
         pare, mostre o que será removido, aguarde confirmação.

REGRA 5: Banco de dados é território protegido
         Qualquer mudança em schema (CREATE TABLE, ALTER TABLE, DROP TABLE):
         plano escrito + backup verificado + aprovação explícita.
         Nunca execute DDL em produção sem janela de manutenção documentada.
```

---

## Protocolo 4 — Após Implementar

```
PASSO 1: TESTAR
         - Execute os testes relevantes para a mudança
         - Confirme que os testes existentes continuam passando
         - Se algum teste falhou: pare e investigue antes de continuar

PASSO 2: VALIDAR
         - Leia o código que foi escrito
         - Confirme que segue os padrões do ENGINEERING_GUIDE.md
         - Confirme que nenhuma regra de segurança foi violada

PASSO 3: ATUALIZAR DOCUMENTAÇÃO
         Use a tabela abaixo para decidir o que atualizar:

         | O que mudou | Atualizar |
         |-------------|-----------|
         | Bug corrigido | KNOWN_ISSUES.md (mover para Resolvidos) + CHANGELOG.md |
         | Nova feature | CHANGELOG.md + PROJECT_STATUS.md + sprint file |
         | Decisão arquitetural | docs/engineering/adr/ (novo ADR) + ARCHITECTURE.md |
         | Mudança no banco | docs/engineering/DATABASE.md |
         | Vulnerabilidade encontrada | KNOWN_ISSUES.md + SECURITY.md |
         | Novo processo de dev | CONTRIBUTING.md + ENGINEERING_GUIDE.md |
         | Sprint concluída | PROJECT_STATUS.md + ROADMAP.md |

PASSO 4: GERAR COMMIT
         Formato: <tipo>(<escopo>): <descrição em minúsculas>
         Exemplos:
           feat(os): adicionar paginação na listagem de ordens
           fix(auth): corrigir sessão não invalidada após logout
           docs(roadmap): adicionar objetivo estratégico por sprint
           test(pricing): adicionar cobertura para endpoint sugerir

PASSO 5: REPORTAR AO HUMANO
         Informe o que foi feito, o que foi testado e o que foi documentado.
         Mencione qualquer coisa inesperada que foi encontrada durante a implementação.
```

---

## Protocolo 5 — Gestão de Incerteza

Quando a IA não tem certeza, o protocolo é:

```
NÍVEL 1: Incerteza sobre como implementar
         → Apresente 2-3 opções com prós e contras de cada uma.
         → Aguarde o humano escolher.
         → Nunca escolha a opção "mais simples" sem apresentar alternativas.

NÍVEL 2: Incerteza sobre o impacto
         → Mapeie explicitamente o que pode quebrar.
         → Proponha uma abordagem conservadora primeiro.
         → Pergunte antes de executar.

NÍVEL 3: Incerteza sobre o estado atual do código
         → Leia os arquivos relevantes antes de assumir qualquer coisa.
         → Nunca implemente baseado em suposição de como o código está estruturado.
         → "Acho que..." não é suficiente — verifique.

NÍVEL 4: Conflito entre documentos
         → ENGINEERING_GUIDE.md prevalece sobre qualquer outro documento.
         → Em caso de conflito, informe o humano antes de prosseguir.
         → Não tome partido silenciosamente — superfícize o conflito.
```

---

## Protocolo 6 — Fim de Sessão

Antes de encerrar, a IA deve:

```
PASSO 1: VERIFICAR TRABALHO INCOMPLETO
         - Existe alguma tarefa iniciada mas não concluída?
         - Existe algum arquivo modificado mas não salvo/commitado?
         - Existe algum teste falhando que ficou pendente?

PASSO 2: ATUALIZAR DOCUMENTAÇÃO DE ESTADO
         - PROJECT_STATUS.md reflete o estado atual?
         - KNOWN_ISSUES.md foi atualizado com novos bugs encontrados?
         - CHANGELOG.md foi atualizado se algo foi entregue?

PASSO 3: REPORTAR HANDOFF
         Informe ao humano:
         - O que foi concluído nesta sessão
         - O que ficou incompleto (e por quê)
         - Riscos ou problemas encontrados que precisam de atenção
         - Próximo passo sugerido para a próxima sessão

PASSO 4: LIMPAR
         - Nenhum arquivo temporário de debug no repositório
         - Nenhum console.log ou print() de debug no código
         - Nenhuma credencial hardcoded introduzida
```

---

## Protocolo 7 — Emergências

Se durante a implementação algo der errado (bug introduzido, dado corrompido, CI quebrado):

```
1. PARE imediatamente. Não tente consertar em cima do erro.
2. Informe o humano do estado atual: o que foi feito, onde está o problema.
3. Não faça rollback sem aprovação explícita do humano.
4. Documente o problema em KNOWN_ISSUES.md antes de qualquer ação.
5. Aguarde instrução.
```

---

## Anti-padrões — O que a IA nunca deve fazer

| Anti-padrão | Por que é problema |
|-------------|-------------------|
| Implementar sem plano aprovado | Risco de quebrar algo inesperado |
| Fazer "melhorias" não solicitadas | Escopo creep, risco de regressão |
| Assumir que o código está como foi documentado | Código e docs podem ter divergido |
| Criar arquivos novos quando poderia editar existentes | Duplicação, fragmentação |
| Commitar tudo de uma vez no final | Impossível rastrear o que quebrou o quê |
| Ignorar testes falhando e prosseguir | Empurra problemas para produção |
| Resolver conflito de documentos silenciosamente | Decisões ocultas são bomba-relógio |
| Apagar código antigo sem mostrar ao humano | Pode ser código em uso não rastreado |
| Fazer DDL no banco sem aprovação | Dados de clientes são irreversíveis |
| Commitar sem mensagem no padrão Conventional Commits | Rastreabilidade zero |

---

## Compatibilidade com Ferramentas

Este workflow foi projetado para funcionar com qualquer IA, mas cada ferramenta tem limitações:

| Ferramenta | Carrega CLAUDE.md automaticamente? | Lê arquivos? | Executa comandos? |
|-----------|-----------------------------------|--------------|--------------------|
| Claude Code | Sim | Sim | Sim |
| GitHub Copilot Chat | Não | Parcialmente | Não |
| Gemini CLI | Não | Sim | Sim |
| ChatGPT/GPT-4 | Não | Com upload | Não |

**Para IAs que não carregam CLAUDE.md automaticamente:**
Copie e cole o conteúdo das seções "Leitura Obrigatória" e "Protocolo de Trabalho" de CLAUDE.md no início da conversa, e aponte para este documento para o fluxo completo.

---

## Resumo Visual

```
INÍCIO DE SESSÃO
       │
       ▼
┌─────────────────────────────────┐
│ 1. Ler CLAUDE.md                │
│ 2. Ler PROJECT_STATUS.md        │
│ 3. Ler ROADMAP.md               │
│ 4. Ler KNOWN_ISSUES.md          │
│ 5. Comunicar entendimento       │
│ 6. Aguardar tarefa              │
└─────────────────────────────────┘
       │
       ▼ (tarefa recebida)
┌─────────────────────────────────┐
│ ANALISAR                        │
│ → arquivos, riscos, testes      │
│ PLANEJAR                        │
│ → lista de mudanças, validação  │
│ APRESENTAR PLANO                │
│ AGUARDAR APROVAÇÃO              │
└─────────────────────────────────┘
       │
       ▼ (aprovado)
┌─────────────────────────────────┐
│ IMPLEMENTAR                     │
│ → um arquivo por vez            │
│ → commits atômicos              │
│ → leia antes de editar          │
└─────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────┐
│ TESTAR                          │
│ VALIDAR                         │
│ ATUALIZAR DOCUMENTAÇÃO          │
│ GERAR COMMIT (Conventional)     │
│ REPORTAR AO HUMANO              │
└─────────────────────────────────┘
       │
       ▼ (fim da sessão)
┌─────────────────────────────────┐
│ VERIFICAR TRABALHO INCOMPLETO   │
│ ATUALIZAR PROJECT_STATUS        │
│ REPORTAR HANDOFF                │
│ LIMPAR                          │
└─────────────────────────────────┘
```
