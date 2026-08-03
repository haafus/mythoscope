---
title: "The Thompson Motif-Index (TMI)"
description: "A reference to the Thompson Motif-Index of Folk-Literature — its place-value classification, composition, edition history, and integration into Mythoscope."
url: /indexes/tmi
tier: B
---

# The Thompson Motif-Index (TMI)

The **Thompson Motif-Index of Folk-Literature** is the standard classification of
the recurring elements of traditional narrative — the *motifs* from which
folktales, myths, ballads, legends, fables, and jests are built. Compiled by
Stith Thompson, it assigns each element a code within a lettered, place-value
hierarchy and documents it with a dense apparatus of cross-references and
attested sources.

This page describes the index as a reference object and how Mythoscope sources,
structures, and enriches it. See also the sibling references —
[Aarne–Thompson–Uther](atu.md) and the [Berezkin areal catalogue](berezkin.md) —
and [the crosswalk](../crosswalk.md) that links all three.

---

## 1. Classification: place-value codes

TMI codes are **place-value**, not free-form taxonomy. Every code begins with a
**letter** naming one of the index's broad chapters, followed by digits read by
place value, with each dotted segment adding a finer level. For a code such as
`A1234.5.6`:

- the letter `A` is the **chapter**;
- the digits are read by place: hundreds give **level 0**, tens **level 1**,
  units **level 2**;
- each **dotted segment** adds one further level (`.5` → level 3, `.6` → level 4).

So `A0` ⊃ `A50` ⊃ `A52` ⊃ `A52.1`: a node's parent is simply the next-broadest
place value. This is what makes the index navigable as a tree — the code itself
encodes the ancestry.

**The `.0` convention.** Codes such as `A52.0` and `A52.0.1` are *interpolated
sub-variants* — finer motifs folded into the 1955–58 revised edition from the
later regional indexes (Cross for Irish, Thompson-Balys for India, Neuman for
Jewish, Boberg for Icelandic, Rotunda for Italian material). The `.0` heading
itself is never a published entry.

---

## 2. Composition

The index carries **46,238 motifs** distributed over **23 chapters** — the
letters `A`–`Z`, skipping `I`, `O`, and `Y`. Each chapter names a broad domain
of narrative (`A` mythological, `B` animals, `D` magic, `K` deceptions, and so
on).

| | |
|---|---|
| Motifs | 46,238 |
| Chapters (letters) | 23 (`A`–`Z`, skipping `I`/`O`/`Y`) |
| With non-empty notes | 41,959 (90.8%) |
| With an extracted definition | 5,556 (12%) |
| With culture-tagged citations | 32,470 |
| With cross-references to other motifs | 7,017 |
| With inline ATU `Type` references | 2,912 |

Nodes by hierarchy level:

| L0 | L1 | L2 | L3 | L4 | L5 | L6 |
|---:|---:|---:|---:|---:|---:|---:|
| 217 | 1,257 | 10,728 | 21,401 | 9,678 | 2,588 | 361 |

The descriptive mass sits at **levels 2–3** (about 76% of all notes text and
extracted definitions). Documentation depth is steeply skewed: the median motif
carries only a single short citation, while a few hundred motifs carry very long
scholarly notes.

---

## 3. What a motif record holds

Each stored motif carries its code, name, and chapter; its corrected
place-value level and parent; and Thompson's raw **notes** — the verbatim
apparatus, always retained as the source of truth. From those notes Mythoscope
decomposes several layers into their own fields:

- **definition** — the leading prose describing the motif, split off from the
  bibliography that follows it;
- **cultures** — citations grouped under the geographic, linguistic, or corpus
  label that tags them (`India:`, `Irish myth:`, `Jewish:`), each mapped to a
  broad region;
- **references** — the general (non-culture-tagged) bibliography;
- **see_also** — cross-references to other motifs, distinguishing Thompson's
  `Cf.` "compare" pointers from direct redirects;
- **atu_inline** — inline `Type N` references to ATU tale types.

Motifs also carry their **printed classification** — the four nested
range-headings above each motif (division, sub-division, sub-sub-division, and
the tens section) — and **former ids**, the earlier codes a revised motif was
renumbered from.

---

## 4. Provenance and edition history

Mythoscope builds TMI from the **Trilogy dataset**
([j-hagedorn/trilogy](https://github.com/j-hagedorn/trilogy), CC-BY-SA), a tidy
CSV rendering that ships the index with a *parsed place-value hierarchy* — the
ancestor path of every motif, which the raw printed index does not provide. That
pre-parsed hierarchy is the reason Trilogy is preferred over parallel
digitizations (such as the MOMFER / fbkarsdorp rendering, which retains more
cross-reference apparatus but leaves the levels to be reconstructed).

Two further sources supply what Trilogy lacks:

- **Katja Mellmann's `TMI_as_CSV`** (CC-BY-4.0) contributes Thompson's **printed
  range-headings** — the division and section titles above each motif — joined
  on by code range, plus a small set of real Thompson motifs the Trilogy CSV had
  dropped.
- **folkmasa.org**, a digitization of the index's English bibliography, is used
  to decode the abbreviated citations into full titles and live book links.

**The two editions.** Thompson renumbered about **1,166 motifs** between the
**first edition** (1932–36) and the **revised edition** (1955–58). Mellmann's
data records the earlier code(s) for each renumbered motif; Mythoscope exposes
these as **former ids** (searchable, so `A14` finds the current `A13.1.1`) and
builds an alias map that redirects an old code to its current motif. The same
map heals references elsewhere that still cite a first-edition code. Validation
confirms the renumbering was local and topic-preserving: of 124 restored
cross-references, all resolve within the same Thompson chapter, and 95% share a
content word with their target.

---

## 5. Enrichment layers

On top of the source, Mythoscope adds interpretive layers — always alongside the
verbatim notes, never in place of them:

- **Culture dictionary.** The culture labels parsed from notes are aggregated
  into a legend of roughly 1,090 distinct labels, with spelling and demonym
  variants folded to a canonical name and each canonical label mapped to a broad
  region. This is what drives the index's geographic views.
- **Bibliography key.** The abbreviated citations are decoded into **320 works,
  236 of them with a book link**, covering about 71% of matched citation uses —
  so a recognised citation on a motif page becomes a link to its source text.
  Thompson-Balys is the single most-cited source, appearing on over 10,000
  motifs.
- **The "substantive" core.** A single tunable heuristic separates
  substantive motifs from grouping scaffolding and thin variations: a motif
  counts as substantive if its notes exceed a size floor **or** it is attested
  across three or more cultures. This yields a substantive core of about
  **5,344 motifs (~12%)**, with major motifs always retained; the remaining ~88%
  is scaffolding and fine variation. Geographic breadth is treated as a genuine
  substance signal, rescuing terse-but-widespread motifs that a size threshold
  alone would drop.

---

## 6. How Mythoscope integrates TMI

The index is browsable as a tree, following the place-value hierarchy, with
per-motif badges showing whether a motif has an extracted definition, its notes
size, its recursive descendant count, and its level; substantive motifs are
accent-coloured. A filter narrows any tree to a chosen tier (full index, with
definitions, substantive only, or with ATU types). An overview dashboard
aggregates the index into geographic, thematic, and diagnostic charts, with the
**culture** as its organizing carrier.

Motif **equivalence** runs through ATU rather than geography. A motif page merges
its related ATU tale types into one section — constituent types (from Uther's
sequences) and types cited in the motif's own notes — with direction markers
distinguishing the two. Its own cross-references to other motifs are served as a
single *Related motifs* list. The full machinery of cross-catalogue linking —
including the direct and via-ATU bridges to Berezkin — is documented in
[the crosswalk](../crosswalk.md).

---

## 7. Known limitations

- The definition-versus-citation split is heuristic (about 85–90% reliable);
  very short one-line definitions are the noisy edge.
- Culture region tags are one of several non-aligned macro-region schemes across
  the sources, and a long tail of rare or compound culture labels carries no
  region.
- Bibliography links cover about 71% of citation uses; foreign long-tail works
  and author-in-journal citations are not linked to a specific edition.
- The `substantive` flag, extracted definitions, region tags, and citation links
  are interpretive enrichments layered on top of the source; the raw notes are
  always retained and shown verbatim.
