/**
 * Monta os dois snapshots (Geral / Estoque) a partir do inventário cru do MercadoPhone.
 *
 * Regra de ouro (BR-070/071): os objetos de saída são construídos campo a campo
 * por ALLOWLIST. Nenhum campo cru é espalhado (`...item`) para dentro do snapshot —
 * é assim que garantimos que custo, fornecedor, nome de cliente, IMEI completo e
 * campos fiscais nunca vazam para a área Geral nem para o navegador.
 *
 * Ver docs/engineering/plans/PLAN-lista-aparelhos-disponiveis.md §"Job de sync".
 */
import { dedup, imeiReal } from "./dedup.js";
import { filtrarAparelhosDisponiveis, idComDetalhe } from "./filter.js";
import { calcularMargem, diasEmEstoque, rotuloEstado } from "./labels.js";
import { compararItens } from "./ordenar.js";
import { calcularIdsCurtos } from "./short-id.js";
import type {
  AvailabilityLookup,
  EstoqueItem,
  GeralItem,
  RawInventoryItem,
  Snapshot,
  StorageSizeLookup,
} from "./types.js";

export interface BuildInput {
  itens: RawInventoryItem[];
  availability: AvailabilityLookup[];
  storageSizes?: StorageSizeLookup[];
  /** Data de referência para "dias em estoque" e `geradoEm` (testes fixam). */
  agora?: Date;
}

export interface BuildOutput {
  geral: Snapshot<GeralItem>;
  estoque: Snapshot<EstoqueItem>;
  /** Diagnóstico para `sync:last` — nunca exposto ao cliente. */
  diagnostico: {
    totalCru: number;
    aposFiltro: number;
    aposDedup: number;
    semPreco: number;
  };
}

function normalizarObs(obs: unknown): string | undefined {
  if (typeof obs !== "string") return undefined;
  const t = obs.replace(/\s+/g, " ").trim();
  return t || undefined;
}

function armazenamento(
  item: RawInventoryItem,
  storageById: Map<number, string>,
): string | null {
  if (item.gbDescricao && item.gbDescricao.trim() && item.gbDescricao.trim() !== "-") {
    return item.gbDescricao.trim();
  }
  if (item.gbId != null) {
    const s = storageById.get(item.gbId);
    if (s && s !== "-") return s;
  }
  return null;
}

export function buildSnapshots(input: BuildInput): BuildOutput {
  const agora = input.agora ?? new Date();
  const storageById = new Map((input.storageSizes ?? []).map((s) => [s.id, s.size]));
  const comDetalheId = idComDetalhe(input.availability);

  const filtrados = filtrarAparelhosDisponiveis(input.itens, input.availability);
  const unicos = dedup(filtrados);

  const idsCurtos = calcularIdsCurtos(
    unicos.map((it) => ({ imei: imeiReal(it.imei), id: it.id })),
  );

  let semPreco = 0;

  const estoqueItens: EstoqueItem[] = unicos.map((it, i) => {
    const comDetalhe = comDetalheId != null && it.produtoDisponibilidadeId === comDetalheId;
    const precoVenda = typeof it.valorVenda === "number" && it.valorVenda > 0 ? it.valorVenda : null;
    if (precoVenda == null) semPreco++;
    const custo = typeof it.valorCusto === "number" && it.valorCusto > 0 ? it.valorCusto : null;
    const { margem, margemPct } = calcularMargem(precoVenda, custo);

    return {
      id: it.id,
      idCurto: idsCurtos[i]!,
      tipoProduto: it.tipoProdutoDescricao?.trim() || String(it.tipoProdutoId ?? ""),
      modelo: it.aparelhoDescricao?.trim() || "—",
      armazenamento: armazenamento(it, storageById),
      cor: it.corDescricao?.trim() || null,
      estado: rotuloEstado(it.estadoProdutoDescricao, comDetalhe),
      saudeBateria: typeof it.saudeBateria === "number" ? it.saudeBateria : null,
      comDetalhe,
      precoVenda,
      dataEntrada: it.dataEntrada ?? null,
      custo,
      margem,
      margemPct,
      diasEmEstoque: diasEmEstoque(it.dataEntrada, agora),
      obsMercadoPhone: normalizarObs(it.obs),
    };
  });

  estoqueItens.sort(compararItens);

  // A Geral é o subconjunto de campos do Estoque — sem custo/margem/dias.
  const geralItens: GeralItem[] = estoqueItens.map((e) => ({
    id: e.id,
    idCurto: e.idCurto,
    tipoProduto: e.tipoProduto,
    modelo: e.modelo,
    armazenamento: e.armazenamento,
    cor: e.cor,
    estado: e.estado,
    saudeBateria: e.saudeBateria,
    comDetalhe: e.comDetalhe,
    precoVenda: e.precoVenda,
    dataEntrada: e.dataEntrada,
  }));

  const geradoEm = agora.toISOString();
  return {
    geral: { geradoEm, total: geralItens.length, itens: geralItens },
    estoque: { geradoEm, total: estoqueItens.length, itens: estoqueItens },
    diagnostico: {
      totalCru: input.itens.length,
      aposFiltro: filtrados.length,
      aposDedup: unicos.length,
      semPreco,
    },
  };
}

/** PII e campos fiscais — proibidos nos DOIS snapshots (BR-070/071). */
export const CAMPOS_PII = [
  "fornecedorNome",
  "fornecedorId",
  "clienteNome",
  "clienteId",
  "obs",
  "observacaoCatalogo",
  "ncm",
  "cfopInt",
  "cfopEst",
  "cfopInterestadualEntrada",
  "cfopEstadualEntrada",
  "cst",
  "cest",
  "codEan",
  "imei",
  "imei2",
  "serialNumber",
  "descricao",
] as const;

/** Além dos de PII, a área Geral também não pode ter custo/margem (BR-070). */
export const CAMPOS_PROIBIDOS_GERAL = [
  ...CAMPOS_PII,
  "valorCusto",
  "custo",
  "margem",
  "margemPct",
  "diasEmEstoque",
  "valorPrazo",
] as const;
