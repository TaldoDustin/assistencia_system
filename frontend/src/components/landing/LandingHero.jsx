import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { FadeInSection } from "./FadeInSection";
import { HERO } from "./content";

export function LandingHero() {
  return (
    <section id="top" className="relative overflow-hidden pb-20 pt-32 lg:pb-28 lg:pt-40">
      <div className="mx-auto flex max-w-6xl flex-col items-center gap-12 px-4 text-center lg:px-6">
        <FadeInSection>
          <h1 className="text-5xl font-semibold leading-[1.1] text-foreground lg:text-6xl">{HERO.title}</h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground lg:text-xl">{HERO.subtitle}</p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <Button asChild size="lg" className="w-full sm:w-auto">
              <Link to="/login">{HERO.primaryCta}</Link>
            </Button>
            <Button asChild variant="outline" size="lg" className="w-full sm:w-auto">
              <a href="#como-funciona">{HERO.secondaryCta}</a>
            </Button>
          </div>
        </FadeInSection>

        {/* Mockup fiel ao Dashboard real (Card + Skeleton do próprio Design System) — nunca
            ilustração genérica de banco de imagens. Trocar por screenshot real é follow-up trivial. */}
        <FadeInSection delay={0.1} className="w-full">
          <Card className="mx-auto max-w-4xl text-left shadow-xl">
            <CardHeader className="flex-row items-center gap-2">
              <span className="h-2.5 w-2.5 rounded-full bg-destructive" />
              <span className="h-2.5 w-2.5 rounded-full bg-chart-3" />
              <span className="h-2.5 w-2.5 rounded-full bg-chart-2" />
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-3">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-40 w-full sm:col-span-3" />
            </CardContent>
          </Card>
        </FadeInSection>
      </div>
    </section>
  );
}
