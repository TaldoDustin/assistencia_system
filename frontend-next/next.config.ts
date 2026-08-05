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
