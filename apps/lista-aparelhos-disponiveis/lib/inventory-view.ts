/**
 * Monta a resposta de /api/inventory conforme o papel — BR-071/076.
 *
 * - geral:   snapshot Geral MENOS as unidades reservadas (elas "somem" da Geral).
 * - estoque: snapshot Estoque com as reservadas marcadas (`reservado`), mais
 *            separadas em `disponiveis` / `reservados` para a UI.
 */
import type { Reserva, Store } from "./store.js";
import type { EstoqueItem, GeralItem, Papel, Snapshot } from "./types.js";

export interface RespostaGeral {
  papel: "geral";
  geradoEm: string;
  itens: GeralItem[];
}

export interface RespostaEstoque {
  papel: "estoque";
  geradoEm: string;
  disponiveis: EstoqueItem[];
  reservados: EstoqueItem[];
}

export async function montarResposta(
  store: Store,
  papel: Papel,
): Promise<RespostaGeral | RespostaEstoque | null> {
  const reservas = await store.getReservas();
  const reservado = (id: number): Reserva | undefined => reservas[String(id)];

  if (papel === "geral") {
    const snap = await store.getSnapshotGeral();
    if (!snap) return null;
    return {
      papel: "geral",
      geradoEm: snap.geradoEm,
      itens: snap.itens.filter((i) => !reservado(i.id)),
    };
  }

  const snap: Snapshot<EstoqueItem> | null = await store.getSnapshotEstoque();
  if (!snap) return null;
  const disponiveis: EstoqueItem[] = [];
  const reservados: EstoqueItem[] = [];
  for (const item of snap.itens) {
    const r = reservado(item.id);
    if (r) reservados.push({ ...item, reservado: r });
    else disponiveis.push(item);
  }
  return { papel: "estoque", geradoEm: snap.geradoEm, disponiveis, reservados };
}
