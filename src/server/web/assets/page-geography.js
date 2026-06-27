import { app, state, api, escapeHtml, escapeAttribute, loadTraditionInfo } from "./core.js";

export async function renderGeography() {
    document.title = "MythoScope - Geography";
    app.innerHTML = `
        <main class="geography-page container">
            <div class="map-frame">
                <div id="geography-map"></div>
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
    const books = item.books.length
        ? item.books.map((book) => `<li>${escapeHtml(book)}</li>`).join("")
        : "<li>No books listed</li>";

    return `
        <div class="popup-title">
            <span class="popup-color" style="background:${escapeAttribute(item.color)}"></span>
            <span>${escapeHtml(item.name)}</span>
        </div>
        <div class="popup-description">${escapeHtml(item.description)}</div>
        <div class="popup-books-title">Books</div>
        <ul class="popup-books">${books}</ul>
    `;
}

function createMarkerIcon(item) {
    return L.divIcon({
        className: "tradition-marker",
        html: `<button class="map-point" type="button" style="--point-color:${escapeAttribute(item.color)}" aria-label="${escapeAttribute(item.name)}"></button>`,
        iconSize: [18, 18],
        iconAnchor: [9, 9],
        popupAnchor: [0, -11],
    });
}

function renderMarkers(map, traditions) {
    const bounds = [];
    const groups = buildCoordinateGroups(traditions);

    groups.forEach((group) => {
        group.forEach((item, index) => {
            const position = getOffsetCoordinate(item, index, group.length);

            L.marker(position, {
                icon: createMarkerIcon(item),
                keyboard: true,
                title: item.name,
            })
                .addTo(map)
                .bindPopup(buildPopupHtml(item), {
                    className: "tradition-popup",
                    closeButton: true,
                    maxWidth: 340,
                });

            bounds.push(position);
        });
    });

    return bounds.length ? L.latLngBounds(bounds) : null;
}

function initializeGeographyMap(traditions) {
    // Real tile-covered world: ±180° longitude and the web-mercator latitude limit.
    // The previous ±240° bounds reached 60° past the tiles on each side, which
    // showed up as gray bands beyond the map.
    const worldBounds = L.latLngBounds([-85.0511, -180], [85.0511, 180]);
    const frame = document.getElementById("geography-map").parentElement;

    // Grow the map to fill the viewport, leaving a 20px gap to the window edges.
    const sizeFrame = () => {
        const top = frame.getBoundingClientRect().top;
        frame.style.height = `${Math.max(320, window.innerHeight - top - 20)}px`;
    };
    sizeFrame(); // size before the map reads its container

    const map = L.map("geography-map", {
        zoomControl: true,
        maxZoom: 7,
        maxBounds: worldBounds,
        maxBoundsViscosity: 1.0,
    });
    state.geographyMap = map;

    L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Topo_Map/MapServer/tile/{z}/{y}/{x}", {
        noWrap: true,
        bounds: worldBounds,
        attribution: "Tiles &copy; Esri",
    }).addTo(map);

    const markerBounds = renderMarkers(map, traditions);
    const fitPadding = L.point(34, 34);

    // Min zoom: the lower of "tiles fill the container" and "all markers fit",
    // so every marker stays reachable without needless gray margins.
    function recomputeMinZoom() {
        const fillZoom = map.getBoundsZoom(worldBounds, true);
        const markerZoom = markerBounds
            ? map.getBoundsZoom(markerBounds, false, fitPadding)
            : fillZoom;
        const minZoom = Math.min(fillZoom, markerZoom);
        map.setMinZoom(minZoom);
        if (map.getZoom() < minZoom) map.setZoom(minZoom);
    }

    recomputeMinZoom();
    if (markerBounds) {
        map.fitBounds(markerBounds, { padding: [34, 34], maxZoom: 4 });
    } else {
        map.setView([20, 15], map.getMinZoom());
    }

    state.geographyResizeHandler = () => { sizeFrame(); map.invalidateSize(); recomputeMinZoom(); };
    window.addEventListener("resize", state.geographyResizeHandler);
}

function showGeographyError(message) {
    const map = document.getElementById("geography-map");
    if (map) map.innerHTML = `<div class="map-error">${escapeHtml(message)}</div>`;
}
