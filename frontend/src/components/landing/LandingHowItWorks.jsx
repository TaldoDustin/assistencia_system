import { ClipboardText, PlayCircle, ChartLineUp } from "@phosphor-icons/react";
import { FadeInSection } from "./FadeInSection";
import { HOW_IT_WORKS } from "./content";

const ICONS = { ClipboardText, PlayCircle, ChartLineUp };

export function LandingHowItWorks() {
  return (
    <section id="como-funciona" className="py-20 lg:py-28">
      <div className="mx-auto max-w-6xl px-4 lg:px-6">
        <FadeInSection className="text-center">
          <h2 className="text-3xl font-semibold text-foreground lg:text-4xl">{HOW_IT_WORKS.title}</h2>
        </FadeInSection>

        <div className="mt-10 grid gap-8 sm:grid-cols-3">
          {HOW_IT_WORKS.steps.map((step, index) => {
            const Icon = ICONS[step.icon];
            return (
              <FadeInSection key={step.name} delay={index * 0.05} className="text-center sm:text-left">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-xl bg-primary/10 sm:mx-0">
                  <Icon className="h-6 w-6 text-primary" weight="duotone" />
                </div>
                <p className="mt-4 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                  Passo {index + 1}
                </p>
                <h3 className="mt-1 text-lg font-medium text-foreground">{step.name}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{step.text}</p>
              </FadeInSection>
            );
          })}
        </div>
      </div>
    </section>
  );
}
