import { api, documentById, escapeHtml, escapeRegex, normalizePreviewText, state } from "./core.js";

// A hit carries only the document reference (B1); title + tradition are resolved from the
// globally-cached document, not carried on the hit.
function hitDocument(item) {
    return documentById(item && item.document_id) || null;
}

export function scoreClass(similarityScore) {
    const percent = Math.round(Number(similarityScore || 0) * 100);
    let cls = "score-low";
    if (percent >= 60) cls = "score-high";
    else if (percent >= 40) cls = "score-medium";
    return {percent, cls};
}

export function resultBookTitle(item) {
    const doc = hitDocument(item);
    return (doc && doc.title) || "Unknown book";
}

export function resultTradition(item) {
    const doc = hitDocument(item);
    return (doc && doc.tradition) || "Unknown";
}

export function chunkMetaLine(item) {
    return `Book: ${resultBookTitle(item)} | Chunk #${item.chunk_index ?? 0}`;
}

// "— Tradition" / "Title" / "chunk N[, score 0.76]" shown under a fragment.
export function attributionLine(item, { withScore = false } = {}) {
    const tradition = resultTradition(item);
    const title = resultBookTitle(item);
    let meta = `chunk ${item.chunk_index ?? 0}`;
    if (withScore && item.similarity_score != null) {
        meta += `, score ${Number(item.similarity_score).toFixed(2)}`;
    }
    return `
        <div class="fragment-attribution">
            <span class="fragment-tradition">— ${escapeHtml(tradition)}</span>
            <span class="fragment-title">${escapeHtml(title)}</span>
            <span class="fragment-chunk">${escapeHtml(meta)}</span>
        </div>
    `;
}

export function pointTooltipHtml(item) {
    const text = normalizePreviewText(item.text) || "No preview available.";
    return `
        <div class="plot-hover-text">${escapeHtml(text)}</div>
        ${attributionLine(item)}
    `;
}

export function searchResultMetaLine(item) {
    return `Tradition: ${resultTradition(item)} | ${chunkMetaLine(item)}`;
}

export function highlightText(text, query) {
    if (!query || !text) return escapeHtml(text);

    const words = query.toLowerCase().split(/\s+/).filter((word) => word.length > 2);
    let escapedText = escapeHtml(text);

    words.forEach((word) => {
        try {
            const regex = new RegExp(`(${escapeRegex(word)})`, "gi");
            escapedText = escapedText.replace(regex, "<mark>$1</mark>");
        } catch {
            // Ignore invalid regex pieces.
        }
    });

    return escapedText;
}

export function chunkTextHtml(item, query = "") {
    const text = item.text || "";
    if (!text) {
        return '<span class="chunk-text-empty">Chunk text is unavailable.</span>';
    }
    return highlightText(text, query);
}

export function renderSearchResultItem(result, data) {
    const {percent, cls} = scoreClass(result.similarity_score);
    return `
        <div class="search-result-item">
            <span class="search-result-topline">
                <span class="result-tradition">${escapeHtml(resultTradition(result))}</span>
                <span class="result-score ${cls}">${percent}% similarity</span>
            </span>
            <span class="search-result-meta">${escapeHtml(searchResultMetaLine(result))}</span>
            <span class="result-text chunk-text"${sourceAttr(result)}>${chunkTextHtml(result, data.query)}</span>
        </div>
    `;
}

// --- Source reveal: preprocessing variants embed a transformed chunk and carry
// the original in `source_text`. Stamp `sourceAttr` on the text element, then
// `wireSourceIcons` appends a hover icon that shows the original in a tooltip. ---

const SOURCE_ICON_SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round"><path d="M4 5a2 2 0 0 1 2-2h9v13H6a2 2 0 0 0-2 2V5Z"/><path d="M15 3h3a2 2 0 0 1 2 2v12a3 3 0 0 1-3 3H7"/><path d="M8 7h4M8 10h4"/></svg>';

// Empty for raw variants (no source_text) → no icon, no extra flag needed.
export function sourceAttr(item) {
    return item && item.source_text ? ` data-source-text="${escapeHtml(item.source_text)}"` : "";
}

let sourceTip = null;
function sourceTipEl() {
    if (!sourceTip) {
        sourceTip = document.createElement("div");
        sourceTip.className = "source-tip";
        document.body.appendChild(sourceTip);
    }
    return sourceTip;
}

export function hideSourceTip() {
    if (sourceTip) sourceTip.style.display = "none";
}

// Remove the shared tooltip node (call on page teardown).
export function destroySourceTip() {
    if (sourceTip) { sourceTip.remove(); sourceTip = null; }
}

function showSourceTip(anchor, text) {
    const tip = sourceTipEl();
    tip.textContent = text;
    tip.style.display = "block";
    const r = anchor.getBoundingClientRect();
    const tr = tip.getBoundingClientRect();
    // Prefer opening to the left (the rail is on the right); flip if there's no room.
    let left = r.left - tr.width - 10;
    if (left < 8) left = Math.min(r.right + 10, window.innerWidth - tr.width - 8);
    const top = Math.min(r.top - 6, window.innerHeight - tr.height - 8);
    tip.style.left = `${Math.max(8, left)}px`;
    tip.style.top = `${Math.max(8, top)}px`;
}

// Append a source icon to each [data-source-text] element in `root` and wire hover/focus.
export function wireSourceIcons(root) {
    root.querySelectorAll("[data-source-text]").forEach((el) => {
        // reflowHtml wraps text in <p class="reflow-p">; land the icon at the end
        // of the last paragraph so it trails the text inline.
        const target = el.querySelector(".reflow-p:last-child") || el;
        const icon = document.createElement("button");
        icon.type = "button";
        icon.className = "src-icon";
        icon.setAttribute("aria-label", "Show source text");
        icon.title = "Source fragment";
        icon.innerHTML = SOURCE_ICON_SVG;
        const src = el.dataset.sourceText;
        icon.addEventListener("mouseenter", () => showSourceTip(icon, src));
        icon.addEventListener("mouseleave", hideSourceTip);
        icon.addEventListener("focus", () => showSourceTip(icon, src));
        icon.addEventListener("blur", hideSourceTip);
        target.appendChild(icon);
    });
}

// Returns { point, neighbors }: the API gives the queried point first, then its
// nearest chunks.
export async function fetchPointWithNeighbors(pointId, chunkIndex, topK = 6, crossTradition = false) {
    const params = new URLSearchParams({top_k: String(topK)});
    if (chunkIndex !== null && chunkIndex !== undefined && chunkIndex !== "") {
        params.set("chunk_index", String(chunkIndex));
    }
    if (crossTradition) params.set("cross_tradition", "true");
    const [point, ...neighbors] = await api(`/api/similarity/points/${encodeURIComponent(state.selectedModel)}/${encodeURIComponent(pointId)}?${params}`);
    if (!point) throw new Error("Point not found");
    return { point, neighbors };
}

export async function runSemanticSearch({query, model, topK = 20}) {
    const results = await api("/api/similarity/search", {
        method: "POST",
        body: JSON.stringify({query, model, top_k: topK}),
    });
    return {results, query, model};
}
