import {
    api, app, state,
    ensureModels, onCleanup,
    escapeHtml, reflowHtml,
    loadTraditionInfo,
    persistSelectedModel, renderModelOptions,
    CATEGORY_NONE,
} from "./core.js";
import { destroyChart, highlightTradition, renderScatter, renderHeatmap, renderDistribution, resizeChart } from "./chart.js";
import {
    attributionLine,
    fetchPointWithNeighbors, renderSearchResultItem,
    runSemanticSearch,
} from "./search-utils.js";
import { renderTraditionList } from "./tree-traditions.js?v=2";

function getTraditionColor(name) {
    const info = state.traditionInfo || {};
    return (info[name] && info[name].color) || CATEGORY_NONE;
}

function getColorMap(traditions) {
    const map = {};
    traditions.forEach((tradition) => {
        map[tradition] = getTraditionColor(tradition);
    });
    return map;
}

const CHART_RENDERERS = {
    scatter: async (el, data) => {
        const traditions = [...new Set((data.points || []).map((p) => p.tradition || "Unknown"))];
        await renderScatter(el, data, { colorMap: getColorMap(traditions), onPointClick: displayPointInfo });
    },
    heatmap: (el, data) => renderHeatmap(el, data),
    distribution: async (el, data) => {
        const names = (data.traditions || []).map((t) => t.name);
        await renderDistribution(el, data, { colorMap: getColorMap(names) });
    },
};

export async function renderEmbeddings() {
    // Load models first so state.textSearch is known before we build the rail.
    try { await ensureModels(); } catch { /* retried in loadModelsIntoSelect */ }
    const textSearch = state.textSearch;
    const searchPanelHtml = textSearch
        ? `<div class="search-panel" id="searchPanel">
                                <textarea id="search-text" placeholder="Type a text for similarity search…"></textarea>
                                <button class="btn btn-primary search-btn" id="search-btn" type="button" disabled>Search ›</button>
                            </div>`
        : `<div class="search-panel search-panel-hint" id="searchPanel">
                                Click a point in the plot to explore its nearest neighbours.
                            </div>`;

    app.innerHTML = `
        <main class="analysis-page container">
            <div class="workspace">
                <div class="library-sidebar">
                    <div id="tree-container">Loading...</div>
                    <div class="sidebar-controls">
                        <div class="form-group">
                            <label>Model:</label>
                            <select id="global-model-select"><option value="">Loading models...</option></select>
                        </div>
                        <div class="form-group">
                            <label>Method:</label>
                            <select id="viz-select"><option value="">Loading...</option></select>
                        </div>
                    </div>
                </div>

                <div class="plot-area">
                    <div class="card plot-container" id="plotContainer">
                        <div class="plot-canvas" id="plotCanvas">
                            <div class="loading-placeholder" id="loadingPlaceholder">Loading visualization...</div>
                            <div id="scatter-plot" style="width: 100%; height: 100%; display: none;"></div>
                        </div>
                    </div>
                </div>

                <div class="sidebar rail">
                    <div class="card">
                        <div class="card-body rail-body">
                            ${searchPanelHtml}
                            <div class="info-content" id="infoContent" style="display:none;"></div>
                        </div>
                    </div>
                </div>
            </div>

            <div id="searchModal">
                <div class="modal-content-reader search-modal-content">
                    <div class="card-header">
                        <strong id="searchModalTitle">Search Results</strong>
                        <button class="btn" id="close-search-modal" type="button">Close</button>
                    </div>
                    <div class="search-results" id="searchResults"></div>
                </div>
            </div>
        </main>
    `;

    bindEmbeddingsControls();

    const onResize = () => resizeChart(document.getElementById("scatter-plot"));
    window.addEventListener("resize", onResize);
    onCleanup(() => {
        window.removeEventListener("resize", onResize);
        destroyChart(document.getElementById("scatter-plot"));
    });

    try {
        await loadSimilarityMethods();
        await loadModelsIntoSelect();
        await initializeAnalysisLibrary();
    } catch (error) {
        console.error(error);
    }
}

function bindEmbeddingsControls() {
    const modelSelect = document.getElementById("global-model-select");
    const vizSelect = document.getElementById("viz-select");
    const searchText = document.getElementById("search-text");
    const searchBtn = document.getElementById("search-btn");

    modelSelect.addEventListener("change", triggerModelChange);
    vizSelect.addEventListener("change", loadVisualization);
    if (searchText && searchBtn) { // absent when text search is off
        searchText.addEventListener("input", () => {
            searchBtn.disabled = searchText.value.trim().length === 0 || !state.selectedModel;
        });
        searchBtn.addEventListener("click", performAnalysisSearch);
    }

    document.getElementById("close-search-modal").addEventListener("click", closeSearchModal);
}

async function loadSimilarityMethods() {
    if (!state.similarityMethods.length) {
        state.similarityMethods = await api("/api/similarity/methods");
    }
    const vizSelect = document.getElementById("viz-select");
    if (vizSelect) {
        vizSelect.innerHTML = state.similarityMethods
            .map((m) => `<option value="${escapeHtml(m.key)}">${escapeHtml(m.label)}</option>`)
            .join("");
    }
}

async function loadModelsIntoSelect() {
    await ensureModels();

    const modelSelect = document.getElementById("global-model-select");
    if (!modelSelect) return;

    modelSelect.innerHTML = renderModelOptions();
    if (!state.models.length) {
        return;
    }

    modelSelect.value = state.selectedModel;
    triggerModelChange();
}

export function triggerModelChange() {
    const modelSelect = document.getElementById("global-model-select");
    const searchText = document.getElementById("search-text");
    const searchBtn = document.getElementById("search-btn");
    if (!modelSelect || !modelSelect.value) return;

    persistSelectedModel(modelSelect.value);
    state.analysisSearchRequestId += 1;
    if (searchBtn && searchText) {
        searchBtn.disabled = searchText.value.trim().length === 0 || !state.selectedModel;
    }
    warmupModel(state.selectedModel);
    loadVisualization();
}

// Fire-and-forget preload so the first text search isn't a cold start.
function warmupModel(model) {
    if (!model || !state.textSearch) return;
    api("/api/similarity/warmup", {
        method: "POST",
        body: JSON.stringify({ model }),
    }).catch(() => {});
}

async function loadVisualization() {
    if (!state.selectedModel) return;

    const method = document.getElementById("viz-select").value;
    const scatterPlot = document.getElementById("scatter-plot");
    const loadingPlaceholder = document.getElementById("loadingPlaceholder");

    loadingPlaceholder.style.display = "block";
    loadingPlaceholder.textContent = "Loading visualization...";
    document.querySelector(".plot-hover-tooltip")?.classList.remove("visible");
    scatterPlot.style.display = "none";
    scatterPlot.style.minWidth = "";
    scatterPlot.style.minHeight = "";
    destroyChart(scatterPlot);

    // The fresh chart renders at full opacity; clear any active tradition so
    // the list and the plot stay in sync.
    document.querySelectorAll("#tree-container .tradition-pick.active")
        .forEach((button) => button.classList.remove("active"));

    try {
        const data = await api(`/api/similarity/projections/${encodeURIComponent(state.selectedModel)}/${encodeURIComponent(method)}`);

        await loadTraditionInfo();
        const chartType = (state.similarityMethods.find((m) => m.key === method) || {}).chart_type || "scatter";
        await CHART_RENDERERS[chartType](scatterPlot, data);

        loadingPlaceholder.style.display = "none";
    } catch (error) {
        loadingPlaceholder.innerHTML = `Error: ${escapeHtml(error.message)}`;
        loadingPlaceholder.style.display = "block";
    }
}

const PENCIL_ICON = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4Z"/></svg>';

function showSearchPanel() {
    const searchPanel = document.getElementById("searchPanel");
    const infoContent = document.getElementById("infoContent");
    if (searchPanel) searchPanel.style.display = "";
    if (infoContent) infoContent.style.display = "none";
    document.getElementById("search-text")?.focus();
}

// Persisted across point clicks: when on, "Similar fragments" lists only
// neighbors from other traditions (cross-cultural parallels).
let crossTradition = false;

export async function displayPointInfo(pointId, chunkIndex = null) {
    if (!state.selectedModel || !pointId) return;

    const infoContent = document.getElementById("infoContent");
    const searchPanel = document.getElementById("searchPanel");
    if (!infoContent) return;

    if (searchPanel) searchPanel.style.display = "none";
    infoContent.style.display = "";
    infoContent.innerHTML = '<div class="info-loading">Loading...</div>';

    try {
        const { point, neighbors } = await fetchPointWithNeighbors(pointId, chunkIndex, 6, crossTradition);
        // Pencil reopens the search box — omit when text search is off.
        const editButton = state.textSearch
            ? `<button class="fragment-edit" id="fragmentEditBtn" type="button" title="New similarity search" aria-label="New similarity search">${PENCIL_ICON}</button>`
            : "";
        let html = `
            <div class="fragment-detail">
                <div class="fragment-text">${reflowHtml(point.text)}</div>
                ${attributionLine(point)}
                ${editButton}
            </div>
            <div class="fragments-divider">
                <span>Similar fragments</span>
                <label class="cross-toggle"><input type="checkbox" id="crossTraditionToggle"${crossTradition ? " checked" : ""}> only other traditions</label>
            </div>
        `;

        if (neighbors.length > 0) {
            html += neighbors.map((neighbor) => `
                <div class="neighbor-item" data-neighbor-id="${escapeHtml(neighbor.id)}" data-neighbor-chunk="${escapeHtml(neighbor.chunk_index)}">
                    <div class="fragment-text">${reflowHtml(neighbor.text || "")}</div>
                    ${attributionLine(neighbor, { withScore: true })}
                </div>
            `).join("");
        } else {
            html += '<div class="search-empty">No similar fragments found.</div>';
        }

        infoContent.innerHTML = html;
        document.getElementById("fragmentEditBtn")?.addEventListener("click", showSearchPanel);
        document.getElementById("crossTraditionToggle")?.addEventListener("change", (e) => {
            crossTradition = e.target.checked;
            displayPointInfo(pointId, chunkIndex);
        });
        infoContent.querySelectorAll(".neighbor-item").forEach((item) => {
            item.addEventListener("click", () => displayPointInfo(item.dataset.neighborId, item.dataset.neighborChunk));
        });
    } catch (error) {
        infoContent.innerHTML = `<div class="info-error">Error: ${escapeHtml(error.message)}</div>`;
    }
}

async function initializeAnalysisLibrary() {
    await loadTraditionInfo();

    const container = document.getElementById("tree-container");
    if (!container) return;

    container.addEventListener("tradition-select", (event) => {
        const scatter = document.getElementById("scatter-plot");
        if (scatter) highlightTradition(scatter, event.detail.tradition);
    });
    await renderTraditionList(container);
}

async function performAnalysisSearch() {
    const searchText = document.getElementById("search-text");
    const searchBtn = document.getElementById("search-btn");
    const text = searchText.value.trim();
    if (!text || !state.selectedModel) return;

    const requestId = state.analysisSearchRequestId + 1;
    state.analysisSearchRequestId = requestId;
    searchBtn.disabled = true;
    searchBtn.textContent = "Searching...";
    openSearchModal("Search Results");
    setSearchResults('<div class="search-loading">Searching... This may take a few seconds.</div>');

    try {
        const data = await runSemanticSearch({
            query: text,
            model: state.selectedModel,
            topK: 20,
        });
        if (requestId !== state.analysisSearchRequestId) return;
        if (!data) return;
        displayAnalysisSearchResults(data);
    } catch (error) {
        if (requestId !== state.analysisSearchRequestId) return;
        setSearchResults(`
            <div class="search-empty">
                Search error: ${escapeHtml(error.message)}
                <small>Check that model ${escapeHtml(state.selectedModel)} is available.</small>
            </div>
        `);
    } finally {
        if (requestId === state.analysisSearchRequestId) {
            searchBtn.disabled = searchText.value.trim().length === 0 || !state.selectedModel;
            searchBtn.textContent = "Search ›";
        }
    }
}

function openSearchModal(title = "Search Results") {
    const modal = document.getElementById("searchModal");
    const modalTitle = document.getElementById("searchModalTitle");
    if (!modal || !modalTitle) return;

    modalTitle.textContent = title;
    modal.style.display = "block";
}

function closeSearchModal() {
    const modal = document.getElementById("searchModal");
    if (modal) modal.style.display = "none";
}

function setSearchResults(html) {
    const results = document.getElementById("searchResults");
    if (results) results.innerHTML = html;
}

function displayAnalysisSearchResults(data) {
    const results = Array.isArray(data.results) ? data.results : [];
    if (!results.length) {
        setSearchResults('<div class="search-empty">Nothing found. Try changing the query.</div>');
        return;
    }

    setSearchResults(`
        <div class="search-summary">
            <strong>Found:</strong> ${results.length} results
            <span>Model: ${escapeHtml(String(data.model || "").replace(/_/g, "/"))}</span>
        </div>
        <div class="search-result-list">
            ${results.map((result) => renderSearchResultItem(result, data)).join("")}
        </div>
    `);
}
