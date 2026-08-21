function srgbChannelToLinear(channel255) {
  const c = channel255 / 255;
  return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
}

function hexToRgb(hex) {
  const normalized = hex.replace("#", "");
  const value = normalized.length === 3
    ? normalized.split("").map((ch) => ch + ch).join("")
    : normalized;
  const num = parseInt(value, 16);
  return { r: (num >> 16) & 255, g: (num >> 8) & 255, b: num & 255 };
}

function relativeLuminance(hex) {
  const { r, g, b } = hexToRgb(hex);
  return (
    0.2126 * srgbChannelToLinear(r) +
    0.7152 * srgbChannelToLinear(g) +
    0.0722 * srgbChannelToLinear(b)
  );
}

/** Razão de contraste WCAG 2.x entre duas cores hex (#RGB ou #RRGGBB). Retorna de 1 a 21. */
export function contrastRatio(hexA, hexB) {
  const lumA = relativeLuminance(hexA);
  const lumB = relativeLuminance(hexB);
  const lighter = Math.max(lumA, lumB);
  const darker = Math.min(lumA, lumB);
  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Achata uma cor semi-transparente sobre um fundo opaco (alpha compositing padrão),
 * simulando o efeito real de `bg-<cor>/10` do Tailwind renderizado sobre uma superfície
 * clara sólida. Usado para testar contraste no cenário real (ex.: badge.jsx), não contra
 * a cor pura.
 */
export function compositeOverBackground(foregroundHex, backgroundHex, opacity) {
  const fg = hexToRgb(foregroundHex);
  const bg = hexToRgb(backgroundHex);
  const mix = (fgChannel, bgChannel) => Math.round(bgChannel * (1 - opacity) + fgChannel * opacity);
  const toHex = (value) => value.toString(16).padStart(2, "0");
  const r = mix(fg.r, bg.r);
  const g = mix(fg.g, bg.g);
  const b = mix(fg.b, bg.b);
  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}
