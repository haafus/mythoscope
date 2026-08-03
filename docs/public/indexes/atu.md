---
title: "The Aarne–Thompson–Uther Index (ATU)"
description: "A reference to the Aarne–Thompson–Uther tale-type index — its four-level hierarchy, composition, provenance in Uther 2004, and integration into Mythoscope."
url: /indexes/atu
tier: B
---

# The Aarne–Thompson–Uther Index (ATU)

The **Aarne–Thompson–Uther index** is the standard catalogue of international
folktale *types* — complete, recurring plots such as *The Dragon-Slayer* or *The
Kind and the Unkind Girls*, each identified by a number and documented with a
plot summary, a record of where it is attested, and its key scholarly
literature. Where the [Thompson Motif-Index](tmi.md) classifies the *elements* of
narrative, ATU classifies whole *stories*: a tale type is, in effect, an ordered
assembly of motifs.

This page describes the index as a reference object and how Mythoscope sources,
structures, and enriches it. See also the [Berezkin areal catalogue](berezkin.md)
and [the crosswalk](../crosswalk.md) linking all three catalogues.

---

## 1. Structure: a four-level hierarchy

An ATU identifier is a **number**, with optional **letter suffix(es)** and an
optional **`*`**: `313`, `313A`, `1861*`, `1525A*`. The star marks a
regional or supplementary type (667 of the ids, about 30%). Ids sort by number
then suffix, so `313 < 313A < 313A* < 1861`.

The catalogue nests four levels — **chapter → division → sub-division → type**:

- **chapter** — 7 canonical top-level classes (Animal Tales; Tales of Magic;
  Religious Tales; Realistic Tales; Tales of the Stupid Ogre; Anecdotes and
  Jokes; Formula Tales), plus an Unclassified bucket;
- **division** — 43 named number ranges (`Supernatural Adversaries 300–399`);
- **sub-division** — an optional finer level (24 groups);
- **subtype families** — a lettered subtype (`313A`) hangs off its base type
  (`313`) where the base exists (970 types have a parent; 412 head a family).

Uther's **plot summaries** are rendered as structured text: TMI motif codes and
cross-type references become links, motif ranges are expanded to link both
endpoints, and a tale's variant forms — which Uther lists inline as
`(1)…(N)` — are rendered as proper ordered lists without losing any of the prose.

---

## 2. Composition

| | |
|---|---|
| Tale types | 2,247 |
| Starred (`*`) types | 667 |
| Chapters | 7 (+ Unclassified) |
| Divisions / sub-divisions | 43 / 24 |
| Subtype families (base types) | 412 |
| With a plot summary | 2,242 |
| With key literature | 1,773 |
| With attestations | 2,220 |
| With remarks | 923 |
| With constituent TMI motifs | 1,642 types / 4,573 links |
| With combinations | 729 types / 4,696 links |
| With Wikidata names / Wikipedia | 481 / 265 |
| With catalogue concordances | 328 |
| With example tales | ~172 types / ~1,457 variants |

---

## 3. What a type record holds

Each stored type carries its id and number; its chapter, division, and
sub-division; its subtype-family links; and Uther's **name** and **plot
summary**. Alongside these sit the fields of his scholarly apparatus and the
enrichments Mythoscope adds:

- **defining motifs** — the defining TMI motif(s) Uther names at the label;
- **references** — Uther's key literature;
- **attestations** — the traditions and languages attesting the type, also
  parsed into peoples and macro-regions;
- **remarks** — historical and textual notes;
- **motifs** — the constituent TMI motif codes;
- **combos** — frequently combined type ids;
- **former name / former ids** — the pre-2004 name and old numbers this type was
  renumbered from or absorbed;
- **tales** — example tales (title and link);
- **Wikidata fields** — multilingual names, Wikipedia and Wikisource links,
  and concordances to other catalogues.

---

## 4. Provenance: Uther 2004

Mythoscope builds ATU from the **Trilogy dataset**
([j-hagedorn/trilogy](https://github.com/j-hagedorn/trilogy), CC-BY-SA), whose
tale-type material derives from a plain-text extraction of the printed catalogue:

> Hans-Jörg Uther, *The Types of International Folktales* (Helsinki: Academia
> Scientiarum Fennica, 2004), **FF Communications 284–286**.

The tale names, plot summaries, and the entire scholarly apparatus (literature,
attestations, remarks) are therefore **verbatim Uther**. There is no open,
machine-readable clean release of these fields — only the copyrighted book — so a
number of source artifacts trace to that text extraction rather than to the
catalogue itself, and are repaired at build time. The chapter of each type is
derived from its number against Uther's canonical ranges (the extraction's own
chapter column is unreliable); omitted division headers are filled from the range
containing the type; and the title/description boundary, which the extraction
sometimes split inside a title, is rejoined and re-split on a single boundary
rule. Characters lost in the extraction (surfacing as a recurring mojibake
sequence) are healed against a curated dictionary of the folklore-scholar names
and journals they corrupt, restoring about 94% of occurrences; the residue is
marked rather than guessed.

**AaTh and ATU numbering.** The catalogue superseded the earlier
Aarne–Thompson (AaTh) numbering, and much older material — including the `Type N`
references inside TMI notes — still cites AaTh numbers. Uther split many types
into letter variants (`650 → 650A/B/C`) or renumbered and merged others; an
alias map built from each type's recorded former ids redirects an old number to
its current type, and an AaTh→ATU concordance (from Wikidata) remaps the rest
where an equivalent exists. Numbers Uther deleted with no concordance are left
unresolved rather than guessed.

---

## 5. Enrichment layers

On top of the verbatim apparatus, Mythoscope adds:

- **Wikidata.** By the ATU-number property, each type is enriched with
  multilingual tale-type names, Wikipedia articles, **Wikisource** links (the
  full primary text of tales of the type, kept distinct from encyclopedic
  summaries), and **concordances** to other catalogues (Grimm/KHM, AaTh, Aesop's
  Perry numbers, Child ballads). Current coverage is roughly 481 names, 265
  Wikipedia, 223 Wikisource, and 328 concordances.
- **Apparatus decoding.** ATU has no author-year key, so individual citations are
  shown as-is, but recurring reference-work, journal, and catalogue
  abbreviations, and famous named collections, are decoded into tooltips with the
  full name and, where one exists, a link to the work (full text preferred).
- **Attestations by people and region.** Uther's attestation prose is parsed into
  `(people, citation)` entries, each people label canonicalised and mapped to a
  macro-region; roughly 260 curated labels cover essentially all of the ~45,000
  people-mentions. Every count is parsed from Uther's own apparatus.
- **Example tales.** Tales are sourced live from D. L. Ashliman's *Folktexts*
  site as lists of links to each variant's text — about 172 types and 1,457
  variants.

---

## 6. How Mythoscope integrates ATU

The index is browsable by its four-level hierarchy through a chapter → division →
sub-division tree, and each type page renders the linkified summary, the decoded
apparatus, the attestation accordion grouped by region, and the enrichment links.
An overview dashboard aggregates the catalogue into geographic, thematic, and
diagnostic charts, with the **people** as its organizing carrier.

ATU is the **hub of the crosswalk**: the constituent-motif sequences that define
each type are the bridge that links the Thompson Motif-Index to the Berezkin
areal catalogue. A type page surfaces its constituent and defining TMI motifs,
the motifs whose notes cite it, and the Berezkin motifs that reference it. The
full cross-catalogue machinery — all six confirmed relations, the broken-link
repair, and the four hypothesis layers — is documented in
[the crosswalk](../crosswalk.md).

---

## 7. Known limitations

- The scholarly apparatus is only partly decoded: series abbreviations and famous
  works get names and links, but individual author-year citations cannot be
  expanded without Uther's full (copyrighted) bibliography.
- Character healing is about 94%; a residual marker stands for a genuinely lost
  diacritic, and a few ambiguous names are left marked rather than guessed.
- The AaTh→ATU remap resolves only the orphaned TMI-note references for which a
  Wikidata concordance exists; the rest are types ATU deleted or renumbered.
- Example tales are titles and deep links (no full text), covering 182 of 2,247
  types.
- All repairs and enrichments are interpretive layers on top of the source; the
  raw fields remain the source of truth.
