import { state, ensureCorpusDocuments, groupDocuments, escapeHtml } from "./core.js";

// Shared scaffold for both trees: renders collapsible major sections; the caller
// fills each major body (renderBody) and wires its leaves (bindLeaves).
export async function renderMajorTree(container, { emptyMessage, prepare, renderBody, bindLeaves }) {
    container.classList.add("library-tree");
    container.innerHTML = "Loading...";

    try {
        const documents = await ensureCorpusDocuments();
        if (!documents.length) {
            container.innerHTML = `<div class="empty-state">${escapeHtml(emptyMessage)}</div>`;
            return;
        }

        const ctx = prepare ? prepare(documents) : {};
        let html = "";
        groupDocuments(documents).forEach((traditions, major) => {
            const collapsed = state.corpusCollapsedMajors.has(major);
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
            const section = button.closest(".major-section");
            section.classList.toggle("collapsed");
            const major = section.dataset.major || "Other";
            if (section.classList.contains("collapsed")) state.corpusCollapsedMajors.add(major);
            else state.corpusCollapsedMajors.delete(major);
        });
    });
}
