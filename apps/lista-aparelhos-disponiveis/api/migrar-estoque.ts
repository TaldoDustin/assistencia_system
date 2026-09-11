/**
 * POST /api/migrar-estoque  { id, local }   → move a unidade entre Estoque 1/2 (role=estoque).
 * BR-081. `local` deve ser 1 ou 2.
 */
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { papelDoRequest, jsonBody } from "../lib/request.js";
import { getStore } from "../lib/store.js";
import type { EstoqueLocal } from "../lib/types.js";

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (req.method !== "POST") {
    res.status(405).json({ erro: "método não suportado" });
    return;
  }
  if (papelDoRequest(req) !== "estoque") {
    res.status(403).json({ erro: "só a área Estoque pode mover unidades" });
    return;
  }

  const { id, local } = jsonBody<{ id?: number; local?: number }>(req.body);
  if (typeof id !== "number" || !Number.isInteger(id)) {
    res.status(400).json({ erro: "id inválido" });
    return;
  }
  if (local !== 1 && local !== 2) {
    res.status(400).json({ erro: "local inválido (use 1 ou 2)" });
    return;
  }

  const store = await getStore();
  await store.setEstoqueLocal(id, local as EstoqueLocal);
  res.status(200).json({ ok: true });
}
