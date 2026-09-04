/**
 * GET /api/health → idade do último snapshot + contagens. Sem dado sensível, sem auth.
 */
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { getStore } from "../lib/store.js";

export default async function handler(_req: VercelRequest, res: VercelResponse): Promise<void> {
  const store = await getStore();
  const [geral, sync, reservas] = await Promise.all([
    store.getSnapshotGeral(),
    store.getSyncStatus(),
    store.getReservas(),
  ]);
  const idadeMin = geral ? Math.round((Date.now() - Date.parse(geral.geradoEm)) / 60_000) : null;
  res.setHeader("Cache-Control", "no-store");
  res.status(geral ? 200 : 503).json({
    ok: Boolean(geral),
    snapshotGeradoEm: geral?.geradoEm ?? null,
    idadeMinutos: idadeMin,
    itensGeral: geral?.total ?? 0,
    reservas: Object.keys(reservas).length,
    ultimoSync: sync ? { em: sync.em, ok: sync.ok, erro: sync.erro ?? null } : null,
  });
}
