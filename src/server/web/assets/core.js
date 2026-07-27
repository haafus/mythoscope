// ===== App root & shared state =====

import { traditionShade } from "./region-color.js";

export const app = document.getElementById("app");

// The single fallback colour for any category/tradition that has no colour of
// its own (missing tradition colour, unknown graph Category, …). Keep in sync
// with the --category-none token in app.css.
export const CATEGORY_NONE = "#6b7280";

// The single "no category" value-layer sentinel (§2.14) — the CATEGORY_NONE of the value
// layer. A genuinely-absent tradition/region reads as this everywhere, not a friendly label.
export const UNASSIGNED = "UNASSIGNED";

export const state = {
    models: [],
    selectedModel: localStorage.getItem("selectedModel") || "",
    corpusDocuments: [],
    docIndex: null,            // document_id -> document (built with the documents)
    selectedCorpusDoc: null,
    selectedNode: null,           // the ONE active tree item: {kind:'region'|'tradition'|'book', …}
    corpusOpenMajor: null,        // accordion: the one open region (expansion, separate from active)
    corpusOpenTradition: null,    // accordion: the one open tradition key
    traditionTree: null,       // region -> { color, description, subdivision, strata, traditions }
    treeIndex: null,           // tradition -> { region, regionColor, coordinates, index, count, … }
    analysisSearchRequestId: 0,
    similarityMethods: [],
    textSearch: false, // from /api/similarity/models; fail closed so a failed fetch never shows the disabled form
};

// ===== Route teardown =====

let routeCleanups = [];

export function onCleanup(fn) {
    routeCleanups.push(fn);
}

export function cleanupRoute() {
    const pending = routeCleanups;
    routeCleanups = [];
    pending.forEach((fn) => {
        try { fn(); } catch (error) { console.error(error); }
    });
}

// ===== HTTP =====

export async function api(path, options = {}) {
    const headers = {...(options.headers || {})};
    if (options.body) headers["Content-Type"] = headers["Content-Type"] || "application/json";
    const response = await fetch(path, {...options, headers});

    if (!response.ok) {
        const text = await response.text();
        let detail = text || response.statusText;
        try {
            const payload = JSON.parse(text);
            detail = payload.detail || payload.error || payload.message || detail;
        } catch {
            // Plain text response.
        }
        throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }

    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("application/json")) return response.json();
    return response.text();
}

// ===== Utilities =====

export function escapeHtml(value) {
    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#39;");
}

export function normalizePreviewText(value) {
    return String(value ?? "").replace(/\s+/g, " ").trim();
}

// A source paragraph is "hard-wrapped" (line breaks inserted at a fixed margin,
// not meaningful) when its lines fill to a common width, producing a run of
// consecutive near-full lines. Verse and lists break by meaning, so even their
// long lines don't come in runs. Requiring uniformity of *every* line (the old
// test) failed on prose blocks with ragged short ends — e.g. several footnotes
// glued together, each ending mid-line. The last line ends the paragraph and is
// naturally short, so it is ignored.
function isHardWrapped(lines) {
    if (lines.length < 2) return false;
    const body = lines.slice(0, -1).map((l) => l.length);
    const width = Math.max(...body);
    if (width < 40 || width > 100) return false;         // too short (verse/list) or not a margin
    const full = body.map((l) => l >= width - 15);       // reached near the wrap margin
    const filled = full.filter(Boolean).length / full.length;
    let run = 0, longestRun = 0;
    for (const isFull of full) { run = isFull ? run + 1 : 0; longestRun = Math.max(longestRun, run); }
    if (body.length <= 2) return filled === 1;           // 1–2 wrapped lines: all must be full
    return longestRun >= 3 && filled >= 0.5;             // prose wraps in runs; verse doesn't
}

// Render source text into paragraphs for a normal (reflowing) column: split on
// blank lines into <p>, and within each paragraph reflow hard-wrapped lines into
// running text (so a narrow column doesn't keep the source's line breaks), while
// preserving intentional line breaks (verse/lists) as <br>. Returns escaped HTML.
export function reflowHtml(value) {
    const paras = String(value ?? "").replace(/\r\n?/g, "\n").split(/\n[ \t]*\n+/);
    return paras.map((para) => {
        const lines = para.split("\n").filter((l) => l.trim());
        if (!lines.length) return "";
        const body = isHardWrapped(lines)
            ? escapeHtml(lines.join(" ").replace(/[ \t]+/g, " ").trim())
            : lines.map((l) => escapeHtml(l.trim())).join("<br>");
        return `<p class="reflow-p">${body}</p>`;
    }).filter(Boolean).join("");
}

export function escapeRegex(value) {
    return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function formatNumber(value) {
    const number = Number(value || 0);
    return Number.isFinite(number) ? number.toLocaleString("en-US") : "0";
}

// ===== Models =====

function modelLabel(model) {
    return (model.name || model.key || "").replace(/_/g, "/");
}

export function persistSelectedModel(key) {
    state.selectedModel = key || "";
    localStorage.setItem("selectedModel", state.selectedModel);
}

export async function ensureModels() {
    if (!state.models.length) {
        const data = await api("/api/similarity/models");
        state.models = Array.isArray(data.models) ? data.models : [];
        state.textSearch = data.text_search !== false;
    }

    const keys = state.models.map((model) => model.key);
    if (!state.selectedModel || !keys.includes(state.selectedModel)) {
        state.selectedModel = keys[0] || "";
    }

    return state.models;
}

export function renderModelOptions(selectedKey = state.selectedModel) {
    if (!state.models.length) return '<option value="">No available models</option>';
    return state.models.map((model) => `
        <option value="${escapeHtml(model.key)}" ${model.key === selectedKey ? "selected" : ""}>
            ${escapeHtml(modelLabel(model))}
        </option>
    `).join("");
}

// ===== Region tree + resolution =====
// The front loads the region → tradition tree and the documents ONCE, then resolves
// everything from the stable references (document_id, tradition) — nothing region/colour
// is carried on a document or a chunk (§2.8, B1).

export async function ensureTraditionTree() {
    if (!state.traditionTree) {
        try {
            const data = await api("/api/corpus/traditions");
            state.traditionTree = data.traditions || {};
        } catch {
            state.traditionTree = {};
        }
        buildTreeIndex();
    }
    return state.traditionTree;
}

function buildTreeIndex() {
    // tradition -> { region, regionColor, coordinates, description, dating, index, count }.
    // `index` is the within-region order by longitude (west→east) so the derived lightness
    // shade weakly encodes geography (§8.1); `count` sizes the ramp.
    const index = new Map();
    for (const [region, node] of Object.entries(state.traditionTree || {})) {
        const ordered = Object.entries(node.traditions || {}).sort((a, b) => {
            const la = (a[1].coordinates || [])[1], lb = (b[1].coordinates || [])[1];
            if (la != null && lb != null && la !== lb) return la - lb;
            return a[0].localeCompare(b[0]);
        });
        ordered.forEach(([name, info], i) => index.set(name, {
            region,
            regionColor: node.color || CATEGORY_NONE,
            coordinates: info.coordinates || null,
            description: info.description || "",
            dating: info.dating || "",
            index: i,
            count: ordered.length,
        }));
    }
    state.treeIndex = index;
}

export function regionOf(tradition) {
    return ((state.treeIndex && state.treeIndex.get(tradition)) || {}).region || "";
}

export function regionColor(tradition) {
    const e = state.treeIndex && state.treeIndex.get(tradition);
    return e ? e.regionColor : CATEGORY_NONE;
}

function isDarkTheme() {
    const attr = document.documentElement.getAttribute("data-theme");
    if (attr) return attr === "dark";
    return !!(window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches);
}

// The per-tradition within-region OKLCH shade (regions.md §8.1), derived from the region
// base + the tradition's order/count — never stored.
export function traditionColor(tradition) {
    const e = state.treeIndex && state.treeIndex.get(tradition);
    if (!e) return CATEGORY_NONE;
    return traditionShade(e.regionColor, e.index, e.count, isDarkTheme());
}

export function traditionInfo(tradition) {
    return (state.treeIndex && state.treeIndex.get(tradition)) || null;
}

// ===== Corpus documents =====

export async function ensureCorpusDocuments() {
    if (!state.corpusDocuments.length) {
        const data = await api("/api/corpus/documents");
        state.corpusDocuments = Array.isArray(data.documents) ? data.documents : [];
        state.docIndex = new Map(state.corpusDocuments.map((d) => [d.document_id, d]));
    }
    return state.corpusDocuments;
}

// Load both the tree and the documents (the front's one global load).
export async function ensureCorpusData() {
    await ensureTraditionTree();
    await ensureCorpusDocuments();
    return state.corpusDocuments;
}

export function documentById(id) {
    return (state.docIndex && state.docIndex.get(id)) || null;
}

export function buildCorpusApiUrl(doc) {
    return `/api/corpus/document?id=${encodeURIComponent((doc && doc.document_id) || "")}`;
}

export function corpusTraditionKey(region, tradition) {
    return `${region || UNASSIGNED}|${tradition || UNASSIGNED}`;
}

// Group documents by region → tradition, in the served tree's canon order (§2.8: the
// structure and order come from the tree, not a client-side reconstruction).
export function groupDocuments(items) {
    const byTradition = new Map();
    items.forEach((doc) => {
        const t = doc.tradition || UNASSIGNED;
        if (!byTradition.has(t)) byTradition.set(t, []);
        byTradition.get(t).push(doc);
    });

    const grouped = new Map();
    for (const [region, node] of Object.entries(state.traditionTree || {})) {
        for (const tradition of Object.keys(node.traditions || {})) {
            const docs = byTradition.get(tradition);
            if (!docs || !docs.length) continue;
            if (!grouped.has(region)) grouped.set(region, new Map());
            grouped.get(region).set(tradition, docs);
        }
    }
    // A document whose tradition is not in the tree shouldn't occur post-validation; bucket
    // it under "Other" rather than dropping it silently.
    for (const [tradition, docs] of byTradition) {
        if (regionOf(tradition)) continue;
        if (!grouped.has(UNASSIGNED)) grouped.set(UNASSIGNED, new Map());
        grouped.get(UNASSIGNED).set(tradition, docs);
    }
    return grouped;
}
