import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { FadeInSection } from "./FadeInSection";
import { PRICING } from "./content";

// Faixas e valores dependem de decisão de monetização ainda não tomada
// (docs/company/PRODUCT_REQUIREMENTS.md) — seção estrutural pronta, valores [DEFINIR].
export function LandingPricing() {
  return (
    <section id="planos" className="bg-card/40 py-20 lg:py-28">
      <div className="mx-auto max-w-3xl px-4 text-center lg:px-6">
        <FadeInSection>
          <h2 className="text-3xl font-semibold text-foreground lg:text-4xl">{PRICING.title}</h2>
          <p className="mt-4 text-sm italic text-muted-foreground">{PRICING.placeholder}</p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Button asChild size="lg" className="w-full sm:w-auto">
              <Link to="/login">{PRICING.ctaPrimary}</Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
              <a href="#cta-final">{PRICING.ctaSecondary}</a>
            </Button>
          </div>
        </FadeInSection>
      </div>
    </section>
  );
}
