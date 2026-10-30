import {
    app, api, state, ensureCorpusData, corpusTraditionKey,
    buildCorpusApiUrl, escapeHtml, formatNumber,
    regionOf, traditionColor, documentById,
} from "./core.js";
import { setHashUrl } from "./url.js?v=1";
import { renderLibraryTree, setActiveNode } from "./tree-sources.js?v=10";

// The URL holds the selection: #/corpus (nothing), ?region=, ?tradition=, ?book=<document_id>.
// While a render restores state from it, selections must not push new history entries.
let restoring = false;

function urlFor(node) {
    const q = (k, v) => `#/corpus?${k}=${encodeURIComponent(v)}`;
    if (!node) return "#/corpus";
    if (node.kind === "region") return q("region", node.key);
    if (node.kind === "tradition") return q("tradition", (node.key || "").split("|")[1] || "");
    if (node.kind === "book" && node.doc) return q("book", node.doc.document_id);
    return "#/corpus";
}

// What the URL asks for, or — when the page is entered from another section with a bare
// URL — the selection the app already holds. Back to a bare URL within Corpus means none.
function nodeFromParams(params, samePage) {
    const bookId = params.get("book");
    const title = params.get("title");   // older links: ?title=…&tradition=…
    const tradition = params.get("tradition");
    const region = params.get("region");
    const doc = bookId ? documentById(bookId)
        : title ? state.corpusDocuments.find((d) => d.title === title && (!tradition || d.tradition === tradition))
        : null;
    if (doc) return { kind: "book", doc };
    if (tradition) return { kind: "tradition", key: corpusTraditionKey(regionOf(tradition), tradition) };
    if (region) return { kind: "region", key: region };
    if (!samePage && state.selectedNode) return state.selectedNode;
    return null;
}

export async function renderCorpus(params = new URLSearchParams(), { samePage = false } = {}) {
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

    await ensureCorpusData();
    const node = nodeFromParams(params, samePage);

    // Open the tree on the selection before it renders.
    if (node && node.kind === "region") {
        state.corpusOpenMajor = node.key;
    } else if (node) {
        const tradition = node.kind === "book" ? node.doc.tradition : (node.key || "").split("|")[1];
        const region = regionOf(tradition);
        state.corpusOpenMajor = region;
        state.corpusOpenTradition = corpusTraditionKey(region, tradition);
    }

    await renderLibraryTree(libraryTree);

    restoring = true;
    try {
        if (node && node.kind === "book") {
            openCorpusDocument(node.doc);
        } else if (node && node.kind === "region") {
            showRegionInfo(node.key);
        } else if (node && node.kind === "tradition") {
            const [region, tradition] = (node.key || "").split("|");
            showTraditionInfo(tradition, region);
        } else {
            selectNode(null);
            showCorpusOverview();   // nothing selected: the whole corpus at a glance
        }
    } finally {
        restoring = false;
    }
    setHashUrl(urlFor(state.selectedNode), false);   // e.g. an old ?title= link becomes ?book=
}

// The single source of truth for "what is selected": set the one active node and reflect it in
// the tree. Region/tradition/book all route through here, so exactly one is ever highlighted.
function selectNode(node) {
    state.selectedNode = node;
    const tree = document.getElementById("libraryTree");
    if (tree) setActiveNode(tree, node);
    if (!restoring) setHashUrl(urlFor(node));
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
    const sizeLines = [
        doc.word_count ? [counted(doc.word_count, "word", "words")] : [],
        doc.sentence_count ? [counted(doc.sentence_count, "sentence", "sentences")] : [],
    ];
    bookInfo.innerHTML = `
        <div class="book-title">${escapeHtml(doc.title)}</div>
        <div class="book-tradition">
            <span class="info-dot" style="--book-color:${escapeHtml(traditionColor(doc.tradition))}"></span>
            <span>${escapeHtml(regionOf(doc.tradition) || "Other")} / ${escapeHtml(doc.tradition || "Unknown")}</span>
        </div>

        ${doc.dating ? `<div class="book-meta">${escapeHtml(doc.dating)}</div>` : ""}
        ${figures(sizeLines)}

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

// Tradition: the same rule one level down — a click on the selected tradition clears the
// selection; a click while one of its books is selected selects the tradition, kept open.
function onTraditionClick(tradition, region) {
    const key = corpusTraditionKey(region, tradition);
    const sel = state.selectedNode;
    if (sel && sel.kind === "tradition" && sel.key === key) {
        clearSelection();
        return;
    }
    if (state.corpusOpenTradition !== key) {
        state.corpusOpenTradition = key;
        document.querySelectorAll("#libraryTree .tradition-group").forEach((g) => {
            const s = g.closest(".major-section");
            const open = corpusTraditionKey(s?.dataset.major, g.dataset.tradition) === key;
            g.classList.toggle("open", open);
            const toggle = g.querySelector(".tradition-toggle");
            if (toggle) toggle.textContent = open ? "▾" : "▸";
        });
    }
    showTraditionInfo(tradition, region);
}

function clearSelection() {
    selectNode(null);
    showCorpusOverview();
}

const regionColorOf = (region) => ((state.traditionTree || {})[region] || {}).color || "#8a8a8a";

// The empty state: three word-count histograms (macro-areas, traditions, books) in the
// reader and the corpus totals in the panel. Every bar label selects what it names.
function showCorpusOverview() {
    const docs = state.corpusDocuments;
    const readerContent = document.getElementById("readerContent");
    const bookInfo = document.getElementById("bookInfo");
    if (!docs.length) {
        renderBookInfo(null);
        return;
    }

    const regions = new Map();
    const traditions = new Map();
    docs.forEach((d) => {
        const region = regionOf(d.tradition) || "Other";
        const r = regions.get(region) || { name: region, words: 0 };
        r.words += d.word_count || 0;
        regions.set(region, r);
        const t = traditions.get(d.tradition) || { name: d.tradition, words: 0 };
        t.words += d.word_count || 0;
        traditions.set(d.tradition, t);
    });
    const byWords = (a, b) => b.words - a.words;
    const books = docs.map((d) => ({ name: d.title, words: d.word_count || 0, doc: d })).sort(byWords);

    const bars = (rows, colorOf, attr) => {
        const max = Math.max(1, ...rows.map((r) => r.words));
        return `<div class="csbars corpus-bars">${rows.map((r) => `
            <div class="csbar-row" title="${escapeHtml(r.name)}: ${formatNumber(r.words)} words">
                <button class="csbar-lab corpus-bar-link" type="button" ${attr(r)}>${escapeHtml(r.name)}</button>
                <span class="csbar-track"><span class="csbar-fill" style="width:${Math.max(1, Math.round((100 * r.words) / max))}%;--bar:${escapeHtml(colorOf(r))}"></span></span>
                <span class="csbar-val">${formatNumber(r.words)}</span>
            </div>`).join("")}</div>`;
    };

    if (readerContent) {
        readerContent.innerHTML = `
            <div class="facet-info corpus-overview">
                <div class="facet-title">Corpus</div>
                <div class="facet-field-label">Volume by macro-area (words)</div>
                ${bars([...regions.values()].sort(byWords), (r) => regionColorOf(r.name), (r) => `data-region="${escapeHtml(r.name)}"`)}
                <div class="facet-field-label">Volume by tradition (words)</div>
                ${bars([...traditions.values()].sort(byWords), (r) => traditionColor(r.name), (r) => `data-tradition="${escapeHtml(r.name)}"`)}
                <div class="facet-field-label">Volume by book (words)</div>
                ${bars(books, (r) => traditionColor(r.doc.tradition), (r) => `data-doc="${escapeHtml(r.doc.document_id)}"`)}
            </div>`;
        readerContent.scrollTop = 0;
        readerContent.querySelectorAll(".corpus-bar-link").forEach((btn) => {
            btn.addEventListener("click", () => {
                const { region, tradition, doc } = btn.dataset;
                if (region) revealRegion(region).then(() => showRegionInfo(region));
                else if (tradition) revealInTree(tradition).then(() => showTraditionInfo(tradition, regionOf(tradition)));
                else if (doc) {
                    const d = docs.find((x) => x.document_id === doc);
                    if (d) revealInTree(d.tradition).then(() => openCorpusDocument(d));
                }
            });
        });
    }

    if (bookInfo) {
        const words = sumWords(docs);
        const sentences = docs.reduce((n, d) => n + (d.sentence_count || 0), 0);
        bookInfo.innerHTML = figures([
            [counted(words, "word", "words")],
            [counted(sentences, "sentence", "sentences")],
            [counted(regions.size, "macro-area", "macro-areas"), counted(traditions.size, "tradition", "traditions"),
                counted(docs.length, "book", "books")],
            [[formatNumber(Math.round(words / docs.length)), "words per book on average"]],
        ]);
    }
}

async function revealRegion(region) {
    state.corpusOpenMajor = region;
    state.corpusOpenTradition = null;
    const tree = document.getElementById("libraryTree");
    if (tree) await renderLibraryTree(tree);
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

// The figures block at the top of the info panel, the same at every level (corpus,
// region, tradition, book): one fact per line, the number set off from its label.
// `lines` is a list of lines; a line is a list of [value, label] pairs joined by " · ".
function figures(lines) {
    const fig = ([value, label]) => `<span class="fig"><b>${escapeHtml(value)}</b> ${escapeHtml(label)}</span>`;
    return `<div class="figs">${lines
        .filter((line) => line.length)
        .map((line) => `<div class="fig-line">${line.map(fig).join('<span class="fig-sep"> · </span>')}</div>`)
        .join("")}</div>`;
}

const counted = (n, one, many) => [formatNumber(n), n === 1 ? one : many];

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

    // The name and colour already head the reader pane, so the panel starts with the numbers.
    let html = figures([
        [counted(words, "word", "words")],
        [counted(sentences, "sentence", "sentences")],
        [byTradition ? counted(traditions.size, "tradition", "traditions") : null,
            counted(docs.length, "book", "books")].filter(Boolean),
        corpusWords
            ? [parentWords ? [percent(words, parentWords), parentLabel] : null,
                [percent(words, corpusWords), "of the corpus"]].filter(Boolean)
            : [],
    ]);

    if (byTradition && traditions.size > 1) {
        const ranked = [...traditions.values()].sort((a, b) => b.words - a.words);
        html += `<div class="description-title">Traditions by volume (words)</div>
            <ol class="group-list">${ranked.map((t) => `<li>
                <button class="group-link" type="button" data-tradition="${escapeHtml(t.name)}" title="${escapeHtml(t.name)}">${escapeHtml(t.name)}</button>
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
