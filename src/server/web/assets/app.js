import { cleanupRoute, parseHash } from "./core.js";
import { renderAbout } from "./page-about.js";
import { renderCorpus } from "./page-corpus.js";
import { renderGeography } from "./page-geography.js";
import { renderEmbeddingsAnalysis } from "./page-embeddings.js";
import { renderGraphPage } from "./page-graphs.js";

const DEFAULT_ROUTE = "/corpus";

// Canonical path -> body class; unknown paths fall back to DEFAULT_ROUTE.
const ROUTE_CLASS = {
    "/corpus": "route-corpus",
    "/geography": "route-geography",
    "/embeddings": "route-embeddings",
    "/beings": "route-graphs",
    "/realms": "route-graphs",
    "/ages": "route-graphs",
    "/about": "route-about",
};

const RENDERERS = {
    "/corpus": renderCorpus,
    "/geography": renderGeography,
    "/embeddings": renderEmbeddingsAnalysis,
    "/beings": () => renderGraphPage("beings"),
    "/realms": () => renderGraphPage("realms"),
    "/ages": () => renderGraphPage("ages"),
    "/about": renderAbout,
};

function setBodyClass(path) {
    document.body.className = `has-main-navbar ${ROUTE_CLASS[path] || ROUTE_CLASS[DEFAULT_ROUTE]}`;
}

function setActiveNav(path) {
    const current = `#${path}`;
    document.querySelectorAll(".nav-links a").forEach((link) => {
        link.classList.toggle("active", link.getAttribute("href") === current);
    });
}

function render() {
    cleanupRoute();

    const { path } = parseHash();
    setBodyClass(path);
    setActiveNav(path);

    const renderer = RENDERERS[path];
    if (renderer) return renderer();
    window.location.hash = `#${DEFAULT_ROUTE}`;
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);
