import { cleanupRoute } from "./core.js";
import { renderCorpus } from "./page-corpus.js?v=39";
import { renderEmbeddings } from "./page-embeddings.js?v=16";
import { renderGraphPage } from "./page-graphs.js?v=46";
import { renderGeography } from "./page-geography.js?v=78";
import { renderMotifs } from "./page-motifs.js?v=99";
import { renderAbout } from "./page-about.js?v=15";

const DEFAULT_ROUTE = "/corpus";

const ROUTES = {
    "/corpus": { title: "Corpus", render: renderCorpus },
    "/embeddings": { title: "Similarity", render: renderEmbeddings },
    "/structure": { title: "Structure", render: renderGraphPage },
    // Former separate pages; old links land on the matching Structure graph.
    "/ages": { title: "Structure", render: () => location.replace("#/structure?graph=ages") },
    "/realms": { title: "Structure", render: () => location.replace("#/structure?graph=realms") },
    "/beings": { title: "Structure", render: () => location.replace("#/structure?graph=beings") },
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

// The path rendered last. A page told it is re-rendering itself (`samePage`) takes a
// bare URL literally — e.g. Back to "#/corpus" means "nothing selected" — while a page
// entered from another section may restore the selection the app already holds.
let lastPath = null;

function render() {
    cleanupRoute();

    const { path, params } = parseHash();
    const route = ROUTES[path];
    if (!route) {
        window.location.hash = `#${DEFAULT_ROUTE}`;
        return;
    }

    const samePage = path === lastPath;
    lastPath = path;
    document.title = `Mythoscope - ${route.title}`;
    setActiveNav(path);
    route.render(params, { samePage });
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", render);
