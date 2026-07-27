import { state, ensureCorpusData, groupDocuments, escapeHtml } from "./core.js";

// Shared scaffold for both trees: renders collapsible major sections; the caller
// fills each major body (renderBody) and wires its leaves (bindLeaves).
export async function renderMajorTree(container, { emptyMessage, prepare, renderBody, bindLeaves }) {
    container.classList.add("library-tree");
    container.innerHTML = "Loading...";

    try {
        const documents = await ensureCorpusData();  // tree + documents (groupDocuments needs the tree)
        if (!documents.length) {
            container.innerHTML = `<div class="empty-state">${escapeHtml(emptyMessage)}</div>`;
            return;
        }

        const ctx = prepare ? prepare(documents) : {};
        const grouped = groupDocuments(documents);
        // No default-open: the tree starts fully collapsed until the user opens a section (or a
        // deep link / prior selection opens one).

        let html = "";
        grouped.forEach((traditions, major) => {
            const collapsed = state.corpusOpenMajor !== major;  // accordion: only the one open region
            html += `<section class="major-section${collapsed ? " collapsed" : ""}" data-major="${escapeHtml(major)}">
                <button class="major-title" type="button">${escapeHtml(major)}</button>
                <div class="major-body">${renderBody(traditions, major, ctx)}</div>
            </section>`;
        });
        container.innerHTML = html;

        bindMajorToggles(container);
        if (bindLeaves) bindLeaves(container, ctx);
    } catch (error) {
        container.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}

function bindMajorToggles(container) {
    container.querySelectorAll(".major-title").forEach((button) => {
        button.addEventListener("click", () => {
            const major = button.closest(".major-section").dataset.major || "Other";
            const opened = state.corpusOpenMajor !== major;   // was collapsed → this click opens it
            state.corpusOpenMajor = opened ? major : null;    // opening one closes the rest
            container.querySelectorAll(".major-section").forEach((s) =>
                s.classList.toggle("collapsed", (s.dataset.major || "Other") !== state.corpusOpenMajor));
            // Any click selects the region (makes it the one active node + shows its page), even a
            // collapsing one — expansion and active are independent.
            container.dispatchEvent(new CustomEvent("region-select", { detail: { region: major }, bubbles: true }));
        });
    });
}
