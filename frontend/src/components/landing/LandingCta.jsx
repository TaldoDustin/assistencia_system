import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { FadeInSection } from "./FadeInSection";
import { CTA_FINAL } from "./content";

export function LandingCta() {
  return (
    <section id="cta-final" className="bg-sidebar py-20 lg:py-24">
      <div className="mx-auto max-w-2xl px-4 text-center lg:px-6">
        <FadeInSection>
          <h2 className="text-3xl font-semibold text-foreground lg:text-4xl">{CTA_FINAL.title}</h2>
          <Button asChild size="lg" className="mt-8">
            <Link to="/login">{CTA_FINAL.cta}</Link>
          </Button>
        </FadeInSection>
      </div>
    </section>
  );
}
