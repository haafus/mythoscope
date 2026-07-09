# 35 · Historical corridors (roadmap M35)

The **human, dated** contact channel: do **historical empires** move motifs across macro-area
boundaries? Two traditions are linked if they were **co-members of the same multi-area empire**
at some date. A *distinct* mechanism from M34 (dated contact as a covariate, not a distance
metric); run at lowered priority after M34's resistance-distance gate failed, and led — per the
roadmap — by the cheap **overlap audit** first.

Data: `aourednik/historical-basemaps` (dated political boundaries, GeoJSON, CC-BY-SA), four
pre-colonial snapshots (**bc1, 1000, 1279, 1500** — Rome/Han → Byzantine/Caliphate/Song → Mongol
→ Ottoman/Ming). Point-in-polygon is ray-casting (no shapely).

## Two honest scoping decisions

1. **Colonial snapshots excluded** (1715/1880) — they blanket the globe administratively (the
   British Empire links India↔Australia), which is not a folk-motif corridor.
2. **historical-basemaps tessellates the world** (every point is in *some* named region, including
   culture-region catch-alls like "Manioc farmers"/"Aboriginal Australians"), so raw "in a polity"
   ≈ always (90%, meaningless). A real corridor is a polity spanning **≥ 3 macro-areas** — the
   filter that keeps Rome, the Mongol khanates, Han, Ming and drops the tessellation cells.

## What it shows

- **Overlap audit — only ~32 % of traditions were ever in a real multi-area empire.** Strongly
  **Old-World / Mongol-belt biased** (Eurasia/Africa ~40–54 %; **South America 0 %, Aboriginal
  Australia 0 %, Oceania 1 %**) — small-scale societies sit *outside* the great empires, exactly
  the coverage bias the roadmap predicted.
- **Globally, empire co-membership adds little** — ΔR²(Jaccard) over great-circle **+ area** is
  only **+0.011** (mostly redundant with distance and area).
- **But the sharp cross-area test is positive.** Between traditions in **different** macro-areas,
  sharing an empire raises mean motif-Jaccard **0.088 vs 0.034 (×2.6)**; even **matched on
  distance**, **0.090 vs 0.061 (+0.029)**. Rome and the Mongol world genuinely carried motifs
  *across* area boundaries — a real corridor, not a proximity artifact. Top empires by reach:
  Roman Empire, Great Khanate, Chagatai Khanate, Golden Horde, Han, Ming.

## Verdict

A **weak but real corridor** — unlike M34's clean negative. Empires moved motifs across areas,
but the effect is **scoped to the empire belt** (~32 % of traditions) and nearly redundant with
distance + area in aggregate. So for the capstone (**M38**), empire co-membership is a **narrow
dated covariate for the Old-World belt, not a general axis.**

**Honest limits.** A couple of top rows are still culture-region labels (Khoisan,
"Desert hunter-gatherers") that span ≥ 3 areas via broad polygons, not empires; **trade routes
(OWTRAD)** — which would add non-imperial Silk-Road / Indian-Ocean edges — are not yet wired.

## Run

```bash
python mockups/35-historical-corridors/build_data.py   # writes data.js; downloads snapshots (~5 MB, cached)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/35-historical-corridors/
```

`data.js` and the `world_*.geojson` snapshots are git-ignored; `land.js` is committed.
