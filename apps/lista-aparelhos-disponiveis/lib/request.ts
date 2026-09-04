/** Helpers de request compartilhados pelas rotas serverless. */
import { COOKIE_NOME, lerAuthEnv, lerCookie, verificarToken } from "./auth.js";
import type { Papel } from "./types.js";

export interface MinimalReq {
  headers: Record<string, string | string[] | undefined>;
  body?: unknown;
}

/** Papel autenticado do request, ou null. */
export function papelDoRequest(req: MinimalReq): Papel | null {
  const cookieHeader = Array.isArray(req.headers.cookie)
    ? req.headers.cookie.join("; ")
    : req.headers.cookie;
  const token = lerCookie(cookieHeader, COOKIE_NOME);
  try {
    const { signingSecret } = lerAuthEnv();
    return verificarToken(token, signingSecret);
  } catch {
    return null;
  }
}

/** Body JSON já parseado (Vercel faz por padrão) ou string. */
export function jsonBody<T = Record<string, unknown>>(body: unknown): T {
  if (body == null) return {} as T;
  if (typeof body === "string") {
    try {
      return JSON.parse(body) as T;
    } catch {
      return {} as T;
    }
  }
  return body as T;
}

export function ipDoRequest(req: MinimalReq): string {
  const xff = req.headers["x-forwarded-for"];
  const raw = Array.isArray(xff) ? xff[0] : xff;
  return (raw?.split(",")[0] ?? "desconhecido").trim();
}
