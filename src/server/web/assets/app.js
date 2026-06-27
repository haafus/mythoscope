import {
    cleanupRoute, normalizeRoute, parseHash,
    setActiveNav, setBodyClass,
} from "./core.js";
import { destroyChart } from "./chart.js";
import { renderHome } from "./page-home.js";
import { renderCorpus } from "./page-corpus.js";
import { renderGeography } from "./page-geography.js";
import { renderEmbeddingsAnalysis } from "./page-embeddings.js";
import { renderGraphPage } from "./page-graphs.js";

function render() {
    cleanupRoute();
    const scatterPlot = document.getElementById("scatter-plot");
    if (scatterPlot) destroyChart(scatterPlot);

    const parsed = parseHash();
    const path = normalizeRoute(parsed.path);
    setBodyClass(path);
    setActiveNav(path);

    if (path !== parsed.path) {
        window.location.hash = `#${path}`;
        return;
    }

    if (path === "/home") return renderHome();
    if (path === "/corpus") return renderCorpus();
    if (path === "/geography") return renderGeography();
    if (path === "/embeddings_analysis") return renderEmbeddingsAnalysis();
    const graphType = path.slice(1);
    if (["beings", "realms", "ages"].includes(graphType)) return renderGraphPage(graphType);

    window.location.hash = "#/corpus";
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);
