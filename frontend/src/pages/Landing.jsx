import { LandingNavbar } from "@/components/landing/LandingNavbar";
import { LandingHero } from "@/components/landing/LandingHero";
import { LandingProblem } from "@/components/landing/LandingProblem";
import { LandingSolution } from "@/components/landing/LandingSolution";
import { LandingBenefits } from "@/components/landing/LandingBenefits";
import { LandingFeatures } from "@/components/landing/LandingFeatures";
import { LandingHowItWorks } from "@/components/landing/LandingHowItWorks";
import { LandingSystemPreview } from "@/components/landing/LandingSystemPreview";
import { LandingDifferentiators } from "@/components/landing/LandingDifferentiators";
import { LandingSocialProof } from "@/components/landing/LandingSocialProof";
import { LandingPricing } from "@/components/landing/LandingPricing";
import { LandingFaq } from "@/components/landing/LandingFaq";
import { LandingCta } from "@/components/landing/LandingCta";
import { LandingFooter } from "@/components/landing/LandingFooter";

// Landing Page institucional — só renderizada em "/" para visitante deslogado
// (ver ProtectedRoute em App.jsx). Ordem das seções conforme
// docs/product/features/LANDING_PAGE.md Parte 2 (Hero -> Problema -> Solução ->
// Benefícios -> Funcionalidades -> Como funciona -> Visão do sistema -> Diferenciais ->
// Prova social -> Planos -> FAQ -> CTA -> Footer).
export default function Landing() {
  return (
    <div className="min-h-screen bg-background">
      <LandingNavbar />
      <main>
        <LandingHero />
        <LandingProblem />
        <LandingSolution />
        <LandingBenefits />
        <LandingFeatures />
        <LandingHowItWorks />
        <LandingSystemPreview />
        <LandingDifferentiators />
        <LandingSocialProof />
        <LandingPricing />
        <LandingFaq />
        <LandingCta />
      </main>
      <LandingFooter />
    </div>
  );
}
