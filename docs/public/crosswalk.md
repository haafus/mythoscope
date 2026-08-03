---
title: "The Motif Crosswalk: TMI ↔ ATU ↔ Berezkin"
description: "An open-access concordance linking the Thompson Motif-Index, the Aarne–Thompson–Uther tale-type index, and Berezkin's areal catalogue, with confirmed edges and four graded hypothesis layers."
url: /crosswalk
tier: B
---

# The Motif Crosswalk: TMI ↔ ATU ↔ Berezkin

The Mythoscope motif crosswalk is a concordance between the three standard
reference catalogues of narrative folklore:

- the **Thompson Motif-Index of Folk-Literature** (**TMI**) — motifs;
- the **Aarne–Thompson–Uther** index (**ATU**) — tale types;
- the **Berezkin & Duvakin** catalogue — motifs classified by geographic area.

Each catalogue answers a different question — what a story *element* is (TMI),
what a whole *plot* is (ATU), and where a motif is *attested* (Berezkin) — and
each was compiled independently, in different decades and different languages,
with no shared identifier. The crosswalk reconstructs the links between them:
given any motif or tale type, it returns the corresponding entries in the other
two catalogues, together with the evidence for each link.

To our knowledge no comparable open-access concordance across all three
catalogues exists. Individual pairings appear inside the printed sources (Uther
lists constituent motifs; Berezkin cites tale-type numbers), but they are
scattered through prose, numbered under superseded schemes, and never inverted
so that a link can be followed from either end. This page describes what the
crosswalk contains, how it is built, how confident each link is, and how to cite
it.

Companion references: [Thompson Motif-Index](indexes/tmi.md) ·
[Aarne–Thompson–Uther](indexes/atu.md) · [Berezkin areal catalogue](indexes/berezkin.md).

---

## 1. Scope

The counts below are for the current build, over **46,230 TMI motifs**,
**2,242 ATU tale types**, and **3,488 Berezkin motifs**.

The crosswalk has two strata:

- a **confirmed** stratum of curated and text-extracted edges, each with an
  explicit provenance (§2–§4);
- a **hypothesis** stratum of four graded suggestion layers — lexical, reasoned,
  inferred, and semantic (§6) — which propose parallels that carry *no* recorded
  link, flagged as candidates for manual review rather than asserted equivalences.

Every confirmed edge is stored in **both directions**, so a link is visible on
the source entry and on the target entry alike.

---

## 2. Confirmed edges

Six independent relations make up the confirmed stratum. They are kept separate
because they capture different senses of "related" and overlap very little — a
motif that *defines* a type is rarely part of its constituent skeleton, and a
note that *cites* a type is rarer still.

| # | Relation | Basis | Coverage (source → target) |
|---|---|---|---|
| 1 | **ATU ↔ TMI — constituent** | the ordered TMI motifs a type is "assembled" from | 1,642 types carry motifs; 3,799 motifs point back to types (3,765 present in the index) |
| 2 | **ATU ↔ TMI — defining** | the single defining motif Uther names at a type's label | 63 types name a defining motif; 62 resolve → 74 motifs |
| 3 | **ATU ↔ TMI — note citation** | `Type N` references inside TMI notes, resolved to ATU | 2,602 motifs cite ≥1 live type; inverted, 802 types |
| 4 | **ATU ↔ TMI — summary citation** | TMI codes named in a type's plot summary | 1,665 types name ≥1 live motif; inverted, 3,810 motifs |
| 5 | **Berezkin ↔ ATU** | tale-type numbers cited in Berezkin titles | 584 resolved edges, 571 reaching a live type |
| 6 | **Berezkin ↔ TMI (direct)** | curated Thompson ids attached to Berezkin motifs | 236 edges |

### 2.1 ATU ↔ TMI — four independent relations

The bridge that powers the whole crosswalk is the **constituent** relation:
Uther's apparatus records, for each tale type, the ordered sequence of TMI
motifs from which the type is built. Inverted, it tells any TMI motif which tale
types it helps compose. Synthetic permutations of these sequences are discarded;
only the ordered unique motif set per type is kept.

Three further ATU ↔ TMI relations run alongside it:

- **Defining** — Uther names a single defining motif beside many type labels.
  This is held apart from the constituent skeleton because *defining a type* is
  not the same as *entering its decomposition*.
- **Note citation** — in a TMI motif's notes, Thompson often points to a tale
  type (`Type 480`). These numbers predate ATU 2004 and are resolved forward
  before an edge is stored (§4).
- **Summary citation** — an ATU plot summary names TMI codes in running prose
  (`… [J2066] …`), which the reader renders as links. Motif **ranges** written
  in the summary (`J1759–J1763`) are expanded to every index code falling inside
  the interval, so a range credits all of its interior members, not just its
  endpoints. This recovers a type's internal motifs and closes incidental gaps
  in the constituent list — narrowing the divergence between the two ATU→TMI
  motif sets from 289 edges to 64 (Jaccard 0.93 → 0.97).

### 2.2 Berezkin ↔ ATU

Many Berezkin catalogue titles cite an ATU type (`… ATU 328A*`). These numbers
are parsed and normalised to canonical tale-type ids — free text arrives wrapped
in parentheses, with trailing commentary, stars, and Cyrillic look-alike
letters. Both directions are built from a single resolved edge set (a number is
resolved to its current type through the ATU alias map, §4), so they are exact
inverses. Of 584 resolved edges, 571 reach a type that exists in our source; the
remaining 13 point to types absent from it and are shown greyed rather than
guessed.

### 2.3 Berezkin ↔ TMI (direct)

The only *direct* Berezkin ↔ TMI bridge (as opposed to the indirect hop through
ATU) is a set of curated Thompson ids that the sister site mapsofmyths attaches
to each Berezkin motif. These are parsed and cleaned to canonical form, keeping
only codes that exist in the Thompson index — yielding 236 edges. Far more pairs
are reachable indirectly (Berezkin → ATU → TMI), but a shared *tale type* is not
the same as a shared *motif*, so the direct and indirect links are kept
distinct.

---

## 3. How the confirmed edges are built

The confirmed stratum is produced by three complementary methods:

1. **Structured field joins.** Where a source records the link explicitly —
   Uther's constituent-motif sequences, his defining motifs, the curated
   Thompson ids on Berezkin motifs — the crosswalk reads the field and inverts
   it. These are the highest-provenance edges.
2. **Free-text citation extraction.** Where a source *mentions* another
   catalogue's identifier in prose — a `Type N` in a TMI note, a `[code]` in an
   ATU summary, an `ATU 328A*` in a Berezkin title — the identifier is parsed
   out, normalised, resolved to a live entry, and stored as an edge with its
   textual provenance retained.
3. **Broken-link repair** (§4) — because catalogue numbering has changed over
   time, a raw reference frequently points to a superseded number; these are
   healed against authoritative renumbering data, and anything unrepairable is
   marked, not fabricated.

---

## 4. Resolving broken references

Numbering across all three catalogues has shifted over the decades, so raw
references are repaired against authoritative concordances, and the
irreparable minority is flagged rather than guessed:

- **AaTh → ATU.** The `Type N` numbers in TMI notes are Aarne–Thompson (AaTh)
  numbers — Thompson wrote them decades before ATU 2004. They resolve straight
  through when the number survives, otherwise via an AaTh→ATU concordance drawn
  from Wikidata (which can be one-to-many where Uther split a type), retaining
  an `AaTh 330A` provenance badge. Numbers with no ATU 2004 equivalent yield no
  edge and are shown greyed.
- **ATU former numbers.** Pre-2004 tale-type numbers (renumbered or merged by
  Uther) resolve through an alias map built from each type's recorded former
  ids. It both redirects an old number to the current type and rescues cited
  numbers in Berezkin titles.
- **TMI first-edition codes.** Symmetrically, a first-edition Thompson code
  (1932–36) renumbered in the 1955–58 revision resolves through the TMI alias
  map, closing dangling ATU→TMI and Berezkin→TMI references.

**Content-fit validation.** Both alias maps are built on authoritative
renumbering data, and the content agrees at both ends of the resolved links.
For TMI, the map restores 124 cross-references in notes that cite an old code;
all 124 resolve to a motif in the *same* Thompson chapter, and in 119 of 124
(95%) the citing motif shares a significant word with its target — Thompson's
renumbering was local and topic-preserving. For ATU, 358 types carry an old
number; where old and new names differ they are re-titlings of the same plot,
not content drift.

---

## 5. The hypothesis stratum

Alongside the recorded edges, four **suggestion layers** propose parallels that
carry *no* confirmed link. They are graded, presented in descending confidence,
and always labelled as hypotheses for manual review — never as asserted
equivalences.

### 5.1 Reasoned parallels (curated)

A hand-curated layer records motifs that are parallel **in meaning** even when
worded in entirely different terms — the case that lexical matching cannot see.
For example, Berezkin's *Valuables brought from the lower world* corresponds to
TMI's *Earth Diver* (`A812`) with no shared vocabulary at all. Each group
carries a theme, an explicit rationale, and a `high`/`medium` confidence.
Currently **17 groups** (7 three-way, 10 pairwise). Because Berezkin and TMI are
both *motif* indexes, they are deeply parallel in cosmogony and etiology; ATU, a
*type* index, joins only on plot-forming motifs, so three-way groups are rare.

### 5.2 Inferred cross-links (transitive)

A small **inferred** layer completes triangles: when two edges share a common
node, the third is added — but only through a low-fan-out pivot (a pivot leading
to at most two nodes in the target catalogue), so that closing through a
type-node (a type being a bag of dozens of constituent motifs) cannot flood the
graph with false "type ≠ motif" edges. Three closures — through a Berezkin
motif, through a TMI motif in ≤2 types, and through a type's near-1:1 defining
motif — yield **72 inferred edges** in total. Each retains the bridge it was
inferred through as provenance.

### 5.3 Lexical parallels (heuristic)

A lexical layer matches names and descriptions across the three catalogues to
surface entries that *look* parallel but have no recorded link. Two TF-IDF
signals are used — one over the name (a precision filter), one over
name-plus-description (recall) — and every existing crosswalk edge is subtracted
out. Each surviving candidate is graded **tier A** (two or more shared
significant title words, or a very strong description match) or **tier B** (a
single-word echo). By tier A / tier B, the layer proposes: ATU~TMI 382 / 220,
Berezkin~TMI 1,446 / 1,425, Berezkin~ATU 21 / 8, plus 22 tier-A triangles. A
**near-identical** band (~127 pairs with an almost verbatim title) is split out
as the strongest candidates for genuine links. The match is lexical, not
semantic: it misses differently worded parallels and admits false matches, which
is why it is offered only as a set of leads.

### 5.4 Semantic parallels (BGE-M3 embeddings)

A semantic layer compares **meaning** rather than words. Each motif (title plus
description) is encoded with the `BAAI/bge-m3` transformer into a 1,024-dimension
vector, and for each motif the nearest cosine look-alikes in the other two
catalogues — minus every confirmed edge — are taken as parallels that share
sense but not vocabulary. On confirmed cross-index pairs, BGE-M3 reaches
recall@10 ≈ 63%, against ≈ 38% for a TF-IDF+SVD (LSA) baseline: embeddings are
substantially stronger at recovering held-out links. Pairs already surfaced by a
higher layer are de-duplicated out, so this layer carries only what the others
miss.

---

## 6. How to use the crosswalk

- **Follow a motif to its plots.** From a TMI motif, the *Related ATU tale
  types* section lists every type the motif composes (constituent) or is cited
  by (note), with a direction marker (⇐ constituent, ⇒ cited, ⇔ both).
- **Follow a plot to its parts.** From an ATU type, the *Constituent TMI motifs*
  and *Defining motif(s)* sections give its motif skeleton; the summary links
  each motif it names in prose.
- **Bridge motif catalogues geographically.** Berezkin's areal distribution
  reaches TMI both directly (the curated concordance, shown first) and through
  ATU. Use the direct link for motif-level equivalence; treat the via-ATU link
  as looser.
- **Mine the hypothesis layers.** For comparative work, the reasoned, inferred,
  lexical, and semantic layers propose candidate parallels that no catalogue
  records — read them as leads to verify, in descending order of confidence.

A **geographic** alignment of Berezkin areas to TMI cultures is deliberately not
built: the catalogues use non-aligned macro-region schemes, so such an overlay
would be coarse and region-level, not motif-to-motif.

---

## 7. How to cite

> Mythoscope. *The Motif Crosswalk: TMI ↔ ATU ↔ Berezkin.* Computational
> comparative-mythology reference. `/crosswalk`.

A DOI is pending and will be added here once assigned; please do not cite a
placeholder identifier in the interim. When citing a specific link, quote the
motif or type name and code alongside the identifier, since all three catalogues
remain works in progress. The underlying source catalogues should be cited in
their own right — see the [TMI](indexes/tmi.md), [ATU](indexes/atu.md), and
[Berezkin](indexes/berezkin.md) reference pages for their editions, authorship,
and licences.
