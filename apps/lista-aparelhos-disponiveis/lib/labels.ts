/**
 * Rótulos de estado e cálculo de margem — BR-070 / QA-31.
 */

const ESTADO: Record<string, string> = {
  LACRADO: "Lacrado",
  SEMINOVO: "Seminovo",
  "OPEN BOX": "Open box",
  NOVO: "Novo",
  CPO: "CPO",
};

/** `estadoProdutoDescricao` cru + flag "com detalhe" → rótulo exibido. */
export function rotuloEstado(estadoCru: string | null, comDetalhe: boolean): string {
  const base = estadoCru ? ESTADO[estadoCru.trim().toUpperCase()] ?? capitalizar(estadoCru) : "Não informado";
  if (comDetalhe && /seminovo/i.test(base)) return "Seminovo (com detalhe)";
  if (comDetalhe) return `${base} (com detalhe)`;
  return base;
}

function capitalizar(s: string): string {
  const t = s.trim().toLowerCase();
  return t ? t[0]!.toUpperCase() + t.slice(1) : t;
}

export interface Margem {
  margem: number | null;
  margemPct: number | null;
}

/** Margem absoluta e percentual. custo 0/null ou venda null → margem indefinida. */
export function calcularMargem(valorVenda: number | null, valorCusto: number | null): Margem {
  if (valorVenda == null || valorCusto == null || valorCusto <= 0) {
    return { margem: null, margemPct: null };
  }
  const margem = Math.round((valorVenda - valorCusto) * 100) / 100;
  const margemPct = Math.round((margem / valorCusto) * 1000) / 10;
  return { margem, margemPct };
}

/** Dias entre `dataEntrada` (YYYY-MM-DD) e a data de referência (default: hoje). */
export function diasEmEstoque(dataEntrada: string | null, ref: Date = new Date()): number | null {
  if (!dataEntrada) return null;
  const t = Date.parse(dataEntrada.length <= 10 ? `${dataEntrada}T00:00:00Z` : dataEntrada);
  if (Number.isNaN(t)) return null;
  const dias = Math.floor((ref.getTime() - t) / 86_400_000);
  return dias < 0 ? 0 : dias;
}
