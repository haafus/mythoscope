// Shared hover-tooltip helpers for the scatter charts (plotly + regl).
// echarts uses its own built-in tooltip, so it doesn't need these.

// Ensure the floating tooltip element exists inside #plotCanvas.
// Returns [container, tooltipEl], or [null, null] if the canvas is absent.
export function getTooltip() {
    const plotCanvas = document.getElementById("plotCanvas");
    if (!plotCanvas) return [null, null];
    let tip = plotCanvas.querySelector(".plot-hover-tooltip");
    if (!tip) {
        tip = document.createElement("div");
        tip.className = "plot-hover-tooltip";
        plotCanvas.appendChild(tip);
    }
    return [plotCanvas, tip];
}

// Place the tooltip near the cursor, flipping and clamping so it stays inside
// the container.
export function positionTooltip(container, tooltip, event) {
    const rect = container.getBoundingClientRect();
    const cx = event?.clientX ?? (rect.left + rect.width / 2);
    const cy = event?.clientY ?? (rect.top + rect.height / 2);
    const gap = 14, pad = 10;
    tooltip.style.left = "0px";
    tooltip.style.top = "0px";
    const w = tooltip.offsetWidth, h = tooltip.offsetHeight;
    let left = cx - rect.left + gap, top = cy - rect.top + gap;
    if (left + w + pad > rect.width) left = cx - rect.left - w - gap;
    if (top + h + pad > rect.height) top = cy - rect.top - h - gap;
    tooltip.style.left = `${Math.max(pad, Math.min(left, rect.width - w - pad))}px`;
    tooltip.style.top = `${Math.max(pad, Math.min(top, rect.height - h - pad))}px`;
}
