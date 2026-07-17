# 23 · Theme × geography

Visualises the **theme × area signal** that
[`macro-area-facets.md`](../../docs/proposals/archive/macro-area-facets.md) only states in
prose ("Category B is 74–77% of European attestations but 27% in Mesoamerica–Andes";
"cosmology is pan-global, tales are regional"). Four views over the Berezkin catalogue.

## 1 · Heatmap — 13 theme groups × 12 macro-areas

Cell colour is **lift** = observed ÷ expected attestations under independence (1.0 =
neutral; warm = over-represented, cool = under); the number is the theme's **share within
that area**. Lift, not raw share, is the right normalisation — Adventures is the largest
block everywhere, so only lift shows it is genuinely *concentrated* in the Eurasian belt
(Europe / Near East / Iran ≈ ×1.2) and *depleted* in the Americas–Pacific (Mesoamerica
×0.5, Australia ×0.3), while celestial cosmology inverts (Sun & Moon ×3.4 in Australia,
×3.1 in Mesoamerica).

## 2 · Co-occurrence matrix — theme × theme

How the 13 blocks co-vary **across traditions**: the correlation of theme shares, on the
**CLR (centered-log-ratio) transform** so the constant-sum closure of a profile doesn't make
the dominant blocks spuriously anti-correlate with everything. Rows/cols are **seriated**
(hierarchical clustering + optimal leaf ordering) so co-occurring blocks sit adjacent. Two
contiguous blocks fall out — a tales block (Adventures · Tricks · Proper names · Formulae ·
Protagonist identity, with Monstrous beings adjoining) and a cosmology block (Sun & Moon ·
Cosmogony · Origin of humans · subsistence · Stars) — with a strong negative rectangle
between them (Cosmogony × Adventures ≈ −0.6). **That recovers Berezkin's Category A vs B
split from co-occurrence alone**, without using his labels.

## 3 · Co-cluster map — traditions × themes (mockup-15 style)

The traditions-×-themes analogue of mockup 15's traditions-×-motifs biclusters:
**SpectralCoclustering** on the tradition × 13-theme proportion matrix groups traditions
*together with* the theme blocks that define them, drawn as filled **footprint blobs**
(one contour per dense region, so a globally-spread cluster shows several regional shapes).
Hover a legend row to isolate one cluster. The seven that fall out are readable worldviews:

- **Adventures** — the Eurasian märchen belt (Europe · Near East · Iran/C/S Asia).
- **Tricks & competitions · Proper names** — the trickster zone (Sub-Saharan Africa ·
  East/SE Asia · N-America).
- **Sun & Moon · Cosmogony** — celestial cosmology (Mesoamerica–Andes · Oceania · E/SE Asia).
- **Plants & animals · Monstrous beings** — etiological (N & W N-America · Siberia · S-America).
- **Origin of humans · subsistence**, **Stars · Formulae**, **Origin of death · Protagonist**.

## 4 · Theme picker

Pick any of the 13 groups and the map shades each tradition by that theme's share of its
corpus (sequential), with the top over-represented areas (by lift) listed below. Makes the
per-block geography directly legible one theme at a time.

## Takeaway

The signal is real and strong: theme is far from uniform over the map. Adventures/tricks
concentrate in the Old-World literate/oral belts, celestial and etiological cosmology in
the Americas–Pacific and the boreal north — the same `theme × area` structure that the
`theme_profile` clustering (mockup 16) found (38% of profile variance is macro-area), here
resolved to the individual block. This is a *systematics* view (stage 3): it maps the space;
it does not date it — that is `stratum` (stage 4).

## Run

```bash
python mockups/23-theme-geography/build_data.py   # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/23-theme-geography/
```

`data.js` is git-ignored; `land.js` (shared world path, copied from mockup 15) is committed.
Coordinates come from the `tradition-coords.json` snapshot.
