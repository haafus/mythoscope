// ===== App root & shared state =====

export const app = document.getElementById("app");

export const state = {
    models: [],
    selectedModel: localStorage.getItem("selectedModel") || "",
    corpusDocuments: [],
    selectedCorpusDoc: null,
    corpusOpenTraditions: new Set(),
    corpusOpenTraditionsInitialized: false,
    corpusCollapsedMajors: new Set(),
    traditionInfo: null,
    analysisSearchRequestId: 0,
    similarityMethods: [],
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

// A source paragraph is "hard-wrapped" (line breaks inserted at a fixed width,
// not meaningful) if its lines cluster around one width — as opposed to verse or
// a list, whose lines are short and uneven. The last line is ignored (it ends the
// paragraph and is naturally short).
function isHardWrapped(lines) {
    if (lines.length < 2) return false;
    const lens = lines.slice(0, -1).map((l) => l.length).sort((a, b) => a - b);
    const med = lens[Math.floor(lens.length / 2)];
    if (med < 40 || med > 90) return false;              // not a wrap width
    return lens.every((l) => l > med - 18 && l < med + 10);  // uniform enough
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

// ===== Corpus =====

export async function ensureCorpusDocuments() {
    if (!state.corpusDocuments.length) {
        const data = await api("/api/corpus/catalog");
        state.corpusDocuments = Array.isArray(data.documents) ? data.documents : [];
    }
    return state.corpusDocuments;
}

export function buildCorpusApiUrl(doc) {
    const params = new URLSearchParams({
        title: doc.title || "",
        major_tradition: doc.major_tradition || "",
        tradition: doc.tradition || "",
        source: doc.source || "corpus",
    });
    return `/api/corpus/documents?${params.toString()}`;
}

export function corpusTraditionKey(major, tradition) {
    return `${major || "Other"}|${tradition || "Unknown"}`;
}

export function groupDocuments(items) {
    const grouped = new Map();

    items.forEach((doc) => {
        const major = doc.major_tradition || "Other";
        const tradition = doc.tradition || "Unknown";

        if (!grouped.has(major)) grouped.set(major, new Map());
        const majorGroup = grouped.get(major);
        if (!majorGroup.has(tradition)) majorGroup.set(tradition, []);
        majorGroup.get(tradition).push(doc);
    });

    return grouped;
}

// A point/chunk id is the book title with spaces turned into underscores
// (normalize_catalog_id), so the title is recovered by reversing that.
export function bookTitleFromId(value) {
    return String(value || "").replace(/\.txt$/i, "").replace(/_/g, " ").trim();
}

// ===== Traditions =====

export async function loadTraditionInfo() {
    if (state.traditionInfo) return state.traditionInfo;
    try {
        const data = await api("/api/corpus/traditions");
        state.traditionInfo = data.traditions || {};
    } catch {
        state.traditionInfo = {};
    }
    return state.traditionInfo;
}
