import {
    app, api, state, ensureCorpusData, corpusTraditionKey,
    buildCorpusApiUrl, escapeHtml, formatNumber,
    regionOf, traditionColor,
} from "./core.js";
import { renderLibraryTree, setActiveNode } from "./tree-sources.js?v=10";

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
    libraryTree.addEventListener("region-select", (e) => onRegionClick(e.detail.region));
    libraryTree.addEventListener("tradition-select", (e) => onTraditionClick(e.detail.tradition, e.detail.region));
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
    } else if (state.selectedNode && state.selectedNode.kind === "book" && state.selectedNode.doc) {
        openCorpusDocument(state.selectedNode.doc);   // a book (picked here or on a graph page) → fully reopen: reader + info + highlight
    } else if (state.selectedNode && state.selectedNode.kind === "region") {
        showRegionInfo(state.selectedNode.key);   // restore the region: highlight AND load its info field
    } else if (state.selectedNode && state.selectedNode.kind === "tradition") {
        const [region, tradition] = (state.selectedNode.key || "").split("|");
        showTraditionInfo(tradition, region);   // restore the tradition: highlight AND load its info field
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
    renderBookInfo(null);   // cleared here; region/tradition callers then fill it with corpus stats
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

// The tree has already toggled when these fire.
// Region: a click on the selected region clears the selection (and leaves it collapsed);
// any other click selects the region and keeps it open, even if something inside it
// was selected and the tree just collapsed it.
function onRegionClick(region) {
    const sel = state.selectedNode;
    if (sel && sel.kind === "region" && sel.key === region) {
        clearSelection();
        return;
    }
    if (state.corpusOpenMajor !== region) {
        state.corpusOpenMajor = region;
        document.querySelectorAll("#libraryTree .major-section").forEach((s) =>
            s.classList.toggle("collapsed", (s.dataset.major || "Other") !== region));
    }
    showRegionInfo(region);
}

// Tradition: a click that collapses it clears the selection; one that expands it selects it.
function onTraditionClick(tradition, region) {
    if (state.corpusOpenTradition !== corpusTraditionKey(region, tradition)) clearSelection();
    else showTraditionInfo(tradition, region);
}

function clearSelection() {
    selectNode(null);
    renderBookInfo(null);
    const readerContent = document.getElementById("readerContent");
    if (readerContent) {
        readerContent.innerHTML = '<div class="reader-placeholder">Choose a title from the literature list.</div>';
    }
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
    renderGroupStats({
        docs: state.corpusDocuments.filter((d) => regionOf(d.tradition) === region),
        byTradition: true,
    });
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
    renderGroupStats({
        docs: state.corpusDocuments.filter((d) => d.tradition === tradition),
        parentWords: sumWords(state.corpusDocuments.filter((d) => regionOf(d.tradition) === region)),
        parentLabel: "of the region",
    });
}

const sumWords = (docs) => docs.reduce((n, d) => n + (d.word_count || 0), 0);

function percent(part, whole) {
    if (!whole) return "";
    const p = (100 * part) / whole;
    return p < 0.1 ? "<0.1%" : `${p < 10 ? p.toFixed(1) : Math.round(p)}%`;
}

// Right-hand panel for a region or tradition: how much text it holds, its share of
// the corpus, and its traditions and books ranked by size (each one opens on click).
function renderGroupStats({ docs, byTradition = false, parentWords = 0, parentLabel = "" }) {
    const bookInfo = document.getElementById("bookInfo");
    if (!bookInfo) return;

    const words = sumWords(docs);
    const sentences = docs.reduce((n, d) => n + (d.sentence_count || 0), 0);
    const corpusWords = sumWords(state.corpusDocuments);
    const traditions = new Map();
    docs.forEach((d) => {
        const t = traditions.get(d.tradition) || { name: d.tradition, words: 0, books: 0 };
        t.words += d.word_count || 0;
        t.books += 1;
        traditions.set(d.tradition, t);
    });

    const counts = [
        byTradition ? `${formatNumber(traditions.size)} ${traditions.size === 1 ? "tradition" : "traditions"}` : "",
        `${formatNumber(docs.length)} ${docs.length === 1 ? "book" : "books"}`,
    ].filter(Boolean).join(" · ");
    const shares = [
        parentWords ? `${percent(words, parentWords)} ${parentLabel}` : "",
        `${percent(words, corpusWords)} of the corpus`,
    ].filter(Boolean).join(" · ");

    // The name and colour already head the reader pane, so the panel starts with the numbers.
    let html = `
        <div class="group-stat">${formatNumber(words)} words · ${formatNumber(sentences)} sentences</div>
        <div class="group-stat-sub">${escapeHtml(counts)}</div>
        ${corpusWords ? `<div class="group-stat-sub">${escapeHtml(shares)}</div>` : ""}`;

    if (byTradition && traditions.size > 1) {
        const ranked = [...traditions.values()].sort((a, b) => b.words - a.words);
        html += `<div class="description-title">Traditions by volume (words)</div>
            <ol class="group-list">${ranked.map((t) => `<li>
                <button class="group-link" type="button" data-tradition="${escapeHtml(t.name)}">${escapeHtml(t.name)}</button>
                <span class="group-count">${formatNumber(t.words)}</span>
            </li>`).join("")}</ol>`;
    }

    const books = [...docs].sort((a, b) => (b.word_count || 0) - (a.word_count || 0));
    if (books.length) {
        html += `<div class="description-title">Books by volume (words)</div>
            <ol class="group-list">${books.map((d) => `<li>
                <button class="group-link" type="button" data-doc="${escapeHtml(d.document_id)}" title="${escapeHtml(d.title)}">
                    ${escapeHtml(d.title)}
                </button>
                <span class="group-count">${formatNumber(d.word_count || 0)}</span>
            </li>`).join("")}</ol>`;
    }

    bookInfo.innerHTML = html;
    bookInfo.querySelectorAll(".group-link[data-doc]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const doc = state.corpusDocuments.find((d) => d.document_id === btn.dataset.doc);
            if (doc) revealInTree(doc.tradition).then(() => openCorpusDocument(doc));
        });
    });
    bookInfo.querySelectorAll(".group-link[data-tradition]").forEach((btn) => {
        btn.addEventListener("click", () => {
            const t = btn.dataset.tradition;
            revealInTree(t).then(() => showTraditionInfo(t, regionOf(t)));
        });
    });
}

// Expand the tree on a tradition (its region and the group itself) before selecting in it.
async function revealInTree(tradition) {
    const region = regionOf(tradition);
    state.corpusOpenMajor = region;
    state.corpusOpenTradition = corpusTraditionKey(region, tradition);
    const tree = document.getElementById("libraryTree");
    if (tree) await renderLibraryTree(tree);
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
