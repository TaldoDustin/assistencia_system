/**
 * Ordenação da lista exibida (pedido do CTO, 2026-09-04):
 *   tipo (iPhone → iPad → MacBook → Apple Watch)
 *   → modelo em ordem natural (IPHONE 9 < IPHONE 11 < IPHONE 11 PRO < IPHONE 11 PRO MAX < …)
 *   → estado (Lacrado/Novo antes de Seminovo; "com detalhe" por último)
 *   → preço crescente (sem preço por último)
 *
 * Como o front agrupa por `modelo + estado` preservando a ordem de inserção, ordenar
 * a lista plana assim já faz os grupos saírem na sequência certa.
 */
import type { EstoqueItem } from "./types.js";

const TIPO_ORDEM: Record<string, number> = {
  IPHONE: 0,
  IPAD: 1,
  MACBOOK: 2,
  "APPLE WATCH": 3,
};

const ESTADO_ORDEM: Record<string, number> = {
  Lacrado: 0,
  Novo: 1,
  "Open box": 2,
  CPO: 3,
  Seminovo: 4,
  "Seminovo (com detalhe)": 5,
};

function rankTipo(t: string): number {
  return TIPO_ORDEM[t.trim().toUpperCase()] ?? 90;
}

function rankEstado(e: string): number {
  if (e in ESTADO_ORDEM) return ESTADO_ORDEM[e]!;
  return /com detalhe/i.test(e) ? 89 : 88;
}

const colador = new Intl.Collator("pt-BR", { numeric: true, sensitivity: "base" });

export function compararItens(a: EstoqueItem, b: EstoqueItem): number {
  const t = rankTipo(a.tipoProduto) - rankTipo(b.tipoProduto);
  if (t) return t;

  const m = colador.compare(a.modelo, b.modelo);
  if (m) return m;

  const e = rankEstado(a.estado) - rankEstado(b.estado);
  if (e) return e;

  const pa = a.precoVenda ?? Number.POSITIVE_INFINITY;
  const pb = b.precoVenda ?? Number.POSITIVE_INFINITY;
  if (pa !== pb) return pa - pb;

  return a.id - b.id;
}
