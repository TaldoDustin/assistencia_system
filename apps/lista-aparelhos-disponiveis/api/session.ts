/**
 * POST /api/session  { senha }  → set-cookie assinado com o papel.
 * DELETE /api/session            → limpa o cookie.
 *
 * Não revela qual senha (Geral/Estoque) foi digitada — só sucesso/falha.
 */
import type { VercelRequest, VercelResponse } from "@vercel/node";
import { cookieDeLogin, cookieDeLogout, emitirToken, lerAuthEnv, papelDaSenha } from "../lib/auth.js";
import { ipDoRequest, jsonBody } from "../lib/request.js";
import { getStore } from "../lib/store.js";

// Só falhas contam contra o limite; a senha certa passa sempre (não trava a
// equipe atrás do mesmo IP da loja). 20 senhas erradas em 5 min = abuso.
const LIMITE_FALHAS = 20;
const JANELA_SEGUNDOS = 300;

export default async function handler(req: VercelRequest, res: VercelResponse): Promise<void> {
  if (req.method === "DELETE") {
    res.setHeader("Set-Cookie", cookieDeLogout());
    res.status(204).end();
    return;
  }
  if (req.method !== "POST") {
    res.status(405).json({ erro: "método não suportado" });
    return;
  }

  let env;
  try {
    env = lerAuthEnv();
  } catch {
    res.status(500).json({ erro: "configuração de senha ausente no servidor" });
    return;
  }

  const { senha } = jsonBody<{ senha?: string }>(req.body);
  const papel = typeof senha === "string" ? papelDaSenha(senha, env) : null;

  if (!papel) {
    const store = await getStore();
    const falhas = await store.bumpRate(`login:${ipDoRequest(req)}`, JANELA_SEGUNDOS);
    res
      .status(falhas > LIMITE_FALHAS ? 429 : 401)
      .json({ erro: falhas > LIMITE_FALHAS ? "muitas tentativas, tente de novo em alguns minutos" : "senha incorreta" });
    return;
  }

  const token = emitirToken(papel, env.signingSecret);
  res.setHeader("Set-Cookie", cookieDeLogin(token));
  res.status(200).json({ papel });
}
