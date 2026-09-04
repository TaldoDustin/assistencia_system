import { describe, expect, it } from "vitest";
import { MercadoPhoneClient } from "../lib/mercadophone.js";
import type { RawInventoryItem } from "../lib/types.js";

const item = (id: number): RawInventoryItem => ({ id } as RawInventoryItem);

/** fetch falso que devolve páginas pré-definidas por número. */
function fakePaginado(paginas: Array<{ items: RawInventoryItem[]; total: number }>): typeof fetch {
  return (async (url: string) => {
    const m = /page=(\d+)/.exec(url);
    const p = m ? Number(m[1]) : 1;
    const pg = paginas[p - 1] ?? { items: [], total: paginas[0]?.total ?? 0 };
    return { ok: true, status: 200, json: async () => ({ ...pg, page: p, limit: 300 }) } as Response;
  }) as unknown as typeof fetch;
}

const full = Array.from({ length: 300 }, (_, i) => item(i));

describe("listarInventarioCompleto", () => {
  it("junta várias páginas até esgotar o total", async () => {
    const mp = new MercadoPhoneClient({
      apiKey: "x",
      fetchImpl: fakePaginado([
        { items: full, total: 450 },
        { items: full.slice(0, 150), total: 450 },
      ]),
    });
    expect(await mp.listarInventarioCompleto()).toHaveLength(450);
  });

  it("aborta se uma página vier vazia antes de esgotar o total", async () => {
    const mp = new MercadoPhoneClient({
      apiKey: "x",
      fetchImpl: fakePaginado([
        { items: full, total: 600 },
        { items: [], total: 600 }, // glitch: página 2 vazia
      ]),
    });
    await expect(mp.listarInventarioCompleto()).rejects.toThrow(/incompleto/i);
  });

  it("página final legitimamente curta não é erro", async () => {
    const mp = new MercadoPhoneClient({
      apiKey: "x",
      fetchImpl: fakePaginado([
        { items: full, total: 342 },
        { items: full.slice(0, 42), total: 342 },
      ]),
    });
    expect(await mp.listarInventarioCompleto()).toHaveLength(342);
  });
});
