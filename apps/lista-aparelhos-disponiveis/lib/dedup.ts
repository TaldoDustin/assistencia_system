/**
 * Deduplicação por IMEI completo — BR-072.
 * Ver docs/product/research/DISCOVERY_LISTA_PRECOS_PUBLICA.md.
 */
import type { RawInventoryItem } from "./types.js";

/** IMEI "real" = 14+ dígitos. "0", "", null e strings curtas contam como ausente. */
export function imeiReal(imei: string | null | undefined): string | null {
  if (!imei) return null;
  const digs = String(imei).replace(/\D/g, "");
  if (digs.length < 14) return null;
  if (/^0+$/.test(digs)) return null;
  return digs;
}

/** Chave de dedup de uma unidade: IMEI real, ou `id:<n>` quando não há IMEI. */
export function chaveDedup(item: RawInventoryItem): string {
  const im = imeiReal(item.imei);
  return im ? `imei:${im}` : `id:${item.id}`;
}

function ts(item: RawInventoryItem): number {
  const d = item.dataModificacao ? Date.parse(item.dataModificacao.replace(" ", "T")) : NaN;
  return Number.isNaN(d) ? 0 : d;
}

/**
 * Colapsa unidades com a mesma chave. Em empate, vence a de `dataModificacao`
 * mais recente (BR-072). Ordem de entrada preservada para as sobreviventes.
 */
export function dedup(itens: RawInventoryItem[]): RawInventoryItem[] {
  const escolhido = new Map<string, RawInventoryItem>();
  for (const it of itens) {
    const k = chaveDedup(it);
    const atual = escolhido.get(k);
    if (!atual || ts(it) >= ts(atual)) escolhido.set(k, it);
  }
  const vivos = new Set(escolhido.values());
  return itens.filter((it) => vivos.has(it));
}
