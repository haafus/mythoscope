import { state, groupDocuments, corpusTraditionKey, escapeHtml, traditionColor } from "./core.js";
import { renderMajorTree } from "./tree-scaffold.js";

export async function renderLibraryTree(container) {
    await renderMajorTree(container, {
        emptyMessage: "No literature found.",
        prepare: (documents) => {
            initTreeOpen(documents);
            return { documents, docIndex: new Map(documents.map((doc, i) => [doc, i])) };
        },
        renderBody: (traditions, major, ctx) => renderTraditionGroups(traditions, major, ctx.docIndex),
        bindLeaves: (container, ctx) => bindTreeLeaves(container, ctx.documents),
    });
}

function initTreeOpen(documents) {
    if (state.corpusTreeInitialized) return;
    const grouped = groupDocuments(documents);
    const firstMajor = grouped.keys().next().value;
    if (firstMajor != null) {
        state.corpusOpenMajor = firstMajor;
        const firstTradition = grouped.get(firstMajor).keys().next().value;
        if (firstTradition != null) state.corpusOpenTradition = corpusTraditionKey(firstMajor, firstTradition);
    }
    state.corpusTreeInitialized = true;
}

function renderTraditionGroups(traditions, major, docIndex) {
    let html = "";
    traditions.forEach((docs, tradition) => {
        const key = corpusTraditionKey(major, tradition);
        const isOpen = state.corpusOpenTradition === key;
        const color = traditionColor(tradition);  // derived region shade (§8.1), not stored

        html += `
            <div class="tradition-group${isOpen ? " open" : ""}" data-tradition="${escapeHtml(tradition)}">
                <button class="tradition-title" type="button" style="--tradition-color:${escapeHtml(color)}">
                    <span class="tradition-dot"></span>
                    <span class="tradition-name">${escapeHtml(tradition)}</span>
                    <span class="tradition-toggle">${isOpen ? "▾" : "▸"}</span>
                </button>
                <ul class="document-list">
                    ${docs.map((doc) => `
                        <li>
                            <button class="document-button" type="button" data-doc-index="${docIndex.get(doc)}" title="${escapeHtml(doc.title)}">
                                ${escapeHtml(doc.title)}
                            </button>
                        </li>
                    `).join("")}
                </ul>
            </div>
        `;
    });
    return html;
}

let bookKeyHandler = null;

function bindTreeLeaves(container, documents) {
    container.querySelectorAll(".tradition-title").forEach((button) => {
        button.addEventListener("click", () => {
            const group = button.closest(".tradition-group");
            const section = button.closest(".major-section");
            const key = corpusTraditionKey(section?.dataset.major, group.dataset.tradition);
            state.corpusOpenTradition = state.corpusOpenTradition === key ? null : key;  // opening one closes the rest
            container.querySelectorAll(".tradition-group").forEach((g) => {
                const s = g.closest(".major-section");
                const open = corpusTraditionKey(s?.dataset.major, g.dataset.tradition) === state.corpusOpenTradition;
                g.classList.toggle("open", open);
                const toggle = g.querySelector(".tradition-toggle");
                if (toggle) toggle.textContent = open ? "▾" : "▸";
            });
        });
    });

    container.querySelectorAll(".document-button").forEach((button) => {
        button.addEventListener("click", () => {
            const doc = documents[Number(button.dataset.docIndex)];
            if (!doc) return;
            container.dispatchEvent(new CustomEvent("book-select", { detail: { doc }, bubbles: true }));
        });
    });

    // ↑/↓ step through the visible book list (single stable handler; a re-render
    // detaches the old container, so drop the previous binding first).
    if (bookKeyHandler) document.removeEventListener("keydown", bookKeyHandler);
    bookKeyHandler = (e) => onBookKeydown(e, container, documents);
    document.addEventListener("keydown", bookKeyHandler);
}

function onBookKeydown(e, container, documents) {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (!container.isConnected) return;
    const tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return;  // don't hijack typing

    const buttons = Array.from(container.querySelectorAll(".document-button"))
        .filter((b) => b.offsetParent !== null);  // only books inside open traditions
    if (!buttons.length) return;
    e.preventDefault();

    const cur = buttons.findIndex((b) => b.classList.contains("active"));
    const delta = e.key === "ArrowDown" ? 1 : -1;
    const next = cur === -1
        ? (delta > 0 ? 0 : buttons.length - 1)
        : Math.min(buttons.length - 1, Math.max(0, cur + delta));
    if (next === cur) return;

    const btn = buttons[next];
    btn.scrollIntoView({ block: "nearest" });
    const doc = documents[Number(btn.dataset.docIndex)];
    if (doc) container.dispatchEvent(new CustomEvent("book-select", { detail: { doc }, bubbles: true }));
}

export function setActiveBook(container, doc) {
    container.querySelectorAll(".document-button").forEach((btn) => btn.classList.remove("active"));
    if (!doc) return;
    const index = state.corpusDocuments.indexOf(doc);
    if (index === -1) return;
    const btn = container.querySelector(`.document-button[data-doc-index="${index}"]`);
    if (btn) btn.classList.add("active");
}
