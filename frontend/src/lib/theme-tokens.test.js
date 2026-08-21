import { describe, it, expect } from "vitest";
import { contrastRatio } from "./contrast";
import { LIGHT_SURFACE, LIGHT_SEMANTIC } from "./theme-tokens";

const AA_NORMAL_TEXT_MIN = 4.5;

describe("cores semânticas do Light Mode -- WCAG AA", () => {
  it.each(Object.entries(LIGHT_SEMANTIC))(
    "%s (%s) passa AA >= 4.5:1 contra a superfície clara",
    (_name, hex) => {
      expect(contrastRatio(hex, LIGHT_SURFACE)).toBeGreaterThanOrEqual(AA_NORMAL_TEXT_MIN);
    }
  );
});
