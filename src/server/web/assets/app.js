import { cleanupRoute, parseHash } from "./core.js";
import { renderAbout } from "./page-about.js";
import { renderCorpus } from "./page-corpus.js";
import { renderGeography } from "./page-geography.js";
import { renderEmbeddingsAnalysis } from "./page-embeddings.js";
import { renderGraphPage } from "./page-graphs.js";

const DEFAULT_ROUTE = "/corpus";

const ROUTES = {
    "/corpus": { cssClass: "route-corpus", render: renderCorpus },
    "/geography": { cssClass: "route-geography", render: renderGeography },
    "/embeddings": { cssClass: "route-embeddings", render: renderEmbeddingsAnalysis },
    "/beings": { cssClass: "route-graphs", render: () => renderGraphPage("beings") },
    "/realms": { cssClass: "route-graphs", render: () => renderGraphPage("realms") },
    "/ages": { cssClass: "route-graphs", render: () => renderGraphPage("ages") },
    "/about": { cssClass: "route-about", render: renderAbout },
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
    const route = ROUTES[path];
    if (!route) {
        window.location.hash = `#${DEFAULT_ROUTE}`;
        return;
    }

    document.body.className = `has-main-navbar ${route.cssClass}`;
    setActiveNav(path);
    route.render();
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);
