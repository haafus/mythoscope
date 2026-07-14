# 63 · Age vs connectivity — where the two axes diverge

The "old regions have deeper mythology" claim (mockups 17 / 39 / 62's `depth` × `peopling`) conflates
two things that usually travel together but need not:

- **age** — when anatomically modern humans first settled the macro-area (ky BP);
- **connectivity** — how embedded the area is in the Old-World diffusion network.

They correlate only weakly, so most regions sit *off* the diagonal. This map colours each region by the
**gap between the two axes**, which is exactly where the natural experiments live: an old-but-isolated
region (Australia) tests whether depth needs *age*; a connected-but-young region (the Old-World hub)
tests whether it needs *connectivity*.

## How connectivity is measured (reproducibly, without myth data)

`connectivity` is a purely geographic proxy — **between-region centrality**:

1. each area's spherical centroid is computed from its traditions' coordinates
   (`mockups/tradition-coords.json`);
2. centrality = Σ over the *other* area centroids of `exp(-great_circle / 4000 km)`.

Central landmasses (Near East, Central Asia) score high; terminal peripheries (Australia, South
America) score low. Two proxies were tried and rejected before this one:

- a **hand-coded** embeddedness scale — transparent but a subjective judgement, so not reproducible;
- a **gravity count of nearby traditions** — dominated by *cataloguing density* (it crowned North
  America "most connected" simply because Berezkin subdivides the Americas finely), measuring the
  ethnographic record rather than diffusion.

Between-region centrality removes the within-area sampling density and is the honest reproducible
version. Under it `age` and `connectivity` are essentially independent (r ≈ +0.14 across 12 areas).

## The gap

`gap = z(connectivity) − z(age)`:

- **gap < 0 — old but isolated** (age exceeds connectivity): Sub-Saharan Africa (−2.83), Aboriginal
  Australia (−2.37), Austronesia & Oceania (−0.68). These are the regions that break the age→depth
  story: old, yet mythologically shallow on the `depth` map, because they were cut off from the
  diffusion network.
- **gap > 0 — connected but young** (connectivity exceeds age): the Old-World hub — Near East (+0.72),
  Europe (+0.69), Iran/C. & S. Asia (+0.58) — is maximally central at a settlement age of only 42–45 ky.
- **gap ≈ 0 — the axes agree**, so the region tells us nothing about which axis drives depth.

### The Bering caveat

Pure geometry files **both Americas** under "connected" — by straight-line distance they are not that
far from Eurasia. Historically they sit behind the Beringian ice/water bottleneck, a barrier that
great-circle distance cannot see (the same blind spot as Australia, except Australia's gap is so large
that distance still catches it). So the *reliable* "connected but young" group is the Old-World hub, not
the New World; the New-World rows are flagged in the table as a geometry artefact.

## What it shows

The off-diagonal regions line up on one side of the argument: the old-but-isolated group (Australia
above all) is old yet shallow, and the connected hub is young yet deep. Both point the same way —
**depth follows embeddedness in the diffusion network, not settlement age alone** — consistent with the
breadth → cross-macro-span collapse (+0.79 → +0.07) and the failed within-family Galton permutation for
`depth × peopling`.

## Build & view

```
python mockups/63-age-connectivity-gap/build_data.py   # writes data.js
```

Then open `index.html`. Equirectangular projection; each tradition point is coloured by its
macro-area's gap on a ColorBrewer RdBu diverging ramp (blue = old & isolated, red = connected & young,
near-white midpoint recedes into the ocean). Regions with |gap| ≥ 0.6 are labelled.
