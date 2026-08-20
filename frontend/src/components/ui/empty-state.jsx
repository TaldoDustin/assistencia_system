import { Tray } from "@phosphor-icons/react";
import { Card, CardContent } from "./card";
import { cn } from "@/lib/utils";

/**
 * Estado vazio reutilizável — generalização do padrão validado em `Dashboard.jsx` (PR #46).
 * @param {{ icon?: import("react").ComponentType, title: string, description?: string, action?: import("react").ReactNode, className?: string }} props
 */
export function EmptyState({ icon, title, description, action, className }) {
  const Icon = icon || Tray;

  return (
    <Card className={cn(className)}>
      <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <Icon className="h-10 w-10 text-muted-foreground" />
        <div>
          <p className="text-card-foreground font-medium">{title}</p>
          {description && <p className="text-muted-foreground text-sm mt-1">{description}</p>}
        </div>
        {action}
      </CardContent>
    </Card>
  );
}
