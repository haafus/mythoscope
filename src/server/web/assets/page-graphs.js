import {
    app, api, escapeHtml, onCleanup, state, CATEGORY_NONE,
    ensureCorpusData, corpusTraditionKey, formatNumber, regionOf, traditionColor,
    documentById, groupDocuments,
} from "./core.js";
import { setHashUrl } from "./url.js?v=1";
import { renderLibraryTree, setActiveBook } from "./tree-sources.js?v=10";

let graphCy = null;

function destroyGraph() {
    if (graphCy) {
        graphCy.destroy();
        graphCy = null;
    }
}

const GRAPH_CATEGORY_COLORS = {
    Character: "#f0d5c8",
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
    BetweennessCentrality: "Betweenness centrality",
    "Adjacent To": "Adjacent to",
    Keyevents: "Key Events",
    Keyactors: "Key Actors",
};

// The three graphs of a book, in switcher order; Structure opens on the last one used.
const GRAPH_TYPES = [["beings", "Beings"], ["realms", "Realms"], ["ages", "Ages"]];
let lastGraphType = "beings";

// What one node of each graph is, for the book summary ("42 characters").
const GRAPH_ENTITY_NOUNS = { beings: "characters", realms: "places", ages: "periods" };
const SUMMARY_TOP_N = 8;

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

// The URL holds the graph, the book and the picked node: #/structure?graph=beings&book=<document_id>&node=<id>.
function urlFor(graphType, doc, nodeId = null) {
    return `#/structure?graph=${graphType}` + (doc ? `&book=${encodeURIComponent(doc.document_id)}` : "")
        + (doc && nodeId ? `&node=${encodeURIComponent(nodeId)}` : "");
}

export async function renderGraphPage(params = new URLSearchParams()) {
    const wanted = params.get("graph");
    let graphType = GRAPH_TYPES.some(([t]) => t === wanted) ? wanted : lastGraphType;
    lastGraphType = graphType;

    app.innerHTML = `
        <main class="graph-page container">
            <div class="workspace">
                <aside class="library-sidebar structure-sidebar">
                    <div class="motifs-tabs" id="graphTabs">
                        ${GRAPH_TYPES.map(([t, label]) => `
                            <button class="motifs-tab${t === graphType ? " active" : ""}" type="button" data-graph="${t}">${label}</button>
                        `).join("")}
                    </div>
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

    // The book on screen (null when none) — distinct from the app-wide state.selectedCorpusDoc,
    // which a bare in-page URL deliberately does not show.
    let currentDoc = null;

    // Switching graphs keeps the page: only the canvas and the rail reload.
    const tabs = document.getElementById("graphTabs");
    tabs.querySelectorAll(".motifs-tab").forEach((btn) => {
        btn.addEventListener("click", () => {
            if (btn.dataset.graph === graphType) return;
            graphType = lastGraphType = btn.dataset.graph;
            tabs.querySelectorAll(".motifs-tab").forEach((b) => b.classList.toggle("active", b === btn));
            setHashUrl(urlFor(graphType, currentDoc));
            if (currentDoc) loadGraphData(currentDoc, graphType);
        });
    });

    const bookList = document.getElementById("graphBookList");
    bookList.addEventListener("book-select", (e) => {
        state.selectedCorpusDoc = e.detail.doc;   // shared across sources + all graph pages
        state.selectedNode = { kind: "book", doc: e.detail.doc };  // keep the global "active item" in sync so sources restores it
        currentDoc = e.detail.doc;
        setActiveBook(bookList, e.detail.doc);
        setHashUrl(urlFor(graphType, e.detail.doc));
        loadGraphData(e.detail.doc, graphType);
    });

    // The book comes from the URL; without one, a graph is always shown (see defaultBook).
    // The tree opens on it: region and tradition expanded, the row scrolled into view.
    await ensureCorpusData();
    const bookId = params.get("book");
    const fromUrl = bookId ? documentById(bookId) : null;
    const carried = fromUrl || defaultBook();
    if (fromUrl) {
        state.selectedCorpusDoc = carried;
        state.selectedNode = { kind: "book", doc: carried };
    } else if (carried) {
        state.selectedCorpusDoc = carried;   // the selected region/tradition stays the active node
    }
    currentDoc = carried;
    const nodeId = carried ? params.get("node") : null;
    setHashUrl(urlFor(graphType, carried, nodeId), false);
    if (carried) {
        const region = regionOf(carried.tradition);
        if (region) {
            state.corpusOpenMajor = region;
            state.corpusOpenTradition = corpusTraditionKey(region, carried.tradition);
        }
    }
    await renderLibraryTree(bookList);

    if (carried) {
        setActiveBook(bookList, carried);
        bookList.querySelector(".document-button.active")?.scrollIntoView({ block: "nearest" });
        loadGraphData(carried, graphType, nodeId);
    }
}

// With no book in the URL: the selected book, else the current book if it lies within the
// selected tradition or region (or anywhere, with nothing selected), else the first book of
// that tradition, region or the whole corpus in tree order.
function defaultBook() {
    const node = state.selectedNode;
    if (node && node.kind === "book" && node.doc) return node.doc;
    const tradition = node && node.kind === "tradition" ? (node.key || "").split("|")[1] : null;
    const region = node && node.kind === "region" ? node.key : null;
    const inScope = (d) => (tradition ? d.tradition === tradition : region ? regionOf(d.tradition) === region : true);
    if (state.selectedCorpusDoc && inScope(state.selectedCorpusDoc)) return state.selectedCorpusDoc;
    for (const [major, traditions] of groupDocuments(state.corpusDocuments)) {
        if (region && major !== region) continue;
        for (const [name, docs] of traditions) {
            if (tradition && name !== tradition) continue;
            if (docs.length) return docs[0];
        }
    }
    return null;
}

const CATEGORY_NOUNS = { Character: "Character", Location: "Place", Epoch: "Period" };

// The rail for a picked node, in the book summary's style: title, a muted line saying what
// it is and where it comes from, its text fields under section labels, and its network
// position as a plain two-column list.
function renderNodeDetails(d, graphType, doc) {
    const fields = GRAPH_INFO_FIELDS[graphType] || GRAPH_INFO_FIELDS.beings;
    const kind = CATEGORY_NOUNS[d.Category];
    const meta = [kind, doc ? `in ${doc.title}` : ""].filter(Boolean).join(" ");

    let html = `<div class="graph-book-title">${escapeHtml(d.display_name || d.Name || d.id)}</div>`;
    if (meta) html += `<div class="graph-book-meta">${escapeHtml(meta)}</div>`;

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
            metrics += `<li><span>${escapeHtml(label)}</span><span class="graph-book-count">${escapeHtml(shown)}</span></li>`;
        } else if (f === "Description") {
            html += `<div class="graph-book-text graph-node-desc">${escapeHtml(value)}</div>`;
        } else {
            html += `<div class="graph-book-label">${escapeHtml(label)}</div>
                <div class="graph-book-text">${escapeHtml(value)}</div>`;
        }
    });
    if (metrics) html += `<div class="graph-book-label">Network</div><ul class="graph-book-list">${metrics}</ul>`;
    return html;
}

// The right rail's default content: what this book is and what its graph holds.
// Shown until a node is picked, and again when the pick is cleared.
function renderBookSummary(doc, data, graphType) {
    const nodes = (data && data.nodes) || [];
    const edges = (data && data.edges) || [];
    const name = (n) => n.display_name || n.Name || n.id;

    const meta = [
        doc.dating,
        doc.word_count ? `${formatNumber(doc.word_count)} words` : "",
        doc.sentence_count ? `${formatNumber(doc.sentence_count)} sentences` : "",
    ].filter(Boolean).join(" · ");

    let html = `<div class="graph-book-title">${escapeHtml(doc.title)}</div>
        <div class="graph-book-tradition">
            <span class="graph-book-dot" style="--book-color:${escapeHtml(traditionColor(doc.tradition))}"></span>
            <span>${escapeHtml(regionOf(doc.tradition) || "Other")} / ${escapeHtml(doc.tradition || "Unknown")}</span>
        </div>`;
    if (meta) html += `<div class="graph-book-meta">${escapeHtml(meta)}</div>`;
    // Known before the graph loads, so it sits first and stays put while the rest fills in.
    if (doc.description) {
        html += `<div class="graph-book-label">Description</div>
            <div class="graph-book-text">${escapeHtml(doc.description)}</div>`;
    }

    if (data) {
        const top = [...nodes].sort((a, b) => (b.Degree || 0) - (a.Degree || 0)).slice(0, SUMMARY_TOP_N);
        if (top.length) {
            html += `<div class="graph-book-label">Most connected</div>
                <ol class="graph-book-list">${top.map((n) => `<li>
                    <button class="graph-book-node" type="button" data-node-id="${escapeHtml(n.id)}">${escapeHtml(name(n))}</button>
                    <span class="graph-book-count">${formatNumber(n.Degree || 0)}</span>
                </li>`).join("")}</ol>`;
        }

        if (graphType === "beings") {
            const counts = new Map();
            edges.forEach((e) => {
                const rel = String(e.relation || "").trim().toLowerCase();
                if (rel) counts.set(rel, (counts.get(rel) || 0) + 1);
            });
            const rels = [...counts].sort((a, b) => b[1] - a[1]).slice(0, SUMMARY_TOP_N);
            if (rels.length) {
                html += `<div class="graph-book-label">Most frequent relations</div>
                    <ol class="graph-book-list">${rels.map(([rel, n]) => `<li>
                        <span>${escapeHtml(rel)}</span><span class="graph-book-count">${formatNumber(n)}</span>
                    </li>`).join("")}</ol>`;
            }
        }

        const noun = GRAPH_ENTITY_NOUNS[graphType] || "entities";
        html += `<div class="graph-book-label">This graph</div>
            <div class="graph-book-text">${formatNumber(nodes.length)} ${noun}, ${formatNumber(edges.length)} links</div>`;
    }

    if (data) html += `<div class="graph-info-empty graph-book-hint">Select a node to see its details.</div>`;
    return html;
}

// Each load supersedes the previous one, so a quick switch of book or graph
// never lets a slower, older response overwrite the newer one.
let loadSeq = 0;

async function loadGraphData(doc, graphType, nodeId = null) {
    const seq = ++loadSeq;
    const bookId = doc.document_id;  // graphs keyed by document_id (D1)
    const infoContent = document.getElementById("graphInfoContent");
    if (infoContent) infoContent.innerHTML = renderBookSummary(doc, null, graphType);
    const placeholder = document.getElementById("graphPlaceholder");
    const canvas = document.getElementById("graphCanvas");
    if (placeholder) placeholder.style.display = "none";  // blank while loading — no "Loading graph…" flash

    destroyGraph();

    try {
        const data = await api(`/api/graphs/${encodeURIComponent(bookId)}/${encodeURIComponent(graphType)}`);
        if (seq !== loadSeq) return;
        if (placeholder) placeholder.style.display = "none";
        renderCytoscapeGraph(canvas, data, graphType, doc, nodeId);
    } catch (error) {
        if (seq !== loadSeq) return;
        if (placeholder) {
            placeholder.textContent = `Error: ${error.message}`;
            placeholder.style.display = "block";
        }
    }
}

function renderCytoscapeGraph(container, data, graphType, doc, nodeId = null) {
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

    // Node tooltip: the node name + a truncated description (same idea as the similarity preview).
    const nodeTip = document.createElement("div");
    nodeTip.className = "graph-node-tooltip";
    container.appendChild(nodeTip);
    const NODE_TIP_MAX = 200;
    const placeNodeTip = (evt) => {
        nodeTip.style.left = (evt.originalEvent.clientX - cachedRect.left + 12) + "px";
        nodeTip.style.top = (evt.originalEvent.clientY - cachedRect.top + 12) + "px";
    };
    cy.on("mouseover", "node", (evt) => {
        cachedRect = container.getBoundingClientRect();
        const node = evt.target;
        const name = node.data("display_name") || node.data("Name") || node.data("id") || "";
        let desc = graphFieldText(node.data("Description"));
        if (desc.length > NODE_TIP_MAX) desc = desc.slice(0, NODE_TIP_MAX).trimEnd() + "…";
        nodeTip.innerHTML = `<strong>${escapeHtml(name)}</strong>${desc ? `<div class="graph-node-tooltip-desc">${escapeHtml(desc)}</div>` : ""}`;
        placeNodeTip(evt);
        nodeTip.style.display = "block";
    });
    cy.on("mousemove", "node", placeNodeTip);
    cy.on("mouseout", "node", () => {
        nodeTip.style.display = "none";
    });

    const infoContent = document.getElementById("graphInfoContent");
    const showSummary = () => {
        if (!infoContent) return;
        infoContent.innerHTML = renderBookSummary(doc, data, graphType);
        // "Most connected" names pick their node, exactly as a click on the canvas would.
        infoContent.querySelectorAll(".graph-book-node").forEach((btn) => {
            btn.addEventListener("click", () => cy.getElementById(btn.dataset.nodeId).emit("tap"));
        });
    };
    showSummary();

    // Pin the selection on this node until the next click elsewhere.
    const pinNode = (node, push = true) => {
        cy.nodes().removeClass("pinned");
        pinnedNode = node;
        pinnedNode.addClass("pinned");
        highlightNode(pinnedNode);
        infoContent.innerHTML = renderNodeDetails(node.data(), graphType, doc);
        setHashUrl(urlFor(graphType, doc, node.id()), push);
    };
    cy.on("tap", "node", (evt) => pinNode(evt.target));

    // A tap on empty canvas clears the pinned selection.
    cy.on("tap", (evt) => {
        if (evt.target !== cy) return;  // background only (node taps handled above)
        pinnedNode = null;
        cy.nodes().removeClass("pinned");
        if (hoveredNode === null) cy.elements().removeClass("faded hover-highlight");
        showSummary();
        setHashUrl(urlFor(graphType, doc));
    });

    // A node from the URL (a shared link, or Back) is restored; one this graph lacks is dropped.
    if (nodeId) {
        const node = cy.getElementById(nodeId);
        if (node.nonempty()) pinNode(node, false);
        else setHashUrl(urlFor(graphType, doc), false);
    }
}
