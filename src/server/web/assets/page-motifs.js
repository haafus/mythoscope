import { app, api, escapeHtml, formatNumber, onCleanup } from "./core.js";

// Module-local navigation state (index, chapter filter, query, selection).
const mState = {
    indexes: null,
    index: "tmi",  // default index on first open (Thompson)
    chapter: "",
    division: "",      // ATU browse level (chapter → division → type)
    subdivision: "",   // ATU finer level (division → sub_division → type)
    query: "",
    selectedId: null,
    motifFilter: "all",  // "all" | "def" | "sub" | "atu"
    flatList: false,     // browse as a flat list (no parent categories) instead of drill-down
    browseChapter: null, // chapter currently shown in the main-panel browse, if any
    browseView: null,    // "root" | "chapter" | null (detail/overview)
};

const LIST_LIMIT = 300;
let searchTimer = null;
// True while renderMotifs is restoring state from the URL, to suppress the URL
// writes that the view functions would otherwise make (avoids feedback/loops).
let restoring = false;

// The current filter/display/selection state as a URL query.
function stateParams() {
    const p = new URLSearchParams();
    p.set("index", mState.index);
    if (mState.chapter) p.set("chapter", mState.chapter);
    if (mState.division) p.set("division", mState.division);
    if (mState.subdivision) p.set("subdivision", mState.subdivision);
    if (mState.query.trim()) p.set("q", mState.query.trim());
    if (mState.motifFilter && mState.motifFilter !== "all") p.set("filter", mState.motifFilter);
    if (mState.flatList) p.set("flat", "1");
    if (mState.selectedId) p.set("id", mState.selectedId);
    else if (mState.browseView === "root") p.set("view", "root");
    else if (mState.browseView === "chapter" && mState.browseChapter) p.set("view", mState.browseChapter);
    return p;
}

// Reflect the current state in the URL. push=true adds a history entry (deliberate
// navigation); push=false replaces it (continuous tweaks like typing). No-op while
// restoring or when the URL is already current.
function syncUrl(push) {
    if (restoring) return;
    const url = `#/motifs?${stateParams().toString()}`;
    if (url === window.location.hash) return;
    if (push) history.pushState(null, "", url);
    else history.replaceState(null, "", url);
}

export async function renderMotifs(params = new URLSearchParams()) {
    app.innerHTML = `
        <main class="motifs-page container">
            <div class="workspace">
                <aside class="library-sidebar motifs-sidebar">
                    <div class="motifs-tabs" id="motifsTabs">${tabsPlaceholder()}</div>
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

    // Restore all filter/display/selection state from the URL (deep links, refresh,
    // back/forward). Guard the view functions from writing the URL while we do.
    restoring = true;
    const wantIndex = params.get("index");
    if (wantIndex && mState.indexes.some((i) => i.index === wantIndex)) mState.index = wantIndex;
    else if (!mState.indexes.some((i) => i.index === mState.index)) mState.index = mState.indexes[0].index;
    mState.chapter = params.get("chapter") || "";
    mState.division = params.get("division") || "";
    mState.subdivision = params.get("subdivision") || "";
    mState.query = params.get("q") || "";
    mState.motifFilter = params.get("filter") || "all";
    mState.flatList = params.get("flat") === "1";

    renderTabs();
    renderChapters();
    wireControls();
    await loadList();

    // The URL is the source of truth for the main view — reset the selection so a
    // stale one doesn't re-open on back/forward.
    const wantId = params.get("id");
    const wantView = params.get("view");
    mState.selectedId = wantId || null;
    mState.browseChapter = null;
    mState.browseView = null;
    if (wantId) await openMotif(mState.index, wantId);
    else if (wantView === "root") await browseRoot();
    else if (wantView) await browseChapterLevel0(wantView);
    else await renderOverview();
    restoring = false;
    syncUrl(false);  // normalise the URL to the restored state (no new history entry)
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
    const idx = currentIndex();
    const all = `<option value="">All ${mState.index === "atu" ? "tale types" : "chapters"} (${formatNumber(idx.count)})</option>`;
    // ATU browses by division (finer than the 7 chapters), grouped under them and
    // ordered by ascending number range (so the chapters/divisions read 1 → 2399).
    if (mState.index === "atu" && (idx.divisions || []).length) {
        // Sub-divisions (optional 3rd level) nest under their division, indented.
        const subsByDiv = new Map();
        for (const s of [...(idx.subdivisions || [])].sort((a, b) => a.start - b.start)) {
            if (!subsByDiv.has(s.division)) subsByDiv.set(s.division, []);
            subsByDiv.get(s.division).push(s);
        }
        const byChapter = new Map();
        for (const d of [...idx.divisions].sort((a, b) => a.start - b.start)) {
            if (!byChapter.has(d.chapter)) byChapter.set(d.chapter, []);
            byChapter.get(d.chapter).push(d);
        }
        const divOption = (d) => {
            const sel = d.name === mState.division && !mState.subdivision ? " selected" : "";
            let html = `<option value="d:${escapeHtml(d.name)}"${sel}>${escapeHtml(d.name)} ${d.start}–${d.end} (${formatNumber(d.count)})</option>`;
            for (const s of subsByDiv.get(d.name) || []) {
                const ssel = s.name === mState.subdivision ? " selected" : "";
                html += `<option value="sd:${escapeHtml(s.name)}"${ssel}>&nbsp;&nbsp;↳ ${escapeHtml(s.name)} ${s.start}–${s.end} (${formatNumber(s.count)})</option>`;
            }
            return html;
        };
        select.innerHTML = all + [...byChapter].map(([ch, divs]) => `
            <optgroup label="${escapeHtml(ch)}">${divs.map(divOption).join("")}</optgroup>`).join("");
        return;
    }
    const chapters = idx.chapters || [];
    select.innerHTML = all +
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
        searchTimer = setTimeout(() => { loadList(); syncUrl(false); }, 250);  // typing → replace
    });
    document.getElementById("motifsChapter").addEventListener("change", (e) => {
        const v = e.target.value;
        // ATU options: "sd:" a sub-division, "d:" a division; everything else a chapter.
        if (v.startsWith("sd:")) { mState.subdivision = v.slice(3); mState.division = ""; mState.chapter = ""; }
        else if (v.startsWith("d:")) { mState.division = v.slice(2); mState.subdivision = ""; mState.chapter = ""; }
        else { mState.chapter = v; mState.division = ""; mState.subdivision = ""; }
        loadList();
        syncUrl(true);
    });
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
    openMotif(mState.index, btn.dataset.id, false);  // stepping → replace, don't flood history
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

// Reset filters/search to a fresh index and repaint the tabs + chapter select.
function resetIndexFilters(index) {
    mState.index = index;
    mState.chapter = "";
    mState.division = "";
    mState.subdivision = "";
    mState.query = "";
    const search = document.getElementById("motifsSearch");
    if (search) search.value = "";
    renderTabs();
    renderChapters();
}

async function switchIndex(index) {
    resetIndexFilters(index);
    await loadList();
}

async function selectIndex(index) {
    // Clicking the index tab is now the way back to its overview — re-render it
    // even when the tab is already active (the old dedicated Overview button).
    if (index === mState.index) {
        renderOverview();
        return;
    }
    resetIndexFilters(index);
    mState.selectedId = null;
    mState.browseChapter = null;
    mState.browseView = null;
    markActive(null);
    syncUrl(true);
    const list = document.getElementById("motifsList");
    const detail = document.getElementById("motifsDetail");
    if (list) list.innerHTML = "";
    if (detail) detail.innerHTML = "";
    // Fetch the list and the overview in parallel, then paint both in the same
    // tick so the sidebar and the dashboard appear together, not one then the other.
    try {
        const [listData, stats] = await Promise.all([
            api(`/api/motifs/${index}/motifs?${listParams()}`),
            api(`/api/motifs/${index}/stats`),
        ]);
        renderList(listData);
        renderOverviewFrom(stats);
    } catch (error) {
        if (detail) detail.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
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
    syncUrl(true);
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

function listParams() {
    const params = new URLSearchParams({ limit: String(LIST_LIMIT) });
    if (mState.chapter) params.set("chapter", mState.chapter);
    if (mState.division) params.set("division", mState.division);
    if (mState.subdivision) params.set("sub_division", mState.subdivision);
    if (mState.query.trim()) params.set("q", mState.query.trim());
    return params;
}

async function loadList() {
    const list = document.getElementById("motifsList");
    if (!list) return;
    list.innerHTML = "";  // empty space while loading — no "Loading" flicker
    try {
        renderList(await api(`/api/motifs/${mState.index}/motifs?${listParams()}`));
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

async function openMotif(index, id, push = true) {
    // Following a cross-link can switch indexes; keep the sidebar in sync.
    if (index !== mState.index) {
        await switchIndex(index);
    }
    mState.selectedId = id;
    mState.browseChapter = null;
    mState.browseView = null;
    markActive(id);
    syncUrl(push);

    const detail = document.getElementById("motifsDetail");
    detail.innerHTML = "";  // blank intermediate screen during the switch (no "Loading" text)
    try {
        const params = new URLSearchParams({ id });
        const data = await api(`/api/motifs/${index}/motif?${params.toString()}`);
        if (data.redirected_from && data.id !== id) {   // an old ATU number → current type
            mState.selectedId = data.id;
            markActive(data.id);
            syncUrl(false);                             // replace the URL with the real id
        }
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

// Full labels for the concordance catalogues (Wikidata).
const CONC_LABELS = { KHM: "Grimm (KHM)", AaTh: "Aarne–Thompson (AaTh)",
                      Aesop: "Aesop (Fabulae)", Perry: "Aesop (Perry Index)", Child: "Child ballad" };

// Full bibliographic imprint for each catalogue, shown as a tooltip on the label so
// a reader can track the referenced numbering back to its source edition.
const CONC_CITATIONS = {
    KHM: "Jacob & Wilhelm Grimm, Kinder- und Hausmärchen (Children's and Household Tales). "
        + "7th edition, 3 vols. Göttingen: Verlag der Dieterichschen Buchhandlung, 1857. "
        + "Codes are the standard KHM tale numbers.",
    AaTh: "Antti Aarne & Stith Thompson, The Types of the Folktale: A Classification and "
        + "Bibliography. FF Communications No. 184, 2nd revision. Helsinki: Academia "
        + "Scientiarum Fennica, 1961.",
    Aesop: "Carl Halm (ed.), Fabulae Aesopicae Collectae. Leipzig: B. G. Teubner, 1852. "
        + "Codes are the Halm fable numbers.",
    Perry: "Ben Edwin Perry, Aesopica: A Series of Texts Relating to Aesop, vol. 1. "
        + "Urbana: University of Illinois Press, 1952. Codes are Perry Index numbers.",
    Child: "Francis James Child, The English and Scottish Popular Ballads. 5 vols. "
        + "Boston & New York: Houghton, Mifflin and Company, 1882–1898.",
};

// ATU multilingual names (Wikidata): one row per language.
function atuNames(names) {
    const langs = Object.keys(names || {});
    if (!langs.length) return "";
    // Language shown the same way as in the Wikipedia section: a small uppercase
    // code tag trailing the name(s).
    const rows = langs.map((lang) =>
        `<div class="motif-altname">${(names[lang] || []).map(escapeHtml).join(", ")} `
        + `<span class="motif-wiki-lang">${escapeHtml(lang)}</span></div>`).join("");
    return section("Also known as", `<div class="motif-altnames">${rows}</div>`);
}

// Concordances to other catalogues (Grimm/KHM, Aarne-Thompson, Aesop, Child).
function atuConcordances(conc) {
    const cats = Object.keys(conc || {});
    if (!cats.length) return "";
    const rows = cats.map((cat) => {
        const cite = CONC_CITATIONS[cat];
        const title = cite ? ` title="${escapeHtml(cite)}"` : "";
        return `<div class="motif-altname"><span class="motif-altname-lang" tabindex="0"${title}>`
            + `${escapeHtml(CONC_LABELS[cat] || cat)}</span>`
            + ` ${(conc[cat] || []).map(escapeHtml).join(", ")}</div>`;
    }).join("");
    return section("Also catalogued as", `<div class="motif-altnames">${rows}</div>`);
}

// Wikipedia articles for the type (Wikidata), each tagged with its language, plus
// a Wikidata link. Tolerates the old en-only shape ({title, url} without lang).
function atuWikipedia(wiki) {
    const list = wiki || [];
    if (!list.length) return "";
    const items = list.map((w) => {
        const lang = w.lang ? ` <span class="motif-wiki-lang">${escapeHtml(w.lang)}</span>` : "";
        return `<li><a href="${escapeHtml(w.url)}" target="_blank" rel="noopener">${escapeHtml(w.title)} <span class="ext-arrow">↗</span></a>${lang}</li>`;
    }).join("");
    return section(`Wikipedia (${list.length})`, `<ul class="motif-wiki-list">${items}</ul>`);
}

// Example folktales of an ATU type (Ashliman AFT): a plain list of links to each
// variant's text (deep-linked to its anchor where resolved, else the type page;
// unresolved tales show as plain titles). Corpus attribution lives on the overview.
function atuTales(tales) {
    if (!tales || !tales.length) return "";
    const rows = tales.map((t) => t.url
        ? `<li class="motif-tale"><a href="${escapeHtml(t.url)}" target="_blank" rel="noopener">${escapeHtml(t.title)} <span class="ext-arrow">↗</span></a></li>`
        : `<li class="motif-tale">${escapeHtml(t.title)}</li>`).join("");
    return section(`Ashliman (${tales.length})`, `<ul class="motif-tales">${rows}</ul>`);
}

// Recurring reference-work / journal abbreviations in the Uther apparatus, with
// their full name (always, as a tooltip) and a link to the work where one exists.
// The per-type bibliography has no key of its own (unlike TMI), so this decodes
// only the standard series/catalogue abbreviations, not individual author-year
// citations (that would need Uther's full bibliography).
const ATU_ABBR = {
    EM: { name: "Enzyklopädie des Märchens", url: "https://en.wikipedia.org/wiki/Enzyklop%C3%A4die_des_M%C3%A4rchens" },
    BP: { name: "Bolte & Polívka, Anmerkungen zu den Kinder- und Hausmärchen", url: "https://en.wikipedia.org/wiki/Ji%C5%99%C3%AD_Pol%C3%ADvka" },
    HDA: { name: "Handwörterbuch des deutschen Aberglaubens", url: "https://de.wikipedia.org/wiki/Handw%C3%B6rterbuch_des_deutschen_Aberglaubens" },
    Perry: { name: "Perry Index (B. E. Perry, Aesopica)", url: "https://en.wikipedia.org/wiki/Perry_Index" },
    JAFL: { name: "Journal of American Folklore", url: "https://en.wikipedia.org/wiki/Journal_of_American_Folklore" },
    ZDMG: { name: "Zeitschrift der Deutschen Morgenländischen Gesellschaft", url: "https://menadoc.bibliothek.uni-halle.de/dmg/" },
    RTP: { name: "Revue des traditions populaires", url: "https://fr.wikipedia.org/wiki/Revue_des_traditions_populaires" },
    Tubach: { name: "F. C. Tubach, Index Exemplorum", url: "https://books.google.com/books/about/Index_Exemplorum.html?id=fz17jgEACAAJ" },
    HDM: { name: "Handwörterbuch des deutschen Märchens", url: "https://www.degruyter.com/serial/hwbdv2-b/html?lang=en" },
    BFP: { name: "Bâlgarski folkloren prikazen katalog (Bulgarian Folktale Catalogue)", url: "https://www.cambridge.org/core/journals/slavic-review/article/abs/bulgarski-folklorni-prikazki-katalog-ed-l-daskalovaperkovska-d-dobreva-j-koceva-e-miceva-sofia-univ-izdatelstvo-sv-kliment-okhridski-1994-825-pp-120-lv/B75A1FE922F3344D24C1C6A869DCBBFD" },
    SUS: { name: "Sravnitel'nyj ukazatel' sjužetov (East Slavic Folktale Catalogue)", url: "https://www.ruthenia.ru/folklore/sus/index.htm" },
    HDS: { name: "Handwörterbuch der deutschen Sage" },
    MNK: { name: "Magyar Népmesekatalógus (Hungarian Folktale Catalogue)" },
};
// Famous named collections / authors that recur by name in the apparatus, each
// with a full title and a link to the work (full text preferred where it exists).
const ATU_WORKS = {
    "Gesta Romanorum": { name: "Gesta Romanorum (medieval Latin tale collection)", url: "https://en.wikisource.org/wiki/Gesta_Romanorum" },
    "Roman de Renart": { name: "Roman de Renart (the Reynard the Fox cycle)", url: "https://en.wikipedia.org/wiki/Reynard_the_Fox" },
    "Disciplina clericalis": { name: "Petrus Alfonsi, Disciplina clericalis", url: "https://en.wikipedia.org/wiki/Disciplina_Clericalis" },
    "Till Eulenspiegel": { name: "Till Eulenspiegel", url: "https://en.wikipedia.org/wiki/Till_Eulenspiegel" },
    Eulenspiegel: { name: "Till Eulenspiegel", url: "https://en.wikipedia.org/wiki/Till_Eulenspiegel" },
    "1001 Nights": { name: "One Thousand and One Nights (Arabian Nights)", url: "https://en.wikipedia.org/wiki/One_Thousand_and_One_Nights" },
    "Legenda aurea": { name: "Jacobus de Voragine, Legenda aurea (Golden Legend)", url: "https://sourcebooks.fordham.edu/basis/goldenlegend/" },
    "Marie de France": { name: "Marie de France (Fables / Lais)", url: "https://en.wikipedia.org/wiki/Marie_de_France" },
    Decameron: { name: "Giovanni Boccaccio, Decameron", url: "https://www.gutenberg.org/ebooks/23700" },
    Boccaccio: { name: "Giovanni Boccaccio, Decameron", url: "https://www.gutenberg.org/ebooks/23700" },
    Pentamerone: { name: "Giambattista Basile, Pentamerone (Lo cunto de li cunti)", url: "https://en.wikipedia.org/wiki/Pentamerone" },
    Basile: { name: "Giambattista Basile, Pentamerone", url: "https://en.wikipedia.org/wiki/Giambattista_Basile" },
    Metamorphoses: { name: "Ovid, Metamorphoses", url: "https://www.gutenberg.org/ebooks/26073" },
    Ovid: { name: "Ovid, Metamorphoses", url: "https://www.gutenberg.org/ebooks/26073" },
    Pauli: { name: "Johannes Pauli, Schimpf und Ernst", url: "https://de.wikipedia.org/wiki/Schimpf_und_Ernst" },
    Bebel: { name: "Heinrich Bebel, Facetiae", url: "https://en.wikipedia.org/wiki/Heinrich_Bebel" },
    Kirchhof: { name: "Hans Wilhelm Kirchhof, Wendunmuth", url: "https://de.wikipedia.org/wiki/Hans_Wilhelm_Kirchhof" },
    Montanus: { name: "Martin Montanus (Schwankbücher)", url: "https://de.wikipedia.org/wiki/Martin_Montanus" },
    Poggio: { name: "Poggio Bracciolini, Facetiae", url: "https://en.wikipedia.org/wiki/Poggio_Bracciolini" },
    Straparola: { name: "Giovan Francesco Straparola, Le piacevoli notti", url: "https://en.wikipedia.org/wiki/Giovanni_Francesco_Straparola" },
    Sercambi: { name: "Giovanni Sercambi, Novelle", url: "https://en.wikipedia.org/wiki/Giovanni_Sercambi" },
    Sacchetti: { name: "Franco Sacchetti, Il Trecentonovelle", url: "https://en.wikipedia.org/wiki/Franco_Sacchetti" },
    Aesop: { name: "Aesop's Fables", url: "https://en.wikipedia.org/wiki/Aesop%27s_Fables" },
    Grimm: { name: "Brothers Grimm, Kinder- und Hausmärchen (KHM)", url: "https://en.wikipedia.org/wiki/Grimms%27_Fairy_Tales" },
    Perrault: { name: "Charles Perrault, Histoires ou contes du temps passé", url: "https://en.wikipedia.org/wiki/Charles_Perrault" },
    Kathasaritsagara: { name: "Somadeva, Kathāsaritsāgara", url: "https://en.wikipedia.org/wiki/Kathasaritsagara" },
    Somadeva: { name: "Somadeva, Kathāsaritsāgara", url: "https://en.wikipedia.org/wiki/Kathasaritsagara" },
    Herodotus: { name: "Herodotus, Histories", url: "https://en.wikipedia.org/wiki/Histories_(Herodotus)" },
    Morlini: { name: "Girolamo Morlini, Novellae" },
};

const ATU_REF = Object.assign({}, ATU_ABBR, ATU_WORKS);
const ATU_ABBR_RE = new RegExp(
    "\\b(" + Object.keys(ATU_REF).sort((a, b) => b.length - a.length)
        .map((k) => k.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")).join("|") + ")\\b", "g");

// Linkify the known abbreviations / works in already-escaped citation text: a link
// where the work has a page, otherwise an <abbr> that shows the full name on hover.
function abbrLinkify(escaped) {
    return escaped.replace(ATU_ABBR_RE, (m) => {
        const a = ATU_REF[m];
        const title = escapeHtml(a.name);
        return a.url
            ? `<a class="motif-abbr" href="${a.url}" target="_blank" rel="noopener" title="${title}">${m}</a>`
            : `<abbr class="motif-abbr" title="${title}">${m}</abbr>`;
    });
}

// Uther's per-type apparatus: `references`/`attestations` are semicolon-delimited
// citation strings (rendered as a list); `remarks` is prose (a paragraph).
function atuProse(title, text, split) {
    if (!text) return "";
    if (split) {
        const parts = text.split(/\s*;\s*/).filter(Boolean);
        const items = parts.map((s) => `<li>${abbrLinkify(escapeHtml(s))}</li>`).join("");
        return section(`${title} (${parts.length})`, `<ul class="motif-cite-list">${items}</ul>`);
    }
    return section(title, `<p class="motif-text">${abbrLinkify(escapeHtml(text))}</p>`);
}

// Why a cross-link couldn't resolve, for a clear tooltip instead of a bare gray chip.
const MISSING_REASON = {
    aath: "Aarne-Thompson (AaTh) tale-type number — no equivalent in ATU 2004",
    tmi_gap: "Motif code not present in the Trilogy TMI index",
};

// Direction marker for the merged motif↔ATU relations (from the TMI motif's view).
// `out` = a plain outgoing reference (this motif → the target); no REL_TITLE
// entry, so it renders the ⇒ glyph with no tooltip.
const REL_MARK = { both: "⇔", appears: "⇐", cited: "⇒", out: "⇒" };
const REL_TITLE = {
    both: "Both: a constituent of this tale type and named in the motif's note",
    appears: "This motif is a constituent of the tale type (from atu_seq)",
    cited: "The tale type is referenced in this motif's note",
};

function linkChips(links) {
    if (!links || !links.length) return `<span class="motif-empty">—</span>`;
    return links.map((l) => {
        const rel = l.rel
            ? `<span class="motif-link-rel" title="${escapeHtml(REL_TITLE[l.rel] || "")}">${REL_MARK[l.rel] || ""}</span>`
            : "";
        // A resolved-via-concordance link carries the original AaTh number it came from.
        const src = l.aath
            ? `<span class="motif-link-src" title="From Aarne-Thompson type ${escapeHtml(l.aath)}, renumbered in ATU 2004">AaTh ${escapeHtml(l.aath)}</span>`
            : "";
        // The minority of '†' cross-references that are bare direct redirects
        // rather than Thompson's 'Cf.' compares.
        const sa = l.see_also
            ? `<span class="motif-link-src" title="A direct 'see also' redirect, not a 'Cf.' compare">see also</span>`
            : "";
        const title = l.exists
            ? (l.aath ? `${l.name || l.id} — from Aarne-Thompson type ${l.aath}` : (l.name || l.id))
            : (MISSING_REASON[l.missing_reason] || `${l.name || l.id} (not in this database)`);
        return `
        <a href="#/motifs?index=${escapeHtml(l.index)}&id=${encodeURIComponent(l.id)}"
           class="motif-link${l.exists ? "" : " missing"}" data-index="${escapeHtml(l.index)}" data-id="${escapeHtml(l.id)}"
           title="${escapeHtml(title)}">
            ${rel}<span class="motif-link-id">${escapeHtml(l.id)}</span>${l.name ? `<span class="motif-link-name">${escapeHtml(l.name)}</span>` : ""}${src}${sa}
        </a>
    `;
    }).join("");
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
        // Browse views re-render (the row set depends on the filter, and that
        // re-render syncs the URL); the detail lineage just toggles classes.
        if (reRenderBrowse()) return;
        detail.querySelectorAll(".motif-tree").forEach((t) => {
            t.classList.toggle("filter-def", sel.value === "def");
            t.classList.toggle("filter-sub", sel.value === "sub");
            t.classList.toggle("filter-atu", sel.value === "atu");
        });
        syncUrl(true);
    });
    const flat = detail.querySelector(".flat-cb");
    if (flat) flat.addEventListener("change", () => {
        mState.flatList = flat.checked;
        reRenderBrowse();  // flat only applies to browse views, which sync the URL
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
    syncUrl(true);
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

// Paint the overview dashboard from already-fetched stats (no network).
function renderOverviewFrom(s) {
    const detail = document.getElementById("motifsDetail");
    if (!detail) return;
    detail.innerHTML = overviewHtml(s);
    detail.scrollTop = 0;
    drawOverviewCharts(s);   // all overview charts — pure CSS/SVG (Plotly stays for similarity)
}

async function renderOverview() {
    const detail = document.getElementById("motifsDetail");
    if (!detail) return;
    mState.selectedId = null;
    mState.browseChapter = null;
    mState.browseView = null;
    markActive(null);
    syncUrl(true);
    detail.innerHTML = "";
    try {
        renderOverviewFrom(await api(`/api/motifs/${mState.index}/stats`));
    } catch (error) {
        detail.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}

// Generic dashboard: a stat-card strip + a grid of chart containers, both driven
// by the server's `cards` and `panels`. drawOverviewCharts() fills the containers.
function overviewHtml(s) {
    if (!s.cards) {
        return `<div class="motif-detail-inner"><div class="reader-placeholder">No overview for this index.</div></div>`;
    }
    const card = (c) => `<div class="stat-card"><div class="stat-num">${formatNumber(c.value)}${c.suffix || ""}</div><div class="stat-label">${escapeHtml(c.label)}</div></div>`;
    const panel = (p) => `<div class="chart-card"><div class="chart-title">${escapeHtml(p.title)}</div><div class="chart" id="${escapeHtml(p.id)}"></div></div>`;
    return `<div class="motif-detail-inner motif-overview">
        <h1 class="overview-title">${escapeHtml(s.title || "")}</h1>
        ${introHtml(s.intro)}
        <div class="stat-cards">${(s.cards || []).map(card).join("")}</div>
        <div class="chart-grid">${(s.panels || []).map(panel).join("")}</div>
    </div>`;
}

// Scholarly header: one-paragraph description, authorship, the source-work
// citation, and the concrete data sources (links). blurb/citation are trusted
// server constants that carry intentional <em>, so they are injected as-is;
// author and source labels are plain text and escaped.
function introHtml(intro) {
    if (!intro) return "";
    const sources = (intro.sources || []).map((x) =>
        `<a class="ov-src" href="${escapeHtml(x.url)}" target="_blank" rel="noopener">${escapeHtml(x.label)} <span class="ext-arrow">↗</span></a>`).join("");
    const row = (k, v) => v ? `<div class="ov-meta-row"><span class="ov-meta-k">${k}</span><span>${v}</span></div>` : "";
    return `<div class="overview-intro">
        <p class="ov-blurb">${intro.blurb || ""}</p>
        <div class="ov-meta">
            ${row("Author", escapeHtml(intro.author || ""))}
            ${row("Source work", intro.citation ? `<span class="ov-cite">${intro.citation}</span>` : "")}
            ${row("Data sources", sources ? `<span class="ov-srcs">${sources}</span>` : "")}
        </div>
    </div>`;
}

// Shared macro-region palette (echoes the geographic-layer mockup) so a region
// reads the same colour in the overview bars and the per-type accordion.
const REGION_COLORS = {
    "Europe": "#4f7096", "Near East": "#c9873f", "Central Asia": "#8a7f4e",
    "South Asia": "#6f9a5a", "East Asia": "#b45c4b", "Southeast Asia": "#4f9d8a",
    "Asia": "#6f9a5a", "Siberia": "#5f8aa0", "Arctic": "#8fb0c4", "Africa": "#9c6a94",
    "North America": "#7d84b8", "Mesoamerica": "#c47a5a", "Mesoamerica & Caribbean": "#c47a5a",
    "South America": "#bd9a43", "Caribbean": "#59a3b0", "Oceania": "#3f9e93", "—": "#b7c0c7",
};
const _FALLBACK_COLORS = ["#4f7096", "#c9873f", "#6f9a5a", "#b45c4b", "#5f8aa0", "#9c6a94", "#bd9a43", "#3f9e93"];
function regionColor(name, i = 0) { return REGION_COLORS[name] || _FALLBACK_COLORS[i % _FALLBACK_COLORS.length]; }

// The overview is a dashboard of ranked bars, histograms, a part-to-whole and a
// two-series comparison — all rendered as pure CSS/SVG. No Plotly here (it stays
// for the similarity page's interactive scatter/heatmap): these marks render
// instantly, carry direct labels, and reuse the region palette. Value keys vary
// (count/bytes/indeg), hence the valFn.
const ACC = "#2a9d8f", HIST_C = "#6b7aa1", COMPO_C = ["#2a9d8f", "#7cc0b6", "#d4e7e3"];

function cssBars(id, rows, labelFn, colorFn, valFn = (r) => r.count) {
    const el = document.getElementById(id);
    if (!el || !rows || !rows.length) return;
    const max = Math.max(1, ...rows.map(valFn));
    el.innerHTML = `<div class="csbars">` + rows.map((r, i) => {
        const lab = labelFn(r), v = valFn(r);
        return `<div class="csbar-row" title="${escapeHtml(lab)}: ${formatNumber(v)}">
            <span class="csbar-lab">${escapeHtml(lab)}</span>
            <span class="csbar-track"><span class="csbar-fill" style="width:${Math.max(2, Math.round(100 * v / max))}%;background:${colorFn(r, i)}"></span></span>
            <span class="csbar-val">${formatNumber(v)}</span>
        </div>`;
    }).join("") + `</div>`;
}

// A single 100% stacked bar for a part-to-whole (composition), with a legend.
function cssStacked(id, rows, colors) {
    const el = document.getElementById(id);
    if (!el || !rows || !rows.length) return;
    const total = rows.reduce((a, r) => a + r.count, 0) || 1;
    const segs = rows.map((r, i) => `<span class="csstack-seg" style="width:${(100 * r.count / total).toFixed(1)}%;background:${colors[i % colors.length]}" title="${escapeHtml(r.label)}: ${formatNumber(r.count)}"></span>`).join("");
    const leg = rows.map((r, i) => `<span><i style="background:${colors[i % colors.length]}"></i>${escapeHtml(r.label)} <b>${Math.round(100 * r.count / total)}%</b></span>`).join("");
    el.innerHTML = `<div class="csstack">${segs}</div><div class="cslegend">${leg}</div>`;
}

// Two-series comparison: a muted "all" bar with the "substantive" subset overlaid
// (bullet style). Both scaled to the same max so the subset reads as a fraction.
function cssBullet(id, rows, labelFn) {
    const el = document.getElementById(id);
    if (!el || !rows || !rows.length) return;
    const max = Math.max(1, ...rows.map((r) => r.count));
    el.innerHTML = `<div class="csbars">` + rows.map((r) => `
        <div class="csbar-row" title="${escapeHtml(labelFn(r))}: ${formatNumber(r.substantive || 0)} / ${formatNumber(r.count)}">
            <span class="csbar-lab">${escapeHtml(labelFn(r))}</span>
            <span class="csbar-track">
                <span class="csbar-fill" style="width:${Math.max(2, Math.round(100 * r.count / max))}%;background:#bcdcd6"></span>
                <span class="csbar-fill csbar-over" style="width:${Math.max(0, Math.round(100 * (r.substantive || 0) / max))}%;background:${ACC}"></span>
            </span>
            <span class="csbar-val">${formatNumber(r.substantive || 0)}</span>
        </div>`).join("") + `</div>
        <div class="cslegend"><span><i style="background:${ACC}"></i>substantive</span><span><i style="background:#bcdcd6"></i>all</span></div>`;
}

// Single dispatcher for the whole overview (replaces the old Plotly path).
function drawOverviewCharts(s) {
    const bars = (id, rows, labelFn, valFn) => cssBars(id, rows, labelFn, () => ACC, valFn);
    const hist = (id, rows, labelFn) => cssBars(id, rows, labelFn, () => HIST_C);
    if (s.regions) {
        const rid = s.index === "atu" ? "atRegions" : s.index === "berezkin" ? "bzRegions" : "ovRegions";
        cssBars(rid, s.regions, (r) => r.region, (r, i) => regionColor(r.region, i));
    }
    if (s.index === "tmi") {
        cssStacked("ovComposition", s.composition, COMPO_C);
        hist("ovLevels", s.levels, (r) => `L${r.level}`);
        hist("ovNotes", s.notes_histogram, (r) => r.bucket);
        cssBullet("ovChapters", s.chapters, (r) => r.id);
        bars("ovCultures", s.top_cultures.slice(0, 15), (r) => r.label);
        hist("ovBreadth", s.breadth_histogram, (r) => r.bucket);
        bars("ovTopNotes", s.top_notes, (r) => `${r.id} ${r.name}`, (r) => r.bytes);
        bars("ovHubs", s.see_also_hubs, (r) => `${r.id} ${r.name}`, (r) => r.indeg);
        bars("ovSources", s.top_sources || [], (r) => r.label);
    } else if (s.index === "berezkin") {
        bars("bzChapters", s.chapters, (r) => r.id);
        if (s.groups) bars("bzGroups", s.groups, (r) => r.label);
        bars("bzAreas", s.top_areas, (r) => r.label);
        bars("bzWidest", s.widest, (r) => r.label);
        hist("bzBreadth", s.breadth, (r) => r.bucket);
    } else if (s.index === "atu") {
        bars("atChapters", s.chapters, (r) => r.label);
        if (s.top_peoples) bars("atPeoples", s.top_peoples, (r) => r.label);
        if (s.reg_breadth) hist("atRegBreadth", s.reg_breadth, (r) => r.bucket);
        bars("atDivisions", s.divisions, (r) => r.label);
        hist("atMotifHist", s.motif_hist, (r) => r.bucket);
        bars("atRich", s.top_rich, (r) => r.label);
        if (s.families) bars("atFamilies", s.families, (r) => r.label);
        if (s.combos) bars("atCombos", s.combos, (r) => r.label);
    }
}

function section(title, bodyHtml) {
    return `<div class="motif-section"><div class="motif-section-title">${escapeHtml(title)}</div>${bodyHtml}</div>`;
}

function linkSection(title, links) {
    return section(title, `<div class="motif-links">${linkChips(links)}</div>`);
}

// Heuristic textual parallels: look-alike motifs in the *other* indexes that carry
// no recorded cross-walk link. A clearly-labelled suggestion layer (not asserted
// links) — each chip tags the target index and its title-similarity score.
const PARALLEL_TAG = { berezkin: "BZ", tmi: "TMI", atu: "ATU" };
function parallelsSection(parallels) {
    if (!parallels || !parallels.length) return "";
    const chips = parallels.map((l) => {
        const pct = Math.round((l.title_sim || 0) * 100);
        const tip = `${l.name || l.id} — title similarity ${l.title_sim}, description ${l.doc_sim}, ${l.shared} shared words`;
        return `
        <a href="#/motifs?index=${escapeHtml(l.index)}&id=${encodeURIComponent(l.id)}"
           class="motif-link motif-parallel${l.exists ? "" : " missing"}" data-index="${escapeHtml(l.index)}" data-id="${escapeHtml(l.id)}"
           title="${escapeHtml(tip)}">
            <span class="motif-link-src">${PARALLEL_TAG[l.index] || escapeHtml(l.index)}</span><span class="motif-link-id">${escapeHtml(l.id)}</span>${l.name ? `<span class="motif-link-name">${escapeHtml(l.name)}</span>` : ""}<span class="motif-parallel-sim" title="${escapeHtml(tip)}">~${pct}%</span>
        </a>`;
    }).join("");
    const note = `<div class="motif-parallel-note">Look-alike motifs in other indexes with no recorded cross-walk link — heuristic text matches to review, not confirmed links.</div>`;
    return section(`Possible parallels (${parallels.length})`, note + `<div class="motif-links">${chips}</div>`);
}

// Curated conceptual parallels found by reasoning — the same mytheme under
// different labels across indexes. Grouped by theme, each with a confidence tag
// (hover for the rationale). Distinct from the lexical "Possible parallels".
function reasonedParallelsSection(groups) {
    if (!groups || !groups.length) return "";
    const blocks = groups.map((g) => {
        const chips = g.links.map((l) => `
        <a href="#/motifs?index=${escapeHtml(l.index)}&id=${encodeURIComponent(l.id)}"
           class="motif-link motif-parallel${l.exists ? "" : " missing"}" data-index="${escapeHtml(l.index)}" data-id="${escapeHtml(l.id)}"
           title="${escapeHtml(l.name || l.id)}">
            <span class="motif-link-src">${PARALLEL_TAG[l.index] || escapeHtml(l.index)}</span><span class="motif-link-id">${escapeHtml(l.id)}</span>${l.name ? `<span class="motif-link-name">${escapeHtml(l.name)}</span>` : ""}
        </a>`).join("");
        return `<div class="motif-parallel-group">
            <div class="motif-parallel-theme">${escapeHtml(g.title)}<span class="motif-parallel-conf conf-${escapeHtml(g.confidence)}" title="${escapeHtml(g.note)}">${escapeHtml(g.confidence)}</span></div>
            <div class="motif-links">${chips}</div>
        </div>`;
    }).join("");
    const note = `<div class="motif-parallel-note">The same mytheme catalogued under different labels across indexes — a curated comparison by reasoning (rationale on each confidence tag; full write-up in the docs).</div>`;
    return section(`Parallels by reasoning (${groups.length})`, note + blocks);
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
    return section(`Attestations by culture (${formatNumber(dist.total)})`, `<div class="motif-dist">${rows}</div>`);
}

// ATU attestations (Uther provenance) grouped by macro-region: an accordion of
// regions, each listing its "People: citation" entries. Falls back to the raw
// prose when the parsed grouping is absent.
// Shared "Attestations by culture" renderer for TMI cultures and ATU peoples:
// region groups (colour dot · name · count), each entry "Label: citation". The
// collapse adapts to volume — all regions open when there are few entries, an
// exclusive accordion (one region at a time) when there are many — so TMI's
// typical single culture isn't hidden behind a click and ATU's 100-people types
// don't become a wall. Citation HTML is pre-rendered by the caller (TMI links to
// its bibliography; ATU linkifies work abbreviations).
function attestationsSection(grouped) {
    if (!grouped || !grouped.total) return "";
    const openAll = grouped.total <= 15;
    const rows = (grouped.regions || []).map((r) => {
        const label = r.region;  // "—" for the unmapped bucket, matching Berezkin & the data
        const items = (r.entries || []).map((e) =>
            `<li class="motif-att-item"><span class="motif-att-people">${escapeHtml(e.label)}</span>${e.cite ? `: <span class="motif-att-cite">${e.cite}</span>` : ""}</li>`).join("");
        return `
        <details class="motif-dist-region"${openAll ? " open" : ` name="motif-att-region"`}>
            <summary><span class="region-dot" style="background:${regionColor(r.region)}"></span><span class="motif-dist-name">${escapeHtml(label)}</span><span class="motif-dist-count">${formatNumber(r.count)}</span></summary>
            <ul class="motif-att-list">${items}</ul>
        </details>`;
    }).join("");
    return section(`Attestations by culture (${formatNumber(grouped.total)})`, `<div class="motif-dist">${rows}</div>`);
}

// ATU peoples: already region-grouped server-side; linkify the citation prose.
function atuAttestations(grouped, raw) {
    if (!grouped || !grouped.total) return atuProse("Attestations by culture", raw, true);
    return attestationsSection({
        total: grouped.total,
        regions: (grouped.regions || []).map((r) => ({
            region: r.region, count: r.count,
            entries: (r.entries || []).map((e) => ({
                label: e.people, cite: e.cite ? abbrLinkify(escapeHtml(e.cite)) : "",
            })),
        })),
    });
}

// TMI cultures: each carries a region and bibliography-linked citations; group
// them into the shared shape (regions by size, the unmapped "—" bucket last).
function tmiAttestations(cultures) {
    if (!cultures || !cultures.length) return "";
    const byRegion = new Map();
    for (const c of cultures) {
        const key = c.region || "—";
        if (!byRegion.has(key)) byRegion.set(key, []);
        byRegion.get(key).push({ label: c.label, cite: (c.citations || []).map(citeHtml).join(", ") });
    }
    const regions = [...byRegion.entries()]
        .map(([region, entries]) => ({ region, count: entries.length, entries }))
        .sort((a, b) => (a.region === "—") - (b.region === "—") || b.count - a.count);
    return attestationsSection({ total: cultures.length, regions });
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
// "—", matching the attestations section's no-region bucket).
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
    return section(`References (${formatNumber(bookKeys.size)})`, `<div class="motif-bib">${rows}</div>`);
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
function renderDetail(d) {
    const links = d.links || {};
    const head = `
        <div class="motif-head">
            <span class="motif-code">${escapeHtml(d.id)}</span>
            <h2 class="motif-name">${escapeHtml(d.name || "—")}</h2>
        </div>`;

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
        if ((links.tmi || []).length) body += linkSection(`Related Thompson motifs (${links.tmi.length})`, links.tmi);
        if ((links.atu || []).length) body += linkSection(`Related ATU tale types (${links.atu.length})`, links.atu);
        if ((links.see_also || []).length) body += linkSection(`Related motifs (${links.see_also.length})`, links.see_also);
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
        if ((links.related || []).length) body += linkSection(`Related motifs (${links.related.length})`, links.related);
        if ((links.atu_related || []).length) body += linkSection(`Related ATU tale types (${links.atu_related.length})`, links.atu_related);
        if ((links.atu_defines || []).length) body += linkSection(`Defines ATU tale type${links.atu_defines.length > 1 ? "s" : ""} (${links.atu_defines.length})`, links.atu_defines);
        if ((links.atu_summary_refs || []).length) body += linkSection(`Named in ATU summaries (${links.atu_summary_refs.length})`, links.atu_summary_refs);
        if ((links.berezkin || []).length) body += linkSection("Referenced by Berezkin motifs", links.berezkin);
        if ((d.cultures || []).length) body += tmiAttestations(d.cultures);
        if ((d.references || []).length) body += section(`References (${d.references.length})`, citeList(d.references));
        if (d.notes) body += section("Source text (notes)", `<p class="motif-text motif-notes-raw">${escapeHtml(d.notes)}</p>`);
    } else if (d.index === "atu") {
        // The pre-2004 Uther name rides under the title as a muted subtitle.
        const sub = d.former_name
            ? `<div class="motif-subtitle">previously ${escapeHtml(d.former_name)}</div>` : "";
        body = `
            <div class="motif-head">
                <span class="motif-code">${escapeHtml(d.id)}</span>
                <div class="motif-name-col">
                    <h2 class="motif-name">${escapeHtml(d.name || "—")}</h2>
                    ${sub}
                </div>
            </div>`;
        // Classification folds chapter, division and sub_division (each with its
        // number range) into one line, as in the Berezkin index.
        const cls = [];
        const withRange = (name, range) => escapeHtml(name)
            + (range ? ` <span class="motif-range">(${range[0]}–${range[1]})</span>` : "");
        if (d.chapter) cls.push(escapeHtml(d.chapter_label || d.chapter));
        if (d.division) cls.push(withRange(d.division, d.division_range));
        if (d.sub_division) cls.push(withRange(d.sub_division, d.sub_division_range));
        if (cls.length) body += section("Classification", `<div class="motif-taxonomy">${cls.join(" · ")}</div>`);
        // Old ATU numbers this type was renumbered from / absorbed (Uther). Shown as
        // plain badges — they are pre-2004 numbers, not live types to link to.
        if ((d.former_ids || []).length) {
            const badges = d.former_ids.map((x) => `<span class="motif-oldid">${escapeHtml(x)}</span>`).join("");
            body += section("Earlier ATU numbers", `<div class="motif-oldids">${badges}</div>`);
        }
        // The TMI motif(s) Uther names as defining the type — distinct from the
        // constituent motifs (atu_seq) further down.
        if ((links.defining || []).length) {
            body += linkSection(links.defining.length > 1 ? "Defining motifs" : "Defining motif", links.defining);
        }
        // summary_html is pre-escaped on the server with motif/type links injected.
        if (d.summary_html) body += section("Summary", `<p class="motif-text">${d.summary_html}</p>`);
        else if (d.summary) body += section("Summary", `<p class="motif-text">${escapeHtml(d.summary)}</p>`);
        body += atuProse("Notes", d.remarks, false);
        if ((links.parent || []).length) body += linkSection("Base type", links.parent);
        if ((links.subtypes || []).length) body += linkSection(`Subtypes (${links.subtypes.length})`, links.subtypes);
        if ((links.combos || []).length) body += linkSection(`Combined with (${links.combos.length})`, links.combos);
        if ((links.tmi || []).length) body += linkSection(`Constituent TMI motifs (${links.tmi.length})`, links.tmi);
        if ((links.tmi_via_notes || []).length) body += linkSection(`Referenced by TMI motifs (via notes) (${links.tmi_via_notes.length})`, links.tmi_via_notes);
        if ((links.berezkin || []).length) body += linkSection("Referenced by Berezkin motifs", links.berezkin);
        body += atuAttestations(d.attestations_grouped, d.attestations);
        body += atuProse("References", d.references, true);
        // Also-known-as / Wikipedia / Ashliman as up-to-three equal columns at
        // the foot; absent ones drop out and the rest fill the row. The first
        // column stacks names then catalogue concordances ("Also catalogued as").
        const namesCol = atuNames(d.names) + atuConcordances(d.concordances);
        const endCols = [namesCol, atuWikipedia(d.wikipedia), atuTales(d.tales)].filter(Boolean);
        if (endCols.length) {
            body += `<div class="motif-cols">${endCols.map((c) => `<div class="motif-col">${c}</div>`).join("")}</div>`;
        }
    }

    // Cross-index parallels at the foot: first the curated conceptual groups
    // (reasoning), then the heuristic lexical look-alikes.
    body += reasonedParallelsSection(d.reasoned_parallels);
    body += parallelsSection(d.parallels);

    // An old ATU number the user navigated to is served as the current type.
    const redirect = d.redirected_from
        ? `<div class="motif-redirect">Redirected from old type <strong>${escapeHtml(d.redirected_from)}</strong></div>`
        : "";
    return `<div class="motif-detail-inner">${redirect}${body}</div>`;
}
