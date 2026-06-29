import { cleanupRoute, parseHash } from "./core.js";
import { renderCorpus } from "./page-corpus.js";
import { renderEmbeddings } from "./page-embeddings.js";
import { renderGraphPage } from "./page-graphs.js";
import { renderGeography } from "./page-geography.js";
import { renderAbout } from "./page-about.js";

const DEFAULT_ROUTE = "/corpus";

const ROUTES = {
    "/corpus": { title: "Sources", render: renderCorpus },
    "/embeddings": { title: "Similarity", render: renderEmbeddings },
    "/ages": { title: "Ages", render: () => renderGraphPage("ages") },
    "/realms": { title: "Realms", render: () => renderGraphPage("realms") },
    "/beings": { title: "Beings", render: () => renderGraphPage("beings") },
    "/geography": { title: "Geography", render: renderGeography },
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
