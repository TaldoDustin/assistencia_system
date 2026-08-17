import { ShoppingCart, Package, CurrencyDollar, UserCircle, Wrench, ChartBar } from "@phosphor-icons/react";
import { Card, CardContent } from "@/components/ui/card";
import { FadeInSection } from "./FadeInSection";
import { FEATURES } from "./content";

const ICONS = { ShoppingCart, Package, CurrencyDollar, UserCircle, Wrench, ChartBar };

export function LandingFeatures() {
  return (
    <section id="funcionalidades" className="bg-card/40 py-20 lg:py-28">
      <div className="mx-auto max-w-6xl px-4 lg:px-6">
        <FadeInSection className="text-center">
          <h2 className="text-3xl font-semibold text-foreground lg:text-4xl">{FEATURES.title}</h2>
          <p className="mx-auto mt-4 max-w-2xl text-base text-muted-foreground">{FEATURES.subtitle}</p>
        </FadeInSection>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {FEATURES.pillars.map((pillar, index) => {
            const Icon = ICONS[pillar.icon];
            return (
              <FadeInSection key={pillar.name} delay={index * 0.05}>
                <Card className="h-full">
                  <CardContent className="pt-6">
                    <Icon className="h-6 w-6 text-primary" weight="duotone" />
                    <h3 className="mt-4 text-lg font-medium text-card-foreground">{pillar.name}</h3>
                    <p className="mt-1 text-sm text-muted-foreground">{pillar.text}</p>
                  </CardContent>
                </Card>
              </FadeInSection>
            );
          })}
        </div>
      </div>
    </section>
  );
}
