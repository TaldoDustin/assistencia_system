import { WarningCircle, ArrowClockwise } from "@phosphor-icons/react";
import { Card, CardContent } from "./card";
import { Button } from "./button";
import { cn } from "@/lib/utils";

/**
 * Estado de erro bloqueante (tela cheia) — generalização de `DashboardError` (PR #46). Usar quando
 * não há dado nenhum para mostrar além do erro.
 * @param {{ title?: string, description?: string, onRetry?: () => void, className?: string }} props
 */
export function ErrorState({
  title = "Não foi possível carregar os dados.",
  description = "Verifique sua conexão e tente novamente.",
  onRetry,
  className,
}) {
  return (
    <Card className={cn("border-destructive/40", className)}>
      <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <WarningCircle className="h-10 w-10 text-destructive" />
        <div>
          <p className="text-card-foreground font-medium">{title}</p>
          {description && <p className="text-muted-foreground text-sm mt-1">{description}</p>}
        </div>
        {onRetry && (
          <Button variant="outline" onClick={onRetry}>
            <ArrowClockwise className="h-4 w-4" />
            Tentar novamente
          </Button>
        )}
      </CardContent>
    </Card>
  );
}

/**
 * Banner de erro não bloqueante — para quando já existe dado (possivelmente desatualizado) na tela e o
 * erro é de uma tentativa de atualização, não da carga inicial. Generalização do banner inline de
 * `Dashboard.jsx`.
 * @param {{ message: string, onRetry?: () => void, className?: string }} props
 */
export function ErrorBanner({ message, onRetry, className }) {
  return (
    <Card className={cn("border-destructive/40 bg-destructive/10", className)}>
      <CardContent className="flex items-center justify-between gap-3 py-3 flex-wrap">
        <div className="flex items-center gap-2 text-sm text-card-foreground">
          <WarningCircle className="h-4 w-4 text-destructive shrink-0" />
          {message}
        </div>
        {onRetry && (
          <Button variant="outline" size="sm" onClick={onRetry}>
            <ArrowClockwise className="h-4 w-4" />
            Tentar novamente
          </Button>
        )}
      </CardContent>
    </Card>
  );
}
