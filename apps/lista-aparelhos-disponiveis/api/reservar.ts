/**
 * POST /api/reservar  { id, vendedor }   → marca a unidade como reservada (role=estoque).
 * A unidade some da área Geral no próximo /api/inventory (BR-076).
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
    res.status(403).json({ erro: "só a área Estoque pode reservar" });
    return;
  }

  const { id, vendedor } = jsonBody<{ id?: number; vendedor?: string }>(req.body);
  if (typeof id !== "number" || !Number.isInteger(id)) {
    res.status(400).json({ erro: "id inválido" });
    return;
  }
  const nome = typeof vendedor === "string" ? vendedor.trim().slice(0, 60) : "";
  if (!nome) {
    res.status(400).json({ erro: "informe o vendedor" });
    return;
  }

  const store = await getStore();
  const r = await store.reservar(id, { vendedor: nome, reservadoEm: new Date().toISOString() });
  if (r === "ja-reservado") {
    res.status(409).json({ erro: "essa unidade já está reservada" });
    return;
  }
  res.status(200).json({ ok: true });
}
