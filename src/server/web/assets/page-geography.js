import { app, escapeHtml, ensureCorpusData, state, traditionColor, onCleanup } from "./core.js";
import { LAND, REGION_PATHS } from "./atlas-geo.js";

export async function renderGeography() {
    app.innerHTML = `
        <main class="geography-page container">
            <div class="geo-workspace">
                <div class="map-frame">
                    <div id="geography-map"></div>
                </div>
            </div>
        </main>
    `;

    try {
        const traditions = await fetchTraditions();
        initAtlas(document.getElementById("geography-map"), traditions);
    } catch (error) {
        console.error(error);
        showGeographyError("Could not load geography data.");
    }
}

function normalizeCoordinates(value) {
    if (!Array.isArray(value) || value.length < 2) return null;
    const lat = Number(value[0]);
    const lon = Number(value[1]);
    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;
    return [lat, lon];
}

// Points from the region tree (per-tradition coordinates) joined with each tradition's book
// titles from the documents; colour is the derived region shade (§8.1), never stored.
async function fetchTraditions() {
    await ensureCorpusData();

    const booksByTradition = new Map();
    (state.corpusDocuments || []).forEach((doc) => {
        const t = doc.tradition || "Unknown";
        if (!booksByTradition.has(t)) booksByTradition.set(t, []);
        booksByTradition.get(t).push(doc.title);
    });

    const points = [];
    for (const [region, node] of Object.entries(state.traditionTree || {})) {
        for (const [name, info] of Object.entries(node.traditions || {})) {
            const coordinates = normalizeCoordinates(info && info.coordinates);
            if (!coordinates) continue;
            points.push({
                name,
                region,
                description: (info && info.description) || "",
                coordinates,
                color: traditionColor(name),
                books: (booksByTradition.get(name) || []).slice().sort(),
            });
        }
    }
    return points.sort((a, b) => a.name.localeCompare(b.name));
}

// Fan co-located traditions out on a small ring so their dots don't overlap.
function placeDots(traditions) {
    const groups = new Map();
    traditions.forEach((item) => {
        const [lat, lon] = item.coordinates;
        const key = `${lat.toFixed(4)},${lon.toFixed(4)}`;
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(item);
    });

    const placed = [];
    groups.forEach((group) => {
        group.forEach((item, index) => {
            let [lat, lon] = item.coordinates;
            if (group.length > 1) {
                const angle = (Math.PI * 2 * index) / group.length;
                lat += Math.sin(angle) * 0.8;
                lon += Math.cos(angle) * 0.8;
            }
            placed.push({ item, cx: lon + 180, cy: 90 - lat });  // equirect: x=lon+180, y=90-lat
        });
    });
    return placed;
}

function buildPopupHtml(item) {
    const booksHtml = item.books.length
        ? `<div class="popup-books-title">Books</div>
           <ul class="popup-books">${item.books.map((book) => {
               const href = `#/corpus?title=${encodeURIComponent(book)}&tradition=${encodeURIComponent(item.name)}`;
               return `<li><a class="popup-book-link" href="${escapeHtml(href)}">${escapeHtml(book)}</a></li>`;
           }).join("")}</ul>`
        : `<div class="popup-empty">No texts yet</div>`;

    return `
        <div class="popup-title">
            <span class="popup-color" style="background:${escapeHtml(item.color)}"></span>
            <span>${escapeHtml(item.name)}</span>
        </div>
        <div class="popup-region">${escapeHtml(item.region)}</div>
        <div class="popup-description">${escapeHtml(item.description)}</div>
        ${booksHtml}
    `;
}

function buildSvgMarkup(placed) {
    const ocean = `<rect x="0" y="0" width="360" height="180" class="atlas-ocean"/>`;
    const land = `<path d="${LAND}" class="atlas-land"/>`;
    const regions = Object.entries(REGION_PATHS).map(([name, d]) => {
        const c = (state.traditionTree[name] || {}).color || "#8a8a8a";
        return `<path d="${d}" class="atlas-region" fill="${escapeHtml(c)}" stroke="${escapeHtml(c)}"/>`;
    }).join("");
    const dots = placed.map((p, i) => {
        const attrs = p.item.books.length
            ? `fill="${escapeHtml(p.item.color)}"`
            : `fill="none" stroke="${escapeHtml(p.item.color)}" opacity="0.6"`;  // known, no texts yet
        return `<circle cx="${p.cx.toFixed(2)}" cy="${p.cy.toFixed(2)}" r="1.7" ${attrs} class="atlas-dot" data-i="${i}"/>`;
    }).join("");
    return `<svg class="atlas-svg">${ocean}${land}${regions}${dots}</svg>`;
}

// Initial viewBox: the dots' bounding box (padded, clamped to the 0..360 / 0..180 canvas).
function fitViewBox(placed) {
    if (!placed.length) return { x: 0, y: 0, w: 360, h: 180 };
    let minX = 360, minY = 180, maxX = 0, maxY = 0;
    placed.forEach((p) => {
        minX = Math.min(minX, p.cx); maxX = Math.max(maxX, p.cx);
        minY = Math.min(minY, p.cy); maxY = Math.max(maxY, p.cy);
    });
    const padX = (maxX - minX) * 0.06 + 6, padY = (maxY - minY) * 0.06 + 6;
    minX = Math.max(0, minX - padX); minY = Math.max(0, minY - padY);
    maxX = Math.min(360, maxX + padX); maxY = Math.min(180, maxY + padY);
    return { x: minX, y: minY, w: maxX - minX, h: maxY - minY };
}

function initAtlas(container, traditions) {
    if (!container) return;
    const placed = placeDots(traditions);
    container.innerHTML = buildSvgMarkup(placed);
    const svg = container.querySelector(".atlas-svg");

    const view = { ...fitViewBox(placed) };
    const maxW = view.w, maxH = view.h;             // fit view is the zoom-out floor (no zooming past it)
    const minW = maxW / 8;
    const apply = () => svg.setAttribute("viewBox", `${view.x} ${view.y} ${view.w} ${view.h}`);
    const pxScale = () => {
        const r = svg.getBoundingClientRect();
        return Math.min(r.width / view.w, r.height / view.h);  // preserveAspectRatio="meet"
    };
    const clamp = () => {
        view.w = Math.min(maxW, view.w); view.h = Math.min(maxH, view.h);
        view.x = Math.max(0, Math.min(360 - view.w, view.x));
        view.y = Math.max(0, Math.min(180 - view.h, view.y));
    };
    apply();

    let dragging = false, lastX = 0, lastY = 0, moved = false;

    svg.addEventListener("wheel", (e) => {
        e.preventDefault();
        const r = svg.getBoundingClientRect();
        const s = pxScale();
        const offX = (r.width - view.w * s) / 2, offY = (r.height - view.h * s) / 2;
        const cx = view.x + (e.clientX - r.left - offX) / s;   // canvas point under cursor (held fixed)
        const cy = view.y + (e.clientY - r.top - offY) / s;
        const factor = e.deltaY < 0 ? 0.85 : 1 / 0.85;
        const nw = Math.min(maxW, Math.max(minW, view.w * factor));
        const nh = nw * (view.h / view.w);
        view.x = cx - (cx - view.x) * (nw / view.w);
        view.y = cy - (cy - view.y) * (nh / view.h);
        view.w = nw; view.h = nh;
        clamp(); apply();
    }, { passive: false });

    svg.addEventListener("pointerdown", (e) => {
        dragging = true; moved = false; lastX = e.clientX; lastY = e.clientY;
        svg.setPointerCapture(e.pointerId); svg.classList.add("dragging");
    });
    svg.addEventListener("pointermove", (e) => {
        if (!dragging) return;
        const s = pxScale();
        view.x -= (e.clientX - lastX) / s;
        view.y -= (e.clientY - lastY) / s;
        lastX = e.clientX; lastY = e.clientY; moved = true;
        clamp(); apply();
    });
    const endDrag = (e) => {
        dragging = false; svg.classList.remove("dragging");
        try { svg.releasePointerCapture(e.pointerId); } catch { /* not captured */ }
    };
    svg.addEventListener("pointerup", endDrag);
    svg.addEventListener("pointercancel", endDrag);

    // --- hover tooltip (name + region + description + books; book links stay clickable) ---
    const tip = document.createElement("div");
    tip.className = "geo-tip";
    tip.style.display = "none";
    container.appendChild(tip);
    let closeTimer = null;
    const cancelClose = () => { if (closeTimer) { clearTimeout(closeTimer); closeTimer = null; } };
    const scheduleClose = () => { cancelClose(); closeTimer = setTimeout(() => { tip.style.display = "none"; }, 200); };
    const showTip = (circle) => {
        if (dragging || moved) return;
        const item = placed[Number(circle.dataset.i)] && placed[Number(circle.dataset.i)].item;
        if (!item) return;
        cancelClose();
        tip.innerHTML = buildPopupHtml(item);
        tip.style.display = "block";
        const cr = circle.getBoundingClientRect(), fr = container.getBoundingClientRect();
        const anchorX = cr.left - fr.left + cr.width / 2, anchorY = cr.top - fr.top;
        const tr = tip.getBoundingClientRect();
        tip.style.left = Math.max(4, Math.min(fr.width - tr.width - 4, anchorX - tr.width / 2)) + "px";
        tip.style.top = Math.max(4, anchorY - tr.height - 8) + "px";
    };
    svg.addEventListener("mouseover", (e) => {
        const c = e.target.closest(".atlas-dot");
        if (c) showTip(c);
    });
    svg.addEventListener("mouseout", (e) => {
        if (e.target.closest(".atlas-dot")) scheduleClose();
    });
    tip.addEventListener("mouseenter", cancelClose);
    tip.addEventListener("mouseleave", scheduleClose);

    onCleanup(() => { cancelClose(); tip.remove(); });
}

function showGeographyError(message) {
    const map = document.getElementById("geography-map");
    if (map) map.innerHTML = `<div class="map-error">${escapeHtml(message)}</div>`;
}
