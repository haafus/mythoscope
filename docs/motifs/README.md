# Motif-index documentation

How MythoScope sources, parses, enriches and cross-links the three traditional
motif indexes — the **Thompson Motif-Index (TMI)**, the **Aarne–Thompson–Uther
(ATU)** tale-type index, and the **Berezkin & Duvakin** areal catalogue.

**Start here:** [`motif-index-data-sources.md`](motif-index-data-sources.md) —
the hub: every source, the `mytho motifs` pipeline, licensing and attribution.

## Core references (the system as built)

| doc | what it covers |
|---|---|
| [`motif-index-data-sources.md`](motif-index-data-sources.md) | **Hub** — sources, pipeline architecture, licenses |
| [`tmi-reference.md`](tmi-reference.md) | TMI: hierarchy, fields, notes decomposition, classification & edition history (Mellmann), overview |
| [`atu-reference.md`](atu-reference.md) | ATU: four-level hierarchy, Uther apparatus, Wikidata & Ashliman enrichment |
| [`berezkin-reference.md`](berezkin-reference.md) | Berezkin: areal codes, mapsofmyths enrichment, overview |
| [`tmi-bibliography-key.md`](tmi-bibliography-key.md) | Generated key decoding TMI citation abbreviations |

## Cross-index links

| doc | what it covers |
|---|---|
| [`crosswalk.md`](crosswalk.md) | **Full reference** for every ATU↔TMI↔Berezkin link, broken-link repair, and the parallels layers |
| [`crosswalk/`](crosswalk/) | Analysis archive — code, CSV data, and reports (link accounting, lexical & reasoned parallels, the generated unresolved-citations snapshot) |

## Sources & editions

| doc | what it covers |
|---|---|
| [`external-tmi-atu-editions.md`](external-tmi-atu-editions.md) | Survey of digitized TMI/ATU editions, a measured quality comparison, and the enrichment roadmap |

## Operations

| doc | what it covers |
|---|---|
| [`troubleshooting.md`](troubleshooting.md) | Running log of cross-cutting issues (macro-area schemes, raw-cache volatility, …) |

## Proposals (forward-looking)

| doc | status |
|---|---|
| [`proposals/tmi-mellmann-migration.md`](proposals/tmi-mellmann-migration.md) | Partially implemented — additive Mellmann phase shipped; full source swap not done |
| [`proposals/motifs-browser-ui.md`](proposals/motifs-browser-ui.md) | Partially implemented — flat-list/sort/search live; unified navigator prototyped in `mockups/motifs-navigator/` |

## Related, elsewhere in the repo

- [`../research/`](../research/) — the computational-folkloristics landscape and
  motif-induction method surveys (research context, not the source pipeline).
- [`../how_to.md`](../how_to.md) — project map and run commands.
