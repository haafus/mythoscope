# Motif-index documentation

This folder explains how MythoScope builds its **motif database**: how it sources,
parses, enriches and cross-links the three traditional indexes —
**Thompson (TMI)**, **Aarne–Thompson–Uther (ATU)**, and the **Berezkin & Duvakin**
areal catalogue. It's the reference behind the `mytho build motifs` pipeline.

**Start with [`motif-index-data-sources.md`](motif-index-data-sources.md)** — the
hub that ties it together: every source, the pipeline end to end, and licensing.
Then read the rest by topic.

**Each index in depth**
- [`tmi-reference.md`](tmi-reference.md) — hierarchy, notes, classification, edition history
- [`atu-reference.md`](atu-reference.md) — hierarchy, Uther apparatus, Wikidata & Ashliman enrichment
- [`berezkin-reference.md`](berezkin-reference.md) — areal codes, mapsofmyths enrichment
- [`tmi-bibliography-key.md`](tmi-bibliography-key.md) — decoded TMI citation abbreviations

**How the indexes connect**
- [`crosswalk.md`](crosswalk.md) — every ATU↔TMI↔Berezkin link, broken-link repair, and the four suggestion layers (lexical & near-identical, reasoned, inferred, semantic BGE-M3)
- [`crosswalk/`](crosswalk/) — analysis archive: code, data and reports behind those links

**Background & operations**
- [`external-tmi-atu-editions.md`](external-tmi-atu-editions.md) — survey of digitized editions and the enrichment roadmap
- [`known-issues.md`](../known-issues.md) — register of known issues, caveats & design tensions
- [`../proposals/`](../proposals/) — forward-looking designs (Mellmann migration, browser UI, region/culture/time-depth entity model + motif-stratum derivation), each partly implemented

Elsewhere in the repo: [`../research/`](../research/) for the field surveys, and
[`../how-to.md`](../how-to.md) for the run commands.
