# The tradition taxonomy we converged on (one-page reference)

A single orientation point for "how are traditions and macro-areas classified?" — the model, the role of
each facet, the settled vocabularies, where to see it applied, and its production status. Distils
[`macro-area-facets.md`](macro-area-facets.md), the adequacy audit (mockup 32), and Element ch. 5 / 8.

## The one thing that changed

There is **no single "major-tradition" hierarchy**. A tradition is described by **several facets at once**,
and time-depth is a property of the **motif**, not the tradition (one tradition carries motifs of many
strata). So the answer is a **multi-entity, multi-facet model**, not a tree.

| Entity | Facets / properties |
|---|---|
| **Tradition** | `area` (12 macro-areas, geographic) · `family` (~11, language/religion) · `subsistence` (4, economy) · `theme_profile` (13-dim genre balance, or the 16-dim narrative variant) |
| **Motif** | `theme` (Berezkin A/B → 13 groups — the primary analytical axis) · `stratum` (7, time-depth, **derived from distribution**) |
| **Attestation** (motif × tradition) | bare presence — the raw material `stratum` is inferred from |

Expressiveness is **multiplicative and cross-entity**: `area × family × subsistence` (≈ 12 × 10 × 4) per
tradition, each motif carrying its `theme` + `stratum`; analysis fixes a `theme` first, then groups by the
tradition axes. That is why no single axis has to be fine-grained.

## Facet roles — necessary, sufficient, optimal (audit: mockup 32, 910 traditions)

The four facets are **not co-equal**, and the set is **not complete**:

- **Load-bearing (necessary):** `area` (unique ΔR² = 0.08) and `theme_profile` (ΔR² = 0.13) carry the real
  unique signal in motif-set similarity.
- **`family` — keep, but not as a motif predictor** (unique ΔR² ≈ 0.01; collinear with area, Cramér's
  V = 0.73). Its job is the **descent backbone** — the tree behind Method B, dating, and ancestral-state
  reconstruction.
- **`subsistence` — targeted covariate only** for the ecology→theme gradient (survived the Galton test,
  mockup 25). Weakest and only external/noisy facet (D-PLACE join) — the **drop-candidate** if that
  hypothesis fails.
- **Optimal granularity: 12 areas / 11 families** beat both coarser and finer partitions (finer overfit).
  This is why an earlier 18-area draft collapsed to 12.
- **Not sufficient alone.** The four facets recover only **~36 %** of motif similarity; the **~64 %**
  residual is cross-continental convergence (contact + deep homology) no facet captures. The taxonomy
  therefore *gains* a fifth axis — **connectivity** (resistance-distance + historical corridors, roadmap
  M34/M35) — and a derived per-tradition **stratum-stack** (M39).
- **The best theme facet is data-driven, not hand-made.** The narrative classification (16 clusters,
  mockup 41) strictly beats Berezkin's 13 hand themes on the Jaccard-ΔR² test (0.125, mockup 42). The
  conclusion (Element ch. 8) is **two orthogonal theme axes** — etiological (best for reading geography)
  and narrative (best for describing a tradition) — a two-facet representation, not a replacement.

## The settled vocabularies

**`area` — 12 macro-areas** (derived deterministically from Berezkin's 16 via `areal_path`):
Europe · Near East & North Africa · Iran, Central & South Asia · East & Mainland SE Asia · Austronesia &
Oceania · Siberia & Arctic–Beringia · Northern & Western North America · Eastern North America ·
Mesoamerica & Central Andes · South America · Sub-Saharan Africa · Aboriginal Australia.

**`family` — ~11** (language seed + religion overlay for literate civilisations): Indo-European · Abrahamic ·
Indic/Dharmic · Sinic · Islamicate · Uralic & Altaic · Circumpolar/Palaeo-Asiatic · Amerindian ·
Sub-Saharan · Austronesian & Papuan · Australian.

**`subsistence` — 4:** forager · pastoralist · horticulturalist · agrarian-state.

**`theme` — Berezkin A/B → 13 groups:** A · Cosmology & etiology (01–09) vs B · Adventures & tricks
(10–13). The A/B split re-emerges from theme co-occurrence without using the labels (mockup 23).

## Where it is applied — mockups to view

| Mockup | Shows |
|---|---|
| **21 · facet-population** | the deterministic recipe run over all 1046 traditions / 3488 motifs (coverage 1042/1046) |
| **32 · facet-adequacy** | the necessity / non-redundancy / granularity / completeness audit — the source of the numbers above |
| **42 · facet-showdown** | 13 hand themes vs the narrative facet, head-to-head |
| **16 / 43 · theme-profiles** | world map of traditions coloured by 13-dim (hand) and 16-dim (narrative) profile |
| **23 · theme-geography** | heatmap of 13 themes × 12 macro-areas (lift) |
| **15 · berezkin-clusters-report** | the 14 biclusters the whole model is grounded on |

```bash
python -m http.server -d mockups 8890   # → http://127.0.0.1:8890/32-facet-adequacy/  (also 21, 42, 16, 43, 23)
```

## Status — designed and validated, not yet in production

This faceted model is proposed and empirically validated (the mockups above), **but not yet wired into the
pipeline.** Today's operational classification is still the earlier, eclectic tree in
`config/traditions.json` — **12 `major_tradition` groups over 23 corpus traditions**, mixing linguistic,
religious, geographic and ethnic axes, and denormalised across the stack (see
[`../reviews/major-tradition-review.md`](../reviews/major-tradition-review.md)). Productionising the facet
recipe (a `region_facets.py` from mockup 21) and the two-axis theme taxonomy is an **open milestone**
(Element ch. 10, milestone 3).

Do **not** conflate three distinct classifications: the operational `major_tradition` tree (config), the
converged **12 geographic macro-areas** (this document), and `REGION_COLORS` in `page-motifs.js` (a
separate motif-level geographic-region palette).
