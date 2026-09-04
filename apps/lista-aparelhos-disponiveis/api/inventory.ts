/**
 * GET /api/inventory → snapshot conforme o papel do cookie.
 * O snapshot "estoque" (com custo) só sai por aqui, com role=estoque — nunca como asset estático.
 */
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { montarResposta } from "../lib/inventory-view.js";
import { papelDoRequest } from "../lib/request.js";
import { getStore } from "../lib/store.js";

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (req.method !== "GET") {
    res.status(405).json({ erro: "método não suportado" });
    return;
  }
  const papel = papelDoRequest(req);
  if (!papel) {
    res.status(401).json({ erro: "não autenticado" });
    return;
  }

  const store = await getStore();
  const resposta = await montarResposta(store, papel);
  if (!resposta) {
    res.status(503).json({ erro: "lista ainda não sincronizada — tente em alguns minutos" });
    return;
  }
  res.setHeader("Cache-Control", "no-store");
  res.status(200).json(resposta);
}
