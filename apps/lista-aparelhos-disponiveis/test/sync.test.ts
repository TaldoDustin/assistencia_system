import { describe, expect, it } from "vitest";
import { rodarSync } from "../lib/sync.js";
import { buildSnapshots } from "../lib/snapshot.js";
import { MemoryStore } from "../lib/store.js";
import { availability, inventarioCru, storageSizes } from "./fixtures.js";

/** fetch falso que devolve as fixtures por rota. */
function fakeFetch(map: Record<string, unknown>, opts: { falharInventory?: boolean } = {}): typeof fetch {
  return (async (url: string) => {
    if (opts.falharInventory && url.includes("/inventory")) {
      return { ok: false, status: 502, json: async () => ({}) } as Response;
    }
    for (const [frag, data] of Object.entries(map)) {
      if (url.includes(frag)) {
        return { ok: true, status: 200, json: async () => data } as Response;
      }
    }
    return { ok: false, status: 404, json: async () => ({}) } as Response;
  }) as unknown as typeof fetch;
}

const MAPA = {
  "/inventory": { total: inventarioCru.length, items: inventarioCru, page: 1, limit: 300 },
  "/catalog/availability": { total: availability.length, items: availability, page: 1, limit: 100 },
  "/catalog/storage-sizes": { total: storageSizes.length, items: storageSizes, page: 1, limit: 100 },
};

// injeta o fetch falso globalmente durante o teste
function comFetch(f: typeof fetch, fn: () => Promise<void>) {
  const orig = globalThis.fetch;
  globalThis.fetch = f;
  return fn().finally(() => { globalThis.fetch = orig; });
}

describe("rodarSync", () => {
  it("popula os 2 snapshots a partir da API", () =>
    comFetch(fakeFetch(MAPA), async () => {
      const store = new MemoryStore();
      const r = await rodarSync(store, "chave-fake");
      expect(r.ok).toBe(true);
      expect((await store.getSnapshotGeral())?.total).toBeGreaterThan(0);
      expect((await store.getSnapshotEstoque())?.total).toBeGreaterThan(0);
      expect((await store.getSyncStatus())?.ok).toBe(true);
    }));

  it("API falhando NÃO sobrescreve o snapshot anterior", () =>
    comFetch(fakeFetch(MAPA, { falharInventory: true }), async () => {
      const store = new MemoryStore();
      const { geral, estoque } = buildSnapshots({ itens: inventarioCru, availability, storageSizes });
      await store.setSnapshots(geral, estoque);
      const antes = (await store.getSnapshotGeral())?.total;

      const r = await rodarSync(store, "chave-fake");
      expect(r.ok).toBe(false);
      expect((await store.getSnapshotGeral())?.total).toBe(antes);
      expect((await store.getSyncStatus())?.ok).toBe(false);
      expect((await store.getSyncStatus())?.erro).toBeTruthy();
    }));
});
