/**
 * POST /api/desreservar  { id }   → libera a reserva (role=estoque).
 */
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { papelDoRequest, jsonBody } from "../lib/request.js";
import { getStore } from "../lib/store.js";

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (req.method !== "POST") {
    res.status(405).json({ erro: "método não suportado" });
    return;
  }
  if (papelDoRequest(req) !== "estoque") {
    res.status(403).json({ erro: "só a área Estoque pode liberar reservas" });
    return;
  }
  const { id } = jsonBody<{ id?: number }>(req.body);
  if (typeof id !== "number" || !Number.isInteger(id)) {
    res.status(400).json({ erro: "id inválido" });
    return;
  }
  const store = await getStore();
  await store.desreservar(id);
  res.status(200).json({ ok: true });
}
