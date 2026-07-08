# Motif-index documentation

This folder explains how MythoScope builds its **motif database**: how it sources,
parses, enriches and cross-links the three traditional indexes —
**Thompson (TMI)**, **Aarne–Thompson–Uther (ATU)**, and the **Berezkin & Duvakin**
areal catalogue. It's the reference behind the `mytho motifs` pipeline.

**Start with [`motif-index-data-sources.md`](motif-index-data-sources.md)** — the
hub that ties it together: every source, the pipeline end to end, and licensing.
Then read the rest by topic.

**Each index in depth**
- [`tmi-reference.md`](tmi-reference.md) — hierarchy, notes, classification, edition history
- [`atu-reference.md`](atu-reference.md) — hierarchy, Uther apparatus, Wikidata & Ashliman enrichment
- [`berezkin-reference.md`](berezkin-reference.md) — areal codes, mapsofmyths enrichment
- [`tmi-bibliography-key.md`](tmi-bibliography-key.md) — decoded TMI citation abbreviations

**How the indexes connect**
- [`crosswalk.md`](crosswalk.md) — every ATU↔TMI↔Berezkin link, broken-link repair, the parallels layers
- [`crosswalk/`](crosswalk/) — analysis archive: code, data and reports behind those links

**Background & operations**
- [`external-tmi-atu-editions.md`](external-tmi-atu-editions.md) — survey of digitized editions and the enrichment roadmap
- [`troubleshooting.md`](troubleshooting.md) — running log of cross-cutting issues
- [`proposals/`](proposals/) — forward-looking designs (Mellmann migration, browser UI), each partly implemented

Elsewhere in the repo: [`../research/`](../research/) for the field surveys, and
[`../how_to.md`](../how_to.md) for the run commands.
