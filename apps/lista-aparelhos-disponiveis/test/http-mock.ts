/** Mock mínimo de VercelRequest/VercelResponse para testar os handlers. */
import type { VercelRequest, VercelResponse } from "@vercel/node";

export interface MockRes {
  statusCode: number;
  body: unknown;
  headers: Record<string, string>;
}

export function mockReq(o: Partial<VercelRequest> & { body?: unknown } = {}): VercelRequest {
  return {
    method: "GET",
    headers: {},
    query: {},
    cookies: {},
    ...o,
  } as unknown as VercelRequest;
}

export function mockRes(): { res: VercelResponse; out: MockRes } {
  const out: MockRes = { statusCode: 0, body: undefined, headers: {} };
  const res = {
    status(code: number) { out.statusCode = code; return this; },
    json(payload: unknown) { out.body = payload; return this; },
    end() { return this; },
    setHeader(k: string, v: string) { out.headers[k.toLowerCase()] = v; },
  } as unknown as VercelResponse;
  return { res, out };
}

export function withEnv(vars: Record<string, string>, fn: () => Promise<void> | void) {
  const saved: Record<string, string | undefined> = {};
  for (const [k, v] of Object.entries(vars)) { saved[k] = process.env[k]; process.env[k] = v; }
  const restore = () => {
    for (const [k, v] of Object.entries(saved)) {
      if (v === undefined) delete process.env[k];
      else process.env[k] = v;
    }
  };
  const p = fn();
  if (p instanceof Promise) return p.finally(restore);
  restore();
  return Promise.resolve();
}
