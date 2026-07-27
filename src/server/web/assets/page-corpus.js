import {
    app, api, state, ensureCorpusData, corpusTraditionKey,
    buildCorpusApiUrl, escapeHtml, formatNumber,
    regionOf, traditionColor,
} from "./core.js";
import { renderLibraryTree, setActiveNode } from "./tree-sources.js?v=8";

export async function renderCorpus(params = new URLSearchParams()) {
    app.innerHTML = `
        <main class="corpus-page container">
            <div class="workspace">
                <aside class="library-sidebar">
                    <div id="libraryTree">Loading...</div>
                </aside>

                <article class="card reader">
                    <div class="reader-content" id="readerContent">
                        <div class="reader-placeholder">Choose a title from the literature list.</div>
                    </div>
                </article>

                <aside class="card panel info-panel">
                    <div class="book-info" id="bookInfo"></div>
                </aside>
            </div>
        </main>
    `;

    const libraryTree = document.getElementById("libraryTree");
    libraryTree.addEventListener("book-select", (e) => openCorpusDocument(e.detail.doc));
    libraryTree.addEventListener("region-select", (e) => showRegionInfo(e.detail.region));
    libraryTree.addEventListener("tradition-select", (e) => showTraditionInfo(e.detail.tradition, e.detail.region));
    renderBookInfo(null);

    const wantedTitle = params.get("title");
    const wantedTradition = params.get("tradition");

    // Deep link to a tradition (atlas point): pre-open its accordion before the tree renders.
    if (wantedTradition && !wantedTitle) {
        await ensureCorpusData();
        const region = regionOf(wantedTradition);
        if (region) {
            state.corpusOpenMajor = region;
            state.corpusOpenTradition = corpusTraditionKey(region, wantedTradition);
            state.corpusTreeInitialized = true;   // keep our choice; don't let initTreeOpen override
        }
    }

    await renderLibraryTree(libraryTree);

    const target = wantedTitle
        ? state.corpusDocuments.find((doc) =>
            doc.title === wantedTitle && (!wantedTradition || doc.tradition === wantedTradition))
        : null;

    if (target) {
        openCorpusDocument(target);
    } else if (wantedTradition) {
        showTraditionInfo(wantedTradition, regionOf(wantedTradition));
    } else if (state.selectedNode) {
        setActiveNode(libraryTree, state.selectedNode);   // restore the one active item (region/tradition/book)
    }
}

// The single source of truth for "what is selected": set the one active node and reflect it in
// the tree. Region/tradition/book all route through here, so exactly one is ever highlighted.
function selectNode(node) {
    state.selectedNode = node;
    const tree = document.getElementById("libraryTree");
    if (tree) setActiveNode(tree, node);
}

function renderBookInfo(doc) {
    const bookInfo = document.getElementById("bookInfo");
    if (!bookInfo) return;

    if (!doc) {
        bookInfo.innerHTML = `
            <div class="empty-state">Select a book to view its words, sentences, and description.</div>
        `;
        return;
    }

    // Only web sources get a clickable link; local file sources show nothing.
    const isWebSource = /^https?:\/\//i.test(doc.url || "");
    const originalUrl = isWebSource
        ? `<a class="original-url-link" href="${escapeHtml(doc.url)}" target="_blank" rel="noopener noreferrer">Source</a>`
        : "";
    bookInfo.innerHTML = `
        <div class="book-title">${escapeHtml(doc.title)}</div>
        <div class="book-tradition">
            <span class="info-dot" style="--book-color:${escapeHtml(traditionColor(doc.tradition))}"></span>
            <span>${escapeHtml(regionOf(doc.tradition) || "Other")} / ${escapeHtml(doc.tradition || "Unknown")}</span>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">${formatNumber(doc.word_count)}</div>
                <div class="stat-label">Words</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">${formatNumber(doc.sentence_count)}</div>
                <div class="stat-label">Sentences</div>
            </div>
        </div>

        <div class="description-title">Description</div>
        <div class="description-text">${escapeHtml(doc.description || "No description available.")}</div>

        ${originalUrl}
    `;
}

function facetField(label, value) {
    if (!value) return "";
    return `<div class="facet-field">
        <div class="facet-field-label">${escapeHtml(label)}</div>
        <div class="facet-field-value">${escapeHtml(value)}</div>
    </div>`;
}

function facetListField(label, items) {
    if (!Array.isArray(items) || !items.length) return "";
    return `<div class="facet-field">
        <div class="facet-field-label">${escapeHtml(label)}</div>
        <ul class="facet-field-list">${items.map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ul>
    </div>`;
}

function renderFacetInfo(name, color, fields) {
    const readerContent = document.getElementById("readerContent");
    if (!readerContent) return;
    renderBookInfo(null);   // a facet has no book panel; the tree highlight is set by the caller (selectNode)
    readerContent.innerHTML = `
        <div class="facet-info">
            <div class="facet-title">
                <span class="facet-dot" style="--facet-color:${escapeHtml(color)}"></span>
                <span>${escapeHtml(name)}</span>
            </div>
            ${fields}
        </div>
    `;
    readerContent.scrollTop = 0;
}

function showRegionInfo(region) {
    const node = (state.traditionTree || {})[region];
    if (!node) return;
    selectNode({ kind: "region", key: region });
    const lead = node.description ? `<div class="facet-lead">${escapeHtml(node.description)}</div>` : "";
    const fields = lead
        + facetListField("Subdivision", node.subdivision)
        + facetListField("Strata", node.strata);
    renderFacetInfo(region, node.color || "#8a8a8a", fields);
}

function showTraditionInfo(tradition, region) {
    const info = ((state.traditionTree || {})[region] || {}).traditions?.[tradition];
    if (!info) return;
    selectNode({ kind: "tradition", key: corpusTraditionKey(region, tradition) });
    const lead = info.description ? `<div class="facet-lead">${escapeHtml(info.description)}</div>` : "";
    const fields = lead
        + facetField("Region", region)
        + facetField("Dating", info.dating);
    renderFacetInfo(tradition, traditionColor(tradition), fields);
}

async function openCorpusDocument(doc) {
    state.selectedCorpusDoc = doc;
    selectNode({ kind: "book", doc });   // the book is the one active item; clears any region/tradition
    renderBookInfo(doc);

    const readerContent = document.getElementById("readerContent");
    if (!readerContent) return;

    readerContent.innerHTML = '<div class="reader-placeholder">Loading book text...</div>';

    try {
        const text = await api(buildCorpusApiUrl(doc));
        readerContent.textContent = text;
        readerContent.scrollTop = 0;
    } catch (error) {
        readerContent.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}
