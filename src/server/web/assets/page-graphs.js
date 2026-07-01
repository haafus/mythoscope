import { app, api, escapeHtml, onCleanup } from "./core.js";
import { renderLibraryTree, setActiveBook } from "./tree-sources.js";

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

    const bookList = document.getElementById("graphBookList");
    bookList.addEventListener("book-select", (e) => {
        setActiveBook(bookList, e.detail.doc);
        loadGraphData(e.detail.doc.title, graphType);
    });
    await renderLibraryTree(bookList);
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

    graphCy = cytoscape({
        container,
        elements: [...nodes, ...edges],
        style: [
            {
                selector: "node",
                style: {
                    "background-color": (ele) => GRAPH_CATEGORY_COLORS[ele.data("Category")] || "#aaaaaa",
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
                    "target-arrow-scale": 0.1,
                    "arrow-scale": 0.1,
                    "curve-style": "bezier",
                    label: "data(relation)",
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
        layout: {name: "cose", idealEdgeLength: 5, padding: 50, spacingFactor: 5, nodeRepulsion: 40000, gravity: 0.0005, numIter: 10000},
        wheelSensitivity: 0.5,
    });

    const cy = graphCy;

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
        tooltipDiv.innerHTML = `${escapeHtml(sName)} &rarr; ${escapeHtml(tName)}<br><strong>${escapeHtml(edge.data("relation") || "")}</strong>`;
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
        let html = `<h4>${escapeHtml(d.display_name || d.Name || d.id)}</h4>`;
        let metrics = "";
        fields.forEach((f) => {
            if (d[f] === undefined || d[f] === null || d[f] === "") return;
            const value = typeof d[f] === "object" ? JSON.stringify(d[f]) : String(d[f]);
            if (GRAPH_METRIC_FIELDS.has(f)) {
                metrics += `<tr><th>${escapeHtml(f)}</th><td>${escapeHtml(value)}</td></tr>`;
            } else if (f === "Description") {
                html += `<p class="graph-info-desc">${escapeHtml(value)}</p>`;  // no label, straight to text
            } else {
                html += `<div class="graph-info-field"><div class="graph-info-label">${escapeHtml(f)}</div>`
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
