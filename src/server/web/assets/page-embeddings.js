import {
    api, app, state,
    ensureModels,
    escapeAttribute, escapeHtml,
    loadTraditionInfo,
    persistSelectedModel, renderModelOptions,
} from "./core.js";
import { destroyChart, highlightTradition, renderScatter, renderHeatmap, renderDistribution, resizeChart } from "./chart.js";
import {
    attributionLine, bindSearchResultClicks,
    fetchPointWithNeighbors, renderSearchResultItem,
    resultBookTitle, runSemanticSearch,
    searchResultMetaLine,
} from "./search-utils.js";
import { renderTraditionList } from "./tradition-list.js";

function getTraditionColor(name, fallback = "#555") {
    const info = state.traditionInfo || {};
    if (info[name] && info[name].color) return info[name].color;

    const cleanName = String(name || "").toLowerCase().replace(/[_\s-]+/g, "").replace(/[^a-z0-9Ѐ-ӿ]/gi, "");
    for (const key in info) {
        const cleanKey = key.toLowerCase().replace(/[_\s-]+/g, "").replace(/[^a-z0-9Ѐ-ӿ]/gi, "");
        if (cleanName === cleanKey && info[key].color) return info[key].color;
    }
    return fallback;
}

function getColorMap(traditions) {
    const colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"];
    const map = {};
    traditions.forEach((tradition, index) => {
        map[tradition] = getTraditionColor(tradition, colors[index % colors.length]);
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

export async function renderEmbeddingsAnalysis() {
    document.title = "Embedding Analysis";
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
                            <div class="search-panel" id="searchPanel">
                                <textarea id="search-text" placeholder="Type a text for similarity search…"></textarea>
                                <button class="btn btn-primary search-btn" id="search-btn" type="button" disabled>Search ›</button>
                            </div>
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

    // ECharts/regl don't auto-resize on window the way Plotly's responsive mode
    // does; keep the active chart fitted to its container.
    state.chartResizeHandler = () => resizeChart(document.getElementById("scatter-plot"));
    window.addEventListener("resize", state.chartResizeHandler);

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
    searchText.addEventListener("input", () => {
        searchBtn.disabled = searchText.value.trim().length === 0 || !state.selectedModel;
    });
    searchBtn.addEventListener("click", performAnalysisSearch);

    document.getElementById("close-search-modal").addEventListener("click", closeSearchModal);
}

async function loadSimilarityMethods() {
    if (!state.similarityMethods.length) {
        state.similarityMethods = await api("/api/similarity/methods");
    }
    const vizSelect = document.getElementById("viz-select");
    if (vizSelect) {
        vizSelect.innerHTML = state.similarityMethods
            .map((m) => `<option value="${escapeAttribute(m.key)}">${escapeHtml(m.label)}</option>`)
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
    if (!model) return;
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

export async function displayPointInfo(pointId, chunkIndex = null) {
    if (!state.selectedModel || !pointId) return;

    const infoContent = document.getElementById("infoContent");
    const searchPanel = document.getElementById("searchPanel");
    if (!infoContent) return;

    if (searchPanel) searchPanel.style.display = "none";
    infoContent.style.display = "";
    infoContent.innerHTML = '<div style="text-align:center; color:#6c757d">Loading...</div>';

    try {
        const results = await fetchPointWithNeighbors(pointId, chunkIndex);
        const point = results[0];
        const neighbors = results.slice(1);
        if (!point) throw new Error("Point not found");
        let html = `
            <div class="fragment-detail">
                <div class="fragment-text">${escapeHtml(point.text)}</div>
                ${attributionLine(point)}
                <button class="fragment-edit" id="fragmentEditBtn" type="button" title="New similarity search" aria-label="New similarity search">${PENCIL_ICON}</button>
            </div>
            <div class="fragments-divider">Similar fragments</div>
        `;

        if (neighbors.length > 0) {
            html += neighbors.map((neighbor) => `
                <div class="neighbor-item" data-neighbor-id="${escapeAttribute(neighbor.id)}" data-neighbor-chunk="${escapeAttribute(neighbor.chunk_index)}">
                    <div class="fragment-text">${escapeHtml(neighbor.text || "")}</div>
                    ${attributionLine(neighbor, { withScore: true })}
                </div>
            `).join("");
        } else {
            html += '<div class="search-empty">No similar fragments found.</div>';
        }

        infoContent.innerHTML = html;
        document.getElementById("fragmentEditBtn")?.addEventListener("click", showSearchPanel);
        infoContent.querySelectorAll(".neighbor-item").forEach((item) => {
            item.addEventListener("click", () => displayPointInfo(item.dataset.neighborId, item.dataset.neighborChunk));
        });
    } catch (error) {
        infoContent.innerHTML = `<div style="color:#d32f2f">Error: ${escapeHtml(error.message)}</div>`;
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
    state.lastAnalysisSearchData = data;
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

    bindSearchResultClicks(document.getElementById("searchResults"), displaySearchModalPointInfo);
}

async function displaySearchModalPointInfo(pointId, chunkIndex = null) {
    if (!state.selectedModel || !pointId) return;

    openSearchModal("Chunk Details");
    setSearchResults('<div class="search-loading">Loading nearest chunks...</div>');

    try {
        const results = await fetchPointWithNeighbors(pointId, chunkIndex);
        const point = results[0];
        const neighbors = results.slice(1);
        if (!point) throw new Error("Point not found");

        setSearchResults(`
            <div class="search-detail">
                <button class="btn btn-outline" type="button" id="backToSearchResults">Back to results</button>
                <div class="search-result-topline">
                    <span class="result-tradition">${escapeHtml(point.tradition)}</span>
                    <span class="search-result-meta">${escapeHtml(searchResultMetaLine(point))}</span>
                </div>
                <div class="search-detail-text">${escapeHtml(point.text)}</div>
            </div>
            <div class="search-summary">
                <strong>Nearest neighbors</strong>
                <span>${escapeHtml(resultBookTitle(point))}</span>
            </div>
            <div class="search-result-list">
                ${neighbors.length ? neighbors.map((neighbor) => renderSearchResultItem(neighbor, {query: ""})).join("") : '<div class="search-empty">No nearest chunks found.</div>'}
            </div>
        `);

        const back = document.getElementById("backToSearchResults");
        if (back) back.addEventListener("click", () => displayAnalysisSearchResults(state.lastAnalysisSearchData || {results: []}));
        bindSearchResultClicks(document.getElementById("searchResults"), displaySearchModalPointInfo);
    } catch (error) {
        setSearchResults(`<div class="search-empty">Load error: ${escapeHtml(error.message)}</div>`);
    }
}
