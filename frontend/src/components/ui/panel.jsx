import { cn } from "@/lib/utils";

/**
 * Recipiente "dominante" da Fase 3.1 (Foundation v2) — para o único elemento de maior peso de
 * cada tela (ex.: métrica hero do Dashboard, painel principal de uma tela de detalhe). Ver
 * docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md §7/§8.
 *
 * Diferente de `Card` (recipiente genérico, ainda usado em toda parte): `Panel` sempre combina
 * borda sutil + sombra. A borda dá a separação no Dark Mode (sombra não é visível em fundo quase
 * preto); a sombra dá a profundidade no Light Mode (spec §3: "sombra é a ferramenta de
 * profundidade no light"). Como os dois (`--color-border` e a cor de sombra do navegador) já
 * reagem ao tema sozinhos, uma única classe funciona nos dois modos — não precisa de variante
 * condicional por tema (`dark:` do Tailwind não é usado neste projeto, ver Global Constraints).
 */
export function Panel({ className, ...props }) {
  return (
    <div
      className={cn("rounded-xl border border-border bg-card text-card-foreground shadow-sm", className)}
      {...props}
    />
  );
}

export function PanelHeader({ className, ...props }) {
  return <div className={cn("flex flex-col space-y-1.5 p-6", className)} {...props} />;
}

export function PanelTitle({ className, ...props }) {
  return (
    <h3
      className={cn("text-lg font-semibold leading-none tracking-tight text-card-foreground", className)}
      {...props}
    />
  );
}

export function PanelDescription({ className, ...props }) {
  return <p className={cn("text-sm text-muted-foreground", className)} {...props} />;
}

export function PanelContent({ className, ...props }) {
  return <div className={cn("p-6 pt-0", className)} {...props} />;
}
