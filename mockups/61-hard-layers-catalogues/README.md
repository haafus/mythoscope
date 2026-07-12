# 61 · Hard layers across catalogues

The **hard-layers (geography) half of [mockup 45](../45-stratigraphic-peeling/)**, ported to all three catalogues —
the companion to [mockup 60](../60-worldview-peel-catalogues/) (which ported the *worldview* half). Where 60 peels
units by their profile over a native **theme** taxonomy, this peels them by their **full attestation footprint** — the
same coverage-corrected geographic hard peel as 45 — and asks one question per catalogue: **do the units stratify into
geographic layers at all?**

## Method

For each catalogue, build the **unit × feature** 0/1 matrix, coverage-correct it (L1 row-norm × idf, so a
densely-catalogued unit does not dominate), and recursively split with Ward clustering (the 45 machinery). ATU and TMI
footprints are **SVD-reduced (40 dims) first** — they are far sparser and higher-dimensional than Berezkin's, and raw
Ward on them just peels single outliers. Blocks are named **geographically** from their continent composition; each
node reports its continent mix, its most over-represented **core features**, and a breadth-based depth register.

| Tab | Units | Features | Continents from |
|-----|-------|----------|-----------------|
| **Berezkin** | 948 traditions | 3,488 motifs | real per-tradition coordinates |
| **ATU** | 165 peoples | 2,242 tale types | attestation region labels |
| **TMI** | 94 cultures | 46,238 motifs | country/people gazetteer |

A per-catalogue **verdict** (stratifies / weakly / does not) is read off the tree: the fraction of units in the single
largest leaf.

## What it shows — the comparison is the finding

- **Berezkin — stratifies** (7 leaf blocks, largest holds 28%). A clean geographic tree: **New World** (→ American:
  Meso/Andean + Amazonian; Circum-Pacific bridge: Siberia + N-American) vs **Old World** (→ Sub-Saharan Africa;
  Eurasian core: Tibet/SE-Asia + SW & C-Asia/India). Leaves are near-single-continent with sharp core motifs. This
  reproduces 45's geography tab.
- **ATU — does not stratify** (largest block 92%). One pan-regional blob of 152 peoples (Eurasia + Americas + Africa
  all mixed) sheds only a 4-people Mesoamerican outlier and a small African group.
- **TMI — does not stratify** (largest block 90%). One blob of 85 cultures (India, Irish myth, Jewish, Icelandic,
  Chinese, Greek…) with **no characteristic motif** — the core-feature extraction returns nothing, the footprints are
  undifferentiated. Only pairs of American/African cultures peel off.

**The clean geographic stratification is a property of Berezkin's areal sampling design, not a universal feature of
folklore indexes.** ATU and TMI — motif/tale-type indexes compiled from world literature without areal design — carry
almost no extractable geographic layering: their footprints are dominated by a shared pan-regional core. That is
[direction 6, the effort/universality confound](../../docs/proposals/synthesis-and-directions.md), seen from the
geography side, and the mirror image of [mockup 60](../60-worldview-peel-catalogues/)'s worldview result.

## Honest limits

Only Berezkin has real coordinates; ATU/TMI continents come from attestation regions / a gazetteer and are
Euro-/literary-biased. Depth is a relative breadth proxy. The small ATU/TMI outlier leaves have inflated core-feature
lifts (a motif shared by 2 cultures scores ×47) — read them as "these few cultures are unlike the blob," not as a real
layer. `build_data.py` builds each footprint matrix, peels (SVD for ATU/TMI), and writes `data.js`. Deterministic.
