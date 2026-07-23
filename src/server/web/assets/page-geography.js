import { app, escapeHtml, ensureCorpusData, state, traditionColor, onCleanup } from "./core.js";
import { LAND, REGION_PATHS } from "./atlas-geo.js";

// Antarctica lifted from the shared coastline (its far-south subpaths, lat <= -58 → y >= 149):
// filling those exact subpaths white shares one geometry with the coastline — no seam.
const ANTARCTICA_D = (LAND || "").split("Z").filter((s) => s.trim())
    .filter((s) => {
        const nums = s.match(/-?\d[\d.]*/g) || [];
        const ys = nums.filter((_, i) => i % 2).map(Number);
        return ys.length && Math.min(...ys) >= 149;
    })
    .map((s) => s + "Z").join("");

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
        ? `<ul class="popup-books">${item.books.map((book) => {
               const href = `#/corpus?title=${encodeURIComponent(book)}&tradition=${encodeURIComponent(item.name)}`;
               return `<li><a class="popup-book-link" href="${escapeHtml(href)}">${escapeHtml(book)}</a></li>`;
           }).join("")}</ul>`
        : "";
    return `
        <div class="popup-title">
            <span class="popup-color" style="background:${escapeHtml(item.color)}"></span>
            <span>${escapeHtml(item.name)}</span>
        </div>
        <div class="popup-region">${escapeHtml(item.region)}</div>
        ${item.description ? `<div class="popup-description">${escapeHtml(item.description)}</div>` : ""}
        ${booksHtml}
    `;
}

function buildSvgMarkup(placed) {
    const regions = Object.entries(REGION_PATHS).map(([name, d]) => {
        const c = (state.traditionTree[name] || {}).color || "#8a8a8a";
        return `<path d="${d}" class="atlas-region" data-region="${escapeHtml(name)}" fill="${escapeHtml(c)}" stroke="${escapeHtml(c)}"/>`;
    }).join("");
    const dots = placed.map((p, i) =>
        `<circle cx="${p.cx.toFixed(2)}" cy="${p.cy.toFixed(2)}" fill="${escapeHtml(p.item.color)}" class="atlas-dot" data-i="${i}"/>`
    ).join("");
    return `<svg class="atlas-svg" viewBox="0 0 360 180" preserveAspectRatio="xMidYMid meet" style="--pr:1.7">`
        + `<rect class="atlas-ocean" width="360" height="180"/>`
        + `<path class="atlas-land" d="${LAND}"/>`
        + (ANTARCTICA_D ? `<path class="atlas-antarctica" d="${ANTARCTICA_D}"/>` : "")
        + `${regions}${dots}</svg>`;
}

function initAtlas(container, traditions) {
    if (!container) return;
    const placed = placeDots(traditions);
    container.innerHTML = buildSvgMarkup(placed);
    const svg = container.querySelector(".atlas-svg");

    // ============================================================================
    // Zoom / pan / double-click — ported from mockup 62 (Google-Maps-style rAF ease).
    // ============================================================================
    const MINW = 60, FRAME_MS = 16.7, DT_MAX = 50, R_COMP = 0.86, RESET_STEP = 0.13;
    const view = { x: 0, y: 0, w: 360, h: 180 };   // animated current viewBox
    const target = { ...view };                     // goal viewBox
    let zraf = null, zPrev = 0, iPrev = 0, resetGlide = null;

    const applyView = () => {
        svg.setAttribute("viewBox", `${view.x} ${view.y} ${view.w} ${view.h}`);
        svg.style.setProperty("--z", Math.pow(view.w / 360, R_COMP).toFixed(4));  // partial counter-scale of dots
    };

    // Uniform lerp of all four viewBox components toward the target keeps the focal point pinned.
    function animateZoom(ts) {
        const dt = zPrev ? Math.min(DT_MAX, ts - zPrev) : FRAME_MS; zPrev = ts;
        const k = 1 - Math.pow(1 - 0.16, dt / FRAME_MS);
        if (resetGlide) {
            const g = resetGlide;
            const step = Math.min(RESET_STEP * dt / FRAME_MS, Math.log(360) - Math.log(target.w));
            target.w = Math.exp(Math.log(target.w) + step);
            if (target.w >= 359.9) { target.w = 360; resetGlide = null; }
            target.h = target.w / 2;
            const s = (360 - g.w0) > 0.01 ? (target.w - g.w0) / (360 - g.w0) : 1;
            target.x = g.x0 * (1 - s);
            target.y = g.y0 * (1 - s);
        }
        view.w += (target.w - view.w) * k;
        view.h = view.w / 2;
        view.x += (target.x - view.x) * k;
        view.y += (target.y - view.y) * k;
        applyView();
        if (Math.abs(target.w - view.w) > 0.05 || Math.abs(target.x - view.x) > 0.05 || Math.abs(target.y - view.y) > 0.05) {
            zraf = requestAnimationFrame(animateZoom);
        } else { Object.assign(view, target); applyView(); zraf = null; zPrev = 0; }
    }
    const kickZoom = () => { if (!zraf) { zPrev = 0; zraf = requestAnimationFrame(animateZoom); } };

    const onWheel = (e) => {
        e.preventDefault();
        stopInertia();
        resetGlide = null;
        hideTip();
        const rect = svg.getBoundingClientRect();
        let d = e.deltaY;
        if (e.deltaMode === 1) d *= 16;
        d = Math.max(-50, Math.min(50, d));
        target.w = Math.min(360, Math.max(MINW, target.w * Math.exp(d * 0.0026)));
        target.h = target.w / 2;
        if (d > 0) {   // zoom out → straight to the centred full-extent view
            const denom = 360 - view.w;
            const s = denom > 0.01 ? (target.w - view.w) / denom : 0;
            target.x = view.x * (1 - s);
            target.y = view.y * (1 - s);
        } else {       // zoom in toward the cursor (holds its world point pinned)
            const px = (e.clientX - rect.left) / rect.width, py = (e.clientY - rect.top) / rect.height;
            const wx = view.x + px * view.w, wy = view.y + py * view.h;
            target.x = Math.max(0, Math.min(360 - target.w, wx - px * target.w));
            target.y = Math.max(0, Math.min(180 - target.h, wy - py * target.h));
        }
        kickZoom();
    };
    svg.addEventListener("wheel", onWheel, { passive: false });

    // --- drag pan with release inertia ---
    let drag = null, iraf = null;
    const vel = { x: 0, y: 0 };
    const stopInertia = () => { if (iraf) { cancelAnimationFrame(iraf); iraf = null; } vel.x = vel.y = 0; iPrev = 0; };
    const panTo = (x, y) => {
        view.x = target.x = Math.max(0, Math.min(360 - view.w, x));
        view.y = target.y = Math.max(0, Math.min(180 - view.h, y));
        applyView();
    };
    function inertia(ts) {
        const dt = iPrev ? Math.min(DT_MAX, ts - iPrev) : FRAME_MS; iPrev = ts;
        const f = dt / FRAME_MS;
        vel.x *= Math.pow(0.90, f); vel.y *= Math.pow(0.90, f);
        const px = view.x, py = view.y;
        panTo(view.x + vel.x * f, view.y + vel.y * f);
        if (view.x === px) vel.x = 0;
        if (view.y === py) vel.y = 0;
        if (Math.abs(vel.x) > 0.02 || Math.abs(vel.y) > 0.02) iraf = requestAnimationFrame(inertia);
        else { iraf = null; iPrev = 0; }
    }
    const onPointerDown = (e) => {
        if (e.button !== 0 || view.w >= 360) return;   // nothing to pan at full extent
        stopInertia(); if (zraf) { cancelAnimationFrame(zraf); zraf = null; }
        resetGlide = null;
        try { svg.setPointerCapture(e.pointerId); } catch { /* not capturable */ }
        drag = { id: e.pointerId, x: e.clientX, y: e.clientY, vx: view.x, vy: view.y,
                 hist: [[performance.now(), e.clientX, e.clientY]] };
        svg.style.cursor = "grabbing";
    };
    const VEL_WINDOW_MS = 60, MICRO_PX = 3;
    function releaseVelocity() {
        const h = drag.hist, now = performance.now(), last = h[h.length - 1];
        if (now - last[0] > FRAME_MS * 2) return;
        let ref = h[0];
        for (const s of h) if (now - s[0] <= VEL_WINDOW_MS) { ref = s; break; }
        const dt = last[0] - ref[0];
        if (dt <= 0) return;
        if (Math.hypot(last[1] - ref[1], last[2] - ref[2]) < MICRO_PX) return;
        const rect = svg.getBoundingClientRect(), k = FRAME_MS / dt;
        vel.x = -(last[1] - ref[1]) / rect.width * view.w * k;
        vel.y = -(last[2] - ref[2]) / rect.height * view.h * k;
    }
    const endDrag = () => {
        if (drag) { vel.x = vel.y = 0; releaseVelocity(); }
        if (drag && (Math.abs(vel.x) > 0.03 || Math.abs(vel.y) > 0.03)) iraf = requestAnimationFrame(inertia);
        drag = null; svg.style.cursor = "";
    };
    const onPointerUp = (e) => { if (drag && e.pointerId === drag.id) endDrag(); };
    const onPointerMove = (e) => {
        if (!drag || e.pointerId !== drag.id) return;
        const rect = svg.getBoundingClientRect();
        panTo(drag.vx - (e.clientX - drag.x) / rect.width * view.w,
              drag.vy - (e.clientY - drag.y) / rect.height * view.h);
        const t = performance.now();
        drag.hist.push([t, e.clientX, e.clientY]);
        while (drag.hist.length > 2 && t - drag.hist[0][0] > 120) drag.hist.shift();
        hideTip();
    };
    const onDblClick = () => {
        stopInertia();
        resetGlide = { x0: view.x, y0: view.y, w0: view.w };
        Object.assign(target, { x: view.x, y: view.y, w: view.w, h: view.h });
        kickZoom();
    };
    svg.addEventListener("pointerdown", onPointerDown);
    svg.addEventListener("dblclick", onDblClick);
    window.addEventListener("pointerup", onPointerUp);
    window.addEventListener("pointercancel", onPointerUp);
    window.addEventListener("pointermove", onPointerMove);
    applyView();

    // ============================================================================
    // Tooltip — dark card anchored above the hovered point (mockup 62 tip styling);
    // rich content (name · region · description · books), links stay clickable.
    // ============================================================================
    const tip = document.createElement("div");
    tip.className = "geo-tip";
    container.appendChild(tip);

    let hiDot = null, curDot = null, closeTimer = null;
    const setPoint = (c) => {
        if (hiDot === c) return;
        if (hiDot) hiDot.classList.remove("hi");
        hiDot = c;
        if (hiDot) hiDot.classList.add("hi");
    };
    const cancelClose = () => { if (closeTimer) { clearTimeout(closeTimer); closeTimer = null; } };
    const hideTip = () => { tip.classList.remove("show"); setPoint(null); curDot = null; };
    const scheduleClose = () => { cancelClose(); closeTimer = setTimeout(hideTip, 200); };

    const showTipFor = (circle) => {
        const item = placed[Number(circle.dataset.i)] && placed[Number(circle.dataset.i)].item;
        if (!item) return;
        tip.innerHTML = buildPopupHtml(item);
        tip.classList.remove("region");
        tip.classList.add("show");
        const cr = circle.getBoundingClientRect(), fr = container.getBoundingClientRect();
        const anchorX = cr.left - fr.left + cr.width / 2, anchorTop = cr.top - fr.top;
        const tr = tip.getBoundingClientRect();
        let top = anchorTop - tr.height - 8;
        if (top < 4) top = anchorTop + cr.height + 8;   // flip below when no room above
        tip.style.left = Math.max(4, Math.min(fr.width - tr.width - 4, anchorX - tr.width / 2)) + "px";
        tip.style.top = top + "px";
    };

    // Regions (mockup 62): a short dwell then the region name, muted, above the cursor.
    const showRegionTip = (name, clientX, clientY) => {
        tip.innerHTML = `<div class="popup-region-only">${escapeHtml(name)}</div>`;
        tip.classList.add("region");
        tip.classList.add("show");
        const fr = container.getBoundingClientRect();
        const cx = clientX - fr.left, cy = clientY - fr.top;
        const tr = tip.getBoundingClientRect();
        let top = cy - tr.height - 12;
        if (top < 4) top = cy + 16;
        tip.style.left = Math.max(4, Math.min(fr.width - tr.width - 4, cx - tr.width / 2)) + "px";
        tip.style.top = top + "px";
    };

    let regionTimer = null;
    const DWELL = 700;
    const clearRegionTimer = () => { if (regionTimer) { clearTimeout(regionTimer); regionTimer = null; } };

    svg.addEventListener("mousemove", (e) => {
        if (drag) return;
        clearRegionTimer();
        const dot = e.target.closest && e.target.closest(".atlas-dot");
        if (dot) {
            setPoint(dot);
            if (dot === curDot) return;
            curDot = dot; cancelClose(); showTipFor(dot);
            return;
        }
        setPoint(null);
        const region = e.target.closest && e.target.closest(".atlas-region");
        if (region) {
            curDot = null; cancelClose(); tip.classList.remove("show");
            const name = region.dataset.region, x = e.clientX, y = e.clientY;
            regionTimer = setTimeout(() => showRegionTip(name, x, y), DWELL);
        } else {
            curDot = null; scheduleClose();
        }
    });
    svg.addEventListener("mouseleave", () => { clearRegionTimer(); curDot = null; scheduleClose(); });
    tip.addEventListener("mouseenter", cancelClose);
    tip.addEventListener("mouseleave", scheduleClose);

    onCleanup(() => {
        stopInertia(); if (zraf) cancelAnimationFrame(zraf);
        cancelClose(); clearRegionTimer();
        window.removeEventListener("pointerup", onPointerUp);
        window.removeEventListener("pointercancel", onPointerUp);
        window.removeEventListener("pointermove", onPointerMove);
        tip.remove();
    });
}

function showGeographyError(message) {
    const map = document.getElementById("geography-map");
    if (map) map.innerHTML = `<div class="map-error">${escapeHtml(message)}</div>`;
}
