import { FadeInSection } from "./FadeInSection";
import { SOCIAL_PROOF } from "./content";

// Regra explícita da spec: nunca inventar depoimento. Sem cliente citável ainda, a seção
// fica marcada como placeholder — nada de texto/nome/logotipo fictício.
export function LandingSocialProof() {
  return (
    <section className="py-16 lg:py-20">
      <div className="mx-auto max-w-3xl px-4 text-center lg:px-6">
        <FadeInSection>
          <h2 className="text-2xl font-semibold text-foreground lg:text-3xl">{SOCIAL_PROOF.title}</h2>
          <p className="mt-4 text-sm italic text-muted-foreground">{SOCIAL_PROOF.placeholder}</p>
        </FadeInSection>
      </div>
    </section>
  );
}
