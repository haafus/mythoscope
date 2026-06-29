import {
    app, api, state,
    buildCorpusApiUrl, escapeHtml, formatNumber,
} from "./core.js";
import { renderLibraryTree, setActiveBook } from "./tree-sources.js";

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
            <div class="empty-state">Select a book to view words, sentences, description, and download options.</div>
            <div class="actions">
                <a class="btn btn-outline" href="/api/corpus/archive">Download Full Archive</a>
            </div>
        `;
        return;
    }

    const url = buildCorpusApiUrl(doc);
    const originalUrl = doc.url
        ? `<a class="original-url-link" href="${escapeHtml(doc.url)}" target="_blank" rel="noopener noreferrer">Original URL</a>`
        : "";
    bookInfo.innerHTML = `
        <div class="book-title">${escapeHtml(doc.title)}</div>
        <div class="book-tradition">
            <span class="info-dot" style="--book-color:${escapeHtml(doc.color || "#6b7280")}"></span>
            <span>${escapeHtml(doc.major_tradition || "Other")} / ${escapeHtml(doc.tradition || "Unknown")}</span>
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

        <div class="actions">
            <a class="btn btn-primary" href="${escapeHtml(url)}" download="${escapeHtml(doc.title || "book")}.txt">Download Book</a>
            <a class="btn btn-outline" href="/api/corpus/archive">Download Full Archive</a>
        </div>
    `;
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
