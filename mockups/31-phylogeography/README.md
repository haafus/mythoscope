# 31 · Phylogeography (roadmap M31)

The etiology-stage **capstone**: for the descent motifs that mockup 30 could date, reconstruct
each one's **origin** — a location *and* an age — and show its spread over the map.

- **Age** = the family-expansion date from mockup 30 (a ceiling — no older than the family root).
- **Location** = the ancestral-location **point estimate** = the spherical centroid of the
  motif's attesting traditions *within its dated family* (the homeland-foothold centre). This
  is the mean of what a full Bayesian relaxed-random-walk over a dated tree would reconstruct
  at the origin node.

Only the inherited, family-concentrated minority (451 motifs) is placed; the areal majority
has no single origin to reconstruct — its history is diffusion (mockup 19).

## What it shows

- **451 descent-motif origins on one map**, coloured by age (1500–9000 BP). They cluster
  densely in **Europe** — the Indo-European märchen belt (~5500 BP), the largest dated set —
  and scatter across N-America, Siberia, Oceania, Sub-Saharan Africa.
- **B4 (fished-out earth)** centres in **Western Oceania**, age ceiling the **Austronesian
  expansion ≤ 5200 BP**; select it to draw its spread lines fanning across the Pacific and out
  to its stray Eurasian/African/American occurrences — a maritime diffusion picture. (The
  famous Māui "fishing up the land" motif, placed and dated.)

## Re-centring — Pacific motifs are not split by the Atlantic seam

An Atlantic-centred equirectangular map puts its seam through the Pacific, so a
Pacific-diffusion motif like B4 gets torn across both edges and its spread into the Americas
*looks* like it goes the wrong way (through Eurasia). Fix: when a motif is selected the map
**re-centres on that motif's own region** — the central meridian `lon0` is the **circular mean
longitude** of its origin + attesting traditions — and the coastline is drawn as three shifted
copies so the world stays continuous under the shift. B4 then sits whole in the middle and its
spread to America reads correctly as **circum-Pacific** (eastward around the ocean), not
overland through Eurasia. The default "all origins" view keeps `lon0 = 0` (Atlantic-centred).

## Honest limits — what it is *not*

This is a **family-resolution proxy**: the location is the range centre and the age is the
family-root ceiling — they are **not the same, node-consistent ancestral node** (B4's Oceanic
range is younger than the 5200 BP Austronesian root). Node-consistent location + age with an
**uncertainty cloud** is what a real **relaxed-random-walk (BEAST)** on a genuinely dated tree
gives; that stays future work. Here we show the point estimate such an RRW converges to on
average. Spread lines are drawn the short way in the (re-centred) frame — no clipping.

## Run

```bash
python mockups/31-phylogeography/build_data.py   # writes data.js (~8 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/31-phylogeography/
```

`data.js` is git-ignored; reads `outputs/motifs/` + mockup 30's committed `glottolog_join.json`;
`land.js` (shared world path) is committed.
