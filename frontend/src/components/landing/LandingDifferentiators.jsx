import { CheckCircle, XCircle } from "@phosphor-icons/react";
import { Card, CardContent } from "@/components/ui/card";
import { FadeInSection } from "./FadeInSection";
import { DIFFERENTIATORS } from "./content";

// Mobile (<640px): lista empilhada, não scroll horizontal de tabela — regra explícita da spec.
export function LandingDifferentiators() {
  return (
    <section className="bg-card/40 py-20 lg:py-28">
      <div className="mx-auto max-w-4xl px-4 lg:px-6">
        <FadeInSection>
          <h2 className="text-center text-3xl font-semibold text-foreground lg:text-4xl">
            {DIFFERENTIATORS.title}
          </h2>
        </FadeInSection>

        <FadeInSection delay={0.1}>
          {/* Desktop/tablet: tabela real */}
          <table className="mt-10 hidden w-full overflow-hidden rounded-xl border border-border sm:table">
            <thead>
              <tr className="bg-card text-sm text-muted-foreground">
                <th className="px-4 py-3 text-left font-medium">Fluxoly</th>
                <th className="px-4 py-3 text-left font-medium">Gestão tradicional</th>
              </tr>
            </thead>
            <tbody>
              {DIFFERENTIATORS.rows.map((row) => (
                <tr key={row.fluxoly} className="border-t border-border">
                  <td className="px-4 py-3 text-sm text-card-foreground">
                    <span className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 shrink-0 text-chart-2" weight="fill" />
                      {row.fluxoly}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-muted-foreground">
                    <span className="flex items-center gap-2">
                      <XCircle className="h-4 w-4 shrink-0 text-muted-foreground" />
                      {row.traditional}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Mobile: lista empilhada */}
          <div className="mt-10 space-y-3 sm:hidden">
            {DIFFERENTIATORS.rows.map((row) => (
              <Card key={row.fluxoly}>
                <CardContent className="space-y-2 pt-6 text-sm">
                  <span className="flex items-center gap-2 text-card-foreground">
                    <CheckCircle className="h-4 w-4 shrink-0 text-chart-2" weight="fill" />
                    {row.fluxoly}
                  </span>
                  <span className="flex items-center gap-2 text-muted-foreground">
                    <XCircle className="h-4 w-4 shrink-0" />
                    {row.traditional}
                  </span>
                </CardContent>
              </Card>
            ))}
          </div>
        </FadeInSection>
      </div>
    </section>
  );
}
