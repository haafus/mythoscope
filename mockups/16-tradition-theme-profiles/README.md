# 16 · Tradition thematic profiles

Tests the idea (from
[`macro-area-facets.md`](../../docs/motifs/proposals/macro-area-facets.md) —
`tradition.theme_profile`) that a tradition's **genre balance** is a signal.

Each Berezkin tradition becomes a **13-dim vector** — the proportion of its attested
motifs falling in each of the 13 thematic groups. Traditions with ≥30 motifs (840 of
them) are clustered **by that profile alone** (k-means, k=8, no geography, no language),
then plotted on the world map coloured by cluster.

## What it shows

- **38%** of the variance in `theme_profile` is explained by macro-area — a strong
  regional signal — yet **62% is orthogonal** to geography, so the profile carries its
  own information.
- The clusters mix region and worldview: a trickster-heavy African profile, a
  märchen/adventure Eurasian one (53% adventures), an adventure+cosmology
  North-American/Beringian one, and a **cosmology-heavy cluster that groups
  Mesoamerica–Andes with Tibet/SE-Asia and Ancient Greece / Indian literary** — a
  cross-continental worldview affinity pure geography or language would miss.

## Caveat

Raw proportions are confounded by **attestation intensity** (a densely catalogued
corpus reflects what was recorded). For analysis use the bias-corrected weights of
[`stratum-derivation.md`](../../docs/motifs/proposals/stratum-derivation.md) §5; here
the raw profile is enough to show the signal exists.

## Run

```bash
python mockups/16-tradition-theme-profiles/build_data.py   # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/16-tradition-theme-profiles/
```

`data.js` is git-ignored. Coordinates come from the committed `tradition-coords.json`
snapshot; where a tradition has none, its areal-subregion centroid is used and the points
are spread so they don't pile up. (Coordinates only place the map dots — the clustering
and the 38% variance-by-macro are computed on theme profiles, so they are unaffected.)
