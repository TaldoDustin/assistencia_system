import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { FadeInSection } from "./FadeInSection";
import { FAQ } from "./content";

export function LandingFaq() {
  return (
    <section id="faq" className="py-20 lg:py-28">
      <div className="mx-auto max-w-3xl px-4 lg:px-6">
        <FadeInSection>
          <h2 className="text-center text-3xl font-semibold text-foreground lg:text-4xl">{FAQ.title}</h2>
        </FadeInSection>

        <FadeInSection delay={0.1}>
          <Accordion type="single" collapsible className="mt-10">
            {FAQ.items.map((item) => (
              <AccordionItem key={item.question} value={item.question}>
                <AccordionTrigger className="text-foreground">{item.question}</AccordionTrigger>
                <AccordionContent className="text-muted-foreground">{item.answer}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </FadeInSection>
      </div>
    </section>
  );
}
