import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { _setStoreParaTeste, getStore } from "../lib/store.js";

const KEYS = [
  "VERCEL",
  "KV_REST_API_URL",
  "KV_REST_API_TOKEN",
  "UPSTASH_REDIS_REST_URL",
  "UPSTASH_REDIS_REST_TOKEN",
];
let saved: Record<string, string | undefined>;

beforeEach(() => {
  saved = Object.fromEntries(KEYS.map((k) => [k, process.env[k]]));
  for (const k of KEYS) delete process.env[k];
  _setStoreParaTeste(null);
});

afterEach(() => {
  for (const k of KEYS) {
    if (saved[k] === undefined) delete process.env[k];
    else process.env[k] = saved[k];
  }
  _setStoreParaTeste(null);
});

describe("getStore", () => {
  it("fora da Vercel e sem Redis → MemoryStore (dev)", async () => {
    const s = await getStore();
    expect(s.constructor.name).toBe("MemoryStore");
  });

  it("na Vercel sem Redis → LANÇA (não degrada em silêncio)", async () => {
    process.env.VERCEL = "1";
    await expect(getStore()).rejects.toThrow(/Redis não configurado/i);
  });
});
