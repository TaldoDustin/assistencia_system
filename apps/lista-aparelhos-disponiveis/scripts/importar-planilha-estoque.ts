/**
 * Import pontual (rodar UMA VEZ): mescla a planilha Excel do organizador (Estoque 1 /
 * Estoque 2 / Estela + notas de condição) no estado atual da ferramenta
 * "Lista de Aparelhos Disponíveis". Fora de `tsconfig.json` (`include`) — não entra no
 * typecheck/CI do app, é tooling de migração pontual, não parte do produto.
 *
 * Entrada: JSON já extraído da planilha (script Python auxiliar, fora do repo — a
 * planilha original fica no computador do operador, nunca é commitada), formato:
 *   [{ status: "ESTOQUE"|"ESTOQUE 2"|"STELLA", modelo, cor, imei, detalhe }]
 *
 * Match: por IMEI completo (14+ dígitos) contra o inventário AO VIVO do MercadoPhone
 * (o snapshot salvo no Redis nunca tem IMEI — BR-070/071 — por isso é preciso buscar
 * de novo na fonte). Regras de escrita:
 *   - estoqueLocal: "ESTOQUE 2" -> 2; "ESTOQUE"/"STELLA" -> 1 (default, BR-081).
 *   - detalhe: só grava se a unidade AINDA NÃO tem nota na ferramenta (nunca sobrescreve).
 *   - Estela: reserva a unidade para a vendedora "Estela" (BR-082) SE ainda não tiver
 *     nenhuma reserva (nunca sobrescreve reserva humana; idempotente se já for Estela).
 *
 * Uso:
 *   npx tsx importar-planilha-estoque.ts <planilha.json>              (dry-run, não escreve nada)
 *   npx tsx importar-planilha-estoque.ts <planilha.json> --apply      (escreve de verdade)
 *
 * Variáveis de ambiente necessárias (via --env-file=.env.local, nunca commitado):
 *   MERCADOPHONE_API_KEY, e (KV_REST_API_URL + KV_REST_API_TOKEN) ou
 *   (UPSTASH_REDIS_REST_URL + UPSTASH_REDIS_REST_TOKEN) para escrever no Redis real.
 *   Sem credencial Redis, cai no MemoryStore (inútil para um import real — só serve
 *   para validar a lógica em dry-run sem tocar em produção).
 */
import { readFileSync } from "node:fs";
import { imeiReal } from "../lib/dedup.js";
import { VENDEDOR_ESTELA } from "../lib/estela.js";
import { MercadoPhoneClient } from "../lib/mercadophone.js";
import { getStore } from "../lib/store.js";
import type { EstoqueLocal } from "../lib/types.js";

interface LinhaPlanilha {
  status: "ESTOQUE" | "ESTOQUE 2" | "STELLA";
  modelo: string;
  cor: string;
  imei: string;
  detalhe: string;
}

async function main(): Promise<void> {
  const apply = process.argv.includes("--apply");
  const jsonPath = process.argv[2];
  if (!jsonPath || jsonPath.startsWith("--")) {
    console.error("uso: npx tsx importar-planilha-estoque.ts <caminho.json> [--apply]");
    process.exit(1);
  }

  const linhas: LinhaPlanilha[] = JSON.parse(readFileSync(jsonPath, "utf8"));
  console.log(`Planilha: ${linhas.length} linhas carregadas.`);

  const apiKey = process.env.MERCADOPHONE_API_KEY ?? "";
  if (!apiKey) {
    console.error("MERCADOPHONE_API_KEY ausente (--env-file=.env.local) — não dá para buscar o inventário ao vivo.");
    process.exit(1);
  }

  console.log("Buscando inventário ao vivo do MercadoPhone (para resolver IMEI -> id)...");
  const mp = new MercadoPhoneClient({ apiKey });
  const itens = await mp.listarInventarioCompleto();
  console.log(`Inventário ao vivo: ${itens.length} itens.`);

  const porImei = new Map<string, number>();
  for (const it of itens) {
    const im = imeiReal(it.imei);
    if (im) porImei.set(im, it.id);
  }

  const store = await getStore();
  console.log(`Store: ${store.constructor.name}${apply ? "" : " (DRY-RUN — nada será escrito)"}`);

  const detalhesAtuais = await store.getDetalhes();
  const reservasAtuais = await store.getReservas();

  let encontrados = 0;
  const naoEncontrados: LinhaPlanilha[] = [];
  let locaisAAplicar = 0;
  let detalhesAPreencher = 0;
  let detalhesJaExistiam = 0;
  let estelaAReservar = 0;
  let estelaJaReservado = 0;
  let estelaConflitoVendedorHumano = 0;

  for (const linha of linhas) {
    const id = porImei.get(linha.imei);
    if (id == null) {
      naoEncontrados.push(linha);
      continue;
    }
    encontrados++;

    const local: EstoqueLocal = linha.status === "ESTOQUE 2" ? 2 : 1;
    locaisAAplicar++;
    if (apply) await store.setEstoqueLocal(id, local);

    if (linha.detalhe) {
      if (detalhesAtuais[String(id)]) {
        detalhesJaExistiam++;
      } else {
        detalhesAPreencher++;
        if (apply) await store.setDetalhe(id, linha.detalhe);
      }
    }

    if (linha.status === "STELLA") {
      const reservaAtual = reservasAtuais[String(id)];
      if (!reservaAtual) {
        estelaAReservar++;
        if (apply) await store.reservar(id, { vendedor: VENDEDOR_ESTELA, reservadoEm: new Date().toISOString() });
      } else if (reservaAtual.vendedor === VENDEDOR_ESTELA) {
        estelaJaReservado++;
      } else {
        estelaConflitoVendedorHumano++;
        console.warn(
          `  ! id ${id} (${linha.modelo}) está marcado Estela na planilha mas já reservado ` +
            `para "${reservaAtual.vendedor}" na ferramenta — NÃO sobrescrito.`,
        );
      }
    }
  }

  console.log("\n=== Relatório ===");
  console.log(`Encontrados no MercadoPhone: ${encontrados} / ${linhas.length}`);
  console.log(`Não encontrados (provavelmente já vendidos/removidos): ${naoEncontrados.length}`);
  console.log(`Localização (Estoque 1/2) aplicada: ${locaisAAplicar}`);
  console.log(`Detalhe preenchido (estava vazio): ${detalhesAPreencher}`);
  console.log(`Detalhe NÃO sobrescrito (já existia): ${detalhesJaExistiam}`);
  console.log(`Estela — reservado agora: ${estelaAReservar}`);
  console.log(`Estela — já estava reservado p/ Estela: ${estelaJaReservado}`);
  console.log(`Estela — conflito com reserva humana (não mexido): ${estelaConflitoVendedorHumano}`);

  if (naoEncontrados.length) {
    console.log("\nNão encontrados (IMEI / modelo):");
    for (const n of naoEncontrados) console.log(`  ${n.imei}  ${n.modelo} ${n.cor} (${n.status})`);
  }

  if (!apply) {
    console.log("\nDRY-RUN — nada foi escrito. Rode de novo com --apply para gravar de verdade.");
  } else {
    console.log("\nGravado no store real.");
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
