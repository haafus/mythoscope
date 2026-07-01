import { app, api, escapeHtml, formatNumber, onCleanup } from "./core.js";

// Module-local navigation state (index, chapter filter, query, selection).
const mState = {
    indexes: null,
    index: "tmi",  // default index on first open (Thompson)
    chapter: "",
    query: "",
    selectedId: null,
    motifFilter: "all",  // "all" | "def" | "sub" | "atu"
    flatList: false,     // browse as a flat list (no parent categories) instead of drill-down
    browseChapter: null, // chapter currently shown in the main-panel browse, if any
    browseView: null,    // "root" | "chapter" | null (detail/overview)
};

const LIST_LIMIT = 300;
let searchTimer = null;

export async function renderMotifs(params = new URLSearchParams()) {
    app.innerHTML = `
        <main class="motifs-page container">
            <div class="workspace">
                <aside class="library-sidebar motifs-sidebar">
                    <div class="motifs-tabs" id="motifsTabs">${tabsPlaceholder()}</div>
                    <button class="motifs-overview-btn" id="motifsOverview">Overview</button>
                    <input type="text" class="motifs-search" id="motifsSearch" placeholder="Search id or name...">
                    <select class="motifs-chapter" id="motifsChapter"></select>
                    <div class="motifs-list" id="motifsList"></div>
                </aside>

                <article class="card reader motifs-detail" id="motifsDetail"></article>
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
    else renderOverview();
}

function currentIndex() {
    return mState.indexes.find((i) => i.index === mState.index) || mState.indexes[0];
}

// Fixed tab order and labels — lets us paint the buttons at their final size
// before the index summaries load, so only the count fills in (no "Loading",
// no height jump). Thompson sits before Berezkin.
const TAB_ORDER = ["tmi", "berezkin", "atu"];
const TAB_LABELS = { tmi: "Thompson", berezkin: "Berezkin", atu: "ATU tale types" };

function tabsPlaceholder() {
    return TAB_ORDER.map((idx) => `
        <button class="motifs-tab" disabled>
            ${escapeHtml(TAB_LABELS[idx])} <span class="motifs-tab-count">&nbsp;</span>
        </button>`).join("");
}

function renderTabs() {
    const tabs = document.getElementById("motifsTabs");
    const ordered = [...mState.indexes].sort(
        (a, b) => TAB_ORDER.indexOf(a.index) - TAB_ORDER.indexOf(b.index));
    tabs.innerHTML = ordered.map((i) => `
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
    document.getElementById("motifsOverview").addEventListener("click", renderOverview);
    // ↑/↓ step through the sidebar list (same handler ref → no duplicates on re-render).
    document.addEventListener("keydown", onMotifsKeydown);
    onCleanup(() => document.removeEventListener("keydown", onMotifsKeydown));
}

// Move the selection to the previous/next motif in the sidebar list and open it.
function stepMotif(delta) {
    const items = Array.from(document.querySelectorAll(".motifs-item"));
    if (!items.length) return;
    const cur = items.findIndex((b) => b.dataset.id === mState.selectedId);
    const next = cur === -1
        ? (delta > 0 ? 0 : items.length - 1)         // nothing selected yet → first/last
        : Math.min(items.length - 1, Math.max(0, cur + delta));
    if (next === cur) return;
    const btn = items[next];
    btn.scrollIntoView({ block: "nearest" });
    openMotif(mState.index, btn.dataset.id);
}

// Cycle to the previous/next index (wrapping), following the tab order.
function stepIndex(delta) {
    const order = TAB_ORDER.filter((id) => mState.indexes.some((i) => i.index === id));
    if (order.length < 2) return;
    const cur = order.indexOf(mState.index);
    selectIndex(order[(cur + delta + order.length) % order.length]);
}

function onMotifsKeydown(e) {
    const arrows = ["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"];
    if (!arrows.includes(e.key)) return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (!document.getElementById("motifsList")) return;  // only on the motifs page
    const tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return;  // don't hijack typing
    e.preventDefault();
    if (e.key === "ArrowDown" || e.key === "ArrowUp") stepMotif(e.key === "ArrowDown" ? 1 : -1);
    else stepIndex(e.key === "ArrowRight" ? 1 : -1);  // Left/Right cycle indexes
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

async function selectIndex(index) {
    if (index === mState.index) return;
    await switchIndex(index);
    renderOverview();
}

// Clicking a chapter root shows that chapter's level-0 motifs in the main panel
// (the same tree table), each a link to drill down.
async function browseChapterLevel0(chapter) {
    const detail = document.getElementById("motifsDetail");
    if (!detail) return;
    mState.selectedId = null;
    mState.browseChapter = chapter;
    mState.browseView = "chapter";
    markActive(null);
    detail.innerHTML = "";
    try {
        const rows = [rootRow(0), chapterRow(chapter, 1, { current: true })];
        if (mState.flatList) {
            // Flat: the chapter's matching motifs at any depth, no categories.
            const data = await fetchFlat(chapter);
            for (const it of data.items) rows.push(treeRow(it, 2));
            if (data.total > data.items.length) rows.push(moreRow(data.total - data.items.length, 2));
        } else {
            // Drill-down: just the immediate child level (L0); the filter hides L0
            // categories whose subtree holds no match (deeper matches still count).
            const params = new URLSearchParams({ chapter, level: "0", limit: String(LIST_LIMIT) });
            const data = await api(`/api/motifs/tmi/motifs?${params.toString()}`);
            for (const it of data.items) rows.push(treeRow(it, 2, { filterable: true }));
        }
        detail.innerHTML = `<div class="motif-detail-inner">${controls(true)}<div class="motif-tree${filterClass()}">${rows.join("")}</div></div>`;
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
        <button class="motifs-item${it.id === mState.selectedId ? " active" : ""}${isCategory(it.id) ? " category" : ""}${it.duplicate ? " duplicate" : ""}" data-id="${escapeHtml(it.id)}" style="--depth:${it.level || 0}">
            <span class="motifs-item-id">${escapeHtml(it.id)}</span>
            <span class="motifs-item-name">${escapeHtml(it.name || "—")}</span>
            <span class="motifs-item-badge${it.substantive ? " is-sub" : ""}">${escapeHtml(it.badge || "")}</span>
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
    mState.browseChapter = null;
    mState.browseView = null;
    markActive(id);

    const detail = document.getElementById("motifsDetail");
    detail.innerHTML = "";  // blank intermediate screen during the switch (no "Loading" text)
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
        bindBibCopy(detail);
    } catch (error) {
        detail.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}

// Click a bibliography entry to copy its citation to the clipboard. Delegated so
// it covers every entry (macro-area groups and "Other") in one listener; clicks
// on the inner status link are left to open that link.
function bindBibCopy(detail) {
    detail.querySelectorAll(".motif-bib-item").forEach((li) => {
        li.addEventListener("click", (e) => {
            if (e.target.closest("a")) return;  // let the status link work
            const text = li.dataset.copy || li.textContent.trim();
            const flash = () => {
                li.classList.add("copied");
                setTimeout(() => li.classList.remove("copied"), 700);
            };
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(text).then(flash, () => {});
            }
        });
    });
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

// The tree-row badge: an optional "definition" check, then notes size and the
// recursive descendant count — each part dot-separated, carrying its own tooltip.
function badgeHtml(node) {
    const parts = [];
    if (node.has_definition) parts.push(`<span class="badge-check" title="Has an extracted definition">✓</span>`);
    if (node.notes_size) parts.push(`<span title="Size of the source notes (definition + bibliography)">${escapeHtml(node.notes_size)}</span>`);
    const dc = node.descendant_counts;
    if (dc && dc.all) {
        // The number swaps with the active filter (all/def/sub/atu) via CSS, like
        // the tier badge — so it counts only the descendants matching the filter.
        parts.push(`<span class="desc-count" data-all="${dc.all}" data-def="${dc.def}" data-sub="${dc.sub}" data-atu="${dc.atu}" title="Descendant motifs matching the active filter, counted recursively"></span>`);
    } else if (node.descendant_count) {
        parts.push(`<span title="Descendant motifs, counted recursively down to the leaves">${node.descendant_count}</span>`);
    }
    const subTitle = node.substantive ? ` title="Substantive motif: notes ≥ 150 bytes or attested in ≥ 3 cultures"` : "";
    return `<span class="motifs-item-badge${node.substantive ? " is-sub" : ""}"${subTitle}>${parts.join(" · ")}</span>`;
}

function treeRow(node, depth, { current = false, filterable = false } = {}) {
    const inner = `<span class="motifs-item-id">${escapeHtml(node.id)}</span><span class="motifs-item-name">${escapeHtml(node.name || "—")}</span>${badgeHtml(node)}`;
    // Filterable rows (children / browse lists) can be hidden by the motif
    // filter, tagged with the tiers they belong to; ancestors and the current
    // motif are never filtered (they form the path).
    // Filter by subtree relevance (self or a descendant matches) so a category
    // stays visible when its matching content is deeper — only this one level
    // is shown, deeper levels still count.
    const tags = filterable
        ? ` filterable${node.def_subtree ? " f-def" : ""}${node.sub_subtree ? " f-sub" : ""}${node.atu_subtree ? " f-atu" : ""}`
        : "";
    if (current) return `<div class="motifs-item motif-tree-row current" style="--depth:${depth}">${inner}</div>`;
    return `<a class="motifs-item motif-tree-row${tags}" data-motif-id="${escapeHtml(node.id)}" href="#/motifs?index=tmi&id=${encodeURIComponent(node.id)}" style="--depth:${depth}">${inner}</a>`;
}

// Motif-filter dropdown shown above a tree in the main panel; counts are
// index-wide tiers from the index summary.
function filterSelect() {
    const idx = currentIndex();
    const opt = (val, label, n) =>
        `<option value="${val}"${mState.motifFilter === val ? " selected" : ""}>` +
        `${label}${n != null ? ` (${formatNumber(n)})` : ""}</option>`;
    return `<select class="motif-filter" aria-label="Filter motifs">
        ${opt("all", "Full index", idx.count)}
        ${opt("def", "With definitions", idx.definition_count)}
        ${opt("sub", "Substantive only", idx.substantive_count)}
        ${opt("atu", "With ATU types", idx.atu_count)}
    </select>`;
}

function filterClass() {
    return mState.motifFilter === "def" ? " filter-def"
        : mState.motifFilter === "sub" ? " filter-sub"
        : mState.motifFilter === "atu" ? " filter-atu" : "";
}

// The control bar above a tree: filter dropdown, plus the "Flat list" toggle in
// the browse views (root / chapter).
function controls(withFlat) {
    const flat = withFlat
        ? `<label class="flat-toggle"><input type="checkbox" class="flat-cb"${mState.flatList ? " checked" : ""}> Flat list</label>`
        : "";
    return `<div class="motif-controls">${filterSelect()}${flat}</div>`;
}

function moreRow(n, depth) {
    return `<div class="motif-subtree-more" style="--depth:${depth}">… ${formatNumber(n)} more</div>`;
}

// Flat motif list for the current filter (matching motifs only, no categories);
// no tier = the whole scope expanded flat.
async function fetchFlat(chapter) {
    const params = new URLSearchParams({ limit: String(LIST_LIMIT) });
    if (chapter) params.set("chapter", chapter);
    if (mState.motifFilter !== "all") params.set("tier", mState.motifFilter);
    return api(`/api/motifs/tmi/motifs?${params.toString()}`);
}

function chapterMeta(id) {
    return (currentIndex().chapters || []).find((c) => c.id === id) || { id, label: id, count: 0 };
}

// A badge whose number follows the active filter tier (all/def/sub/atu) via a
// CSS content-swap; falls back to a plain count for indexes without tiers.
function tierBadge(counts) {
    if (counts.sub == null) return `<span class="motifs-item-badge">${formatNumber(counts.all)}</span>`;
    return `<span class="motifs-item-badge tier-badge" data-all="${formatNumber(counts.all)}"` +
        ` data-def="${formatNumber(counts.def)}" data-sub="${formatNumber(counts.sub)}"` +
        ` data-atu="${formatNumber(counts.atu)}"></span>`;
}

// Catalog root "/" — badge is the total motif count; clicking lists the chapters.
function rootRow(depth, { current = false } = {}) {
    const idx = currentIndex();
    const badge = tierBadge({ all: idx.count, def: idx.definition_count, sub: idx.substantive_count, atu: idx.atu_count });
    const inner = `<span class="motifs-item-id">/</span><span class="motifs-item-name">All motifs</span>${badge}`;
    if (current) return `<div class="motifs-item motif-tree-row current" style="--depth:${depth}">${inner}</div>`;
    return `<a class="motifs-item motif-tree-row" href="#" data-root="1" style="--depth:${depth}">${inner}</a>`;
}

// Chapter row — badge is the chapter's total descendant count; clicking lists its L0 motifs.
function chapterRow(chapterId, depth, { current = false, filterable = false } = {}) {
    const c = chapterMeta(chapterId);
    // Show the chapter letter in the code (id) column, the title in the name.
    const title = c.label.split(" — ").slice(1).join(" — ") || c.label;
    const badge = tierBadge({ all: c.count, def: c.definitions, sub: c.substantive, atu: c.atu });
    const inner = `<span class="motifs-item-id">${escapeHtml(c.id)}</span><span class="motifs-item-name">${escapeHtml(title)}</span>${badge}`;
    if (current) return `<div class="motifs-item motif-tree-row current" style="--depth:${depth}">${inner}</div>`;
    // A chapter is in a tier if it holds at least one motif of that tier.
    const tags = filterable
        ? ` filterable${c.definitions ? " f-def" : ""}${c.substantive ? " f-sub" : ""}${c.atu ? " f-atu" : ""}`
        : "";
    return `<a class="motifs-item motif-tree-row${tags}" href="#" data-chapter-root="${escapeHtml(chapterId)}" style="--depth:${depth}">${inner}</a>`;
}

// One tree: / -> chapter -> every parent -> the motif (highlighted) -> its direct children.
function renderTmiTree(d) {
    const rows = [rootRow(0), chapterRow(d.chapter, 1)];
    let depth = 2;
    for (const a of d.breadcrumbs || []) rows.push(treeRow(a, depth++));
    rows.push(treeRow({ id: d.id, name: d.name, level: d.level, descendant_count: d.descendant_count, descendant_counts: d.descendant_counts, notes_size: d.notes_size, has_definition: d.has_definition, substantive: d.substantive }, depth, { current: true }));
    for (const c of d.children || []) rows.push(treeRow(c, depth + 1, { filterable: true }));
    if (d.children_truncated) rows.push(`<div class="motif-subtree-more" style="--depth:${depth + 1}">… more sub-motifs</div>`);
    return `${controls(false)}<div class="motif-tree${filterClass()}">${rows.join("")}</div>`;
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
    const reRenderBrowse = () => {
        if (mState.browseView === "root") { browseRoot(); return true; }
        if (mState.browseView === "chapter") { browseChapterLevel0(mState.browseChapter); return true; }
        return false;
    };
    const sel = detail.querySelector(".motif-filter");
    if (sel) sel.addEventListener("change", () => {
        mState.motifFilter = sel.value;
        // Browse views re-render (the row set depends on the filter); the detail
        // lineage just toggles the hide/badge classes on its built tree.
        if (reRenderBrowse()) return;
        detail.querySelectorAll(".motif-tree").forEach((t) => {
            t.classList.toggle("filter-def", sel.value === "def");
            t.classList.toggle("filter-sub", sel.value === "sub");
            t.classList.toggle("filter-atu", sel.value === "atu");
        });
    });
    const flat = detail.querySelector(".flat-cb");
    if (flat) flat.addEventListener("change", () => {
        mState.flatList = flat.checked;
        reRenderBrowse();
    });
}

// Catalog root view: "/" (current, total count) + the chapter rows.
async function browseRoot() {
    const detail = document.getElementById("motifsDetail");
    if (!detail) return;
    mState.selectedId = null;
    mState.browseChapter = null;
    mState.browseView = "root";
    markActive(null);
    detail.innerHTML = "";
    try {
        const rows = [rootRow(0, { current: true })];
        if (mState.flatList) {
            // Flat: every (matching) motif of the index, no chapters/categories.
            const data = await fetchFlat("");
            for (const it of data.items) rows.push(treeRow(it, 1));
            if (data.total > data.items.length) rows.push(moreRow(data.total - data.items.length, 1));
        } else {
            for (const c of currentIndex().chapters || []) rows.push(chapterRow(c.id, 1, { filterable: true }));
        }
        detail.innerHTML = `<div class="motif-detail-inner">${controls(true)}<div class="motif-tree${filterClass()}">${rows.join("")}</div></div>`;
        detail.scrollTop = 0;
        bindTreeLinks(detail);
    } catch (error) {
        detail.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}

// --- index overview dashboard ------------------------------------------------

async function renderOverview() {
    const detail = document.getElementById("motifsDetail");
    if (!detail) return;
    mState.selectedId = null;
    mState.browseChapter = null;
    mState.browseView = null;
    markActive(null);
    detail.innerHTML = "";
    try {
        const s = await api(`/api/motifs/${mState.index}/stats`);
        detail.innerHTML = overviewHtml(s);
        detail.scrollTop = 0;
        drawCharts(s);
    } catch (error) {
        detail.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}

// Generic dashboard: a stat-card strip + a grid of chart containers, both driven
// by the server's `cards` and `panels`. drawCharts() fills the containers.
function overviewHtml(s) {
    if (!s.cards) {
        return `<div class="motif-detail-inner"><div class="reader-placeholder">No overview for this index.</div></div>`;
    }
    const card = (c) => `<div class="stat-card"><div class="stat-num">${formatNumber(c.value)}${c.suffix || ""}</div><div class="stat-label">${escapeHtml(c.label)}</div></div>`;
    const panel = (p) => `<div class="chart-card"><div class="chart-title">${escapeHtml(p.title)}</div><div class="chart" id="${escapeHtml(p.id)}"></div></div>`;
    return `<div class="motif-detail-inner motif-overview">
        <h2 class="overview-title">${escapeHtml(s.title || "")}</h2>
        <div class="stat-cards">${(s.cards || []).map(card).join("")}</div>
        <div class="chart-grid">${(s.panels || []).map(panel).join("")}</div>
    </div>`;
}

function drawCharts(s, attempt = 0) {
    const P = window.Plotly;
    if (!P) { if (attempt < 25) setTimeout(() => drawCharts(s, attempt + 1), 200); return; }  // CDN still loading
    const cfg = { displayModeBar: false, responsive: true };
    const ACC = "#2a9d8f", MUT = "#bcdcd6";  // teal — distinct from the blue UI accent
    const lay = (e = {}) => Object.assign({
        margin: { l: 44, r: 12, t: 8, b: 34 }, height: 240, font: { size: 11 },
        paper_bgcolor: "transparent", plot_bgcolor: "transparent", showlegend: false,
        hoverlabel: { bgcolor: "#000", bordercolor: "#000", font: { color: "#fff" } },
    }, e);
    const vbar = (id, rows, xk, yk, extra) => P.newPlot(id,
        [{ type: "bar", x: rows.map((r) => r[xk]), y: rows.map((r) => r[yk]), marker: { color: ACC } }], lay(extra), cfg);
    // Height scales with the row count so Plotly shows every bar's label (it
    // decimates labels when many bars are crammed into a fixed height).
    const hbar = (id, rows, label, val, extra) => P.newPlot(id,
        [{ type: "bar", orientation: "h", x: rows.map((r) => r[val]), y: rows.map(label), marker: { color: ACC } }],
        lay(Object.assign({
            height: Math.max(240, rows.length * 19 + 24), margin: { l: 160, r: 12, t: 8, b: 30 },
            // Hold the tick labels off the bars so they don't read as glued to them.
            yaxis: { ticklabelstandoff: 8 },
        }, extra)), cfg);

    if (s.index === "tmi") {
        P.newPlot("ovComposition", [{
            type: "pie", hole: 0.55, sort: false, textinfo: "label+percent",
            labels: s.composition.map((c) => c.label), values: s.composition.map((c) => c.count),
            marker: { colors: [ACC, "#7cc0b6", "#d4e7e3"] },
        }], lay(), cfg);
        vbar("ovLevels", s.levels, "level", "count");
        vbar("ovNotes", s.notes_histogram, "bucket", "count");
        P.newPlot("ovChapters", [
            { type: "bar", x: s.chapters.map((c) => c.id), y: s.chapters.map((c) => c.count), marker: { color: MUT }, name: "all" },
            { type: "bar", x: s.chapters.map((c) => c.id), y: s.chapters.map((c) => c.substantive), marker: { color: ACC }, name: "substantive" },
        ], lay({ barmode: "overlay", showlegend: true, legend: { orientation: "h", y: 1.18, font: { size: 10 } } }), cfg);
        hbar("ovRegions", s.regions.slice().reverse(), (r) => r.region, "count", { margin: { l: 130, r: 12, t: 8, b: 30 } });
        hbar("ovCultures", s.top_cultures.slice(0, 15).reverse(), (r) => r.label, "count", { margin: { l: 110, r: 12, t: 8, b: 30 } });
        vbar("ovBreadth", s.breadth_histogram, "bucket", "count");
        hbar("ovTopNotes", s.top_notes.slice().reverse(), (r) => `${r.id} ${r.name}`.slice(0, 26), "bytes");
        hbar("ovHubs", s.see_also_hubs.slice().reverse(), (r) => `${r.id} ${r.name}`.slice(0, 26), "indeg");
        hbar("ovSources", (s.top_sources || []).slice().reverse(), (r) => r.label, "count", { margin: { l: 120, r: 12, t: 8, b: 30 } });
    } else if (s.index === "berezkin") {
        vbar("bzChapters", s.chapters, "id", "count");
        // mapsofmyths thematic groups — only present when the enrichment ran.
        if (s.groups) hbar("bzGroups", s.groups.slice().reverse(), (r) => r.label.slice(0, 34), "count", { margin: { l: 220, r: 12, t: 8, b: 30 } });
        hbar("bzRegions", s.regions.slice().reverse(), (r) => r.region, "count", { margin: { l: 150, r: 12, t: 8, b: 30 } });
        hbar("bzAreas", s.top_areas.slice().reverse(), (r) => r.label.slice(0, 22), "count", { margin: { l: 150, r: 12, t: 8, b: 30 } });
        hbar("bzWidest", s.widest.slice().reverse(), (r) => r.label.slice(0, 26), "count", { margin: { l: 170, r: 12, t: 8, b: 30 } });
        vbar("bzBreadth", s.breadth, "bucket", "count");
    } else if (s.index === "atu") {
        hbar("atChapters", s.chapters.slice().reverse(), (r) => r.label.slice(0, 22), "count", { margin: { l: 150, r: 12, t: 8, b: 30 } });
        hbar("atDivisions", s.divisions.slice().reverse(), (r) => r.label.slice(0, 30), "count", { margin: { l: 210, r: 12, t: 8, b: 30 } });
        vbar("atMotifHist", s.motif_hist, "bucket", "count");
        hbar("atRich", s.top_rich.slice().reverse(), (r) => r.label.slice(0, 26), "count", { margin: { l: 170, r: 12, t: 8, b: 30 } });
    }
}

function section(title, bodyHtml) {
    return `<div class="motif-section"><div class="motif-section-title">${escapeHtml(title)}</div>${bodyHtml}</div>`;
}

function linkSection(title, links) {
    return section(title, `<div class="motif-links">${linkChips(links)}</div>`);
}

// Tradition-level distribution (mapsofmyths): total attesting traditions, broken
// down by macro-region; each region expands to the named traditions.
// Title-case an ALL-CAPS label as a proper name (first letter of each word,
// rest lower-case): "SOUTHWEST AND CENTRAL ASIA" -> "Southwest And Central Asia".
function titleCase(s) {
    return s.toLowerCase().replace(/(^|[\s\-–—'’/(])(\p{L})/gu, (m, sep, ch) => sep + ch.toUpperCase());
}

function berezkinDistribution(dist) {
    if (!dist || !dist.total) return "";
    // Region names arrive as the ALL-CAPS top areal-path label; title-case them.
    // Tradition names are already properly capitalized, so leave them untouched.
    // A shared name makes the regions an exclusive accordion: opening one
    // collapses the others (native <details name> behavior).
    const rows = (dist.regions || []).map((r) => `
        <details class="motif-dist-region" name="motif-dist-region">
            <summary><span class="motif-dist-name">${escapeHtml(titleCase(r.region))}</span><span class="motif-dist-count">${formatNumber(r.count)}</span></summary>
            <div class="motif-dist-traditions">${(r.traditions || []).map(escapeHtml).join(", ")}</div>
        </details>`).join("");
    return section(`Ethne (${formatNumber(dist.total)})`, `<div class="motif-dist">${rows}</div>`);
}

// One bibliography source: resolved works show author · year — title; unresolved
// citations fall back to the raw "surname year" key (muted, with the status).
function bibSourceHtml(s) {
    if (s.author) {
        const year = s.year ? ` <span class="motif-bib-year">${escapeHtml(s.year)}</span>` : "";
        const title = s.title ? ` — <span class="motif-bib-title">${escapeHtml(s.title)}</span>` : "";
        // Plain-text form copied to the clipboard on click.
        const copy = [s.author, s.year].filter(Boolean).join(" ") + (s.title ? ` — ${s.title}` : "");
        return `<li class="motif-bib-item" data-copy="${escapeHtml(copy)}" title="Click to copy"><span class="motif-bib-author">${escapeHtml(s.author)}</span>${year}${title}</li>`;
    }
    // The status word links to the Berezkin bibliography page so it can be looked up.
    const tag = s.status && s.status !== "resolved"
        ? ` <a class="motif-bib-status" href="http://areasofmyths.com/biblio.html" target="_blank" rel="noopener">(${escapeHtml(s.status)})</a>`
        : "";
    return `<li class="motif-bib-item motif-bib-unresolved" data-copy="${escapeHtml(s.key)}" title="Click to copy">${escapeHtml(s.key)}${tag}</li>`;
}

// Berezkin source bibliography (areasofmyths.com): a collapsible list per macro-
// area with its sources, then the citations not tied to any areal code (headed
// "—", matching the Ethne section's no-region bucket).
function berezkinBibliography(bib) {
    const areas = (bib && bib.by_area) || [];
    const unattached = (bib && bib.unattached) || [];
    if (!areas.length && !unattached.length) return "";
    // Shared name -> exclusive accordion: opening one collapses the others.
    const areaBlock = (a) => `
        <details class="motif-bib-area" name="motif-bib">
            <summary><span class="motif-bib-region">${escapeHtml(a.region || a.area_code)}</span><span class="motif-bib-count">${formatNumber((a.sources || []).length)}</span></summary>
            <ul class="motif-bib-list">${(a.sources || []).map(bibSourceHtml).join("")}</ul>
        </details>`;
    let rows = areas.map(areaBlock).join("");
    if (unattached.length) {
        rows += `
        <details class="motif-bib-area" name="motif-bib">
            <summary><span class="motif-bib-region">—</span><span class="motif-bib-count">${formatNumber(unattached.length)}</span></summary>
            <ul class="motif-bib-list">${unattached.map(bibSourceHtml).join("")}</ul>
        </details>`;
    }
    // Distinct books across the whole motif (a work can span several macro-areas).
    const bookKeys = new Set();
    areas.forEach((a) => (a.sources || []).forEach((s) => bookKeys.add(s.key)));
    unattached.forEach((s) => bookKeys.add(s.key));
    return section(`Bibliography (${formatNumber(bookKeys.size)})`, `<div class="motif-bib">${rows}</div>`);
}

// A citation: linked to its source book when the server resolved one.
function citeHtml(c) {
    const text = escapeHtml(c.text || "");
    if (!c.url) return `<span class="motif-cite">${text}</span>`;
    return `<a class="motif-cite linked" href="${escapeHtml(c.url)}" target="_blank" rel="noopener"
               title="${escapeHtml(c.title || c.url)}">${text} <span class="ext-arrow">↗</span></a>`;
}

function citeList(items) {
    return `<ul class="motif-cites">${items.map((c) => `<li>${citeHtml(c)}</li>`).join("")}</ul>`;
}

// Attestations grouped by macro-region: each region name is printed once, then
// its cultures — one culture per row (label + its citation link, any further
// links stacked under the first). Cultures with no region come last, un-headed.
function culturesHtml(cultures) {
    const groups = new Map();  // region -> [culture]; the "" bucket renders last
    for (const c of cultures) {
        const key = c.region || "";
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(c);
    }
    // Regions ordered by how many cultures they hold (most first); no-region last.
    const regions = [...groups.keys()].filter(Boolean)
        .sort((a, b) => groups.get(b).length - groups.get(a).length);
    if (groups.has("")) regions.push("");
    const row = (c) => `
        <div class="motif-culture-row">
            <span class="motif-culture-label">${escapeHtml(c.label)}</span>
            <div class="motif-culture-cites">${(c.citations || [])
                .map((cite) => `<div class="motif-culture-cite">${citeHtml(cite)}</div>`).join("")}</div>
        </div>`;
    const group = (region) => `
        <div class="motif-culture-group">
            ${region ? `<div class="motif-culture-region-head">${escapeHtml(region)}</div>` : ""}
            ${groups.get(region).map(row).join("")}
        </div>`;
    return `<div class="motif-cultures">${regions.map(group).join("")}</div>`;
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
        // The Russian original name rides under the English one, left-aligned with
        // it (inside the name column) and muted.
        const subtitle = d.name_rus && d.name_rus !== d.name
            ? `<div class="motif-subtitle">${escapeHtml(d.name_rus)}</div>` : "";
        body = `
            <div class="motif-head">
                <span class="motif-code">${escapeHtml(d.id)}</span>
                <div class="motif-name-col">
                    <h2 class="motif-name">${escapeHtml(d.name || "—")}</h2>
                    ${subtitle}
                </div>
            </div>`;
        if (d.definition) {
            let inner = `<p class="motif-text motif-def">${escapeHtml(d.definition)}</p>`;
            if (d.definition_rus && d.definition_rus !== d.definition) {
                inner += `<p class="motif-text motif-def motif-text-rus">${escapeHtml(d.definition_rus)}</p>`;
            }
            body += section("Definition", inner);
        }
        // Classification folds in the chapter (letter + name) alongside the
        // mapsofmyths type/group taxonomy.
        const clsParts = [d.motif_type, d.motif_group].filter(Boolean).map(escapeHtml);
        const chapter = d.chapter_label || d.chapter;
        if (chapter) {
            // Alongside a type/group the chapter is a muted, italic trailer; when it
            // is the only classification (fallback), show it in the normal style.
            clsParts.push(clsParts.length
                ? `<span class="motif-taxonomy-chapter">${escapeHtml(chapter)}</span>`
                : escapeHtml(chapter));
        }
        if (clsParts.length) {
            body += section("Classification", `<div class="motif-taxonomy">${clsParts.join(" · ")}</div>`);
        }
        // Cross-references to other motifs and indexes come before the distribution.
        if ((links.tmi || []).length) body += linkSection("Thompson motifs (TMI)", links.tmi);
        if ((links.atu || []).length) body += linkSection("ATU tale types", links.atu);
        if ((links.see_also || []).length) body += linkSection("See also (Berezkin)", links.see_also);
        // Macro-areas: hide the whole section when the motif has none.
        if ((d.areas || []).length) {
            const areas = d.areas.map((a) =>
                `<span class="motif-area${a.name ? "" : " unresolved"}" title="area ${escapeHtml(a.id)}">${escapeHtml(a.name || a.id)}</span>`).join("");
            body += section(`Macro-areas (${d.areas.length})`, `<div class="motif-areas">${areas}</div>`);
        }
        body += berezkinDistribution(d.traditions);
        body += berezkinBibliography(d.bibliography);
        if (d.source_url) {
            body += section("Source", `<a class="motif-source-link" href="${escapeHtml(d.source_url)}" target="_blank" rel="noopener">${escapeHtml(d.source_url)} <span class="ext-arrow">↗</span></a>`);
        }
    } else if (d.index === "tmi") {
        // Hierarchy tree first, then all the motif's own information, and the raw
        // source `notes` verbatim at the very end.
        body = renderTmiTree(d);
        body += head;
        if (d.duplicate) {
            body += `<p class="motif-dup-note">Source code <strong>${escapeHtml(d.code || d.id)}</strong> is reused for several distinct motifs; shown here under <strong>${escapeHtml(d.id)}</strong>.</p>`;
        }
        if (d.definition) body += section("Definition", `<p class="motif-text motif-def">${escapeHtml(d.definition)}</p>`);
        if ((links.see_also || []).length) body += linkSection("See also", links.see_also);
        if ((links.see_also_cf || []).length) body += linkSection("Compare (cf.)", links.see_also_cf);
        if ((links.atu || []).length) body += linkSection("Appears in ATU tale types", links.atu);
        if ((links.atu_inline || []).length) body += linkSection("Referenced tale types (Type …)", links.atu_inline);
        if ((links.berezkin || []).length) body += linkSection("Berezkin motifs mapping here", links.berezkin);
        if ((d.cultures || []).length) body += section(`Attestations by culture (${d.cultures.length})`, culturesHtml(d.cultures));
        if ((d.references || []).length) body += section(`References (${d.references.length})`, citeList(d.references));
        if (d.notes) body += section("Source text (notes)", `<p class="motif-text motif-notes-raw">${escapeHtml(d.notes)}</p>`);
    } else if (d.index === "atu") {
        body = head + chapterLine;
        if (d.division) body += section("Division", `<p class="motif-text">${escapeHtml(d.division)}</p>`);
        if (d.summary) body += section("Summary", `<p class="motif-text">${escapeHtml(d.summary)}</p>`);
        if ((links.tmi || []).length) body += linkSection(`Constituent TMI motifs (${links.tmi.length})`, links.tmi);
        if ((links.combos || []).length) body += linkSection("Combined with", links.combos);
        if ((links.berezkin || []).length) body += linkSection("Referenced by Berezkin motifs", links.berezkin);
    }

    return `<div class="motif-detail-inner">${body}</div>`;
}
