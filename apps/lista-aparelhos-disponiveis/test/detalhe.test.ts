import { beforeEach, describe, expect, it } from "vitest";
import detalheHandler from "../api/detalhe.js";
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

describe("MemoryStore.setDetalhe / getDetalhes", () => {
  it("grava, corta em 280, limpa com vazio", async () => {
    await store.setDetalhe(alvo, "  marca de uso leve  ");
    expect((await store.getDetalhes())[String(alvo)]?.texto).toBe("marca de uso leve");

    await store.setDetalhe(alvo, "x".repeat(400));
    expect((await store.getDetalhes())[String(alvo)]!.texto.length).toBe(280);

    await store.setDetalhe(alvo, "   ");
    expect((await store.getDetalhes())[String(alvo)]).toBeUndefined();
  });
});

describe("montarResposta injeta o detalhe nos dois papéis", () => {
  it("geral e estoque veem o mesmo texto", async () => {
    await store.setDetalhe(alvo, "tela trocada — original");
    const g = (await montarResposta(store, "geral")) as { itens: Array<{ id: number; detalhe?: { texto: string } }> };
    expect(g.itens.find((i) => i.id === alvo)?.detalhe?.texto).toBe("tela trocada — original");
    const e = (await montarResposta(store, "estoque")) as { disponiveis: Array<{ id: number; detalhe?: { texto: string } }> };
    expect(e.disponiveis.find((i) => i.id === alvo)?.detalhe?.texto).toBe("tela trocada — original");
  });
});

describe("POST /api/detalhe", () => {
  it("geral não pode editar → 403", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await detalheHandler(mockReq({ method: "POST", headers: { cookie: cookie("geral") }, body: { id: alvo, texto: "x" } }), res);
      expect(out.statusCode).toBe(403);
    }));

  it("estoque edita → aparece na Geral no próximo inventory", () =>
    withEnv(ENV, async () => {
      const d = mockRes();
      await detalheHandler(mockReq({ method: "POST", headers: { cookie: cookie("estoque") }, body: { id: alvo, texto: "arranhão na lateral" } }), d.res);
      expect(d.out.statusCode).toBe(200);

      const g = mockRes();
      await inventoryHandler(mockReq({ headers: { cookie: cookie("geral") } }), g.res);
      const body = g.out.body as { itens: Array<{ id: number; detalhe?: { texto: string } }> };
      expect(body.itens.find((i) => i.id === alvo)?.detalhe?.texto).toBe("arranhão na lateral");
    }));

  it("id inválido → 400", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await detalheHandler(mockReq({ method: "POST", headers: { cookie: cookie("estoque") }, body: { texto: "x" } }), res);
      expect(out.statusCode).toBe(400);
    }));
});
