// Per-tradition within-region shades (regions.md §8.1). Hold the region's hue and
// chroma; vary only lightness on a perceptually-uniform OKLCH band so every shade still
// reads as that region and stays colour-blind-robust. N traditions ramp across the band
// (grow-then-clamp, centred on the base); the texted corpus is ≤ ~7/region, so the plain
// L-ramp always suffices (the large-N L×C lattice never triggers here).

const BAND = { light: [0.42, 0.80], dark: [0.55, 0.92] };
const DL_TARGET = 0.045;

function srgbToLinear(c) { return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4); }
function linearToSrgb(c) { return c <= 0.0031308 ? 12.92 * c : 1.055 * Math.pow(c, 1 / 2.4) - 0.055; }

function hexToRgb(hex) {
    const h = String(hex || "").replace("#", "");
    return [0, 2, 4].map((i) => parseInt(h.slice(i, i + 2), 16) / 255);
}
function rgbToHex(r, g, b) {
    const f = (x) => Math.round(Math.max(0, Math.min(1, x)) * 255).toString(16).padStart(2, "0");
    return `#${f(r)}${f(g)}${f(b)}`;
}

function linearRgbToOklab(r, g, b) {
    const l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b;
    const m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b;
    const s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b;
    const l_ = Math.cbrt(l), m_ = Math.cbrt(m), s_ = Math.cbrt(s);
    return [
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    ];
}
function oklabToLinearRgb(L, a, b) {
    const l_ = L + 0.3963377774 * a + 0.2158037573 * b;
    const m_ = L - 0.1055613458 * a - 0.0638541728 * b;
    const s_ = L - 0.0894841775 * a - 1.2914855480 * b;
    const l = l_ ** 3, m = m_ ** 3, s = s_ ** 3;
    return [
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
    ];
}

export function hexToOklch(hex) {
    const [r, g, b] = hexToRgb(hex).map(srgbToLinear);
    const [L, a, bb] = linearRgbToOklab(r, g, b);
    let H = Math.atan2(bb, a);
    if (H < 0) H += 2 * Math.PI;
    return { L, C: Math.hypot(a, bb), H };
}

function inGamut(r, g, b) {
    const e = 1e-4;
    return [r, g, b].every((x) => x >= -e && x <= 1 + e);
}

export function oklchToHex(L, C, H) {
    // Clip chroma down (keeping L, H) until the colour is representable in sRGB.
    let c = C;
    for (let i = 0; i < 24; i++) {
        const rgb = oklabToLinearRgb(L, c * Math.cos(H), c * Math.sin(H));
        if (inGamut(...rgb)) return rgbToHex(...rgb.map(linearToSrgb));
        c *= 0.92;
    }
    return rgbToHex(...oklabToLinearRgb(L, 0, 0).map(linearToSrgb));
}

// The shade for tradition `index` of `count` in a region, off its base hex.
// index is the within-region order (by longitude; caller decides), count the region size.
export function traditionShade(regionHex, index, count, dark = false) {
    const { L: Lbase, C, H } = hexToOklch(regionHex);
    const [lo, hi] = BAND[dark ? "dark" : "light"];
    if (!count || count <= 1) return oklchToHex(Lbase, C, H);       // N==1 → the base swatch
    const W = Math.min(hi - lo, (count - 1) * DL_TARGET);
    let L = Lbase - W / 2 + index * (W / (count - 1));
    // Slide the whole ramp back inside the safe band, then clamp for safety.
    const rampLo = Lbase - W / 2, rampHi = Lbase + W / 2;
    if (rampLo < lo) L += lo - rampLo;
    else if (rampHi > hi) L -= rampHi - hi;
    return oklchToHex(Math.max(lo, Math.min(hi, L)), C, H);
}
