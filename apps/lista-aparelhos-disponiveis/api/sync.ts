/**
 * POST/GET /api/sync   → roda o job de sincronização (cron / operador).
 *
 * Protegido por segredo **só via header** — nunca query string (a query entra
 * nos logs de acesso da Vercel). Aceita:
 *   - `Authorization: Bearer <CRON_SECRET>`  (injetado pelo Vercel Cron)
 *   - `Authorization: Bearer <SYNC_SECRET>`  (GitHub Actions / operador)
 *   - `x-sync-secret: <SYNC_SECRET>`         (operador)
 */
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { rodarSync } from "../lib/sync.js";
import { getStore } from "../lib/store.js";

function autorizado(req: VercelRequest): boolean {
  const auth = req.headers.authorization;
  const cronSecret = process.env.CRON_SECRET;
  if (cronSecret && auth === `Bearer ${cronSecret}`) return true;
  const secret = process.env.SYNC_SECRET;
  if (!secret) return false;
  const h = req.headers["x-sync-secret"];
  if ((Array.isArray(h) ? h[0] : h) === secret) return true;
  if (auth === `Bearer ${secret}`) return true;
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
