import { app, api, escapeHtml, onCleanup, state, CATEGORY_NONE } from "./core.js";
import { renderLibraryTree, setActiveBook } from "./tree-sources.js?v=9";

let graphCy = null;

function destroyGraph() {
    if (graphCy) {
        graphCy.destroy();
        graphCy = null;
    }
}

const GRAPH_CATEGORY_COLORS = {
    Character: "#dcd0ff",
    Location: "#c8e6c9",
    Epoch: "#fff3cd",
    Other: "#cccccc",
};

const GRAPH_INFO_FIELDS = {
    beings: ["Description", "Roles", "Epithets", "Attributes", "Actions", "Degree", "BetweennessCentrality"],
    realms: ["Description", "Function", "Adjacent To", "Degree", "BetweennessCentrality"],
    ages: ["Description", "Keyactors", "Keyevents", "Degree"],
};
// Numeric metrics stay as a compact two-column table at the end of the panel.
const GRAPH_METRIC_FIELDS = new Set(["Degree", "BetweennessCentrality"]);
// Display labels for fields whose data key is not presentation-ready.
const GRAPH_FIELD_LABELS = {
    BetweennessCentrality: "Betweenness Centrality",
    "Adjacent To": "Adjacent to",
    Keyevents: "Key Events",
    Keyactors: "Key Actors",
};

// Repair metadata joined before dicts were flattened server-side: replace any
// leftover Python-style "{'k': 'v', ...}" fragment in a string with its values,
// e.g. "…, {'Power': 'Strong hand', 'Judgment': 'Sees all'}, …" -> "…, Strong
// hand, Sees all, …". A no-op once the graph is rebuilt (no fragments remain).
function stripDictFragments(s) {
    if (s.indexOf("{") === -1) return s;
    const replaced = s.replace(/\{[^{}]*\}/g, (frag) =>
        [...frag.matchAll(/:\s*'([^']*)'|:\s*"([^"]*)"/g)].map((m) => m[1] ?? m[2]).join(", "));
    return replaced.split(",").map((p) => p.trim()).filter(Boolean).join(", ");
}

// Render a raw field value to a trimmed display string, or "" when it carries no
// content — an empty object/array, a blank or "nan" string — so the caller can
// skip the field instead of printing "{}", "[]" or "nan".
function graphFieldText(raw) {
    if (raw === undefined || raw === null) return "";
    if (typeof raw === "number") return String(raw);
    const clean = (v) => String(v).trim();
    const kept = (v) => v && v.toLowerCase() !== "nan";
    if (Array.isArray(raw)) return raw.map(clean).filter(kept).join(", ");
    if (typeof raw === "object") {
        return Object.entries(raw)
            .map(([k, v]) => [k, clean(v)])
            .filter(([, v]) => kept(v))
            .map(([k, v]) => `${k}: ${v}`)
            .join(", ");
    }
    const s = stripDictFragments(clean(raw));
    return s.toLowerCase() === "nan" ? "" : s;
}

// fcose has no seed option; its randomness comes from the global Math.random.
// Run the layout under a seeded PRNG (mulberry32) so the same graph lays out
// identically every time, then restore. Different graphs still differ.
function runSeededLayout(cy, options, seed) {
    const original = Math.random;
    let s = seed >>> 0;
    Math.random = () => {
        s = (s + 0x6D2B79F5) | 0;
        let t = Math.imul(s ^ (s >>> 15), 1 | s);
        t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
        return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
    try { cy.layout(options).run(); } finally { Math.random = original; }
}

export async function renderGraphPage(graphType) {
    app.innerHTML = `
        <main class="graph-page container">
            <div class="workspace">
                <aside class="library-sidebar">
                    <div id="graphBookList">Loading...</div>
                </aside>
                <section class="graph-area">
                    <div class="graph-canvas" id="graphCanvas">
                        <div class="graph-placeholder" id="graphPlaceholder">Select a book to view its graph.</div>
                    </div>
                </section>
                <aside class="graph-rail rail">
                    <div class="card graph-info-panel" id="graphInfoPanel">
                        <div id="graphInfoContent" class="rail-body">
                            <div class="graph-info-empty">Select a node to see its details.</div>
                        </div>
                    </div>
                </aside>
            </div>
        </main>
    `;

    onCleanup(destroyGraph);

    const onResize = () => {
        if (!graphCy) return;
        graphCy.minZoom(1e-3);   // relax the floor so the refit isn't clamped by the old one
        graphCy.resize();
        graphCy.fit(graphCy.elements(), 40);
        graphCy.minZoom(graphCy.zoom());   // re-floor at the new fit
    };
    window.addEventListener("resize", onResize);
    onCleanup(() => window.removeEventListener("resize", onResize));

    const bookList = document.getElementById("graphBookList");
    bookList.addEventListener("book-select", (e) => {
        state.selectedCorpusDoc = e.detail.doc;   // shared across sources + all graph pages
        setActiveBook(bookList, e.detail.doc);
        loadGraphData(e.detail.doc.document_id, graphType);  // graphs keyed by document_id (D1)
    });
    await renderLibraryTree(bookList);

    // Restore the selection carried over from another section.
    if (state.selectedCorpusDoc) {
        setActiveBook(bookList, state.selectedCorpusDoc);
        loadGraphData(state.selectedCorpusDoc.document_id, graphType);
    }
}

async function loadGraphData(bookId, graphType) {
    const placeholder = document.getElementById("graphPlaceholder");
    const canvas = document.getElementById("graphCanvas");
    if (placeholder) placeholder.style.display = "none";  // blank while loading — no "Loading graph…" flash

    destroyGraph();

    try {
        const data = await api(`/api/graphs/${encodeURIComponent(bookId)}/${encodeURIComponent(graphType)}`);
        if (placeholder) placeholder.style.display = "none";
        renderCytoscapeGraph(canvas, data, graphType);
    } catch (error) {
        if (placeholder) {
            placeholder.textContent = `Error: ${error.message}`;
            placeholder.style.display = "block";
        }
    }
}

function renderCytoscapeGraph(container, data, graphType) {
    if (typeof cytoscape === "undefined") {
        const placeholder = document.getElementById("graphPlaceholder");
        if (placeholder) {
            placeholder.textContent = "Cytoscape.js library could not be loaded.";
            placeholder.style.display = "block";
        }
        return;
    }

    const nodes = (data.nodes || []).map((node) => ({data: node}));
    const edges = (data.edges || []).map((edge) => ({data: edge}));
    const edgeLabels = graphType === "beings";  // ages/realms edges are all the same relation — no label

    graphCy = cytoscape({
        container,
        elements: [...nodes, ...edges],
        style: [
            {
                selector: "node",
                style: {
                    "background-color": (ele) => GRAPH_CATEGORY_COLORS[ele.data("Category")] || CATEGORY_NONE,
                    width: (ele) => ele.data("size") || 3,
                    height: (ele) => ele.data("size") || 3,
                    label: (ele) => ele.data("display_name") || ele.data("Name") || ele.data("id"),
                    "font-size": "2.2px",
                    "text-valign": "bottom",
                    "text-halign": "center",
                    "text-margin-y": 1,
                    "border-width": 0.2,
                    "border-color": "#555",
                },
            },
            {
                selector: "edge",
                style: {
                    width: 0.2,
                    "line-color": "#aaa",
                    "target-arrow-color": "#aaa",
                    "target-arrow-shape": "triangle",
                    "arrow-scale": 0.1,
                    "curve-style": "bezier",
                    label: edgeLabels ? "data(relation)" : "",
                    "font-size": "1.5px",
                    "text-rotation": "autorotate",
                    "text-margin-y": -1,
                    "text-background-opacity": 0.7,
                    "text-background-color": "#ffffff",
                },
            },
            {
                selector: "node.hover-highlight",
                style: {"border-width": 0.3, "border-color": "#ffaa00", "overlay-opacity": 0.3, "overlay-color": "#ffaa00", "overlay-padding": "1px"},
            },
            {
                selector: "edge.hover-highlight",
                style: {width: 0.4, "line-color": "#ffaa00", "target-arrow-color": "#ffaa00"},
            },
            {
                selector: "node.pinned",
                style: {"border-width": 0.6, "border-color": "#ff8800", "overlay-opacity": 0.35, "overlay-color": "#ffaa00", "overlay-padding": "1px"},
            },
            {
                selector: ".faded",
                style: {opacity: 0.1},
            },
        ],
        layout: {name: "preset", fit: false},  // fit:false — don't zoom onto the (0,0) cluster (huge nodes)
        wheelSensitivity: 0.5,
        maxZoom: 10,
    });

    const cy = graphCy;

    // Measure the canvas, then run fcose HEADLESS so it also fits the viewport (centre + right
    // zoom) up front — fcose's own animation instead plays from the (0,0) corner and only fits at
    // the end. With the viewport already framed, animate the nodes from a slight inward collapse
    // out to their final spots: a visible settle that stays centred, no corner, no zoom jump.
    cy.resize();
    runSeededLayout(cy, {
        name: "fcose", animate: false, randomize: true,
        idealEdgeLength: 15, nodeSeparation: 30, nodeRepulsion: 4500, gravity: 0.25,
    }, 1);
    // fcose fits the graph to the viewport, so the current zoom is the "whole graph
    // visible" level — floor min zoom there (can't zoom out past the bounding box).
    cy.minZoom(cy.zoom());

    const finals = cy.nodes().map((n) => ({n, x: n.position("x"), y: n.position("y")}));
    const bb = cy.elements().boundingBox();
    const cx = (bb.x1 + bb.x2) / 2;
    const cyc = (bb.y1 + bb.y2) / 2;
    cy.batch(() => finals.forEach((f) => f.n.position({x: cx + (f.x - cx) * 0.6, y: cyc + (f.y - cyc) * 0.6})));
    finals.forEach((f) => f.n.animate({position: {x: f.x, y: f.y}}, {duration: 200, easing: "ease-out"}));

    let hoveredNode = null;
    let pinnedNode = null;  // click-pinned selection; survives mouseout until the next click

    const highlightNode = (node) => {
        const set = node.union(node.neighborhood().nodes()).union(node.connectedEdges());
        cy.elements().removeClass("faded hover-highlight");
        cy.elements().not(set).addClass("faded");
        set.addClass("hover-highlight");
    };
    const restoreHighlight = () => {
        if (pinnedNode) highlightNode(pinnedNode);
        else cy.elements().removeClass("faded hover-highlight");
    };

    cy.on("mouseover", "node", (evt) => {
        if (hoveredNode === evt.target) return;
        hoveredNode = evt.target;
        highlightNode(hoveredNode);
    });
    cy.on("mouseout", "node", () => {
        hoveredNode = null;
        restoreHighlight();  // fall back to the pinned node, if any
    });

    const tooltipDiv = document.createElement("div");
    tooltipDiv.className = "graph-edge-tooltip";
    container.appendChild(tooltipDiv);

    let cachedRect = container.getBoundingClientRect();
    cy.on("mouseover", "edge", (evt) => {
        cachedRect = container.getBoundingClientRect();
        const edge = evt.target;
        const sName = cy.getElementById(edge.data("source")).data("display_name") || edge.data("source");
        const tName = cy.getElementById(edge.data("target")).data("display_name") || edge.data("target");
        tooltipDiv.innerHTML = `${escapeHtml(sName)}<br><strong>${escapeHtml(edge.data("relation") || "")}</strong><br>${escapeHtml(tName)}`;
        tooltipDiv.style.left = (evt.originalEvent.clientX - cachedRect.left + 10) + "px";
        tooltipDiv.style.top = (evt.originalEvent.clientY - cachedRect.top + 10) + "px";
        tooltipDiv.style.display = "block";
    });
    cy.on("mousemove", "edge", (evt) => {
        tooltipDiv.style.left = (evt.originalEvent.clientX - cachedRect.left + 10) + "px";
        tooltipDiv.style.top = (evt.originalEvent.clientY - cachedRect.top + 10) + "px";
    });
    cy.on("mouseout", "edge", () => {
        tooltipDiv.style.display = "none";
    });

    const infoContent = document.getElementById("graphInfoContent");
    const infoPlaceholder = '<div class="graph-info-empty">Select a node to see its details.</div>';
    if (infoContent) infoContent.innerHTML = infoPlaceholder;

    cy.on("tap", "node", (evt) => {
        // Pin the selection on this node until the next click elsewhere.
        cy.nodes().removeClass("pinned");
        pinnedNode = evt.target;
        pinnedNode.addClass("pinned");
        highlightNode(pinnedNode);

        const d = evt.target.data();
        const fields = GRAPH_INFO_FIELDS[graphType] || GRAPH_INFO_FIELDS.beings;
        let html = `<h3>${escapeHtml(d.display_name || d.Name || d.id)}</h3>`;
        let metrics = "";
        fields.forEach((f) => {
            const value = graphFieldText(d[f]);
            if (!value) return;  // skip absent/empty fields ({}, [], blank, nan)
            const label = GRAPH_FIELD_LABELS[f] || f;
            if (GRAPH_METRIC_FIELDS.has(f)) {
                // Betweenness is a long float — round to 5 decimals for display.
                const shown = f === "BetweennessCentrality" && typeof d[f] === "number"
                    ? String(Math.round(d[f] * 1e5) / 1e5)
                    : value;
                metrics += `<tr><th>${escapeHtml(label)}</th><td>${escapeHtml(shown)}</td></tr>`;
            } else if (f === "Description") {
                html += `<p class="graph-info-desc">${escapeHtml(value)}</p>`;  // no label, straight to text
            } else {
                html += `<div class="graph-info-field"><div class="graph-info-label">${escapeHtml(label)}</div>`
                      + `<div class="graph-info-value">${escapeHtml(value)}</div></div>`;
            }
        });
        if (metrics) html += `<table>${metrics}</table>`;
        infoContent.innerHTML = html;
    });

    // A tap on empty canvas clears the pinned selection.
    cy.on("tap", (evt) => {
        if (evt.target !== cy) return;  // background only (node taps handled above)
        pinnedNode = null;
        cy.nodes().removeClass("pinned");
        if (hoveredNode === null) cy.elements().removeClass("faded hover-highlight");
        if (infoContent) infoContent.innerHTML = infoPlaceholder;
    });
}
