# TMI label normalization in mockup 07 (`all` + `tmi` views)

The `all` and `tmi` views normalize TMI's free-text culture labels through the
curated pipeline dictionary `src/motifs/sources/culture_dict.py`
(`canonical()`): it merges spelling/abbreviation variants (`Icel.`/`Cf. Icel.`
→ `Icelandic`, `China` → `Chinese`, `Indian` → `India`, `Scotch` → `Scottish`,
`Esthonian` → `Estonian`), strips `(sub-area)` parentheticals and a leading
`Cf.`, and **keeps genre labels distinct** (`Italian Novella`, `Spanish
Exempla`, `Buddhist myth`, `English romance` are not folded into an ethnos).
Berezkin and ATU labels are left untouched. `K` / `MIN_DF` / `MAX_DF_FRAC` /
`MIN_CULT` are unchanged, so the diff below isolates the effect of
normalization alone.

## Headline numbers

| view | metric | before (raw) | after (normalized) |
|------|--------|-------------:|-------------------:|
| all  | motifs kept       | 12,163 | 12,400 |
| all  | traditions (cols) |  1,093 |  1,061 |
| all  | co-clusters       |     16 |     16 |
| tmi  | motifs kept       |  6,622 |  6,829 |
| tmi  | traditions (cols) |    139 |     95 |
| tmi  | co-clusters       |     11 |     13 |

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

## The cost (why you'd also retune, separately)

At the **same** `K`, shrinking the TMI vocabulary (139 → 95) leaves the
spectral partition with a longer tail of degenerate singleton clusters
(`Cheremis`, `Tahltan`, `Gold Coast`, `Ila`, `English romance`, each alone).
The big clusters are cleaner and larger, but a follow-up would lower `MIN_DF`
(now that labels are consolidated) and/or drop `K` for TMI to absorb that tail.
That is a separate tuning step and deliberately not done here.

Baseline (`before`) and normalized (`after`) per-cluster summaries were captured
with `compare.py` over each build's `data.js` while iterating.
