import { cleanupRoute, parseHash } from "./core.js";
import { renderAbout } from "./page-about.js";
import { renderCorpus } from "./page-corpus.js";
import { renderGeography } from "./page-geography.js";
import { renderEmbeddingsAnalysis } from "./page-embeddings.js";
import { renderGraphPage } from "./page-graphs.js";

const DEFAULT_ROUTE = "/corpus";

const ROUTES = {
    "/corpus": renderCorpus,
    "/geography": renderGeography,
    "/embeddings": renderEmbeddingsAnalysis,
    "/beings": () => renderGraphPage("beings"),
    "/realms": () => renderGraphPage("realms"),
    "/ages": () => renderGraphPage("ages"),
    "/about": renderAbout,
};

function setActiveNav(path) {
    const current = `#${path}`;
    document.querySelectorAll(".nav-links a").forEach((link) => {
        link.classList.toggle("active", link.getAttribute("href") === current);
    });
}

function render() {
    cleanupRoute();

    const { path } = parseHash();
    const renderPage = ROUTES[path];
    if (!renderPage) {
        window.location.hash = `#${DEFAULT_ROUTE}`;
        return;
    }

    setActiveNav(path);
    renderPage();
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);
