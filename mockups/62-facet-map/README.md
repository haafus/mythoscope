# 62 · Facet map

One world map, a facet switcher. The same set of Berezkin traditions is coloured by whichever
**tradition facet** you pick — the four axes of the converged taxonomy
([`tradition-taxonomy-final.md`](../../docs/proposals/tradition-taxonomy-final.md)) side by side on
the geography, so you can *see* how each cross-cuts the map.

Answers the open UI gap from `docs/reviews/2026-07-repo-review.md` **F7** (`family`/areal facet in the
data but not on any map) and gives `area`, `family`, `theme` and `subsistence` a single shared view.

## The four facets

- **Area · 12** — deterministic from `areal_path` (reuses mockup 21's `area_of`). Near-total coverage
  (4 traditions have an empty `areal_path`).
- **Family · 11** — from the language chain (reuses mockup 21's `family_of`): language seed + area
  fallback for ambiguous cases.
- **Narrative cluster · 16** — the dominant of mockup 41's 16 data-driven narrative clusters in a
  tradition's motif set (argmax of its narrative profile); only for traditions with ≥ 30 motifs.
  Berezkin's 13 hand themes were tried first but are useless as a facet — the *Adventures* catch-all
  is the argmax almost everywhere; the narrative clusters are balanced and vary across the map.
- **Subsistence · 4** — from D-PLACE, the nearest Ethnographic-Atlas society within 250 km (reuses
  mockup 22's `dplace_subsistence.json`).

Grey points have no value on the active facet.

## What it shows

- **`area` and `family` correlate but cross-cut.** One family spans several areas (Austronesian across
  Nusantara, Oceania, Madagascar; Amerindian across all four American areas), and one area holds several
  families — the visual case for keeping both as distinct axes.
- **`narrative` splits Old World vs New World.** The magic-wife / magic-flight complexes dominate Eurasia
  and Africa, while the monster-swallower complex dominates the Americas, Pacific rim and Australia — a
  divide the uniform Berezkin *Adventures* argmax hid completely.
- **`subsistence` tracks ecology**, not descent — horticulturalists across the tropics, agrarian states
  across Eurasia, foragers in Australia / boreal North America / Siberia, pastoralists in the steppe belt.

## Build & view

```
python mockups/62-facet-map/build_data.py   # writes data.js
```

Then open `index.html`. Equirectangular projection; where a tradition has no real coordinate the areal
sub-region centroid is used and co-located points are spread.
