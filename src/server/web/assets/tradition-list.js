import {
    state, ensureCorpusDocuments, groupDocuments,
    escapeHtml,
} from "./core.js";

// Same major -> tradition grouping and styling as the book tree, but stops at
// traditions (no book leaves) and emits "tradition-select" (tradition or null
// when toggled off) instead of opening a book.
export async function renderTraditionList(container) {
    container.classList.add("library-tree");
    container.innerHTML = "Loading...";

    try {
        const documents = await ensureCorpusDocuments();
        if (!documents.length) {
            container.innerHTML = '<div class="empty-state">No traditions found.</div>';
            return;
        }
        renderList(container, documents);
    } catch (error) {
        container.innerHTML = `<div class="error-state">${escapeHtml(error.message)}</div>`;
    }
}

function renderList(container, documents) {
    const grouped = groupDocuments(documents);

    let html = "";
    grouped.forEach((traditions, major) => {
        const isMajorCollapsed = state.corpusCollapsedMajors.has(major);
        html += `<section class="major-section${isMajorCollapsed ? " collapsed" : ""}" data-major="${escapeHtml(major)}">
            <button class="major-title" type="button">${escapeHtml(major)}</button>
            <div class="major-body">`;

        traditions.forEach((docs, tradition) => {
            const color = docs[0] && docs[0].color ? docs[0].color : "#6b7280";
            html += `
                <button class="tradition-title tradition-pick" type="button" data-tradition="${escapeHtml(tradition)}" style="--tradition-color:${escapeHtml(color)}">
                    <span class="tradition-dot"></span>
                    <span class="tradition-name">${escapeHtml(tradition)}</span>
                </button>`;
        });

        html += "</div></section>";
    });

    container.innerHTML = html;

    container.querySelectorAll(".major-title").forEach((button) => {
        button.addEventListener("click", () => {
            const section = button.closest(".major-section");
            section.classList.toggle("collapsed");
            const major = section.dataset.major || "Other";
            if (section.classList.contains("collapsed")) state.corpusCollapsedMajors.add(major);
            else state.corpusCollapsedMajors.delete(major);
        });
    });

    container.querySelectorAll(".tradition-pick").forEach((button) => {
        button.addEventListener("click", () => {
            const wasActive = button.classList.contains("active");
            container.querySelectorAll(".tradition-pick.active").forEach((b) => b.classList.remove("active"));
            const selected = wasActive ? null : button.dataset.tradition;
            if (selected) button.classList.add("active");
            container.dispatchEvent(new CustomEvent("tradition-select", {
                detail: { tradition: selected },
                bubbles: true,
            }));
        });
    });
}
