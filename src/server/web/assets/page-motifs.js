import { app, api, escapeHtml, formatNumber } from "./core.js";

// Module-local navigation state (index, chapter filter, query, selection).
const mState = {
    indexes: null,
    index: "berezkin",
    chapter: "",
    query: "",
    selectedId: null,
};

const LIST_LIMIT = 300;
let searchTimer = null;

export async function renderMotifs(params = new URLSearchParams()) {
    app.innerHTML = `
        <main class="motifs-page container">
            <div class="workspace">
                <aside class="library-sidebar motifs-sidebar">
                    <div class="motifs-tabs" id="motifsTabs">Loading...</div>
                    <input type="text" class="motifs-search" id="motifsSearch" placeholder="Search id or name...">
                    <select class="motifs-chapter" id="motifsChapter"></select>
                    <div class="motifs-list" id="motifsList"></div>
                </aside>

                <article class="card reader motifs-detail" id="motifsDetail">
                    <div class="reader-placeholder">Select a motif to see its description and cross-index links.</div>
                </article>
            </div>
        </main>
    `;

    try {
        const data = await api("/api/motifs/indexes");
        mState.indexes = data.indexes || [];
    } catch (error) {
        const msg = /not built/i.test(error.message)
            ? "Motif database not built yet. Run <code>mytho motifs</code> to build it."
            : escapeHtml(error.message);
        app.querySelector(".workspace").innerHTML = `<div class="empty-state">${msg}</div>`;
        return;
    }

    if (!mState.indexes.length) {
        app.querySelector(".workspace").innerHTML = `<div class="empty-state">No motif indexes available.</div>`;
        return;
    }

    // Honour deep links: #/motifs?index=atu&id=510A
    const wantIndex = params.get("index");
    if (wantIndex && mState.indexes.some((i) => i.index === wantIndex)) mState.index = wantIndex;
    else if (!mState.indexes.some((i) => i.index === mState.index)) mState.index = mState.indexes[0].index;

    renderTabs();
    renderChapters();
    wireControls();
    await loadList();

    const wantId = params.get("id");
    if (wantId) openMotif(mState.index, wantId);
    else if (mState.selectedId) openMotif(mState.index, mState.selectedId);
}

function currentIndex() {
    return mState.indexes.find((i) => i.index === mState.index) || mState.indexes[0];
}

function renderTabs() {
    const tabs = document.getElementById("motifsTabs");
    tabs.innerHTML = mState.indexes.map((i) => `
        <button class="motifs-tab${i.index === mState.index ? " active" : ""}"
                data-index="${escapeHtml(i.index)}" title="${escapeHtml(i.long_label || i.label)}">
            ${escapeHtml(i.label)} <span class="motifs-tab-count">${formatNumber(i.count)}</span>
        </button>
    `).join("");
    tabs.querySelectorAll(".motifs-tab").forEach((btn) => {
        btn.addEventListener("click", () => selectIndex(btn.dataset.index));
    });
}

function renderChapters() {
    const select = document.getElementById("motifsChapter");
    const chapters = currentIndex().chapters || [];
    select.innerHTML =
        `<option value="">All chapters (${formatNumber(currentIndex().count)})</option>` +
        chapters.map((c) => `<option value="${escapeHtml(c.id)}"${c.id === mState.chapter ? " selected" : ""}>
            ${escapeHtml(c.label)} (${formatNumber(c.count)})
        </option>`).join("");
}

function wireControls() {
    const search = document.getElementById("motifsSearch");
    search.value = mState.query;
    search.addEventListener("input", () => {
        mState.query = search.value;
        clearTimeout(searchTimer);
        searchTimer = setTimeout(loadList, 250);
    });
    document.getElementById("motifsChapter").addEventListener("change", (e) => {
        mState.chapter = e.target.value;
        loadList();
    });
}

async function switchIndex(index) {
    mState.index = index;
    mState.chapter = "";
    mState.query = "";
    const search = document.getElementById("motifsSearch");
    if (search) search.value = "";
    renderTabs();
    renderChapters();
    await loadList();
}

function selectIndex(index) {
    if (index === mState.index) return;
    switchIndex(index);
}

// Clicking a chapter root shows that chapter's level-0 motifs in the main panel
// (the same tree table), each a link to drill down.
async function browseChapterLevel0(chapter) {
    const detail = document.getElementById("motifsDetail");
    if (!detail) return;
    mState.selectedId = null;
    markActive(null);
    detail.innerHTML = `<div class="reader-placeholder">Loading...</div>`;
    try {
        const params = new URLSearchParams({ chapter, level: "0", limit: String(LIST_LIMIT) });
        const data = await api(`/api/motifs/tmi/motifs?${params.toString()}`);
        const rows = [rootRow(0), chapterRow(chapter, 1, { current: true })];
        for (const it of data.items) rows.push(treeRow(it, 2));
        detail.innerHTML = `<div class="motif-detail-inner"><div class="motif-tree">${rows.join("")}</div></div>`;
        detail.scrollTop = 0;
        bindTreeLinks(detail);
    } catch (error) {
        detail.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}

async function loadList() {
    const list = document.getElementById("motifsList");
    if (!list) return;
    list.innerHTML = `<div class="motifs-loading">Loading...</div>`;
    try {
        const params = new URLSearchParams({ limit: String(LIST_LIMIT) });
        if (mState.chapter) params.set("chapter", mState.chapter);
        if (mState.query.trim()) params.set("q", mState.query.trim());
        const data = await api(`/api/motifs/${mState.index}/motifs?${params.toString()}`);
        renderList(data);
    } catch (error) {
        list.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}

function renderList(data) {
    const list = document.getElementById("motifsList");
    if (!data.items.length) {
        list.innerHTML = `<div class="empty-state">No motifs match.</div>`;
        return;
    }
    const shown = data.items.length;
    const more = data.total > shown
        ? `<div class="motifs-more">Showing ${formatNumber(shown)} of ${formatNumber(data.total)} — refine your search.</div>`
        : "";
    // TMI ids without a dot are the broad top-level categories — show them bold.
    const isCategory = (id) => mState.index === "tmi" && !id.includes(".");
    list.innerHTML = data.items.map((it) => `
        <button class="motifs-item${it.id === mState.selectedId ? " active" : ""}${isCategory(it.id) ? " category" : ""}${it.duplicate ? " duplicate" : ""}${it.leaf ? " leaf" : ""}" data-id="${escapeHtml(it.id)}" style="--depth:${it.level || 0}">
            <span class="motifs-item-id">${escapeHtml(it.id)}</span>
            <span class="motifs-item-name">${escapeHtml(it.name || "—")}</span>
            <span class="motifs-item-badge">${escapeHtml(it.badge || "")}</span>
        </button>
    `).join("") + more;
    list.querySelectorAll(".motifs-item").forEach((btn) => {
        btn.addEventListener("click", () => openMotif(mState.index, btn.dataset.id));
    });
}

function markActive(id) {
    document.querySelectorAll(".motifs-item").forEach((btn) => {
        btn.classList.toggle("active", btn.dataset.id === id);
    });
}

async function openMotif(index, id) {
    // Following a cross-link can switch indexes; keep the sidebar in sync.
    if (index !== mState.index) {
        await switchIndex(index);
    }
    mState.selectedId = id;
    markActive(id);

    const detail = document.getElementById("motifsDetail");
    detail.innerHTML = `<div class="reader-placeholder">Loading...</div>`;
    try {
        const params = new URLSearchParams({ id });
        const data = await api(`/api/motifs/${index}/motif?${params.toString()}`);
        detail.innerHTML = renderDetail(data);
        detail.scrollTop = 0;
        detail.querySelectorAll(".motif-link").forEach((a) => {
            a.addEventListener("click", (e) => {
                e.preventDefault();
                openMotif(a.dataset.index, a.dataset.id);
            });
        });
        bindTreeLinks(detail);
    } catch (error) {
        detail.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}

function linkChips(links) {
    if (!links || !links.length) return `<span class="motif-empty">—</span>`;
    return links.map((l) => `
        <a href="#/motifs?index=${escapeHtml(l.index)}&id=${encodeURIComponent(l.id)}"
           class="motif-link${l.exists ? "" : " missing"}" data-index="${escapeHtml(l.index)}" data-id="${escapeHtml(l.id)}"
           title="${escapeHtml(l.name || l.id)}${l.exists ? "" : " (not in this database)"}">
            <span class="motif-link-id">${escapeHtml(l.id)}</span>${l.name ? `<span class="motif-link-name">${escapeHtml(l.name)}</span>` : ""}
        </a>
    `).join("");
}

function treeRow(node, depth, { current = false } = {}) {
    const count = node.descendant_count ? `${node.descendant_count} · ` : "";
    const badge = `<span class="motifs-item-badge">${count}L${escapeHtml(String(node.level ?? ""))}</span>`;
    const inner = `<span class="motifs-item-id">${escapeHtml(node.id)}</span><span class="motifs-item-name">${escapeHtml(node.name || "—")}</span>${badge}`;
    const leaf = (!current && node.leaf) ? " leaf" : "";
    if (current) return `<div class="motifs-item motif-tree-row current${leaf}" style="--depth:${depth}">${inner}</div>`;
    return `<a class="motifs-item motif-tree-row${leaf}" data-motif-id="${escapeHtml(node.id)}" href="#/motifs?index=tmi&id=${encodeURIComponent(node.id)}" style="--depth:${depth}">${inner}</a>`;
}

function chapterMeta(id) {
    return (currentIndex().chapters || []).find((c) => c.id === id) || { id, label: id, count: 0 };
}

// Catalog root "/" — badge is the total motif count; clicking lists the chapters.
function rootRow(depth, { current = false } = {}) {
    const badge = `<span class="motifs-item-badge">${formatNumber(currentIndex().count)}</span>`;
    const inner = `<span class="motifs-item-id">/</span><span class="motifs-item-name">All motifs</span>${badge}`;
    if (current) return `<div class="motifs-item motif-tree-row current" style="--depth:${depth}">${inner}</div>`;
    return `<a class="motifs-item motif-tree-row" href="#" data-root="1" style="--depth:${depth}">${inner}</a>`;
}

// Chapter row — badge is the chapter's total descendant count; clicking lists its L0 motifs.
function chapterRow(chapterId, depth, { current = false } = {}) {
    const c = chapterMeta(chapterId);
    const badge = `<span class="motifs-item-badge">${formatNumber(c.count)}</span>`;
    const inner = `<span class="motifs-item-name">${escapeHtml(c.label)}</span>${badge}`;
    if (current) return `<div class="motifs-item motif-tree-row current" style="--depth:${depth}">${inner}</div>`;
    return `<a class="motifs-item motif-tree-row" href="#" data-chapter-root="${escapeHtml(chapterId)}" style="--depth:${depth}">${inner}</a>`;
}

// One tree: / -> chapter -> every parent -> the motif (highlighted) -> its direct children.
function renderTmiTree(d) {
    const rows = [rootRow(0), chapterRow(d.chapter, 1)];
    let depth = 2;
    for (const a of d.breadcrumbs || []) rows.push(treeRow(a, depth++));
    rows.push(treeRow({ id: d.id, name: d.name, level: d.level, descendant_count: d.descendant_count }, depth, { current: true }));
    for (const c of d.children || []) rows.push(treeRow(c, depth + 1));
    if (d.children_truncated) rows.push(`<div class="motif-subtree-more" style="--depth:${depth + 1}">… more sub-motifs</div>`);
    return `<div class="motif-tree">${rows.join("")}</div>`;
}

function bindTreeLinks(detail) {
    detail.querySelectorAll("[data-motif-id]").forEach((el) => {
        el.addEventListener("click", (e) => { e.preventDefault(); openMotif("tmi", el.dataset.motifId); });
    });
    detail.querySelectorAll("[data-chapter-root]").forEach((el) => {
        el.addEventListener("click", (e) => { e.preventDefault(); browseChapterLevel0(el.dataset.chapterRoot); });
    });
    detail.querySelectorAll("[data-root]").forEach((el) => {
        el.addEventListener("click", (e) => { e.preventDefault(); browseRoot(); });
    });
}

// Catalog root view: "/" (current, total count) + the chapter rows.
function browseRoot() {
    const detail = document.getElementById("motifsDetail");
    if (!detail) return;
    mState.selectedId = null;
    markActive(null);
    const rows = [rootRow(0, { current: true })];
    for (const c of currentIndex().chapters || []) rows.push(chapterRow(c.id, 1));
    detail.innerHTML = `<div class="motif-detail-inner"><div class="motif-tree">${rows.join("")}</div></div>`;
    detail.scrollTop = 0;
    bindTreeLinks(detail);
}

function section(title, bodyHtml) {
    return `<div class="motif-section"><div class="motif-section-title">${escapeHtml(title)}</div>${bodyHtml}</div>`;
}

function linkSection(title, links) {
    return section(title, `<div class="motif-links">${linkChips(links)}</div>`);
}

function renderDetail(d) {
    const links = d.links || {};
    const head = `
        <div class="motif-head">
            <span class="motif-code">${escapeHtml(d.id)}</span>
            <h2 class="motif-name">${escapeHtml(d.name || "—")}</h2>
        </div>`;
    const chapterLine = `<div class="motif-chapter">${escapeHtml(d.chapter_label || d.chapter || "")}</div>`;

    let body = "";
    if (d.index === "berezkin") {
        body = head + chapterLine;
        if (d.definition) body += section("Definition", `<p class="motif-text">${escapeHtml(d.definition)}</p>`);
        if (d.source_url) {
            body += section("Source", `<a class="motif-source-link" href="${escapeHtml(d.source_url)}" target="_blank" rel="noopener">${escapeHtml(d.source_url)} ↗</a>`);
        }
        const areas = (d.areas || []).map((a) =>
            `<span class="motif-area${a.name ? "" : " unresolved"}" title="area ${escapeHtml(a.id)}">${escapeHtml(a.name || a.id)}</span>`).join("");
        body += section(`Areal distribution (${(d.areas || []).length})`,
            areas ? `<div class="motif-areas">${areas}</div>` : `<span class="motif-empty">—</span>`);
        if ((links.atu || []).length) body += linkSection("ATU tale types", links.atu);
        if ((links.see_also || []).length) body += linkSection("See also (Berezkin)", links.see_also);
    } else if (d.index === "tmi") {
        // Hierarchy tree first, then all the motif's own information.
        body = renderTmiTree(d);
        body += head;
        if (d.duplicate) {
            body += `<p class="motif-dup-note">Source code <strong>${escapeHtml(d.code || d.id)}</strong> is reused for several distinct motifs; shown here under <strong>${escapeHtml(d.id)}</strong>.</p>`;
        }
        if (d.notes) body += section("Notes", `<p class="motif-text">${escapeHtml(d.notes)}</p>`);
        if ((links.atu || []).length) body += linkSection("Appears in ATU tale types", links.atu);
    } else if (d.index === "atu") {
        body = head + chapterLine;
        if (d.division) body += section("Division", `<p class="motif-text">${escapeHtml(d.division)}</p>`);
        if (d.summary) body += section("Summary", `<p class="motif-text">${escapeHtml(d.summary)}</p>`);
        body += linkSection(`Constituent TMI motifs (${(links.tmi || []).length})`, links.tmi);
        if ((links.combos || []).length) body += linkSection("Combined with", links.combos);
        if ((links.berezkin || []).length) body += linkSection("Referenced by Berezkin motifs", links.berezkin);
    }

    return `<div class="motif-detail-inner">${body}</div>`;
}
