# Assistencia-System — Engineering Guide

**Versão:** 1.0
**Objetivo:** Definir os padrões técnicos, arquiteturais e de qualidade do Assistencia-System.

---

# Filosofia do Projeto

O Assistencia-System é um sistema de gestão para assistência técnica.

O objetivo principal do projeto é fornecer uma plataforma:

* confiável;
* previsível;
* segura;
* escalável;
* simples de manter.

Nenhuma funcionalidade nova deve comprometer a estabilidade existente.

---

# Ordem de Prioridade

Toda decisão técnica deve seguir esta ordem:

1. Segurança
2. Estabilidade
3. Integridade dos dados
4. Regras de negócio
5. Testabilidade
6. Manutenibilidade
7. Performance
8. Novas funcionalidades

Nunca inverter essa ordem.

---

# Fluxo Obrigatório

Toda tarefa deve seguir obrigatoriamente:

1. Compreender o problema.
2. Identificar riscos.
3. Criar plano.
4. Implementar.
5. Validar.
6. Executar testes.
7. Documentar.
8. Gerar commit.

Nenhuma etapa pode ser ignorada.

---

# Regras de Refatoração

Durante qualquer refatoração:

* nunca alterar regras de negócio;
* nunca alterar comportamento esperado;
* nunca alterar banco sem plano de migração;
* nunca remover código sem confirmar que está morto;
* nunca fazer refatorações massivas.

Grandes alterações devem ser divididas em pequenas sprints.

---

# Arquitetura

A arquitetura deve evoluir continuamente para:

* baixo acoplamento;
* alta coesão;
* responsabilidade única;
* separação de camadas;
* reutilização de código.

Evitar:

* God Objects;
* God Functions;
* arquivos gigantes;
* lógica duplicada;
* dependências circulares.

---

# Backend

Toda regra de negócio deve ficar fora das rotas.

As rotas devem apenas:

* validar entrada;
* chamar serviços;
* retornar resposta.

Sempre que possível:

Routes → Services → Repository → Database

---

# Frontend

Componentes devem possuir responsabilidade única.

Evitar:

* lógica de negócio em componentes;
* duplicação de formulários;
* chamadas HTTP espalhadas.

Toda comunicação com a API deve passar pelo client central.

---

# Banco de Dados

Nunca alterar tabelas diretamente.

Toda alteração deve:

* preservar dados existentes;
* ser reversível;
* possuir estratégia de migração.

Evitar colunas redundantes.

Sempre criar índices quando houver consultas frequentes.

---

# Segurança

Todo código novo deve considerar:

* SQL Injection;
* XSS;
* CSRF;
* autenticação;
* autorização;
* validação de entrada;
* upload seguro;
* proteção de sessão.

Nenhum segredo deve existir no repositório.

---

# Tratamento de Erros

Nunca ocultar exceções.

Toda exceção deve:

* ser registrada em log;
* possuir mensagem clara;
* retornar resposta adequada.

Nunca utilizar except vazio.

---

# Logs

Logs devem conter apenas informações úteis.

Não registrar:

* senhas;
* tokens;
* cookies;
* dados sensíveis.

---

# Testes

Nenhuma funcionalidade crítica pode ser alterada sem testes.

Prioridade:

1. Unitários
2. Integração
3. End-to-End
4. Smoke Test

Cobertura mínima desejada:

* Regras de negócio: 90%
* Serviços: 80%
* API: 70%

---

# Qualidade

Todo código novo deve:

* possuir nomes claros;
* possuir responsabilidade única;
* evitar duplicações;
* utilizar constantes;
* utilizar tipagem quando possível;
* ser facilmente testável.

---

# Commits

Um commit deve resolver apenas um problema.

Exemplos:

* fix(auth): corrige validação de sessão
* refactor(stock): extrai serviço de estoque
* test(os): adiciona testes de criação de OS

Nunca misturar backend e frontend sem necessidade.

---

# Pull Requests

Todo PR deve conter:

* objetivo;
* arquivos alterados;
* impacto esperado;
* riscos;
* testes executados.

---

# Checklist Obrigatório

Antes do merge confirmar:

* aplicação inicia;
* login funciona;
* dashboard funciona;
* ordens de serviço funcionam;
* estoque funciona;
* shopping list funciona;
* usuários funcionam;
* backup funciona;
* build frontend funciona;
* testes passam.

---

# Dívida Técnica

Toda sprint deve reduzir a dívida técnica.

Nenhuma sprint deve aumentar:

* duplicações;
* complexidade;
* acoplamento;
* código morto.

---

# Objetivo Final

O Assistencia-System deve evoluir continuamente sem necessidade de reescrita completa.

Cada alteração deve deixar o projeto mais organizado, mais seguro e mais fácil de manter do que estava anteriormente.
