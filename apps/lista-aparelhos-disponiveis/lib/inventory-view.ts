/**
 * Monta a resposta de /api/inventory conforme o papel — BR-071/076/081.
 *
 * - geral:   snapshot Geral MENOS as unidades reservadas E só as do Estoque 1
 *            (BR-081 — Estoque 2 nunca aparece na área pública).
 * - estoque: snapshot Estoque com cada unidade marcada com `estoqueLocal` e,
 *            quando reservada, `reservado` — dividido em `estoque1` / `estoque2`
 *            (por localização, reservadas inclusive) e `disponiveis` (união dos
 *            dois locais, só as não reservadas).
 */
import type { Reserva, Store } from "./store.js";
import type { EstoqueItem, EstoqueLocal, GeralItem, Papel, Snapshot } from "./types.js";

export interface RespostaGeral {
  papel: "geral";
  geradoEm: string;
  itens: GeralItem[];
}

export interface RespostaEstoque {
  papel: "estoque";
  geradoEm: string;
  estoque1: EstoqueItem[];
  estoque2: EstoqueItem[];
  disponiveis: EstoqueItem[];
}

export async function montarResposta(
  store: Store,
  papel: Papel,
): Promise<RespostaGeral | RespostaEstoque | null> {
  const [reservas, detalhes, locais] = await Promise.all([
    store.getReservas(),
    store.getDetalhes(),
    store.getEstoqueLocais(),
  ]);
  const reservado = (id: number): Reserva | undefined => reservas[String(id)];
  const localDe = (id: number): EstoqueLocal => locais[String(id)] ?? 1;
  const detalheDe = <T extends { id: number }>(item: T): T => {
    const d = detalhes[String(item.id)];
    return d ? { ...item, detalhe: d } : item;
  };

  if (papel === "geral") {
    const snap = await store.getSnapshotGeral();
    if (!snap) return null;
    return {
      papel: "geral",
      geradoEm: snap.geradoEm,
      itens: snap.itens.filter((i) => !reservado(i.id) && localDe(i.id) === 1).map(detalheDe),
    };
  }

  const snap: Snapshot<EstoqueItem> | null = await store.getSnapshotEstoque();
  if (!snap) return null;
  const estoque1: EstoqueItem[] = [];
  const estoque2: EstoqueItem[] = [];
  const disponiveis: EstoqueItem[] = [];
  for (const base of snap.itens) {
    const item = detalheDe(base);
    const r = reservado(item.id);
    const local = localDe(item.id);
    const completo: EstoqueItem = { ...item, estoqueLocal: local, ...(r ? { reservado: r } : {}) };
    (local === 1 ? estoque1 : estoque2).push(completo);
    if (!r) disponiveis.push(completo);
  }
  return { papel: "estoque", geradoEm: snap.geradoEm, estoque1, estoque2, disponiveis };
}
