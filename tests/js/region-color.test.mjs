import "./_stub-dom.mjs";
import assert from "node:assert/strict";
import { test } from "node:test";

import { hexToOklch, traditionShade } from "../../src/server/web/assets/region-color.js";

const HEX = /^#[0-9a-f]{6}$/;

test("N==1 returns the region base swatch", () => {
    const base = "#4F7A4E";
    assert.equal(traditionShade(base, 0, 1).toLowerCase(), base.toLowerCase());
});

test("shades are valid hex and preserve the region hue", () => {
    const base = "#E0B45E";
    const baseH = hexToOklch(base).H;
    for (let i = 0; i < 4; i++) {
        const shade = traditionShade(base, i, 4);
        assert.ok(HEX.test(shade), shade);
        // Hue held (small tolerance for gamut clipping); every shade still reads as the region.
        assert.ok(Math.abs(hexToOklch(shade).H - baseH) < 0.05);
    }
});

test("multiple traditions get distinct, ordered lightness", () => {
    const base = "#C0392B";
    const shades = [0, 1, 2, 3, 4].map((i) => traditionShade(base, i, 5));
    const uniq = new Set(shades.map((s) => s.toLowerCase()));
    assert.equal(uniq.size, 5);  // all distinct
    const Ls = shades.map((s) => hexToOklch(s).L);
    const sorted = [...Ls].sort((a, b) => a - b);
    assert.deepEqual(Ls, sorted);  // monotonically increasing lightness across the ramp
});

test("dark-theme band lifts lightness above the light band", () => {
    const base = "#2E7CB8";
    const light = hexToOklch(traditionShade(base, 3, 4, false)).L;
    const dark = hexToOklch(traditionShade(base, 3, 4, true)).L;
    assert.ok(dark > light);
});
