import { escapeHtml, traditionColor } from "./core.js";
import { renderMajorTree } from "./tree-scaffold.js?v=3";

// Tradition leaves (no books); emits "tradition-select" with the tradition, or
// null when the active one is toggled off.
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
        const color = traditionColor(tradition);  // derived region shade (§8.1)
        html += `
            <button class="tradition-title tradition-pick" type="button" data-tradition="${escapeHtml(tradition)}" style="--tradition-color:${escapeHtml(color)}">
                <span class="tradition-dot"></span>
                <span class="tradition-name">${escapeHtml(tradition)}</span>
            </button>`;
    });
    return html;
}

let traditionKeyHandler = null;

function bindTraditionPicks(container) {
    container.querySelectorAll(".tradition-pick").forEach((button) => {
        button.addEventListener("click", () => selectPick(container, button));
    });

    // ↑/↓ step through the tradition list (single stable handler; a re-render
    // detaches the old container, so drop the previous binding first).
    if (traditionKeyHandler) document.removeEventListener("keydown", traditionKeyHandler);
    traditionKeyHandler = (e) => onTraditionKeydown(e, container);
    document.addEventListener("keydown", traditionKeyHandler);
}

function selectPick(container, button) {
    const wasActive = button.classList.contains("active");
    container.querySelectorAll(".tradition-pick.active").forEach((b) => b.classList.remove("active"));
    const selected = wasActive ? null : button.dataset.tradition;
    if (selected) button.classList.add("active");
    container.dispatchEvent(new CustomEvent("tradition-select", { detail: { tradition: selected }, bubbles: true }));
}

function onTraditionKeydown(e, container) {
    if (e.key !== "ArrowDown" && e.key !== "ArrowUp") return;
    if (e.metaKey || e.ctrlKey || e.altKey) return;
    if (!container.isConnected) return;
    const tag = (e.target.tagName || "").toLowerCase();
    if (tag === "input" || tag === "textarea" || tag === "select") return;  // don't hijack typing

    const buttons = Array.from(container.querySelectorAll(".tradition-pick"))
        .filter((b) => b.offsetParent !== null);  // only traditions inside open macro-areas
    if (!buttons.length) return;
    e.preventDefault();

    const cur = buttons.findIndex((b) => b.classList.contains("active"));
    const delta = e.key === "ArrowDown" ? 1 : -1;
    const next = cur === -1
        ? (delta > 0 ? 0 : buttons.length - 1)
        : Math.min(buttons.length - 1, Math.max(0, cur + delta));
    if (next === cur) return;

    const btn = buttons[next];
    btn.scrollIntoView({ block: "nearest" });
    selectPick(container, btn);  // btn wasn't active → this selects it
}
