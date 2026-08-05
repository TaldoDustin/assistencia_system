import path from "node:path";
import type { NextConfig } from "next";

// Protótipo de avaliação (ver frontend-next/README.md e docs/engineering/adr/ADR-012.md).
// Em dev local, proxya /api/* para o Flask rodando em 127.0.0.1:5080. Isso faz o browser
// enxergar tudo como same-origin (localhost:3000), então o cookie de sessão do Flask
// funciona sem nenhuma mudança de CORS no backend. Ver validação empírica no README.
const FLASK_DEV_ORIGIN =
  process.env.FLUXOLY_FLASK_DEV_ORIGIN?.trim() || "http://127.0.0.1:5080";

const nextConfig: NextConfig = {
  // Evita que o Turbopack suba a raiz do projeto até C:\Users\souzi (onde há um
  // package-lock.json solto, fora deste repositório) só por causa de um lockfile
  // externo detectado acima do cwd.
  turbopack: {
    root: path.join(__dirname),
  },
  // "localhost" e "127.0.0.1" são origens distintas para o navegador. Sem isso, o
  // dev server bloqueia os chunks JS (HMR/_next/static) quando acessado via 127.0.0.1,
  // e a página carrega só o HTML/CSS sem hidratar -- tela em branco/preta, sem erro
  // visível no console além do aviso no log do servidor.
  allowedDevOrigins: ["localhost", "127.0.0.1"],
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${FLASK_DEV_ORIGIN}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;
