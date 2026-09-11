/**
 * Ajustes automáticos da reserva "Estela" — BR-082.
 *
 * Toda unidade cuja situação de estoque é "Disponível com detalhe" (`comDetalhe`)
 * é reservada automaticamente para a vendedora Estela durante o sync — reaproveita
 * o mecanismo de reserva já existente (BR-076/077) para sumir da área Geral, sem
 * filtro novo. Se a unidade deixar de ter essa situação, a reserva Estela é
 * liberada automaticamente. Nunca mexe numa reserva feita por um vendedor humano.
 */
import type { Reserva } from "./store.js";
import type { EstoqueItem } from "./types.js";

export const VENDEDOR_ESTELA = "Estela";

export interface AjustesEstela {
  paraReservar: number[];
  paraLiberar: number[];
}

export function calcularAjustesEstela(
  itens: EstoqueItem[],
  reservasAtuais: Record<string, Reserva>,
): AjustesEstela {
  const comDetalheIds = new Set(itens.filter((i) => i.comDetalhe).map((i) => i.id));

  const paraReservar = [...comDetalheIds].filter((id) => !reservasAtuais[String(id)]);

  const paraLiberar = Object.entries(reservasAtuais)
    .filter(([id, r]) => r.vendedor === VENDEDOR_ESTELA && !comDetalheIds.has(Number(id)))
    .map(([id]) => Number(id));

  return { paraReservar, paraLiberar };
}
