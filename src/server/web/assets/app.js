import { cleanupRoute, parseHash } from "./core.js";
import { renderAbout } from "./page-about.js";
import { renderCorpus } from "./page-corpus.js";
import { renderGeography } from "./page-geography.js";
import { renderEmbeddingsAnalysis } from "./page-embeddings.js";
import { renderGraphPage } from "./page-graphs.js";

const DEFAULT_ROUTE = "/corpus";

const ROUTES = {
    "/corpus": { title: "Sources", render: renderCorpus },
    "/geography": { title: "Geography", render: renderGeography },
    "/embeddings": { title: "Similarity", render: renderEmbeddingsAnalysis },
    "/beings": { title: "Beings", render: () => renderGraphPage("beings") },
    "/realms": { title: "Realms", render: () => renderGraphPage("realms") },
    "/ages": { title: "Ages", render: () => renderGraphPage("ages") },
    "/about": { title: "About", render: renderAbout },
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

    document.title = `MythoScope - ${route.title}`;
    setActiveNav(path);
    route.render();
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);
