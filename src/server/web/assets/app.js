import {
    cleanupRoute, parseHash,
    setActiveNav, setBodyClass, DEFAULT_ROUTE,
} from "./core.js";
import { destroyChart } from "./chart.js";
import { renderHome } from "./page-home.js";
import { renderCorpus } from "./page-corpus.js";
import { renderGeography } from "./page-geography.js";
import { renderEmbeddingsAnalysis } from "./page-embeddings.js";
import { renderGraphPage } from "./page-graphs.js";

const RENDERERS = {
    "/home": renderHome,
    "/corpus": renderCorpus,
    "/geography": renderGeography,
    "/embeddings": renderEmbeddingsAnalysis,
    "/beings": () => renderGraphPage("beings"),
    "/realms": () => renderGraphPage("realms"),
    "/ages": () => renderGraphPage("ages"),
};

function render() {
    cleanupRoute();
    const scatterPlot = document.getElementById("scatter-plot");
    if (scatterPlot) destroyChart(scatterPlot);

    const { path } = parseHash();
    setBodyClass(path);
    setActiveNav(path);

    const renderer = RENDERERS[path];
    if (renderer) return renderer();
    window.location.hash = `#${DEFAULT_ROUTE}`;
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);
