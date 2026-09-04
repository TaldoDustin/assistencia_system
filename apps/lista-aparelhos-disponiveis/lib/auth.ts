/**
 * Sessão de 2 níveis por senha compartilhada (ADR-013 Q2).
 *
 * A senha é comparada em tempo (quase-)constante com as env vars; o navegador
 * recebe só um cookie assinado com HMAC contendo o papel — nunca a senha.
 * Não há login individual (decisão da Discovery).
 */
import { createHmac, timingSafeEqual } from "node:crypto";
import type { Papel } from "./types.js";

const TTL_SEGUNDOS = 12 * 60 * 60;
export const COOKIE_NOME = "sess";

export interface AuthEnv {
  senhaGeral: string;
  senhaEstoque: string;
  signingSecret: string;
}

export function lerAuthEnv(env: NodeJS.ProcessEnv = process.env): AuthEnv {
  const senhaGeral = env.SENHA_GERAL ?? "";
  const senhaEstoque = env.SENHA_ESTOQUE ?? "";
  const signingSecret = env.COOKIE_SIGNING_SECRET ?? "";
  if (!senhaGeral || !senhaEstoque || !signingSecret) {
    throw new Error("SENHA_GERAL / SENHA_ESTOQUE / COOKIE_SIGNING_SECRET ausentes");
  }
  if (senhaGeral === senhaEstoque) {
    throw new Error("SENHA_GERAL e SENHA_ESTOQUE não podem ser iguais");
  }
  return { senhaGeral, senhaEstoque, signingSecret };
}

function eqConstante(a: string, b: string): boolean {
  const ba = Buffer.from(a);
  const bb = Buffer.from(b);
  if (ba.length !== bb.length) {
    // ainda gasta tempo comparando algo, para não vazar o tamanho
    timingSafeEqual(ba, ba);
    return false;
  }
  return timingSafeEqual(ba, bb);
}

/** Retorna o papel correspondente à senha, ou null. */
export function papelDaSenha(senha: string, env: AuthEnv): Papel | null {
  if (eqConstante(senha, env.senhaEstoque)) return "estoque";
  if (eqConstante(senha, env.senhaGeral)) return "geral";
  return null;
}

interface TokenPayload {
  role: Papel;
  exp: number;
}

function sign(data: string, secret: string): string {
  return createHmac("sha256", secret).update(data).digest("base64url");
}

export function emitirToken(role: Papel, secret: string, agora = Date.now()): string {
  const payload: TokenPayload = { role, exp: Math.floor(agora / 1000) + TTL_SEGUNDOS };
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${body}.${sign(body, secret)}`;
}

export function verificarToken(
  token: string | undefined,
  secret: string,
  agora = Date.now(),
): Papel | null {
  if (!token || !token.includes(".")) return null;
  const [body, mac] = token.split(".") as [string, string];
  const esperado = sign(body, secret);
  if (!eqConstante(mac, esperado)) return null;
  try {
    const payload = JSON.parse(Buffer.from(body, "base64url").toString("utf8")) as TokenPayload;
    if (payload.exp * 1000 < agora) return null;
    if (payload.role !== "geral" && payload.role !== "estoque") return null;
    return payload.role;
  } catch {
    return null;
  }
}

export function cookieDeLogin(token: string): string {
  return [
    `${COOKIE_NOME}=${token}`,
    "Path=/",
    "HttpOnly",
    "Secure",
    "SameSite=Lax",
    `Max-Age=${TTL_SEGUNDOS}`,
  ].join("; ");
}

export function cookieDeLogout(): string {
  return `${COOKIE_NOME}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0`;
}

export function lerCookie(header: string | undefined, nome: string): string | undefined {
  if (!header) return undefined;
  for (const parte of header.split(";")) {
    const [k, ...v] = parte.trim().split("=");
    if (k === nome) return v.join("=");
  }
  return undefined;
}
