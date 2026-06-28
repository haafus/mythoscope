import { escapeHtml } from "./core.js";
import { renderMajorTree } from "./tree-scaffold.js";

// Same major -> tradition grouping and styling as the book tree, but stops at
// traditions (no book leaves) and emits "tradition-select" (tradition or null
// when toggled off) instead of opening a book.
export async function renderTraditionList(container) {
    await renderMajorTree(container, {
        emptyMessage: "No traditions found.",
        renderBody: (traditions) => renderTraditionPicks(traditions),
        bindLeaves: (container) => bindTraditionPicks(container),
    });
}

function renderTraditionPicks(traditions) {
    let html = "";
    traditions.forEach((docs, tradition) => {
        const color = docs[0] && docs[0].color ? docs[0].color : "#6b7280";
        html += `
            <button class="tradition-title tradition-pick" type="button" data-tradition="${escapeHtml(tradition)}" style="--tradition-color:${escapeHtml(color)}">
                <span class="tradition-dot"></span>
                <span class="tradition-name">${escapeHtml(tradition)}</span>
            </button>`;
    });
    return html;
}

function bindTraditionPicks(container) {
    container.querySelectorAll(".tradition-pick").forEach((button) => {
        button.addEventListener("click", () => {
            const wasActive = button.classList.contains("active");
            container.querySelectorAll(".tradition-pick.active").forEach((b) => b.classList.remove("active"));
            const selected = wasActive ? null : button.dataset.tradition;
            if (selected) button.classList.add("active");
            container.dispatchEvent(new CustomEvent("tradition-select", { detail: { tradition: selected }, bubbles: true }));
        });
    });
}
