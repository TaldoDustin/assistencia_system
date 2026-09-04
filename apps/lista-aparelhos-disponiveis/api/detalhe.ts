/**
 * POST /api/detalhe  { id, texto }  → grava/limpa a nota de condição da unidade (role=estoque).
 *
 * Nota curada manualmente ("marca de uso leve", "tela trocada — original", …). Visível
 * também na área Geral (decisão do CTO, 2026-09-04). Texto vazio limpa a nota.
 * A responsabilidade pelo conteúdo (não colocar dado pessoal) é de quem edita.
 */
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { papelDoRequest, jsonBody } from "../lib/request.js";
import { getStore } from "../lib/store.js";

const MAX = 280;

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (req.method !== "POST") {
    res.status(405).json({ erro: "método não suportado" });
    return;
  }
  if (papelDoRequest(req) !== "estoque") {
    res.status(403).json({ erro: "só a área Estoque pode editar detalhes" });
    return;
  }

  const { id, texto } = jsonBody<{ id?: number; texto?: string }>(req.body);
  if (typeof id !== "number" || !Number.isInteger(id)) {
    res.status(400).json({ erro: "id inválido" });
    return;
  }
  if (typeof texto !== "string") {
    res.status(400).json({ erro: "texto inválido" });
    return;
  }

  const store = await getStore();
  await store.setDetalhe(id, texto.slice(0, MAX));
  res.status(200).json({ ok: true });
}
