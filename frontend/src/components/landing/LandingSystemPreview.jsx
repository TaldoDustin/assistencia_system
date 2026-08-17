import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { FadeInSection } from "./FadeInSection";
import { SYSTEM_PREVIEW } from "./content";

// Mesma regra do Hero: mockup construído com os componentes reais do Design System
// (Card/Badge/Skeleton), nunca imagem de banco de imagens ou ilustração genérica.
export function LandingSystemPreview() {
  return (
    <section className="py-20 lg:py-28">
      <div className="mx-auto max-w-6xl px-4 text-center lg:px-6">
        <FadeInSection>
          <h2 className="text-3xl font-semibold text-foreground lg:text-4xl">{SYSTEM_PREVIEW.title}</h2>
          <p className="mx-auto mt-4 max-w-xl text-base text-muted-foreground">{SYSTEM_PREVIEW.subtitle}</p>
        </FadeInSection>

        <FadeInSection delay={0.1}>
          <Card className="mx-auto mt-10 max-w-4xl text-left shadow-xl">
            <CardHeader className="flex-row items-center justify-between">
              <span className="text-sm font-medium text-card-foreground">Fila de Atendimento</span>
              <Badge>Em andamento</Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              {[0, 1, 2, 3].map((row) => (
                <div key={row} className="flex items-center gap-3">
                  <Skeleton className="h-9 w-9 shrink-0 rounded-full" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-3 w-1/3" />
                    <Skeleton className="h-2.5 w-1/2" />
                  </div>
                  <Skeleton className="h-6 w-16 shrink-0 rounded-full" />
                </div>
              ))}
            </CardContent>
          </Card>
        </FadeInSection>
      </div>
    </section>
  );
}
