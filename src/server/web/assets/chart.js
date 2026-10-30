
import { normalizePreviewText, CATEGORY_NONE, escapeHtml, traditionInfo } from "./core.js";
import { pointTooltipHtml } from "./search-utils.js";
import { getTooltip, positionTooltip } from "./chart-tooltip.js";
import { dimColor } from "./chart-color.js";

let activeChart = null;
let tooltipHandlers = null;

export function destroyChart(el) {
    if (tooltipHandlers) {
        clearTooltipHandlers(el);
    }
    if (window.Plotly) {
        try { Plotly.purge(el); } catch { /* already torn down */ }
    }
    activeChart = null;
    el.innerHTML = "";
    el.dataset.plotly = "";
    el.dataset.heatmap = "";
    el._heatmap = null;
    el._traditions = null;
}

// A tree selection lights its rows and columns in the heatmap and fades the rest.
function highlightHeatmap(el, selection) {
    const { labels } = el._heatmap || {};
    if (!labels) return;
    const inSel = (i) => !selection || (selection instanceof Set ? selection.has(labels[i]) : labels[i] === selection);
    el.querySelectorAll(".hm-cell").forEach((cell) =>
        cell.classList.toggle("faded", !(inSel(+cell.dataset.r) || inSel(+cell.dataset.c))));
    el.querySelectorAll(".hm-label").forEach((l) =>
        l.classList.toggle("faded", !inSel(+(l.dataset.row ?? l.dataset.col))));
}

export function resizeChart(el) {
    if (el.dataset.heatmap === "1") { fitHeatmap(el); return; }
    if (window.Plotly && el.dataset.plotly === "1") {
        setTimeout(() => Plotly.relayout(el, { autosize: true }), 100);
    }
}

// null/"" resets. Traces map to el._traditions order.
// `selection`: null/"" → all lit; a tradition string → that one; a Set of names → those
// (used for a whole region — dim every tradition not in the region). Same dimming either way.
export function highlightTradition(el, selection) {
    if (el.dataset.heatmap === "1") return highlightHeatmap(el, selection);
    if (!window.Plotly || el.dataset.plotly !== "1") return;
    const traditions = el._traditions || [];
    const colors = el._traditionColors || [];
    if (!traditions.length) return;
    const inSel = selection instanceof Set ? (t) => selection.has(t) : (t) => t === selection;
    const lit = (t) => !selection || inSel(t);
    const color = traditions.map((t, i) => (lit(t) ? colors[i] : dimColor(colors[i])));
    const opacity = traditions.map((t) => (lit(t) ? 0.74 : 0.45));
    Plotly.restyle(el, { "marker.color": color, "marker.opacity": opacity });
}

export async function renderScatter(el, data, { colorMap, onPointClick }) {
    const points = Array.isArray(data.points) ? data.points : [];
    if (!window.Plotly || !points.length) throw new Error("Projection data is empty.");

    el.style.display = "block";

    const traditions = [...new Set(points.map((p) => p.tradition || "Unknown"))];
    el._traditions = traditions; // trace order, for highlightTradition
    el._traditionColors = traditions.map((t) => colorMap[t] || CATEGORY_NONE);

    const traces = traditions.map((tradition) => {
        const pts = points.filter((p) => (p.tradition || "Unknown") === tradition);
        return {
            type: "scattergl",
            x: pts.map((p) => p.x),
            y: pts.map((p) => p.y),
            mode: "markers",
            name: tradition,
            marker: {
                size: 6,
                opacity: 0.74,
                color: colorMap[tradition],
                line: { width: 0.4, color: "rgba(255,255,255,0.85)" },
            },
            customdata: pts.map((p) => [
                p.id,
                p.tradition,
                p.chunk_index,
                normalizePreviewText(p.text).substring(0, 220),
            ]),
            hoverinfo: "none",
        };
    });

    const layout = {
        dragmode: "pan",   // default modebar tool
        margin: { l: 50, r: 28, t: 28, b: 48 },
        plot_bgcolor: "#fbfcfd",
        paper_bgcolor: "#fff",
        hovermode: "closest",
        hoverdistance: 3, // match the marker radius (size 6) so hover triggers only on the point
        hoverlabel: {
            align: "left",
            bgcolor: "#fff",
            bordercolor: "#ced4da",
            font: { color: "#212529", size: 12 },
            namelength: 24,
        },
        showlegend: false,
        xaxis: { automargin: true, gridcolor: "#edf1f5", zeroline: false, tickfont: { size: 11, color: "#6c757d" } },
        yaxis: { automargin: true, gridcolor: "#edf1f5", zeroline: false, tickfont: { size: 11, color: "#6c757d" } },
    };

    await Plotly.newPlot(el, traces, layout, {
        responsive: true,
        displaylogo: false,
        displayModeBar: true,
        scrollZoom: true,
        modeBarButtonsToRemove: ["autoScale2d"],
    });
    el.dataset.plotly = "1";
    bindTooltip(el);
    el.on("plotly_click", (event) => {
        if (event.points && event.points[0]) {
            onPointClick(event.points[0].customdata[0], event.points[0].customdata[2]);
        }
    });
}

// Tradition similarity heatmap (after mockup 13): similarity = 1 − the stored centroid distance,
// double-centred so each tradition's overall closeness to everything drops out; colour shows how
// much closer (teal) or farther (orange) a pair is than expected. Rows are seriated by clustering.
export async function renderHeatmap(el, data) {
    const labels = data.traditions || [];
    const dist = data.distances || [];
    const n = labels.length;
    if (!n) throw new Error("Heatmap data is empty.");

    const sim = dist.map((row) => row.map((d) => 1 - d));
    const rowMean = sim.map((row, i) => row.reduce((s, v, j) => (j === i ? s : s + v), 0) / Math.max(1, n - 1));
    let total = 0, count = 0;
    sim.forEach((row, i) => row.forEach((v, j) => { if (i !== j) { total += v; count += 1; } }));
    const mean = count ? total / count : 0;
    const resid = (i, j) => sim[i][j] - rowMean[i] - rowMean[j] + mean;
    let maxDev = 0;
    for (let i = 0; i < n; i++) for (let j = 0; j < n; j++) if (i !== j) maxDev = Math.max(maxDev, Math.abs(resid(i, j)));
    maxDev = maxDev || 1;

    el._heatmap = { labels, sim, resid, maxDev, order: seriate(dist) };
    el._traditions = labels;   // the region dimming looks up which traditions are on the chart
    el.dataset.heatmap = "1";
    el.style.display = "block";
    drawHeatmap(el);
    bindHeatmapTooltip(el);
}

// Average-linkage clustering of the distances; each merge is oriented so that the ends that meet
// are the closest pair — a cheap stand-in for optimal leaf ordering.
function seriate(dist) {
    let clusters = dist.map((_, i) => [i]);
    const avg = (a, b) => {
        let s = 0;
        a.forEach((x) => b.forEach((y) => { s += dist[x][y]; }));
        return s / (a.length * b.length);
    };
    while (clusters.length > 1) {
        let best = [0, 1], bestD = Infinity;
        for (let a = 0; a < clusters.length; a++) {
            for (let b = a + 1; b < clusters.length; b++) {
                const d = avg(clusters[a], clusters[b]);
                if (d < bestD) { bestD = d; best = [a, b]; }
            }
        }
        const A = clusters[best[0]], B = clusters[best[1]];
        const rA = A.slice().reverse(), rB = B.slice().reverse();
        const joined = [[A, B], [rA, B], [A, rB], [rA, rB]]
            .map(([x, y]) => [x, y, dist[x[x.length - 1]][y[0]]])
            .sort((p, q) => p[2] - q[2])[0];
        clusters = clusters.filter((_, k) => k !== best[0] && k !== best[1]).concat([joined[0].concat(joined[1])]);
    }
    return clusters[0] || [];
}

// t in [-1, 1]: orange (farther) ← warm neutral → teal (closer than expected).
function divergingColor(t) {
    const neutral = [244, 242, 236], closer = [14, 92, 84], farther = [194, 65, 12];
    const to = t >= 0 ? closer : farther, k = Math.min(1, Math.abs(t));
    const c = neutral.map((x, i) => Math.round(x + (to[i] - x) * k));
    return `rgb(${c[0]},${c[1]},${c[2]})`;
}

// Drawn at a nominal 26px cell and scaled down (labels included) to fit the card without
// scrolling; it never grows past the nominal size.
function drawHeatmap(el) {
    const { labels, sim, resid, maxDev, order } = el._heatmap;
    const n = labels.length;
    const cell = 26, lab = 150, head = 118;
    const width = lab + n * cell + 8, height = head + n * cell + 4;

    let svg = `<svg class="heatmap-svg" viewBox="0 0 ${width} ${height}" data-w="${width}" data-h="${height}" data-grid-x="${lab}" data-grid-w="${n * cell - 2}">`;
    order.forEach((ci, c) => {
        const x = lab + c * cell + cell / 2;
        svg += `<text class="hm-label" data-col="${ci}" x="${x}" y="${head - 6}" transform="rotate(-55 ${x} ${head - 6})">${escapeHtml(labels[ci])}</text>`;
    });
    order.forEach((ri, r) => {
        const y = head + r * cell;
        const info = traditionInfo(labels[ri]);
        svg += `<text class="hm-label" data-row="${ri}" x="${lab - 10}" y="${y + cell / 2 + 4}" text-anchor="end">${escapeHtml(labels[ri])}</text>`;
        svg += `<rect x="${lab - 6}" y="${y + 3}" width="3" height="${cell - 6}" rx="1" fill="${escapeHtml(info?.regionColor || CATEGORY_NONE)}"/>`;
        order.forEach((ci, c) => {
            const self = ri === ci;
            const dev = self ? 0 : resid(ri, ci);
            const t = self ? 1 : Math.max(-1, Math.min(1, dev / maxDev));
            svg += `<rect class="hm-cell" data-r="${ri}" data-c="${ci}" data-sim="${sim[ri][ci].toFixed(3)}" data-dev="${dev.toFixed(3)}"`
                + ` x="${lab + c * cell}" y="${y}" width="${cell - 2}" height="${cell - 2}" rx="3" fill="${divergingColor(t)}"/>`;
        });
    });
    svg += "</svg>";
    const ramp = [-1, -0.5, 0, 0.5, 1].map(divergingColor).join(", ");
    el.innerHTML = `<div class="heatmap-wrap">${svg}
        <div class="heatmap-legend"><span>farther</span><span class="heatmap-ramp" style="background:linear-gradient(90deg, ${ramp})"></span><span>closer than expected</span></div></div>`;
    fitHeatmap(el);
}

function fitHeatmap(el) {
    const wrap = el.querySelector(".heatmap-wrap"), svg = el.querySelector(".heatmap-svg");
    const legend = el.querySelector(".heatmap-legend");
    if (!wrap || !svg) return;
    const style = getComputedStyle(wrap);
    const availW = wrap.clientWidth - parseFloat(style.paddingLeft) - parseFloat(style.paddingRight);
    const availH = el.parentElement.clientHeight - parseFloat(style.paddingTop) - parseFloat(style.paddingBottom)
        - legend.offsetHeight - parseFloat(getComputedStyle(legend).marginTop);
    const w = +svg.dataset.w, h = +svg.dataset.h;
    const scale = Math.max(0.1, Math.min(1, availW / w, availH / h));
    svg.setAttribute("width", Math.floor(w * scale));
    svg.setAttribute("height", Math.floor(h * scale));
    // The legend sits centred under the grid of cells, not under the labels.
    const gridX = +svg.dataset.gridX * scale, gridW = +svg.dataset.gridW * scale;
    legend.style.width = "max-content";
    const legendW = Math.max(gridW, legend.offsetWidth);
    legend.style.width = `${Math.round(legendW)}px`;
    legend.style.marginLeft = `${Math.round(Math.max(0, gridX + (gridW - legendW) / 2))}px`;
}

// Bound once per element (the plot element outlives every re-render); reads the current map.
function bindHeatmapTooltip(el) {
    if (el._heatmapTooltipBound) return;
    const [canvas, tooltip] = getTooltip();
    if (!canvas) return;
    el._heatmapTooltipBound = true;
    el.addEventListener("mousemove", (event) => {
        if (!el._heatmap) return;
        const { labels } = el._heatmap;
        const cell = event.target.closest(".hm-cell");
        el.classList.toggle("hm-hovering", !!cell);
        el.querySelectorAll(".hm-label.on").forEach((l) => l.classList.remove("on"));
        if (!cell) { tooltip.classList.remove("visible"); return; }
        const r = +cell.dataset.r, c = +cell.dataset.c, dev = +cell.dataset.dev;
        el.querySelector(`.hm-label[data-row="${r}"]`)?.classList.add("on");
        el.querySelector(`.hm-label[data-col="${c}"]`)?.classList.add("on");
        tooltip.innerHTML = r === c
            ? `<strong>${escapeHtml(labels[r])}</strong>`
            : `<strong>${escapeHtml(labels[r])}</strong> ↔ <strong>${escapeHtml(labels[c])}</strong>`
                + `<div>similarity ${cell.dataset.sim}</div>`
                + `<div class="hm-tip-dev">${dev >= 0 ? "+" : "−"}${Math.abs(dev).toFixed(3)} ${dev >= 0 ? "closer" : "farther"} than expected</div>`;
        tooltip.classList.add("visible");
        positionTooltip(canvas, tooltip, event);
    });
    el.addEventListener("mouseleave", () => {
        if (!el._heatmap) return;
        el.classList.remove("hm-hovering");
        el.querySelectorAll(".hm-label.on").forEach((l) => l.classList.remove("on"));
        tooltip.classList.remove("visible");
    });
}

function bindTooltip(plotEl) {
    const [canvas, tooltip] = getTooltip();
    if (!canvas) return;
    clearTooltipHandlers(plotEl);

    const hide = () => { tooltip.classList.remove("visible"); };

    const show = (event) => {
        const point = event.points && event.points[0];
        if (!point) return hide();

        const custom = Array.isArray(point.customdata) ? point.customdata : [];
        // Must be keyed document_id (custom[0]) — attributionLine resolves via documentById.
        tooltip.innerHTML = pointTooltipHtml({
            document_id: custom[0],
            chunk_index: custom[2],
            text: custom[3],
        });
        tooltip.classList.add("visible");
        positionTooltip(canvas, tooltip, event.event);
    };

    const move = (event) => {
        if (tooltip.classList.contains("visible")) {
            positionTooltip(canvas, tooltip, event);
        }
    };

    plotEl.on("plotly_hover", show);
    plotEl.on("plotly_unhover", hide);
    plotEl.addEventListener("mouseleave", hide);
    plotEl.addEventListener("mousemove", move);
    tooltipHandlers = { plotEl, show, hide, move };
}

function clearTooltipHandlers(plotEl) {
    if (!tooltipHandlers) return;
    const h = tooltipHandlers;
    if (typeof plotEl.removeListener === "function") {
        plotEl.removeListener("plotly_hover", h.show);
        plotEl.removeListener("plotly_unhover", h.hide);
    }
    plotEl.removeEventListener("mouseleave", h.hide);
    plotEl.removeEventListener("mousemove", h.move);
    tooltipHandlers = null;
}

