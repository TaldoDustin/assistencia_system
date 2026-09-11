/**
 * Ordenação da lista exibida:
 *   tipo (iPhone → iPad → MacBook → Apple Watch) — pedido do CTO, 2026-09-04
 *   → modelo em ordem natural (IPHONE 9 < IPHONE 11 < IPHONE 11 PRO < IPHONE 11 PRO MAX < …)
 *   → estado (Lacrado/Novo antes de Seminovo; "com detalhe" por último)
 *   → GB crescente → cor (alfabética) → saúde de bateria decrescente (maior % primeiro)
 *     — pedido do CTO, 2026-09-11, substitui o antigo tiebreak por preço.
 *   → (só na área Estoque) dias parado em estoque decrescente (mais parado primeiro)
 *
 * Como o front agrupa por `modelo + estado` preservando a ordem de inserção, ordenar
 * a lista plana assim já faz os grupos saírem na sequência certa. `compararItens` é usado
 * nas duas áreas (Geral e Estoque); `compararItensEstoque` só na área Estoque, que ordena
 * de forma diferente da Geral por isso precisa de arrays ordenados separadamente (ver
 * `snapshot.ts`) em vez de a Geral derivar da mesma ordenação da Estoque.
 */
import type { EstoqueItem, GeralItem } from "./types.js";

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

/** GB extraído do texto de armazenamento ("128GB" -> 128); sem número reconhecível -> por último. */
function rankArmazenamento(a: string | null): number {
  if (!a) return Number.POSITIVE_INFINITY;
  const m = a.match(/\d+/);
  return m ? parseInt(m[0], 10) : Number.POSITIVE_INFINITY;
}

const colador = new Intl.Collator("pt-BR", { numeric: true, sensitivity: "base" });

/** tipo → modelo → estado → GB → cor → bateria (sem o desempate final por id). */
function compararBase(a: GeralItem, b: GeralItem): number {
  const t = rankTipo(a.tipoProduto) - rankTipo(b.tipoProduto);
  if (t) return t;

  const m = colador.compare(a.modelo, b.modelo);
  if (m) return m;

  const e = rankEstado(a.estado) - rankEstado(b.estado);
  if (e) return e;

  const g = rankArmazenamento(a.armazenamento) - rankArmazenamento(b.armazenamento);
  if (g) return g;

  const c = colador.compare(a.cor ?? "", b.cor ?? "");
  if (c) return c;

  const sa = a.saudeBateria ?? Number.NEGATIVE_INFINITY;
  const sb = b.saudeBateria ?? Number.NEGATIVE_INFINITY;
  if (sa !== sb) return sb - sa; // maior % primeiro

  return 0;
}

/** Ordem usada na área Geral (e como base da área Estoque). */
export function compararItens(a: GeralItem, b: GeralItem): number {
  const base = compararBase(a, b);
  if (base) return base;
  return a.id - b.id;
}

/** Ordem usada na área Estoque: igual à Geral, com "dias parado" como desempate extra. */
export function compararItensEstoque(a: EstoqueItem, b: EstoqueItem): number {
  const base = compararBase(a, b);
  if (base) return base;

  const da = a.diasEmEstoque ?? -1;
  const db = b.diasEmEstoque ?? -1;
  if (da !== db) return db - da; // mais dias parado primeiro

  return a.id - b.id;
}
