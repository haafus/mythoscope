import { app, escapeHtml, loadTraditionInfo, onCleanup } from "./core.js";

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

    if (typeof L === "undefined") {
        showGeographyError("Map library could not be loaded.");
        return;
    }

    try {
        const traditions = await fetchTraditions();
        initializeGeographyMap(traditions);
    } catch (error) {
        console.error(error);
        showGeographyError("Could not load geography data.");
    }
}

function isValidColor(value) {
    return typeof value === "string" && /^#[0-9a-f]{6}$/i.test(value.trim());
}

function normalizeCoordinates(value) {
    if (!Array.isArray(value) || value.length < 2) return null;

    const lat = Number(value[0]);
    const lon = Number(value[1]);

    if (!Number.isFinite(lat) || !Number.isFinite(lon)) return null;
    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) return null;

    return [lat, lon];
}

function normalizeTraditions(raw) {
    return Object.entries(raw || {})
        .map(([name, info]) => {
            const coordinates = normalizeCoordinates(info && info.coordinates);
            if (!coordinates) return null;

            return {
                name,
                description: info.description || "",
                coordinates,
                color: isValidColor(info.color) ? info.color : "#334155",
                books: Array.isArray(info.books) ? info.books.filter(Boolean) : [],
            };
        })
        .filter(Boolean)
        .sort((a, b) => a.name.localeCompare(b.name));
}

async function fetchTraditions() {
    const raw = await loadTraditionInfo();
    return normalizeTraditions(raw);
}

function buildCoordinateGroups(traditions) {
    const groups = new Map();

    traditions.forEach((item) => {
        const [lat, lon] = item.coordinates;
        const key = `${lat.toFixed(4)},${lon.toFixed(4)}`;
        if (!groups.has(key)) groups.set(key, []);
        groups.get(key).push(item);
    });

    return groups;
}

function getOffsetCoordinate(item, index, total) {
    if (total <= 1) return item.coordinates;

    const [lat, lon] = item.coordinates;
    const angle = (Math.PI * 2 * index) / total;
    const radius = 0.8;

    return [
        lat + Math.sin(angle) * radius,
        lon + Math.cos(angle) * radius,
    ];
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
        <div class="popup-description">${escapeHtml(item.description)}</div>
        ${booksHtml}
    `;
}

function createMarkerIcon(item) {
    return L.divIcon({
        className: "tradition-marker",
        html: `<button class="map-point${item.books.length ? "" : " empty"}" type="button" style="--point-color:${escapeHtml(item.color)}" aria-label="${escapeHtml(item.name)}${item.books.length ? "" : " (no texts yet)"}"></button>`,
        iconSize: [18, 18],
        iconAnchor: [9, 9],
        popupAnchor: [0, -11],
    });
}

function renderMarkers(map, traditions) {
    const bounds = [];
    const markers = new Map();
    const groups = buildCoordinateGroups(traditions);

    // Grace period before a hover-opened popup closes, so the pointer can travel
    // from the marker into the popup to click a book link without it vanishing.
    let closeTimer = null;
    const cancelClose = () => {
        if (closeTimer) {
            clearTimeout(closeTimer);
            closeTimer = null;
        }
    };
    const scheduleClose = (marker) => {
        cancelClose();
        closeTimer = setTimeout(() => marker.closePopup(), 200);
    };

    groups.forEach((group) => {
        group.forEach((item, index) => {
            const position = getOffsetCoordinate(item, index, group.length);

            const marker = L.marker(position, {
                icon: createMarkerIcon(item),
                keyboard: true,
                title: item.name,
            })
                .addTo(map)
                .bindPopup(buildPopupHtml(item), {
                    className: "tradition-popup",
                    closeButton: false,
                    maxWidth: 340,
                });

            marker.on("mouseover", () => {
                cancelClose();
                marker.openPopup();
            });
            marker.on("mouseout", () => scheduleClose(marker));

            // Keep the popup alive while the pointer is over it (so its book links
            // stay clickable), and close it once the pointer leaves the popup.
            marker.on("popupopen", (event) => {
                const el = event.popup.getElement();
                if (!el) return;
                el.addEventListener("mouseenter", cancelClose);
                el.addEventListener("mouseleave", () => scheduleClose(marker));
            });

            markers.set(item.name, marker);
            bounds.push(position);
        });
    });

    return { bounds: bounds.length ? L.latLngBounds(bounds) : null, markers };
}

function initializeGeographyMap(traditions) {
    // Real tile-covered world: ±180° longitude and the web-mercator latitude limit.
    const worldBounds = L.latLngBounds([-85.0511, -180], [85.0511, 180]);

    // Start at 1 (whole world) so fitBounds can pick the right opening zoom; the
    // floor is then pinned to that opening zoom below, so the map never zooms out
    // past the start view. Zoom in goes to street level (7).
    const map = L.map("geography-map", {
        zoomControl: true,
        minZoom: 1,
        maxZoom: 7,
        maxBounds: worldBounds,
        maxBoundsViscosity: 0.5,
    });

    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", {
        noWrap: true,
        bounds: worldBounds,
        attribution: "Tiles &copy; Esri",
    }).addTo(map);

    const { bounds: markerBounds, markers } = renderMarkers(map, traditions);

    // The map fills its grid cell via CSS; make sure Leaflet reads that height.
    map.invalidateSize();

    if (markerBounds) {
        // Start with every marker in view.
        map.fitBounds(markerBounds, { padding: [30, 30], animate: false });
    } else {
        map.setView([20, 15], 1);
    }

    // Pin the minimum zoom to the opening view so the user can zoom in but never
    // back out past the initial all-markers frame.
    map.setMinZoom(map.getZoom());

    const onResize = () => map.invalidateSize();
    window.addEventListener("resize", onResize);
    onCleanup(() => {
        window.removeEventListener("resize", onResize);
        map.remove();
    });

    return { map, markers };
}

function showGeographyError(message) {
    const map = document.getElementById("geography-map");
    if (map) map.innerHTML = `<div class="map-error">${escapeHtml(message)}</div>`;
}
