# Public documentation — structure at a glance

The settled composition of the site's public documentation. This is the map; the reasoning,
sources, and execution order live in [`public-docs-plan.md`](public-docs-plan.md).

- **Delivery:** hybrid — the interactive app stays an SPA at `/app`; the public docs are
  **static (SSG) pages at clean URLs**, built by `scripts/build_docs.py` into the web root.
- **Language:** English · **Name:** Mythoscope · **~16 pages, 3 tiers.**

## Site map

```
mythoscope.io
│
├─ /                         A1  Overview  ······················  (landing — thesis + CTA)
│
├─ Explore ▾  (the SPA app, /app)
│   ├─ /app#/corpus              Sources
│   ├─ /app#/embeddings          Similarity
│   ├─ /app#/ages · /realms · /beings   Graphs
│   ├─ /app#/geography           Atlas
│   └─ /app#/motifs              Motifs
│
├─ Research ▾  (the static docs)
│   │
│   ├─ ── A · The argument ───────────────────────────────
│   │   ├─ /what-we-found                        A2  What we found
│   │   ├─ /cases/{swan-maiden,…}                A3  Case studies
│   │   └─ /how-it-works                         A4  How it works
│   │
│   ├─ ── B · Reference & surveys (SEO / citation magnets) ──
│   │   ├─ /crosswalk                            B1  Motif crosswalk (TMI↔ATU↔Berezkin) ★
│   │   ├─ /indexes/{tmi,atu,berezkin}           B2  The three indexes
│   │   ├─ /research/computational-folkloristics B3  Field survey (+ /research/landscape)
│   │   ├─ /research/corpus-sourcing             B4  Corpus-sourcing atlas
│   │   ├─ /research/encyclopedias               B5  How the encyclopedias carve the world
│   │   └─ /regions                              B6  The 14 regions
│   │
│   └─ ── C · Participate ────────────────────────────────
│       ├─ /contribute                           C1  Contribute
│       ├─ /resources                            C2  Resources (data+DOI, API, awesome-list)
│       ├─ /publications                         C3  Publications (citation hub)
│       ├─ /updates                              C4  Updates / Notes (blog)
│       └─ /credit                               C5  Credit & authorship
│
├─ About                     A5  /about  ·········  Vision · manifesto · the -scope name
└─ ⭐ GitHub
```

★ flagship asset.

## Tier A — the argument (narrative, human entry)

| ID | Page | URL | Source |
|----|------|-----|--------|
| A1 | Overview (landing) | `/` | README + Element 01 + Figma pitch |
| A2 | What we found | `/what-we-found` | Element 06/10, findings draft |
| A3 | Three motifs through the machine | `/cases/{swan-maiden,sun-and-moon,fished-up-earth}` | Element 09 |
| A4 | How it works | `/how-it-works` | Element 03 + how-to |
| A5 | About / Vision | `/about` | Figma + Element 01 |

## Tier B — reference & surveys (SEO & citation magnets)

| ID | Page | URL | Source |
|----|------|-----|--------|
| B1 | Motif crosswalk (TMI ↔ ATU ↔ Berezkin) ★ | `/crosswalk` | crosswalk.md (translate) |
| B2 | The three indexes | `/indexes/{tmi,atu,berezkin}` | tmi/atu/berezkin-reference |
| B3 | Field survey: computational folkloristics | `/research/computational-folkloristics` (+ `/research/landscape`) | comp-folk survey + landscape |
| B4 | Corpus-sourcing atlas | `/research/corpus-sourcing` | corpus-sourcing-survey |
| B5 | How the great encyclopedias carve the world | `/research/encyclopedias` | encyclopedias-survey |
| B6 | The 14 regions | `/regions` | regions.md |

## Tier C — participate (engagement & contributors)

| ID | Page | URL | Source |
|----|------|-----|--------|
| C1 | Contribute | `/contribute` | Figma "Join the Collaboration" |
| C2 | Resources | `/resources` | data+DOI, OpenAPI, GitHub, awesome-list |
| C3 | Publications (citation hub) | `/publications` | papers/DOIs + "How to cite" |
| C4 | Updates / Notes (blog) | `/updates` | motif/mockup of the month |
| C5 | Credit & authorship | `/credit` | attribution ladder, CRediT, CARE |

## Navigation (header)

```
[logo → /]   Explore ▾            Research ▾               About     ⭐ GitHub
             └ SPA app views      └ docs TOC (A · B · C)   (A5)
```

- **Explore ▾** = the live tool (no indexing needed). **Research ▾** = the static docs.
- Logo → the Overview landing. Contextual "learn more" links go from app views into the docs
  (Motifs→Crosswalk, Atlas→14 regions, Similarity→How it works).

## Footer (persistent, outside `#app`; thin on `/app`, full on doc pages)

```
Read                    Connect                          Get updates
· Overview              · GitHub · Bluesky · Mastodon    [ email → Subscribe ]  (Buttondown)
· What we found         · YouTube · Substack
· Crosswalk             · Discord (when live)
· Surveys               · hello@mythoscope.io
· Contribute
· Publications
────────────────────────────────────────────────────────────────────────────
© 2026 Mythoscope · content CC-BY-SA · data CC-BY · code MIT   ·  Cite · API · awesome-list
```

## Out of scope / internal

- **Deferred:** Learn (tutorials/workshops); Team / Partners (until real).
- **Stays in the repo, not on the site:** `docs/proposals/*`, `docs/reviews/*`,
  `known-issues.md`, `docs/ROADMAP.md`, the `papers/1–5` drafts, parsing logs — the internal
  reasoning layer.

*Execution order: see [`public-docs-plan.md`](public-docs-plan.md) §16.*
