export const app = document.getElementById("app");

// Shared app data only. Per-page resources (maps, charts, listeners) live in
// each page's closure and are released via onCleanup, not stashed here.
export const state = {
    models: [],
    selectedModel: localStorage.getItem("selectedModel") || "",
    corpusDocuments: [],
    selectedCorpusDoc: null,
    corpusOpenTraditions: new Set(),
    corpusOpenTraditionsInitialized: false,
    corpusCollapsedMajors: new Set(),
    traditionInfo: null,
    lastAnalysisSearchData: null,
    analysisSearchRequestId: 0,
    similarityMethods: [],
};

export function parseHash() {
    const raw = (window.location.hash || "#/").slice(1) || "/";
    const splitAt = raw.indexOf("?");
    const path = splitAt === -1 ? raw : raw.slice(0, splitAt);
    const query = splitAt === -1 ? "" : raw.slice(splitAt + 1);
    return {
        path: path || "/",
        params: new URLSearchParams(query),
    };
}

// Single source of truth for routes: canonical path -> body class, plus the
// aliases that redirect to a canonical path. Anything unknown falls back to
// DEFAULT_ROUTE.
export const DEFAULT_ROUTE = "/corpus";

const ROUTE_CLASS = {
    "/home": "route-home",
    "/corpus": "route-corpus",
    "/geography": "route-geography",
    "/embeddings": "route-embeddings",
    "/beings": "route-graphs",
    "/realms": "route-graphs",
    "/ages": "route-graphs",
};

function routeClass(path) {
    return ROUTE_CLASS[path] || ROUTE_CLASS[DEFAULT_ROUTE];
}

export function setBodyClass(path) {
    document.body.className = `has-main-navbar ${routeClass(path)}`;
}

export function setActiveNav(path) {
    document.querySelectorAll(".nav-links a").forEach((link) => {
        const href = link.getAttribute("href") || "";
        const hashPath = (href.split("#")[1] || "/").split("?")[0] || "/";
        link.classList.toggle("active", hashPath === path);
    });
}

// Per-page teardown registry. A page registers its cleanups while it renders;
// the router runs them all (and clears the list) when navigating away.
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

// A point/chunk id is the book title with spaces turned into underscores
// (normalize_catalog_id), so the title is recovered by reversing that.
export function bookTitleFromId(value) {
    return String(value || "").replace(/\.txt$/i, "").replace(/_/g, " ").trim();
}

export function escapeRegex(value) {
    return String(value).replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

export function formatNumber(value) {
    const number = Number(value || 0);
    return Number.isFinite(number) ? number.toLocaleString("en-US") : "0";
}

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
    return `${major || "Other"}\u0000${tradition || "Unknown"}`;
}

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
