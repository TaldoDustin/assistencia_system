import { Card, CardContent } from "@/components/ui/card";
import { FadeInSection } from "./FadeInSection";
import { PROBLEM } from "./content";

export function LandingProblem() {
  return (
    <section className="py-20 lg:py-28">
      <div className="mx-auto max-w-6xl px-4 lg:px-6">
        <FadeInSection>
          <h2 className="text-center text-3xl font-semibold text-foreground lg:text-4xl">{PROBLEM.title}</h2>
        </FadeInSection>

        <div className="mt-10 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {PROBLEM.cards.map((text, index) => (
            <FadeInSection key={text} delay={index * 0.05}>
              <Card className="h-full">
                <CardContent className="pt-6 text-sm text-card-foreground">{text}</CardContent>
              </Card>
            </FadeInSection>
          ))}
        </div>

        <FadeInSection>
          <p className="mx-auto mt-10 max-w-2xl text-center text-base text-muted-foreground">{PROBLEM.closing}</p>
        </FadeInSection>
      </div>
    </section>
  );
}
