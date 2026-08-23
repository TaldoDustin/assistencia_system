import { cn } from "@/lib/utils";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "./card";

/**
 * Recipiente "dominante" da Fase 3.1 (Foundation v2) — para o único elemento de maior peso de
 * cada tela (ex.: métrica hero do Dashboard, painel principal de uma tela de detalhe). Ver
 * docs/engineering/plans/PLAN-design-system-fase3-visual-experience.md §7/§8.
 *
 * Diferente de `Card` (recipiente genérico, ainda usado em toda parte): `Panel` sempre combina
 * borda sutil + sombra. A borda dá a separação no Dark Mode (sombra não é visível em fundo quase
 * preto); a sombra dá a profundidade no Light Mode (spec §3: "sombra é a ferramenta de
 * profundidade no light"). A sombra não reage ao tema (é um valor fixo do Tailwind) — funciona
 * nos dois modos porque é sutil o bastante para ler como profundidade no Light Mode e
 * simplesmente não aparecer (sem prejuízo) contra um fundo já quase-preto no Dark Mode. Não
 * precisa de variante condicional por tema (`dark:` do Tailwind não é usado neste projeto, ver
 * Global Constraints).
 */
export function Panel({ className, ...props }) {
  return <Card className={cn("shadow-sm", className)} {...props} />;
}

export const PanelHeader = CardHeader;
export const PanelTitle = CardTitle;
export const PanelDescription = CardDescription;
export const PanelContent = CardContent;
