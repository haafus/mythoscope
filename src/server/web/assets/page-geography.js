import { app, state, api, escapeHtml, escapeAttribute, loadTraditionInfo } from "./core.js";
import { renderTraditionList } from "./tradition-list.js";

export async function renderGeography() {
    document.title = "MythoScope - Geography";
    app.innerHTML = `
        <main class="geography-page container">
            <div class="geo-workspace">
                <aside class="library-sidebar">
                    <div id="geographyTraditions">Loading...</div>
                </aside>
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
        const markers = initializeGeographyMap(traditions);

        const listEl = document.getElementById("geographyTraditions");
        listEl.addEventListener("tradition-select", (event) => {
            const map = state.geographyMap;
            if (!map) return;
            const name = event.detail.tradition;
            if (!name) { map.closePopup(); return; }
            const marker = markers.get(name);
            if (!marker) return;
            map.flyTo(marker.getLatLng(), Math.max(map.getZoom(), 4), { duration: 0.6 });
            marker.openPopup();
        });
        await renderTraditionList(listEl);
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
        ? item.books.map((book) => {
            const href = `#/corpus?title=${encodeURIComponent(book)}&tradition=${encodeURIComponent(item.name)}`;
            return `<li><a class="popup-book-link" href="${escapeAttribute(href)}">${escapeHtml(book)}</a></li>`;
        }).join("")
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
    const markers = new Map();
    const groups = buildCoordinateGroups(traditions);

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
                    closeButton: true,
                    maxWidth: 340,
                });

            markers.set(item.name, marker);
            bounds.push(position);
        });
    });

    return { bounds: bounds.length ? L.latLngBounds(bounds) : null, markers };
}

function initializeGeographyMap(traditions) {
    // Real tile-covered world: ±180° longitude and the web-mercator latitude limit.
    // The previous ±240° bounds reached 60° past the tiles on each side, which
    // showed up as gray bands beyond the map.
    const worldBounds = L.latLngBounds([-85.0511, -180], [85.0511, 180]);

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

    const { bounds: markerBounds, markers } = renderMarkers(map, traditions);
    const fitPadding = L.point(34, 34);

    // Min zoom is the lower of "tiles fill the container" and "all markers fit",
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
    // The map fills its grid cell via CSS; make sure Leaflet reads that height.
    map.invalidateSize();
    recomputeMinZoom();

    if (markerBounds) {
        map.fitBounds(markerBounds, { padding: [34, 34], maxZoom: 4 });
    } else {
        map.setView([20, 15], map.getMinZoom());
    }

    state.geographyResizeHandler = () => { map.invalidateSize(); recomputeMinZoom(); };
    window.addEventListener("resize", state.geographyResizeHandler);

    return markers;
}

function showGeographyError(message) {
    const map = document.getElementById("geography-map");
    if (map) map.innerHTML = `<div class="map-error">${escapeHtml(message)}</div>`;
}
