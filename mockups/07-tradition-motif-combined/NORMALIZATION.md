# TMI label normalization in mockup 07 (`all` + `tmi` views)

The `all` and `tmi` views normalize TMI's free-text culture labels through the
curated pipeline dictionary `src/motifs/sources/culture_dict.py`
(`canonical()`): it merges spelling/abbreviation variants (`Icel.`/`Cf. Icel.`
→ `Icelandic`, `China` → `Chinese`, `Indian` → `India`, `Scotch` → `Scottish`,
`Esthonian` → `Estonian`), strips `(sub-area)` parentheticals and a leading
`Cf.`, and **keeps genre labels distinct** (`Italian Novella`, `Spanish
Exempla`, `Buddhist myth`, `English romance` are not folded into an ethnos).
Berezkin and ATU labels are left untouched.

The clustering parameters were then **retuned** for the two normalized views
(passed from `07/build_data.py`, so the standalone 05/06 mockups keep their
original baselines):

| view | param | before | after |
|------|-------|-------:|------:|
| all  | `K` (co-clusters)   | 16 | **14** |
| tmi  | `K`                 | 16 | **12** |
| tmi  | `MIN_DF`            | 20 | **12** |
| tmi  | `MAX_DF_FRAC`, `MIN_CULT` | 0.33, 2 | 0.33, 2 (kept) |

## Headline numbers

| view | metric | before (raw, K=16) | after (normalized + retuned) |
|------|--------|-------------------:|-----------------------------:|
| all  | motifs kept       | 12,163 | 12,400 |
| all  | traditions (cols) |  1,093 |  1,061 |
| all  | co-clusters       |     16 |     14 |
| all  | degenerate cl.    |      1 |      0 |
| tmi  | motifs kept       |  6,622 |  6,893 |
| tmi  | traditions (cols) |    139 |    117 |
| tmi  | co-clusters       |     11 |     11 |
| tmi  | degenerate cl.    |      — |      3 |

Fewer, cleaner columns; slightly more motifs kept (labels that were split
across variants now clear `MIN_CULT`).

## What got better

- **Variant splits merged.** In the raw `all` C1 the grab-bag led with
  `… Icel, Missouri French …`; after, `Icelandic` joins its real neighbours and
  a clean `C2 = India · Icelandic · U.S. · Welsh · Norse · Aztec` appears (the
  `Indian→India` and `Icel→Icelandic` merges pull the literate-mythology group
  together).
- **Duplicate compound labels collapsed.** Raw `tmi` clusters listed the same
  people three times (`England, U.S`, `England, Scotland, U.S`, …); those
  dedupe after parenthetical stripping.
- **Genre labels preserved** — `Italian Novella`, `Spanish Exempla`,
  `Buddhist myth`, `English romance` stay separate, as intended.

## Choosing the retuned parameters

A grid sweep over TMI (`K` × `MIN_DF` × `MAX_DF_FRAC` × `MIN_CULT`), scored by
degenerate-cluster count, size balance, biggest-cluster dominance and mean
tradition purity, settled the choices:

- **Lower `K` (16 → 12) is the main win.** At `K`=16 the partition was *forced*
  to carve ~6 degenerate clusters; `K`=12 yields 11 clusters with only the
  3 stubborn ones and lower dominance.
- **`MIN_DF` 20 → 12** keeps more real traditions and *more* motifs (6,893 vs
  6,829) without adding degeneracy — enabled by a small robustness fix in
  `06/build_data.py` that drops all-zero columns (a tradition passing `MIN_DF`
  but whose every motif was filtered by `MIN_CULT`), which previously crashed
  the SVD below `MIN_DF`≈18.
- **`MAX_DF_FRAC` kept at 0.33.** Dropping it to 0.20 balances clusters best but
  *excludes `India` and `Irish myth`* (the two largest TMI traditions) from the
  feature set entirely — unacceptable for a tradition map, so we keep them and
  accept that they anchor one large "world literate mythologies" cluster (C1).
- **`MIN_CULT` kept at 2.** Raising to 3 halves the motifs kept (≈2,600) and
  creates *more* singleton clusters.

## Residual: the sparse-Africa tail

Three tiny TMI clusters survive at every setting — `Gold Coast · Hottentot`,
`Ila · Benga`, `Ibo`. TMI simply cites very few African motifs, so these labels
are genuinely isolated; the only way to remove them is to drop them below
`MIN_DF`, which would also discard other legitimate mid-frequency traditions.
Left as-is, since they honestly reflect the catalogue's coverage.

Baseline (`before`) and final (`after`) per-cluster summaries were captured with
`compare.py` over each build's `data.js` while iterating.
