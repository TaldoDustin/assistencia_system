import { beforeEach, describe, expect, it } from "vitest";
import migrarHandler from "../api/migrar-estoque.js";
import inventoryHandler from "../api/inventory.js";
import { emitirToken } from "../lib/auth.js";
import { montarResposta } from "../lib/inventory-view.js";
import { buildSnapshots } from "../lib/snapshot.js";
import { MemoryStore, _setStoreParaTeste } from "../lib/store.js";
import { availability, inventarioCru, storageSizes } from "./fixtures.js";
import { mockReq, mockRes, withEnv } from "./http-mock.js";

const ENV = { SENHA_GERAL: "1111", SENHA_ESTOQUE: "2222", COOKIE_SIGNING_SECRET: "seg-teste-comprido-o-suficiente" };
const cookie = (r: "geral" | "estoque") => `sess=${emitirToken(r, ENV.COOKIE_SIGNING_SECRET)}`;

let store: MemoryStore;
let alvo: number;

beforeEach(async () => {
  store = new MemoryStore();
  _setStoreParaTeste(store);
  const { geral, estoque } = buildSnapshots({ itens: inventarioCru, availability, storageSizes });
  await store.setSnapshots(geral, estoque);
  alvo = geral.itens[0]!.id;
});

describe("MemoryStore.setEstoqueLocal / getEstoqueLocais", () => {
  it("ausência no store = Estoque 1 (default)", async () => {
    expect((await store.getEstoqueLocais())[String(alvo)]).toBeUndefined();
  });

  it("grava e sobrescreve", async () => {
    await store.setEstoqueLocal(alvo, 2);
    expect((await store.getEstoqueLocais())[String(alvo)]).toBe(2);
    await store.setEstoqueLocal(alvo, 1);
    expect((await store.getEstoqueLocais())[String(alvo)]).toBe(1);
  });
});

describe("montarResposta — BR-081 (Estoque 1/2)", () => {
  it("item novo nasce em Estoque 1 e aparece na Geral", async () => {
    const e = (await montarResposta(store, "estoque")) as {
      estoque1: Array<{ id: number; estoqueLocal: number }>;
      estoque2: Array<{ id: number }>;
    };
    expect(e.estoque1.find((i) => i.id === alvo)?.estoqueLocal).toBe(1);
    expect(e.estoque2.some((i) => i.id === alvo)).toBe(false);

    const g = (await montarResposta(store, "geral")) as { itens: Array<{ id: number }> };
    expect(g.itens.some((i) => i.id === alvo)).toBe(true);
  });

  it("movido para Estoque 2: some da Geral e de estoque1, aparece em estoque2 e em disponiveis", async () => {
    await store.setEstoqueLocal(alvo, 2);
    const e = (await montarResposta(store, "estoque")) as {
      estoque1: Array<{ id: number }>;
      estoque2: Array<{ id: number; estoqueLocal: number }>;
      disponiveis: Array<{ id: number }>;
    };
    expect(e.estoque1.some((i) => i.id === alvo)).toBe(false);
    expect(e.estoque2.find((i) => i.id === alvo)?.estoqueLocal).toBe(2);
    expect(e.disponiveis.some((i) => i.id === alvo)).toBe(true);

    const g = (await montarResposta(store, "geral")) as { itens: Array<{ id: number }> };
    expect(g.itens.some((i) => i.id === alvo)).toBe(false);
  });
});

describe("POST /api/migrar-estoque", () => {
  it("geral não pode mover → 403", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await migrarHandler(
        mockReq({ method: "POST", headers: { cookie: cookie("geral") }, body: { id: alvo, local: 2 } }),
        res,
      );
      expect(out.statusCode).toBe(403);
    }));

  it("estoque move → item some da Geral no próximo inventory", () =>
    withEnv(ENV, async () => {
      const m = mockRes();
      await migrarHandler(
        mockReq({ method: "POST", headers: { cookie: cookie("estoque") }, body: { id: alvo, local: 2 } }),
        m.res,
      );
      expect(m.out.statusCode).toBe(200);

      const g = mockRes();
      await inventoryHandler(mockReq({ headers: { cookie: cookie("geral") } }), g.res);
      const body = g.out.body as { itens: Array<{ id: number }> };
      expect(body.itens.some((i) => i.id === alvo)).toBe(false);
    }));

  it("id inválido → 400", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await migrarHandler(mockReq({ method: "POST", headers: { cookie: cookie("estoque") }, body: { local: 2 } }), res);
      expect(out.statusCode).toBe(400);
    }));

  it("local inválido → 400", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await migrarHandler(
        mockReq({ method: "POST", headers: { cookie: cookie("estoque") }, body: { id: alvo, local: 3 } }),
        res,
      );
      expect(out.statusCode).toBe(400);
    }));

  it("método não suportado → 405", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await migrarHandler(mockReq({ method: "GET", headers: { cookie: cookie("estoque") } }), res);
      expect(out.statusCode).toBe(405);
    }));
});
