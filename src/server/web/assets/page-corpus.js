import {
    app, api, state,
    buildCorpusApiUrl, escapeHtml, formatNumber,
    regionOf, traditionColor,
} from "./core.js";
import { renderLibraryTree, setActiveBook } from "./tree-sources.js?v=6";

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

    await renderLibraryTree(libraryTree);

    // Deep link from the geography popups: #/corpus?title=…&tradition=…
    const wantedTitle = params.get("title");
    const wantedTradition = params.get("tradition");
    const target = wantedTitle
        ? state.corpusDocuments.find((doc) =>
            doc.title === wantedTitle && (!wantedTradition || doc.tradition === wantedTradition))
        : null;

    if (target) {
        openCorpusDocument(target);
    } else if (state.selectedCorpusDoc) {
        setActiveBook(libraryTree, state.selectedCorpusDoc);
    }
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

// Semicolon-separated strings (subdivision, strata) rendered as a bullet list.
function facetListField(label, value) {
    const items = (value || "").split(";").map((s) => s.trim()).filter(Boolean);
    if (!items.length) return "";
    return `<div class="facet-field">
        <div class="facet-field-label">${escapeHtml(label)}</div>
        <ul class="facet-field-list">${items.map((s) => `<li>${escapeHtml(s)}</li>`).join("")}</ul>
    </div>`;
}

function renderFacetInfo(color, kind, name, fields) {
    const readerContent = document.getElementById("readerContent");
    if (!readerContent) return;
    readerContent.innerHTML = `
        <div class="facet-info">
            <div class="facet-kind">${escapeHtml(kind)}</div>
            <div class="facet-title">
                <span class="info-dot" style="--book-color:${escapeHtml(color)}"></span>
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
    const lead = node.description ? `<div class="facet-lead">${escapeHtml(node.description)}</div>` : "";
    const fields = lead
        + facetListField("Subdivision", node.subdivision)
        + facetListField("Strata", node.strata);
    renderFacetInfo(node.color || "#8a8a8a", "Region", region, fields);
}

function showTraditionInfo(tradition, region) {
    const info = ((state.traditionTree || {})[region] || {}).traditions?.[tradition];
    if (!info) return;
    const lead = info.description ? `<div class="facet-lead">${escapeHtml(info.description)}</div>` : "";
    const fields = lead
        + facetField("Region", region)
        + facetField("Dating", info.dating);
    renderFacetInfo(traditionColor(tradition), "Tradition", tradition, fields);
}

async function openCorpusDocument(doc) {
    state.selectedCorpusDoc = doc;
    const libraryTree = document.getElementById("libraryTree");
    if (libraryTree) setActiveBook(libraryTree, doc);
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
