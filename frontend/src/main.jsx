import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import * as Sentry from '@sentry/react'
import './index.css'
import App from './App.jsx'

// Sprint Observabilidade -- só inicializa com VITE_SENTRY_DSN definida
// (mesmo padrão opcional do backend, app.py). environment usa import.meta.env.PROD,
// variável nativa do Vite -- projeto não tem staging, só dev/produção.
// send_default_pii não é passado (default já é false no SDK JS) e
// tracesSampleRate=0 (sem tracing de performance) espelham a decisão já
// tomada no backend (app.py).
const sentryDsn = import.meta.env.VITE_SENTRY_DSN
if (sentryDsn) {
  Sentry.init({
    dsn: sentryDsn,
    environment: import.meta.env.PROD ? 'production' : 'development',
    release: import.meta.env.VITE_SENTRY_RELEASE,
    tracesSampleRate: 0,
  })
}

function ErrorFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="text-center space-y-2">
        <p className="text-lg font-semibold text-foreground">Algo deu errado.</p>
        <p className="text-sm text-muted-foreground">Recarregue a página. Se o problema continuar, contate o suporte.</p>
      </div>
    </div>
  )
}

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Sentry.ErrorBoundary fallback={<ErrorFallback />}>
      <App />
    </Sentry.ErrorBoundary>
  </StrictMode>,
)
