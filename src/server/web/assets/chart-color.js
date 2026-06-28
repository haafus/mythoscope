const PLOT_BG = [251, 252, 253]; // #fbfcfd

function hexToRgb(hex) {
    const c = String(hex).replace("#", "");
    const pairs = c.length === 3
        ? [0, 1, 2].map((i) => c[i] + c[i])
        : [c.slice(0, 2), c.slice(2, 4), c.slice(4, 6)];
    return pairs.map((h) => parseInt(h, 16));
}

// Blend a color toward the plot background. Dimmed points are tinted (not just
// faded) so overlapping markers don't add up to bright clumps.
export function dimColor(hex, ratio = 0.86) {
    const rgb = hexToRgb(hex);
    const blend = rgb.map((v, i) => Math.round(v + (PLOT_BG[i] - v) * ratio));
    return `rgb(${blend[0]},${blend[1]},${blend[2]})`;
}
