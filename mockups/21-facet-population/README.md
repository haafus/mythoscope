# 21 · Deterministic facet population

Answers a build question, not a research one: **does the deterministic population recipe
in [`macro-area-facets.md`](../../docs/proposals/macro-area-facets.md) actually
cover the whole corpus** before it becomes `region_facets.py`? Runs the three deterministic
facet functions over all 1046 traditions and 3488 motifs and reports coverage + shape.

## What it runs

- **`area(areal_path)` — 12 macro-areas.** A pure function of `areal_path[0]` with a few
  `areal_path[1]` reassignments for the 4 macros that straddle two areas (Western-Europe/
  North-Africa, SW-&-Central-Asia/Aryan-India, Tibet/SE-Asia, NA-North-&-West). Covers
  **1042 / 1046**; the 4 misses are traditions with an **empty `areal_path`** (Bhuiya,
  Dobruja Turks, …) — a data gap, not a recipe gap.
- **`theme(motif_group_num)` — category A/B + 13 groups.** Covers **3347 / 3488**; the 141
  misses have no `motif_group_num` in the source. Confirms the corpus shape: adventures
  (1243) and tricks (620) dominate, Category B outnumbers A overall (1924 vs 1423).
- **`family(language[0])` — the linguistic seed of the 11 culture families.** 90% resolve
  directly from `language[0]`; +9% by area-fallback for ambiguous families (Afroasiatic →
  Abrahamic vs Sub-Saharan by area; Caucasian; New-World isolates). The remaining **10 are
  linguistic isolates** (Ainu, Andamanese, Basque, Burushaski, Elamite, Nivkh, Sumerian)
  that have no family bucket and need per-case curation.

## The honest part

`family` is where the recipe is *not* fully deterministic. The four **religion-overlay**
families — Abrahamic, Islamicate, Indic/Dharmic, Sinic — are cultural, not linguistic, and
`berezkin.json` carries no religion field, so here they are **approximated** from language
+ area (e.g. Semitic Afroasiatic in the Near East → Abrahamic; North-Caucasian → Islamicate).
Every assignment is tagged **`seed`** (direct from language) or **`area-fallback`** (resolved
by area) so the approximate ones are visible. Productionising `family` means a small curated
religion overlay on top of this seed — exactly the ~dozens of rows the proposal predicted.

## Takeaway

`area` and `theme` are production-ready deterministic functions today (100% modulo data
gaps). `family` needs one curated overlay file; its linguistic seed already covers 99% and
this mockup shows precisely which rows the overlay must touch.

## Run

```bash
python mockups/21-facet-population/build_data.py   # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/21-facet-population/
```

`data.js` is git-ignored.
