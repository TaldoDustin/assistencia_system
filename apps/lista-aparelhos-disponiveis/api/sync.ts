/**
 * POST /api/sync   → roda o job de sincronização (cron / operador).
 * GET  /api/sync    → idem (permite acionar pela barra de endereço com ?secret=).
 *
 * Protegido por SYNC_SECRET (header `x-sync-secret` ou query `secret`). O Vercel Cron
 * chama sem header custom, então também aceitamos o header `authorization: Bearer`.
 */
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { rodarSync } from "../lib/sync.js";
import { getStore } from "../lib/store.js";

function autorizado(req: VercelRequest): boolean {
  const auth = req.headers.authorization;
  // Vercel Cron injeta `Authorization: Bearer <CRON_SECRET>` automaticamente.
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && auth === `Bearer ${cronSecret}`) return true;
  // Acionamento manual (operador / GitHub Actions de fallback).
  const secret = process.env.SYNC_SECRET;
  if (!secret) return false;
  const h = req.headers["x-sync-secret"];
  if ((Array.isArray(h) ? h[0] : h) === secret) return true;
  if (auth === `Bearer ${secret}`) return true;
  if (typeof req.query.secret === "string" && req.query.secret === secret) return true;
  return false;
}

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (!autorizado(req)) {
    res.status(401).json({ erro: "não autorizado" });
    return;
  }
  const apiKey = process.env.MERCADOPHONE_API_KEY ?? "";
  if (!apiKey) {
    res.status(500).json({ erro: "MERCADOPHONE_API_KEY ausente" });
    return;
  }
  const store = await getStore();
  const resultado = await rodarSync(store, apiKey);
  res.status(resultado.ok ? 200 : 502).json(resultado);
}
