import { beforeEach, describe, expect, it } from "vitest";
import sessionHandler from "../api/session.js";
import inventoryHandler from "../api/inventory.js";
import reservarHandler from "../api/reservar.js";
import desreservarHandler from "../api/desreservar.js";
import { emitirToken } from "../lib/auth.js";
import { buildSnapshots } from "../lib/snapshot.js";
import { MemoryStore, _setStoreParaTeste } from "../lib/store.js";
import { availability, inventarioCru, storageSizes } from "./fixtures.js";
import { mockReq, mockRes, withEnv } from "./http-mock.js";

const ENV = {
  SENHA_GERAL: "1111",
  SENHA_ESTOQUE: "2222",
  COOKIE_SIGNING_SECRET: "segredo-de-teste-bem-comprido-aqui",
};

let store: MemoryStore;

beforeEach(async () => {
  store = new MemoryStore();
  _setStoreParaTeste(store);
  const { geral, estoque } = buildSnapshots({ itens: inventarioCru, availability, storageSizes });
  await store.setSnapshots(geral, estoque);
});

const cookie = (role: "geral" | "estoque") =>
  `sess=${emitirToken(role, ENV.COOKIE_SIGNING_SECRET)}`;

describe("POST /api/session", () => {
  it("senha de estoque → papel estoque + cookie", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await sessionHandler(mockReq({ method: "POST", body: { senha: "2222" } }), res);
      expect(out.statusCode).toBe(200);
      expect((out.body as { papel: string }).papel).toBe("estoque");
      expect(out.headers["set-cookie"]).toMatch(/sess=/);
    }));

  it("senha errada → 401", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await sessionHandler(mockReq({ method: "POST", body: { senha: "xxxx" } }), res);
      expect(out.statusCode).toBe(401);
    }));

  it("rate-limit só conta falhas; senha certa nunca é bloqueada", () =>
    withEnv(ENV, async () => {
      const ip = { "x-forwarded-for": "9.9.9.9" };
      let ultimo = 0;
      for (let i = 0; i < 25; i++) {
        const { res, out } = mockRes();
        await sessionHandler(mockReq({ method: "POST", body: { senha: "no" }, headers: ip }), res);
        ultimo = out.statusCode;
      }
      expect(ultimo).toBe(429); // 25 falhas > limite (20)

      // ...mas a senha correta ainda entra, mesmo com o IP "quente"
      const { res, out } = mockRes();
      await sessionHandler(mockReq({ method: "POST", body: { senha: "2222" }, headers: ip }), res);
      expect(out.statusCode).toBe(200);
    }));

  it("acerto de senha não incrementa o contador de falhas", () =>
    withEnv(ENV, async () => {
      const ip = { "x-forwarded-for": "8.8.8.8" };
      for (let i = 0; i < 30; i++) {
        const { res } = mockRes();
        await sessionHandler(mockReq({ method: "POST", body: { senha: "1111" }, headers: ip }), res);
      }
      const { res, out } = mockRes();
      await sessionHandler(mockReq({ method: "POST", body: { senha: "1111" }, headers: ip }), res);
      expect(out.statusCode).toBe(200);
    }));
});

describe("GET /api/inventory por papel", () => {
  it("sem cookie → 401", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await inventoryHandler(mockReq(), res);
      expect(out.statusCode).toBe(401);
    }));

  it("papel geral: sem custo, sem PII", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await inventoryHandler(mockReq({ headers: { cookie: cookie("geral") } }), res);
      expect(out.statusCode).toBe(200);
      const txt = JSON.stringify(out.body);
      expect(txt).not.toMatch(/custo|margem|clienteNome|fornecedorNome/i);
      expect(txt).not.toMatch(/\d{14,}/);
    }));

  it("papel estoque: traz custo e margem", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await inventoryHandler(mockReq({ headers: { cookie: cookie("estoque") } }), res);
      const body = out.body as { disponiveis: Array<{ custo: number | null }> };
      expect(body.disponiveis.some((i) => i.custo != null)).toBe(true);
    }));
});

describe("reserva (BR-076/077)", () => {
  it("geral não pode reservar → 403", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await reservarHandler(mockReq({ method: "POST", headers: { cookie: cookie("geral") }, body: { id: 1, vendedor: "Ana" } }), res);
      expect(out.statusCode).toBe(403);
    }));

  it("estoque reserva; item some da Geral; 2ª reserva → 409", () =>
    withEnv(ENV, async () => {
      const { estoque } = buildSnapshots({ itens: inventarioCru, availability, storageSizes });
      const alvo = estoque.itens[0]!.id;

      const r1 = mockRes();
      await reservarHandler(mockReq({ method: "POST", headers: { cookie: cookie("estoque") }, body: { id: alvo, vendedor: "Ana" } }), r1.res);
      expect(r1.out.statusCode).toBe(200);

      const g = mockRes();
      await inventoryHandler(mockReq({ headers: { cookie: cookie("geral") } }), g.res);
      const geral = g.out.body as { itens: Array<{ id: number }> };
      expect(geral.itens.some((i) => i.id === alvo)).toBe(false);

      const e = mockRes();
      await inventoryHandler(mockReq({ headers: { cookie: cookie("estoque") } }), e.res);
      const est = e.out.body as { reservados: Array<{ id: number; reservado?: { vendedor: string } }> };
      expect(est.reservados.find((i) => i.id === alvo)?.reservado?.vendedor).toBe("Ana");

      const r2 = mockRes();
      await reservarHandler(mockReq({ method: "POST", headers: { cookie: cookie("estoque") }, body: { id: alvo, vendedor: "Bia" } }), r2.res);
      expect(r2.out.statusCode).toBe(409);

      const d = mockRes();
      await desreservarHandler(mockReq({ method: "POST", headers: { cookie: cookie("estoque") }, body: { id: alvo } }), d.res);
      expect(d.out.statusCode).toBe(200);
      const g2 = mockRes();
      await inventoryHandler(mockReq({ headers: { cookie: cookie("geral") } }), g2.res);
      expect((g2.out.body as { itens: Array<{ id: number }> }).itens.some((i) => i.id === alvo)).toBe(true);
    }));

  it("reserva exige vendedor", () =>
    withEnv(ENV, async () => {
      const { res, out } = mockRes();
      await reservarHandler(mockReq({ method: "POST", headers: { cookie: cookie("estoque") }, body: { id: 1, vendedor: "  " } }), res);
      expect(out.statusCode).toBe(400);
    }));
});
