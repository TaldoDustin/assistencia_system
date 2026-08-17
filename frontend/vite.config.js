import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    environment: 'jsdom',
    setupFiles: './src/test/setup.js',
    // tests/e2e/ é Playwright (npm run test:e2e), não Vitest — exclusão
    // explícita evita que o runner errado tente executar aquele arquivo.
    include: ['src/**/*.{test,spec}.{js,jsx}'],
  },
  define: {
    // Sprint Observabilidade -- release do Sentry via git commit, sem exigir
    // configuração manual na Vercel (VERCEL_GIT_COMMIT_SHA já é injetada
    // automaticamente em todo build). Ausente em build local -> "dev".
    'import.meta.env.VITE_SENTRY_RELEASE': JSON.stringify(process.env.VERCEL_GIT_COMMIT_SHA || 'dev'),
  },
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:5080',
        changeOrigin: true,
      },
    },
  },
  base: '/',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
})
