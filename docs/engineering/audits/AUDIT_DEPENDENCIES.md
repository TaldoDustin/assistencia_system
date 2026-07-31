# AUDIT_DEPENDENCIES — Impacto da Renomeação (TD-12 / Sprint Housekeeping)

**Data:** 2026-07-31
**Fase:** Sprint Housekeeping — Fase 1 (Auditoria), item 2 de 4
**Método:** `git grep` para contagem determinística de imports (código + testes) + Graphify
(`graphify explain`) para relações semânticas/indiretas que o import puro não captura. Nenhum arquivo
foi alterado nesta etapa.

**Insumo:** `docs/engineering/audits/AUDIT_LEGACY.md` (Fase 1, item 1).

---

## Como ler esta tabela

- **Dependências** = quantos arquivos fazem `import`/`from ... import` do módulo (código + testes),
  contado via `git grep`. É o número relevante para "quantos arquivos preciso tocar ao renomear isto".
- **Risco** = chance de quebrar algo em produção se o rename for malfeito.
- **Complexidade** = esforço/coordenação exigido, não só contagem de arquivos. Um módulo com poucas
  dependências mas muito tamanho/centralidade (`irflow_blueprints_api.py`) ou que depende de
  infraestrutura externa (env vars, URLs) é mais complexo que um módulo com várias dependências mas
  puramente mecânicas.

| Símbolo | Significado |
|---------|-------------|
| 🟢 Mecânico | Rename + atualizar imports + rodar testes. Um commit, baixo risco. |
| 🟠 Coordenação | Mecânico mas com mais superfície (módulo-hub, muitos dependentes) ou depende de decisão externa não-destrutiva (ex.: confirmar antes de remover scripts). |
| 🔴 Planejamento | Exige janela de manutenção, mudança em painel externo (Render/Vercel/GitHub), ou é tamanho/risco grande o suficiente para merecer sua própria etapa dedicada dentro da Fase 4. |

---

## 1. Módulos Python `irflow_*.py`

| Item | Dependências (código+testes) | Risco | Complexidade | Observação |
|------|:--:|:--:|:--:|------------|
| `irflow_blueprints_api.py` | 1 | Alto | 🔴 Planejamento | Só `app.py` importa, mas o arquivo tem ~130KB (TD-01) e recebe funções de outros módulos por injeção de parâmetro em `create_api_blueprint()` — grep de import não captura essa superfície. Renomear é trivial; **revisar o diff** não é. Considerar se a quebra em módulos menores (TD-01) deveria vir antes do rename, para não renomear um arquivo que via ser dividido logo depois |
| `irflow_core.py` | 10 (5 módulos de código + 3 testes + `test_sync.py`) | Médio | 🟠 Coordenação | Hub real: `app.py`, `irflow_os.py`, `irflow_reports.py`, `irflow_price_tables.py`, `irflow_reference_data.py` importam dele — **e também `fluxoly_vendas_service.py`** (um módulo já `fluxoly_*` depende de um módulo `irflow_*`; renomear não quebra nada, mas vale registrar o acoplamento cruzado) |
| `irflow_os.py` | 4 (`app.py`, `irflow_reports.py`, 2 testes) | Médio | 🟠 Coordenação | Domínio central de OS — poucas dependências diretas, mas concentra lógica de garantia de reparo (V1.5) adicionada recentemente; testar bem depois do rename |
| `irflow_validation.py` | 7 | Baixo | 🟢 Mecânico | Muitas dependências mas puramente utilitário (`parse_float`/`parse_int`/`safe_json`) — baixo risco de quebra semântica |
| `irflow_audit.py` | 6 | Baixo | 🟢 Mecânico | Auditoria central reutilizável — bem testado (`test_audit_log.py`) |
| `irflow_reference_data.py` | 4 | Baixo | 🟢 Mecânico | |
| `irflow_mercadophone.py` | 3 | Médio | 🟢 Mecânico | Poucas dependências diretas, mas é o maior módulo do projeto (667 linhas, cobertura 27% — ver `PROJECT_STATUS.md`); rename em si é seguro, cobertura baixa é risco pré-existente, não causado pelo rename |
| `irflow_price_tables.py` | 3 | Baixo | 🟢 Mecânico | |
| `irflow_unidades_serializadas_service.py` | 3 | Baixo | 🟢 Mecânico | |
| `irflow_logging.py` | 4 | Baixo | 🟢 Mecânico | |
| `irflow_clientes_service.py` | 2 | Baixo | 🟢 Mecânico | |
| `irflow_web.py` | 2 | Baixo | 🟢 Mecânico | |
| `irflow_blueprints_auth.py` | 1 | Baixo | 🟢 Mecânico | |
| `irflow_blueprints_main.py` | 1 | Baixo | 🟢 Mecânico | |
| `irflow_clientes_controller.py` | 1 | Baixo | 🟢 Mecânico | |
| `irflow_clientes_repository.py` | 1 | Baixo | 🟢 Mecânico | |
| `irflow_produtos_controller.py` | 1 | Baixo | 🟢 Mecânico | |
| `irflow_produtos_repository.py` | 1 | Baixo | 🟢 Mecânico | |
| `irflow_produtos_service.py` | 1 | Baixo | 🟢 Mecânico | |
| `irflow_rate_limit.py` | 1 | Baixo | 🟢 Mecânico | |
| `irflow_reports.py` | 1 | Baixo | 🟢 Mecânico | |
| `irflow_storage.py` | 1 | Baixo | 🟢 Mecânico | Cobertura 25% (ver `PROJECT_STATUS.md`) — mesma observação de `irflow_mercadophone.py`: risco pré-existente, não introduzido pelo rename |
| `irflow_unidades_serializadas_controller.py` | 1 | Baixo | 🟢 Mecânico | |
| `irflow_unidades_serializadas_repository.py` | 1 | Baixo | 🟢 Mecânico | |

**`app.py` não é um item de rename** (é o entrypoint Flask, não carrega prefixo `irflow_`), mas é o nó
mais central do grafo (degree 170) e **é tocado em praticamente todo item acima** — importa 17 módulos
`irflow_*` diretamente. Não soma risco por item individual, mas define a ordem de execução: qualquer
sequência de commits da Fase 4 vai gerar 17 pequenos diffs em `app.py`, um por módulo renomeado. Sugestão:
agrupar num único commit de atualização de imports em `app.py` ao final de cada lote de renomes, em vez
de um commit por módulo — ainda "uma mudança por vez" no sentido de escopo (só imports), não mistura com
lógica.

### Achado adicional confirmado pelo Graphify

`fluxoly_vendas_service.py` (convenção nova) importa de `irflow_core.py` (convenção antiga) — mostra que
a convivência das duas nomenclaturas já criou acoplamento cruzado real, não é só uma questão estética.
Reforça o caso de negócio para concluir o rebranding: cada módulo novo que depender de um módulo antigo
aumenta o número de arquivos tocados quando o antigo finalmente for renomeado.

---

## 2. Configuração órfã em `pyproject.toml`

| Item | Dependências | Risco | Complexidade |
|------|:--:|:--:|:--:|
| `irflow_blueprints_admin` (isort `known_first_party` + coverage `source`) | 0 (arquivo não existe) | Nenhum | 🟢 Mecânico — remover a entrada |
| `irflow_blueprints_inventory` (idem) | 0 (arquivo não existe) | Nenhum | 🟢 Mecânico — remover a entrada |
| `irflow_blueprints_orders` (idem) | 0 (arquivo não existe) | Nenhum | 🟢 Mecânico — remover a entrada |

Sem risco de execução (a linha só afeta isort/coverage, não o runtime), mas vale confirmar antes que
esses três módulos foram de fato consolidados em `irflow_blueprints_api.py` e não apenas perdidos —
checar `git log --follow` se restar dúvida.

---

## 3. Variáveis de ambiente `IR_FLOW_*`

| Item | Dependências | Risco | Complexidade |
|------|:--:|:--:|:--:|
| 14 variáveis `IR_FLOW_*` (ver `AUDIT_LEGACY.md` seção 2) | `app.py`, `irflow_blueprints_api.py`, `irflow_core.py`, `.env.example`, `tests/conftest.py` + 4 arquivos de teste, `frontend/playwright.config.js`, `DEPLOY.md` | Alto | 🔴 Planejamento | `IR_FLOW_DATA_DIR` ativa `IS_SERVER_RUNTIME` — se o Render tiver essa variável configurada no dashboard e o código for renomeado sem atualizar o dashboard no mesmo instante, a detecção de runtime quebra silenciosamente (mesma classe de causa-raiz do KI-027 já registrado). **Não fazer como parte dos commits mecânicos da Fase 4** — precisa de uma janela coordenada: atualizar código e dashboard do Render na mesma operação, testar em produção logo em seguida |

---

## 4. Infraestrutura externa (fora do repositório)

| Item | Dependências | Risco | Complexidade |
|------|:--:|:--:|:--:|
| Nome do repositório GitHub | Clones locais, CI, possíveis webhooks/integrações externas | Alto | 🔴 Planejamento — já deferido conscientemente em ADR-006/ADR-008 |
| URL de produção Render (`irflow-backend.onrender.com`) | CORS, DNS/bookmarks, qualquer client externo (MercadoPhone?) | Alto | 🔴 Planejamento — idem |
| URL de produção Vercel (`assistencia-system.vercel.app`) | CORS, DNS/bookmarks | Alto | 🔴 Planejamento — idem |
| `assets/ir_flow.ico` + `build_exe.ps1` + `build_setup.ps1` + `installer.iss` | 0 arquivos ativos referenciam esses scripts (nenhum CI/doc aponta para eles) | Baixo | 🟠 Coordenação — não é rename, é decisão de manter/remover (candidato a `AUDIT_REPOSITORY.md`, não Fase 4) |

---

## 5. Frontend — branding e testes

| Item | Dependências | Risco | Complexidade |
|------|:--:|:--:|:--:|
| `frontend/README.md`, `frontend/src/api/client.js`, `frontend/src/index.css` (comentários/strings) | Nenhuma — são strings/comentários, não afetam build | Baixo | 🟢 Mecânico |
| `frontend/tests/e2e/app.spec.js` (`ADMIN_PASS = "irflow@2024"`) | 1 arquivo de teste E2E | Baixo | 🟢 Mecânico — confirmar que não é senha real de nenhum ambiente antes de trocar |
| `frontend/dist/` desatualizado (título ainda "IR Flow") | Servido publicamente se a Vercel usar o `dist/` commitado em vez de buildar do fonte | Médio | 🟢 Mecânico — só rodar `npm run build` e recommitar; **confirmar antes se a Vercel builda do fonte ou serve o dist commitado** (se for o segundo caso, isso é um achado de produção, não só de repositório) |

---

## Ordem sugerida para a Fase 4 (do menor para o maior risco)

1. **Limpeza mecânica sem dependências** — 3 entradas mortas em `pyproject.toml` (seção 2)
2. **Módulos 🟢 com 1-4 dependências** — os 18 módulos marcados 🟢 acima, em lotes pequenos, cada
   lote seguido de um commit único de atualização de imports em `app.py`
3. **Módulos 🟠 (hub)** — `irflow_core.py`, `irflow_os.py` — depois que os módulos que dependem deles
   já estiverem estáveis no novo padrão, para reduzir o número de arquivos em trânsito simultaneamente
4. **`irflow_blueprints_api.py`** (🔴, sozinho) — decidir antes se a quebra em módulos menores (TD-01)
   acontece antes ou depois; se depois, este é o último módulo `.py` a renomear
5. **Frontend branding + rebuild de `dist/`** — pode acontecer em paralelo a qualquer ponto acima,
   sem dependência de ordem
6. **`IR_FLOW_*` (env vars) + infraestrutura externa (repo/domínios)** — **não entram nesta sprint**
   como execução; ficam registrados como itens que exigem janela de manutenção dedicada, decisão já
   alinhada com ADR-006/ADR-008. Revisitar como iniciativa própria, não como parte dos commits mecânicos.

---

## Próximo passo

`AUDIT_DOCUMENTATION.md` — referências a nomes legados na documentação que não são registro histórico
deliberado (a maioria já foi identificada na seção 4 de `AUDIT_LEGACY.md`; este documento confirma que
não sobrou nada fora do que já foi categorizado e decide, item a item, o que precisa de edição de texto
versus o que fica como está).
