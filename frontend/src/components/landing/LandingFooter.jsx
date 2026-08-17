import { FOOTER } from "./content";

export function LandingFooter() {
  return (
    <footer className="bg-sidebar border-t border-sidebar-border py-10">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-6 px-4 text-center lg:flex-row lg:justify-between lg:px-6 lg:text-left">
        <div className="flex items-center gap-2">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary">
            <span className="text-xs font-bold text-primary-foreground">F</span>
          </div>
          <span className="text-sm font-semibold text-sidebar-foreground">Fluxoly</span>
        </div>

        <nav className="flex flex-wrap items-center justify-center gap-4">
          {FOOTER.links.map((link) => (
            <a
              key={link.label}
              href={link.href}
              className="text-sm text-sidebar-foreground/70 transition-colors hover:text-sidebar-foreground"
            >
              {link.label}
            </a>
          ))}
        </nav>

        <p className="text-xs text-sidebar-foreground/60">{FOOTER.copyright}</p>
      </div>
    </footer>
  );
}
