/**
 * Filtros de inclusão do catálogo — BR-074 e BR-075.
 * Ver docs/product/research/DISCOVERY_LISTA_PRECOS_PUBLICA.md §4.1 e §4.2.
 */
import type { AvailabilityLookup, RawInventoryItem } from "./types.js";

/** tipoProdutoId dos aparelhos Apple serializados que entram (BR-074). AirPods/Pencil ficam de fora (QA-39). */
export const TIPOS_APARELHO = new Set(["3719", "4959", "4960", "4961"]); // IPHONE / MACBOOK / APPLE WATCH / IPAD

/** BR-074 — só aparelho serializado, nunca acessório/peça/serviço/brinde. */
export function isAparelho(item: RawInventoryItem): boolean {
  if (item.snAcessorio === 1) return false;
  if (item.snPeca === 1) return false;
  if (item.snServico === 1) return false;
  return TIPOS_APARELHO.has(String(item.tipoProdutoId));
}

/**
 * BR-075 — só unidades cuja situação de estoque tem snExibirPdv === 1
 * ("Disponível para venda" e "Disponível com detalhe"). Resolve os ids a partir
 * do lookup vivo, sem hardcode (a loja pode renomear/recriar situações).
 */
export function idsVisiveisNaVitrine(availability: AvailabilityLookup[]): Set<number> {
  return new Set(
    availability.filter((a) => a.snExibirPdv === 1).map((a) => a.id),
  );
}

export function isDisponivel(
  item: RawInventoryItem,
  idsVisiveis: Set<number>,
): boolean {
  return item.produtoDisponibilidadeId != null && idsVisiveis.has(item.produtoDisponibilidadeId);
}

/** id da situação "com detalhe" (avaria estética) — para a etiqueta na UI. */
export function idComDetalhe(availability: AvailabilityLookup[]): number | null {
  const m = availability.find((a) => /detalhe/i.test(a.name));
  return m ? m.id : null;
}

/** Aplica os dois filtros. */
export function filtrarAparelhosDisponiveis(
  itens: RawInventoryItem[],
  availability: AvailabilityLookup[],
): RawInventoryItem[] {
  const idsVisiveis = idsVisiveisNaVitrine(availability);
  return itens.filter((it) => isAparelho(it) && isDisponivel(it, idsVisiveis));
}
