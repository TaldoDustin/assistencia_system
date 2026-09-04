/**
 * Job de sincronização: MercadoPhone → 2 snapshots no store.
 * Chamado por /api/sync (cron a cada ~20 min — ADR-013 Q6).
 *
 * Se a API do MercadoPhone falhar, o snapshot anterior é PRESERVADO
 * (nunca sobrescrito por lista vazia) e o erro fica em sync:last.
 */
import { MercadoPhoneClient } from "./mercadophone.js";
import { buildSnapshots } from "./snapshot.js";
import type { Store } from "./store.js";

export interface SyncResult {
  ok: boolean;
  erro?: string;
  diagnostico?: unknown;
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
    const status = { em: agora.toISOString(), ok: true, diagnostico };
    await store.setSyncStatus(status);
    return { ok: true, diagnostico };
  } catch (e) {
    const erro = e instanceof Error ? e.message : String(e);
    await store.setSyncStatus({ em: agora.toISOString(), ok: false, erro });
    return { ok: false, erro };
  }
}
