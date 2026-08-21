import { describe, it, expect } from "vitest";
import { contrastRatio, compositeOverBackground } from "./contrast";
import { LIGHT_SURFACE, LIGHT_SEMANTIC } from "./theme-tokens";

const AA_NORMAL_TEXT_MIN = 4.5;
const BADGE_TINT_OPACITY = 0.1;

// badge.jsx renderiza as cores semânticas como texto sobre um fundo do próprio tom a 10% de
// opacidade ("bg-<cor>/10 text-<cor>"), composto sobre a superfície clara real por baixo -- não
// contra branco puro. Os dois fundos reais do app: o card (branco) e o fundo de página
// (--color-background, cinza muito claro).
const LIGHT_PAGE_BACKGROUND = "#F5F6FA";
const REAL_LIGHT_SURFACES = [LIGHT_SURFACE, LIGHT_PAGE_BACKGROUND];

describe("cores semânticas do Light Mode -- WCAG AA (cenário real: badge com tint a 10%)", () => {
  it.each(Object.entries(LIGHT_SEMANTIC))(
    "%s (%s) passa AA >= 4.5:1 como texto sobre seu próprio tint a 10pct, em ambas as superfícies claras",
    (_name, hex) => {
      for (const surface of REAL_LIGHT_SURFACES) {
        const compositedBadgeBg = compositeOverBackground(hex, surface, BADGE_TINT_OPACITY);
        expect(contrastRatio(hex, compositedBadgeBg)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT_MIN);
      }
    }
  );
});
