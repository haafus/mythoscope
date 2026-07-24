
import { normalizePreviewText, CATEGORY_NONE } from "./core.js";
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
}

export function resizeChart(el) {
    if (window.Plotly && el.dataset.plotly === "1") {
        setTimeout(() => Plotly.relayout(el, { autosize: true }), 100);
    }
}

// null/"" resets. Traces map to el._traditions order.
export function highlightTradition(el, tradition) {
    if (!window.Plotly || el.dataset.plotly !== "1") return;
    const traditions = el._traditions || [];
    const colors = el._traditionColors || [];
    if (!traditions.length) return;
    const selected = (t) => !tradition || t === tradition;
    const color = traditions.map((t, i) => (selected(t) ? colors[i] : dimColor(colors[i])));
    const opacity = traditions.map((t) => (selected(t) ? 0.74 : 0.45));
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

    await Plotly.newPlot(el, traces, layout, { responsive: true, displaylogo: false, displayModeBar: true, scrollZoom: true });
    el.dataset.plotly = "1";
    bindTooltip(el);
    el.on("plotly_click", (event) => {
        if (event.points && event.points[0]) {
            onPointClick(event.points[0].customdata[0], event.points[0].customdata[2]);
        }
    });
}

export async function renderHeatmap(el, data) {
    const traditions = data.traditions || [];
    const distances = data.distances || [];
    if (!window.Plotly || !traditions.length) throw new Error("Heatmap data is empty.");

    el.style.display = "block";

    const trace = {
        type: "heatmap",
        z: distances,
        x: traditions,
        y: traditions,
        colorscale: "Viridis",
        hovertemplate: "Distance between %{x} and %{y}: %{z:.4f}<extra></extra>",
    };

    const layout = {
        margin: { l: 120, r: 60, t: 40, b: 140 },
        paper_bgcolor: "#fff",
        plot_bgcolor: "#fff",
        xaxis: { tickangle: 45, tickfont: { size: 11 }, automargin: true },
        yaxis: { tickfont: { size: 11 }, automargin: true },
    };

    await Plotly.newPlot(el, [trace], layout, { responsive: true, displaylogo: false, displayModeBar: true });
    el.dataset.plotly = "1";
}

export async function renderDistribution(el, data, { colorMap }) {
    const traditions = data.traditions || [];
    if (!window.Plotly || !traditions.length) throw new Error("Distribution data is empty.");

    el.style.display = "block";

    const names = traditions.map((t) => t.name);
    const trace = {
        type: "bar",
        x: traditions.map((t) => t.chunks),
        y: names,
        orientation: "h",
        marker: { color: names.map((n) => colorMap[n]) },
        text: traditions.map((t) => `${t.chunks.toLocaleString()} chunks (${t.percentage}%)`),
        textposition: "outside",
        cliponaxis: false,
        hovertemplate: "<b>%{y}</b><br>Chunks: %{x:,}<br>Source texts: %{customdata}<extra></extra>",
        customdata: traditions.map((t) => t.doc_count),
    };

    const layout = {
        margin: { l: 160, r: 140, t: 40, b: 60 },
        paper_bgcolor: "#fff",
        plot_bgcolor: "rgba(248,249,250,0.95)",
        showlegend: false,
        height: Math.max(500, 28 * names.length + 120),
        xaxis: { title: { text: "Number of chunks" }, automargin: true, tickfont: { size: 11 } },
        yaxis: { autorange: "reversed", tickfont: { size: 11 }, automargin: true },
    };

    await Plotly.newPlot(el, [trace], layout, { responsive: true, displaylogo: false, displayModeBar: true });
    el.dataset.plotly = "1";
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

