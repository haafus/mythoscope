import { cleanupRoute } from "./core.js";
import { renderCorpus } from "./page-corpus.js?v=21";
import { renderEmbeddings } from "./page-embeddings.js?v=10";
import { renderGraphPage } from "./page-graphs.js?v=36";
import { renderGeography } from "./page-geography.js?v=78";
import { renderMotifs } from "./page-motifs.js?v=99";
import { renderAbout } from "./page-about.js";

const DEFAULT_ROUTE = "/corpus";

const ROUTES = {
    "/corpus": { title: "Sources", render: renderCorpus },
    "/embeddings": { title: "Similarity", render: renderEmbeddings },
    "/ages": { title: "Ages", render: () => renderGraphPage("ages") },
    "/realms": { title: "Realms", render: () => renderGraphPage("realms") },
    "/beings": { title: "Beings", render: () => renderGraphPage("beings") },
    "/geography": { title: "Atlas", render: renderGeography },
    "/motifs": { title: "Motifs", render: renderMotifs },
    "/about": { title: "About", render: renderAbout },
};

function parseHash() {
    const raw = window.location.hash.slice(1) || "/";
    const splitAt = raw.indexOf("?");
    const path = splitAt === -1 ? raw : raw.slice(0, splitAt);
    const query = splitAt === -1 ? "" : raw.slice(splitAt + 1);
    return {
        path: path || "/",
        params: new URLSearchParams(query),
    };
}

function setActiveNav(path) {
    const current = `#${path}`;
    document.querySelectorAll(".nav-links a").forEach((link) => {
        link.classList.toggle("active", link.getAttribute("href") === current);
    });
}

function render() {
    cleanupRoute();

    const { path, params } = parseHash();
    const route = ROUTES[path];
    if (!route) {
        window.location.hash = `#${DEFAULT_ROUTE}`;
        return;
    }

    document.title = `Mythoscope - ${route.title}`;
    setActiveNav(path);
    route.render(params);
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);
