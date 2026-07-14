# 62 · Facet map

One world map, a facet switcher. The same set of Berezkin traditions is coloured by whichever
**tradition facet** you pick — the four axes of the converged taxonomy
([`tradition-taxonomy-final.md`](../../docs/proposals/tradition-taxonomy-final.md)) side by side on
the geography, so you can *see* how each cross-cuts the map.

Answers the open UI gap from `docs/reviews/2026-07-repo-review.md` **F7** (`family`/areal facet in the
data but not on any map) and gives `area`, `family`, `theme` and `subsistence` a single shared view.

## The six facets

- **Area · 12** — deterministic from `areal_path` (reuses mockup 21's `area_of`). Near-total coverage
  (4 traditions have an empty `areal_path`).
- **Family · 11** — from the language chain (reuses mockup 21's `family_of`): language seed + area
  fallback for ambiguous cases.
- **Narrative profile cluster · 8** — traditions *clustered by their thematic composition* (KMeans
  k=8 over the 16-dim narrative profile of mockup 41, the mockup-43 move), not coloured by a single
  dominant group. Each cluster is named by the two narrative complexes it most over-represents vs the
  global average. Only traditions with ≥ 30 motifs are clustered. (A dominant-group facet was tried
  first but is useless — Berezkin's *Adventures* catch-all wins almost everywhere, and even the
  narrative argmax is lopsided.)
- **Subsistence · 4** — from D-PLACE, the nearest Ethnographic-Atlas society within 250 km (reuses
  mockup 22's `dplace_subsistence.json`).
- **Motif diversity · β** — *continuous*: β-turnover (γ/α) per macro-area from mockup 52, broadcast to
  its traditions on a blue→red scale. α (per-tradition richness) is a cataloguing-effort artefact, so β
  is used — low = a homogeneous shared stock (diffusion belt), high = internally divergent traditions.
- **Tradition depth · mean rank** — *continuous*: the mean **depth-rank** of a tradition's motifs. A
  motif's depth = its breadth (# attesting traditions, mockup 17); breadth is heavy-tailed, so each
  motif's breadth is first turned into a 0–1 percentile and then averaged over the tradition — a robust
  "average depth" that a raw mean of breadth (swamped by a few pan-global motifs, and unbounded) is not.
  Deeper = older / broader motif stock. (Deep-*share* — fraction in the top-15% tier, mockup 39 — is the
  compositional alternative; mean-rank keeps the full gradient.)

Grey points have no value on the active facet.

## What it shows

- **`area` and `family` correlate but cross-cut.** One family spans several areas (Austronesian across
  Nusantara, Oceania, Madagascar; Amerindian across all four American areas), and one area holds several
  families — the visual case for keeping both as distinct axes.
- **`narrative` clusters cross-cut geography.** The 8 profile clusters group cultures by the genre balance
  of their corpus, and some span continents (a magic-wife/ogre cluster across Eurasia–Africa, a
  monster-swallower/miraculous-birth cluster across the Americas and Pacific) — the point of clustering by
  composition rather than by location.
- **`subsistence` tracks ecology**, not descent — horticulturalists across the tropics, agrarian states
  across Eurasia, foragers in Australia / boreal North America / Siberia, pastoralists in the steppe belt.

## Build & view

```
python mockups/62-facet-map/build_data.py   # writes data.js
```

Then open `index.html`. Equirectangular projection; where a tradition has no real coordinate the areal
sub-region centroid is used and co-located points are spread.
