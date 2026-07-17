# ADR: map palette and projection

- **Status:** accepted (with one open sub-decision, §2.3)
- **Date:** 2026-07-16
- **Scope:** how region maps are coloured and projected across the mockups (esp. 62) and the app Atlas.
- **Supersedes/extends:** the palette canon in [`regions.md`](../regions.md) §8 remains
  authoritative for the *values*; this ADR records the *reasoning* behind palette and projection choices and
  the decisions that have no other home (projection, basemap tiles, presentation constants).

Cross-refs: [`regions.md`](../regions.md) §8 (palette table),
[`../reviews/archive/color-system-review.md`](../../reviews/archive/color-system-review.md),
[`tradition-architecture-unified.md`](../tradition-architecture-unified.md) §3.

---

## 1. Context

The 14-region canon needs one visual identity that reads the same in every view (region map, atlas, motif
bars). Two questions recur and had no recorded decision: **which palette** and **which map projection** — and
the two are coupled to a third, **which basemap tiles** (tiles only exist for one projection).

---

## 2. Palette

### 2.1 Decision — CARTOColors **Prism** is the canon

The 14-region palette is built on **CARTOColors Prism**, a cartographer-designed, CVD-validated qualitative
palette, laid spectrally along the out-of-Africa arc with three hand-tuned swaps for New-World / Pacific
legibility. Full table and per-region `base`/`light`/`dark` ramp ends live in `regions.md` §8. **Colour carries
the sequence; borders + labels carry the neighbour distinction** (per-pair contrast is deliberately not
maximised).

Rationale: Prism is punchy, validated for colour-blind separation, and cartographer-designed; it distinguishes
14 adjacent regions better than any associative scheme we tried.

### 2.2 Rejected as canon — the "intuitive" (associative) palette

We explored an **associative** palette keyed to imagery anchors: ochre = Aboriginal Australia (the anchor),
saffron = South Asia, imperial vermilion = East Asia, Amazon emerald = Lowland S. America, Pacific cyan =
Austronesia, Persian rose = Caucasus & Iran, glacial = Circumpolar, El Dorado gold = Mesoamerica, desert sand
= Near East, temperate-forest green = Europe, laterite = Sub-Saharan Africa, jade = Mainland SE Asia,
Tengri-blue = Inner Asia, SW turquoise = Native N. America.

**Not adopted as the canon.** A fully associative 14-region palette cannot hold: associations cluster (many
"jungle greens", many "water/sky blues") and collide, contrast drops (pale sand / ice wash out against the
ocean), and it fails the CVD-separation bar Prism passes. It works as a moodboard, not as a reference map that
must separate 14 regions fast.

**Retained as an optional view.** The intuitive palette ships as a selectable variant in mockup 62
(`Regions · Winkel (intuitive)`, `Regions · equirect (intuitive)`), not as the product default. Adjustments
made while exploring it (kept with the variant, not promoted to canon):
- **Circumpolar** deepened `#9DB9C9 → #5F86A6` — the pale ice merged with the ocean fill under the 0.35
  overlay.

### 2.3 Open sub-decision — Near East vs Mesoamerica in the intuitive palette

In the intuitive palette both Near East (`#E0B45E`, desert sand) and Mesoamerica (`#C99A2E`, El Dorado gold)
are gold and read as one. Resolution direction: **keep Near East at its sand `#E0B45E`** (deepening it merged
it with terracotta Sub-Saharan Africa) and **move Mesoamerica deeper** — candidates **`#B67B22`** (bronze,
maximal separation) or **`#C6851C`** (amber). Mesoamerica's anchor stays *gold* (Inca/El Dorado metalwork);
jade / turquoise / cochineal / Maya-blue were rejected because green/turquoise/red/blue are taken by adjacent
regions. **Final pick pending; canon (Prism) is unaffected either way.**

---

## 3. Projection

### 3.1 Decision — equirectangular is the engine default; Winkel Tripel is the atlas-style view

- **Our SVG map engine stays equirectangular (Plate Carrée):** `x = lon`, `y = lat`, linear. Simple, exact,
  and every baked path is already in this space. Its cost is horizontal polar stretch.
- **Winkel Tripel** (National Geographic's standard, computed from the same lon/lat) is offered as an
  **atlas-style view** in mockup 62 — a balanced compromise projection without the polar stretch. Region areas,
  coastline, graticule, and tradition points are all reprojected and fitted into the same `0 0 360 180` canvas
  so the existing zoom/pan keep working.
- **Equal Earth / Mollweide / Robinson** were considered (equal-area / compromise) but not wired in; Winkel
  covers the "atlas look" need.

### 3.2 The tiles ↔ projection coupling (the constraint that drives §4)

Raster world-tile basemaps exist **only in Web Mercator (EPSG:3857)**. Therefore:

| Want | Basemap available |
|---|---|
| A raster basemap under the map | **Web Mercator only** (polar area distortion) |
| equirectangular / Winkel / Equal Earth | **no tiles** — vector-only: our own coastline + ocean fill |
| a "globe" | vector tiles reprojected client-side (MapLibre globe) |

So a light tiled basemap and a non-stretched projection are **mutually exclusive**. Where tiles matter (the
Atlas) we accept Web Mercator; where the projection matters (thematic region maps) we draw our own coastline
and skip tiles.

---

## 4. Basemap tiles (Atlas)

- **Decision:** the Atlas basemap is **CARTO Positron** (`light_all`), replacing Esri World Topo. Positron's
  flat, near-white land stops the busy topography from fighting the flat region fills. It is Web Mercator (the
  Atlas is already Mercator), so the region overlay and markers were unaffected.
- Positron exists **only** in EPSG:3857 raster (and as vector tiles via MapLibre) — not in 4326 / Winkel /
  Equal Earth. This is the §3.2 constraint in practice.
- **Ocean/background colour is `#d4dadc`** — sampled directly from a Positron water tile (`light_all/3/1/3`;
  land/paper is `#fafaf8`). The Atlas map-frame + Leaflet letterbox were set to `#d4dadc` so there is no seam.

---

## 5. Presentation constants (thematic region maps, mockup 62)

- **Ocean fill `#eef3f4`** (the mockup ocean), clipped to the **projection envelope** (pole lines + ±180°
  meridians) — never a full-canvas rect, so Winkel corners and equirect margins stay clean.
- **Page behind the map `#ffffff`** in the app card (mockup canvas is white); the standalone previews use the
  mockup beige `#f4f1ea`.
- **Antarctica `#ffffff`** (ice), split from the coastline by latitude (south of −60°) so it can be painted
  white without a doubled edge.
- **Graticule** every 30° (`#9fb0bb`; the ±180°/±90° frame slightly stronger).
- **Tradition points shade exactly like the Regions facet:** `mix(color, dark, 1/3)`. The Prism views reuse
  the hand-tuned `REGION_DARK`; the intuitive views get a synthesised dark (`L×0.62, S×1.12` in HLS) of
  matching depth. (Base-brightness points were tried and are not the default.)

---

## 6. Consequences

- One canon palette (Prism) everywhere; the associative palette is a documented, selectable alternative, not a
  fork of the canon.
- The Atlas is Web Mercator by necessity (tiles); thematic maps can use equirectangular or Winkel because they
  carry their own coastline.
- §2.3 (intuitive Near East/Mesoamerica) is the only open item; it does not touch the Prism canon.
- If the palette is ever moved to the derived area-gradient of
  [`tradition-architecture-unified.md`](../tradition-architecture-unified.md) §3, this
  ADR and `regions.md` §8 are the two documents to revise together.
