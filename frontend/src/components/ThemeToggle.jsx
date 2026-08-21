import { Sun, Moon, Monitor } from "@phosphor-icons/react";
import { Button } from "@/components/ui/button";
import { useTheme } from "@/contexts/ThemeContext";

const NEXT_THEME = { system: "light", light: "dark", dark: "system" };
const ICON_BY_THEME = { system: Monitor, light: Sun, dark: Moon };
const LABEL_BY_THEME = {
  system: "Tema: automático (segue o sistema)",
  light: "Tema: claro",
  dark: "Tema: escuro",
};

export default function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const Icon = ICON_BY_THEME[theme];

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={() => setTheme(NEXT_THEME[theme])}
      aria-label={`${LABEL_BY_THEME[theme]} — clique para alternar`}
      className="h-8 w-8 text-sidebar-foreground/70 hover:text-sidebar-foreground hover:bg-sidebar-accent"
    >
      <Icon className="h-4 w-4" />
    </Button>
  );
}
