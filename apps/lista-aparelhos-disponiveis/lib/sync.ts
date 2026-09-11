/**
 * Job de sincronização: MercadoPhone → 2 snapshots no store.
 * Chamado por /api/sync (cron a cada ~20 min — ADR-013 Q6).
 *
 * Se a API do MercadoPhone falhar, o snapshot anterior é PRESERVADO
 * (nunca sobrescrito por lista vazia) e o erro fica em sync:last.
 */
import { calcularAjustesEstela, VENDEDOR_ESTELA } from "./estela.js";
import { MercadoPhoneClient } from "./mercadophone.js";
import { buildSnapshots } from "./snapshot.js";
import type { Store } from "./store.js";
import type { EstoqueItem } from "./types.js";

export interface SyncResult {
  ok: boolean;
  erro?: string;
  diagnostico?: unknown;
}

/** Aplica os ajustes de reserva automática da Estela (BR-082) a partir do snapshot recém-sincronizado. */
async function aplicarAjustesEstela(store: Store, itens: EstoqueItem[], agora: Date): Promise<void> {
  const reservas = await store.getReservas();
  const { paraReservar, paraLiberar } = calcularAjustesEstela(itens, reservas);
  for (const id of paraReservar) {
    await store.reservar(id, { vendedor: VENDEDOR_ESTELA, reservadoEm: agora.toISOString() });
  }
  for (const id of paraLiberar) {
    await store.desreservar(id);
  }
}

export async function rodarSync(store: Store, apiKey: string, agora = new Date()): Promise<SyncResult> {
  try {
    const mp = new MercadoPhoneClient({ apiKey });
    const [itens, availability, storageSizes] = await Promise.all([
      mp.listarInventarioCompleto(),
      mp.listarAvailability(),
      mp.listarStorageSizes(),
    ]);
    if (itens.length === 0) throw new Error("inventário vazio — não sobrescrevendo snapshot");

    const { geral, estoque, diagnostico } = buildSnapshots({ itens, availability, storageSizes, agora });
    await store.setSnapshots(geral, estoque);
    await aplicarAjustesEstela(store, estoque.itens, agora);
    const status = { em: agora.toISOString(), ok: true, diagnostico };
    await store.setSyncStatus(status);
    return { ok: true, diagnostico };
  } catch (e) {
    const erro = e instanceof Error ? e.message : String(e);
    await store.setSyncStatus({ em: agora.toISOString(), ok: false, erro });
    return { ok: false, erro };
  }
}
