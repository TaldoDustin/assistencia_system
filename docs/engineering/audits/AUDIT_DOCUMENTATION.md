# AUDIT_DOCUMENTATION — Nomenclatura Legada na Documentação (TD-12 / Sprint Housekeeping)

**Data:** 2026-07-31
**Fase:** Sprint Housekeeping — Fase 1 (Auditoria), item 3 de 4
**Método:** `git grep` direcionado (links, badges, imagens, diagramas, comandos) além do grep simples
de termo já feito em `AUDIT_LEGACY.md` — para não deixar passar branding escondido em exemplos,
screenshots ou instruções de instalação. Nenhum arquivo foi alterado nesta etapa.

**Insumos:** `AUDIT_LEGACY.md` (item 1), `AUDIT_DEPENDENCIES.md` (item 2).

---

## Escopo ampliado verificado

| Categoria | Resultado |
|-----------|-----------|
| Badges (shields.io / img.shields.io) | **Nenhum encontrado.** README não usa badges de build/coverage/versão — as únicas ocorrências da palavra "badge" no repo são sobre badges de UI do produto (status de venda/garantia), não do README |
| Imagens embutidas em markdown (`![...](...)`) | **Nenhuma.** Nenhum arquivo `.md` do projeto usa sintaxe de imagem |
| Arquivos de imagem versionados (`.png`/`.jpg`/`.gif`/`.svg`) fora de `frontend/` | **Nenhum.** Toda a documentação é texto puro — sem screenshots, GIFs ou diagramas-como-imagem |
| Diagramas ASCII citando `irflow`/`assistencia` | Revisados um a um (`DOMAIN_MODEL.md`, `ENGINEERING_GUIDE.md`, `ADR-007/008`, `MIGRATION_unidades_serializadas.md`) — todas as ocorrências são **referências técnicas corretas** a nomes de arquivo reais, não erros de documentação. Nenhum diagrama tem nomenclatura incoerente com o código atual |
| Links/URLs (todo domínio único citado em `.md`) | Mapeados por completo (tabela abaixo) — nada novo além do já registrado em `AUDIT_LEGACY.md`, exceto um exemplo genérico em `DEPLOY.md` |
| Exemplos de comando `curl`/API | Só 1 ocorrência (`KNOWN_ISSUES.md`, sobre cookies de sessão contra `127.0.0.1` — não usa branding, não é achado) |
| Comandos de instalação | Só o já mapeado em `AUDIT_LEGACY.md` (`cd assistencia_system` em `CONTRIBUTING.md` e no docstring de `scripts/import_legacy_db.py`) |

### Domínios/URLs citados em toda a documentação

| Domínio | Ocorrências | Já mapeado em `AUDIT_LEGACY.md`? |
|---------|:--:|:--:|
| `irflow-backend.onrender.com` | 4 | Sim |
| `assistencia-system.vercel.app` | 3 | Sim |
| `assistencia-system.fly.dev` | 2 | Sim (hospedagem legada, já removida) |
| `irflow-frontend.vercel.app` | 1 | **Não** — novo achado (ver abaixo) |
| `localhost` / `127.0.0.1` | 7 | N/A — genérico, não é branding |
| `vercel.com`, `render.com`, `semver.org`, `keepachangelog.com` | 1 cada | N/A — domínios de terceiros, não do projeto |

### Achado novo — `DEPLOY.md`

`DEPLOY.md:81` usa `https://irflow-frontend.vercel.app` como **URL de exemplo genérico** ("A Vercel
fornecerá uma URL pública (ex: ...)"), não uma URL real em produção (a URL real é
`assistencia-system.vercel.app`, já mapeada). Baixo risco — é só um exemplo desatualizado num guia,
sem efeito em produção. Categoria: documentação. Recomendação: renomear junto com o restante de
`DEPLOY.md` na Fase 4.

---

## Achado mais importante desta auditoria — ADR-008 já propõe uma estratégia diferente da sugerida em `AUDIT_DEPENDENCIES.md`

`docs/engineering/adr/ADR-008.md` (2026-07-27, "Rebranding técnico incremental") — a decisão que
introduziu a convenção `fluxoly_*` para módulos novos — já contém, na seção "Decisão", uma ordem
sugerida (explicitamente **"não comprometida"**, ou seja, uma sugestão a revisitar quando o épico for
escopado, não uma obrigação) para o rebranding completo:

> "...documentação restante → infraestrutura (`irflow_logging.py` → `fluxoly_logging.py`, etc., **com
> aliases temporários**) → variáveis de ambiente (`FLUXOLY_*` **com fallback para `IR_FLOW_*`**) →
> remoção do legado quando não houver mais consumidores."

Isso é **diferente** da estratégia de "rename direto" proposta em `AUDIT_DEPENDENCIES.md` seção 1 para
os módulos 🟢/🟠. A ADR sugere manter um alias/fallback temporário em vez de cortar de uma vez — mais
seguro para módulos-hub (`irflow_core.py`) e essencial para as variáveis de ambiente (onde já é a
abordagem recomendada por esta auditoria também, de forma independente).

**Isto precisa ser uma decisão explícita da Fase 2 (Planejamento), não algo que eu decida
unilateralmente aqui:**

| Abordagem | Onde já foi proposta | Prós | Contras |
|-----------|----------------------|------|---------|
| Rename direto (cortar de uma vez) | `AUDIT_DEPENDENCIES.md` (esta sprint) | Mais simples, sem código morto de transição | Sem rede de segurança se algo depender do nome antigo fora do que o grep encontrou |
| Rename + alias temporário | `ADR-008` (2026-07-27, já aceita) | Rede de segurança — nome antigo continua funcionando por um tempo | Mais um passo (remover o alias depois), risco de o alias nunca ser removido e virar dívida permanente |

Para os módulos 🟢 (baixo risco, poucas dependências, já confirmadas por `git grep`), rename direto
parece proporcional — a rede de segurança de um alias tem pouco valor quando já se sabe exatamente
quem depende do módulo. Para `irflow_core.py`/`irflow_os.py` (🟠) e principalmente para as variáveis
`IR_FLOW_*` (🔴, já fora desta sprint), a abordagem de `ADR-008` (alias/fallback) parece mais prudente
e já está pré-aprovada pelo CTO nessa ADR — não seria uma decisão nova, só aplicar o que já foi aceito.

---

## Contexto adicional confirmado — por que o rename de repositório/domínio está fora de escopo

`docs/company/BRAND_IDENTITY.md` seção 9 (2026-07-10) já vincula esse rename especificamente a **"janela
planejada antes do lançamento comercial"** — não a esta sprint. Isso conecta o item 4 de
`AUDIT_DEPENDENCIES.md` (repositório GitHub, URLs Render/Vercel) a
`docs/company/RELEASE_1.0_MASTER_CHECKLIST.md` (checklist de certificação para o primeiro cliente
pagante), não a um prazo arbitrário. Confirma, com uma segunda fonte independente (`BRAND_IDENTITY.md`
além de `ADR-006`/`ADR-008`), que manter esses itens fora da Fase 4 é a decisão certa.

---

## Documentos que citam nomenclatura legada como registro histórico (confirmado — nada a mudar)

Revisão item a item dos arquivos listados na seção 4 de `AUDIT_LEGACY.md`: todos são registros
históricos deliberados (`CHANGELOG.md`, ADRs, `BRAND_IDENTITY.md`, `.TESTING_REPORT.md`) ou exemplos que
refletem o estado real atual do repositório (`CONTRIBUTING.md`, `import_legacy_db.py`) e que naturalmente
se atualizam quando o item de infraestrutura correspondente for renomeado. Nenhum documento novo
encontrado fora desse padrão.

---

## Conclusão

Nenhum achado novo de nomenclatura fora do já mapeado em `AUDIT_LEGACY.md`/`AUDIT_DEPENDENCIES.md`,
exceto o exemplo genérico em `DEPLOY.md`. O valor real desta auditoria foi confirmar que **a Fase 2
(Planejamento) tem uma decisão de estratégia genuína a tomar** — rename direto vs. alias/fallback
temporário (já pré-aprovado em `ADR-008` para infraestrutura/env vars) — antes de qualquer commit da
Fase 4.

## Próximo passo

`AUDIT_REPOSITORY.md` — estrutura geral de pastas, arquivos soltos, duplicações, e uma decisão sobre
`assets/ir_flow.ico` + `build_exe.ps1` + `build_setup.ps1` + `installer.iss` (candidatos a remoção,
identificados em `AUDIT_DEPENDENCIES.md` seção 4, ainda não investigados a fundo).
