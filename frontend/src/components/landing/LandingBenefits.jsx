import { FadeInSection } from "./FadeInSection";
import { BENEFITS } from "./content";

// Sem ícone de módulo, sem jargão técnico — regra explícita da spec para esta seção.
export function LandingBenefits() {
  return (
    <section className="py-20 lg:py-28">
      <div className="mx-auto max-w-6xl px-4 lg:px-6">
        <FadeInSection>
          <h2 className="text-center text-3xl font-semibold text-foreground lg:text-4xl">{BENEFITS.title}</h2>
        </FadeInSection>

        <div className="mt-10 grid gap-8 sm:grid-cols-2">
          {BENEFITS.items.map((item, index) => (
            <FadeInSection key={item.lead} delay={index * 0.05}>
              <p className="text-base text-card-foreground">
                <strong className="font-semibold text-foreground">{item.lead}</strong> — {item.text}
              </p>
            </FadeInSection>
          ))}
        </div>
      </div>
    </section>
  );
}
