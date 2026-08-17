import { ArrowRight } from "@phosphor-icons/react";
import { FadeInSection } from "./FadeInSection";
import { SOLUTION } from "./content";

// Diagrama "antes" (ferramentas espalhadas) -> "depois" (um único fluxo), conforme a spec —
// construído com ícones/tokens do próprio Design System, sem imagem externa.
const SCATTERED = ["Planilha", "Caderno", "WhatsApp", "Sistema à parte"];

export function LandingSolution() {
  return (
    <section className="bg-card/40 py-20 lg:py-28">
      <div className="mx-auto max-w-6xl px-4 text-center lg:px-6">
        <FadeInSection>
          <h2 className="text-3xl font-semibold text-foreground lg:text-4xl">{SOLUTION.title}</h2>
          <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground">{SOLUTION.text}</p>
        </FadeInSection>

        <FadeInSection delay={0.1}>
          <div className="mt-12 flex flex-col items-center justify-center gap-6 sm:flex-row">
            <div className="flex flex-wrap items-center justify-center gap-2">
              {SCATTERED.map((label) => (
                <span
                  key={label}
                  className="rounded-full border border-border bg-card px-3 py-1.5 text-xs text-muted-foreground"
                >
                  {label}
                </span>
              ))}
            </div>
            <ArrowRight className="h-6 w-6 shrink-0 rotate-90 text-primary sm:rotate-0" />
            <span className="flex h-14 w-14 items-center justify-center rounded-xl bg-primary text-primary-foreground">
              <span className="text-lg font-bold">F</span>
            </span>
          </div>
        </FadeInSection>
      </div>
    </section>
  );
}
