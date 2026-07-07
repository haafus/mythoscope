# The Thompson Motif-Index in MythoScope

How the Thompson Motif-Index of Folk-Literature (TMI) is sourced, parsed,
interpreted, and enriched in this project. Companion file:
[`tmi-bibliography-key.md`](tmi-bibliography-key.md) (citation decoding).

---

## 1. Source

We use the **Trilogy dataset** ([j-hagedorn/trilogy](https://github.com/j-hagedorn/trilogy),
CC-BY-SA): TMI and ATU as tidy CSVs. The TMI file ships **46,230 motifs** with a
*parsed place-value hierarchy* — the columns `level_0 … level_6` give each
motif's ancestor path, which the raw printed index does not. That parsed
hierarchy is why we prefer Trilogy.

Parallel digitizations considered and **not** used as the spine:

- **MOMFER / [fbkarsdorp/tmi](https://github.com/fbkarsdorp/tmi)** — 46,248
  entries, retains `+`/dagger cross-references and more duplicates, but has **no
  parsed hierarchy columns** (you would have to reconstruct levels yourself).
- **[folkmasa.org](https://folkmasa.org/motiv/motif.htm)** — a digitization of
  the *English bibliography* with live book links; we use it only to decode
  citation abbreviations (see §8), not for the motifs themselves.

Source columns in the Trilogy TMI CSV:
`id, chapter_name, motif_name, notes, level, chapter_id, level_0 … level_6`.

Parsing lives in `src/motifs/sources/trilogy.py`.

---

## 2. Hierarchy (place-value)

TMI codes are **place-value**, not free-form taxonomy. For a code like `A1234.5.6`:

- the **letter** (`A`) is the chapter;
- digits are read by place value: hundreds → **level 0**, tens → **level 1**,
  units → **level 2**;
- each **dotted segment** adds one more level (`.5` → L3, `.6` → L4 …).

So `A0` (L0) ⊃ `A50` (L1) ⊃ `A52` (L2) ⊃ `A52.1` (L3). A node's **parent** is the
next-broadest place value, which is exactly the `level_{level-1}` column.

### The `.0` convention

`A52.0`, `A52.0.1` etc. are **interpolated sub-variants** — finer motifs added
into the 1955–58 revised edition from later regional indexes (Cross/Irish,
Thompson-Balys/India, Neuman/Jewish, Boberg/Icelandic, Rotunda/Italian). The
`.0` heading itself is never a published row; in the source these rows carry
`level = NA`.

---

## 3. Composition

| | |
|---|---|
| Motifs | 46,238 (46,230 Trilogy + 8 net from the Mellmann supplement, §5) |
| Chapters (letters) | 23 (`A`–`Z`, skipping `I`/`O`/`Y`) |
| With non-empty notes | 41,959 (90.8%) |
| With an extracted definition | 8,456 (18%) |
| With culture-tagged citations | 32,470 |
| With `†` motif cross-references | 7,017 |
| With inline ATU `Type` references | 2,912 |
| With a printed classification (division1-3 + section, §4a) | ~46,213 (99.97%) |

Nodes per level:

| L0 | L1 | L2 | L3 | L4 | L5 | L6 |
|---:|---:|---:|---:|---:|---:|---:|
| 217 | 1,257 | 10,728 | 21,401 | 9,678 | 2,588 | 361 |

The descriptive mass sits at **L2–L3** (~76% of all notes text and definitions).
Notes size is steeply skewed: median **34 bytes** (one short citation), p90 ~147
bytes; only a few hundred motifs exceed 800 bytes.

---

## 4. Record fields

Each stored TMI motif (`outputs/motifs/tmi.json → motifs[]`):

| field | meaning |
|---|---|
| `id` | motif code, after duplicate disambiguation (§5) |
| `code` | original source code (differs from `id` only for duplicates) |
| `name` | motif name |
| `chapter` / `chapter_name` | letter + chapter title |
| `level` | corrected place-value depth (§5) |
| `parent` | corrected parent id (§5) |
| `notes` | raw source notes, after the bleed fix (§5) |
| `definition` | leading prose split out of `notes` (§6) |
| `cultures` | `{culture label: [citation strings]}` (§6) |
| `references` | flat list of citation segments (§6) |
| `see_also` | `{ref: [ids], cf: [ids]}` from `†` cross-refs (§6) |
| `atu_inline` | ATU type ids from inline `Type N` (§6) |
| `division` / `division_range` | printed division-1 heading + code range (§4a) |
| `sub_division` / `sub_division_range` | division-2 heading + range (§4a) |
| `division3` / `division3_range` | division-3 heading + range (§4a) |
| `section` / `section_range` | the tens section heading + range (§4a) |
| `former_ids` | earlier (1st-edition) codes this motif was renumbered from (§4b) |

Index-level keys: `label, long_label, attribution, homepage, chapters,
culture_legend`, plus the browse hierarchy `divisions` / `subdivisions` /
`subdivisions3` / `sections` (§4a, §7) and the `aliases` redirect map (§4b).

---

## 4a. Printed classification (from Mellmann)

The Trilogy CSV carries the code hierarchy but not Thompson's **printed
range-headings**. We lift those from Katja Mellmann's `TMI_as_CSV` (CC-BY-4.0,
source `mellmann` in `config/motifs.json`) and join them onto our motifs by code
range — four nested levels above the motif:

```
chapter (A)  →  division1 (A0–A99 Creator)  →  division2 (A300–A399 Gods of the
underworld)  →  division3 (A650–A699 Nature of the universe)  →  section
(A1810 Creation of felidae)  →  motif
```

- Parsed once in `trilogy._mellmann_classification`; division1-3 ranges are
  printed, **section** ranges are derived from consecutive tens (so a heading may
  span >1 ten, e.g. Rodentia A1840–A1859), the last in a chapter capped at +9.
- `trilogy._assign_tmi_divisions` attaches `division/sub_division/division3/
  section` (+ `_range`) to each motif by chapter+number containment (covers dup
  `~N` and mangled ids too), and builds the browse lists **141 division / 138
  sub-division / 49 sub-sub / 1,408 section**. A title's trailing taxonomic
  `Note:` clause is dropped (captured as the first period-terminated clause).
- The Titles feed the **Classification** line on the motif page and the
  chapter→division→…→section **browse dropdown** (mirroring the ATU section).
  Mellmann also supplies the 8-net **supplement motifs** (§5).

The read service (`src/server/services/motifs.py`) adds **derived** fields at
serve time — never stored: `notes_size`, `has_definition`, `substantive` (§9),
`descendant_count`, `leaf`, `breadcrumbs`, `children`, and resolved cross-walk
links.

---

## 4b. Edition history & redirects (from Mellmann)

Thompson renumbered ~1,166 motifs between the **first edition** (1932–36) and the
**revised edition** (1955–58). Mellmann's `1st ed.` column records the earlier
code(s) per current motif; we lift it in `trilogy._mellmann_first_edition`,
mirroring the ATU index's old-number system:

- **`former_ids`** — the earlier code(s) a revised motif carries, shown as grey
  chips in an **Earlier Thompson codes** section after the references, and
  matched by search (`A14` finds the current `A13.1.1`). Only emitted when the
  first-edition code differs from the current one.
- **`aliases`** (index-level, `{old code: current code}`) — every old code that is
  **not itself a live motif** and is claimed by exactly one current motif (478
  codes; ambiguous ones dropped). Navigating to an old code (`#/motifs?index=tmi&
  id=A14`) serves the current motif flagged with `redirected_from`, exactly like
  an old ATU number.
- **Mirror-close.** The cross-walk (`crosswalk.build`, `tmi_aliases`) resolves any
  ATU→TMI reference to an old code through `aliases` before matching, closing
  dangling links (`B478` → `B495.1`, `A14` → `A13.1.1`) — the mirror of how the
  ATU `aliases` close pre-2004 tale-type numbers.

**Content-fit validation.** The map restores **124** `Cf.`/`†` cross-references in
TMI notes that cite a renumbered first-edition code. All **124 (100%)** resolve to
a motif in the *same Thompson chapter* (no cross-chapter jumps), and in **119
(95%)** the citing motif shares a content word with the resolved target (e.g.
`D999`→`D1006` *Magic Buttocks* cited by *Speaking Buttocks*; `D1019`→`D1024`
*Magic Egg* cited by *Magic Wishing-Eggs*). The 5% without a shared surface word
are same-chapter and thematically related (stemming misses: *Horses* → *Prophetic
Horse*). Thompson's renumbering was local and topic-preserving, so old→current
restoration keeps the meaning.

---

## 5. Build-time interpretation decisions

All in `trilogy._finalize_tmi` / `_parse_tmi`.

- **Parent.** `parent = level_{level-1}` when `level > 0`. For the `.0` family
  (`level = NA`, derivation skips) the parent is recovered by **id-trim** —
  strip the trailing dotted segment until an existing id is found
  (`A52.0.1 → A52.0 → A52`). The most-specific existing dotted ancestor wins; a
  dot-less code with no parent is just a root (not a defect).
- **Level.** Ordinary motifs keep the dataset's place-value `level` (it is
  authoritative). Only the broken `.0` interpolations get a depth recomputed
  from their corrected parents.
- **Duplicate codes.** 8 codes are given to more than one motif — **by Thompson
  himself**, where regional supplements (Cross, Neuman, Balys, Thompson-Balys)
  were slotted under existing numbers (`B172.2, E755.2.8, K1352, K561.1.1, M202.1,
  N591, S222, Z64`). Two are printing redundancies (`K1352, K561.1.1` — same name
  twice): these **collapse** to the copy with the most notes. The other 6 are
  genuinely distinct motifs sharing a code: both are kept, the copy with the most
  notes keeps the bare code and the rest take a synthetic **`~N`** suffix (`S222`
  = "Man sells child", `*Types 756B`; `S222~2` = "Prince plans to kill father").
  `~` is invalid in Thompson notation, so the id is never mistaken for a real code
  or swept into range/citation matching. Survivors of a shared code are flagged
  `duplicate` and carry a banner linking the sibling; `code` preserves the bare
  number.
- **Notes run-on (defect).** Motif **`A736.1.1`** has an unclosed `notes` cell
  in the source that swallows the serialized text of ~4,200 later rows. We cut
  the note at the first `<code>. †<code>.` row-start marker (which never appears
  in a genuine note). 467,200 → 428 bytes; no data lost — the bled-in rows all
  exist in full as their own records.

These are logged at build time as `TMI defect: …` warnings.

### Mellmann supplement (recovered motifs)

Ten real Thompson motifs that the Trilogy CSV dropped are imported from Mellmann
(`trilogy._mellmann_supplement`, whitelist `_MEL_SUPPLEMENT`) — injected **before**
`_finalize_tmi`, so they gain parent/level/classification and join the cross-walk:

- **imported (7 leaves + 3 headings):** `C867.2, D2150, H1333.5.0.3, J2500, P100,
  Q323, T317.0.1, X751, Z356.1, Z357`. `X751` closes a dangling ATU reference.
- **cleaned on ingest:** a robust code/title split tolerant of Mellmann's malformed
  rows (`X751.Marriage…`, `T317.0.1 Life…` — missing dot/space), and a name
  override repairing the `Z56.1 … detruction` typo → `Z356.1` "…from destruction…".
- **excluded:** the dup-notation copies we already hold as `~N` (`B172.2.2`,
  `M202.1[.1]`, `N591[b]`) and `B31` (a first-edition motif dropped in the revised
  index). Re-runs are idempotent (guarded on the existing id set).

The supplement adds exactly 10 motifs (46,228 after dedup + 10 = **46,238**);
relative to Trilogy's raw 46,230 rows that reads as +8 net, since `_finalize_tmi`
first collapses 2 same-name redundant rows.

---

## 6. Notes decomposition

A `notes` string packs several layers; `src/motifs/sources/tmi_notes.py`
separates them, keeping the raw `notes` as the source of truth.

- **definition** — the leading prose, taken up to the first bibliography marker
  (` --`, `†`, `Type`, a `*`/`**Author`, or a culture label — a double
  significance mark before the first author, `**N. Soumtzov …`, is consumed
  whole so the second `*` never leaks onto the definition). Heuristic, ~85%
  reliable; short one-line "definitions" are the noisy edge. Four passes clean
  up the leaks the marker split leaves behind:
  - **leading-citation blanking** (`_is_leading_citation`) — when the head
    before the first marker is itself a citation (carries a bibliographic
    *locus* — `No. 7`, a roman numeral + page, a year, a publisher imprint
    `(Strassburg 1904)`, `ibid.`, `pp.` — and no English prose word), the
    definition is left blank rather than showing a stray reference. Fires on
    ~2,600 motifs whose notes open straight into a source (`J21.22` "Nouvelles
    de Sens No. 7"; `A240` "D. Nielson … (Strassburg 1904)").
  - **trailing-citation trimming** (`_trim_trailing_citation`) — prose that
    runs into a citation is cut at the earliest sentence boundary after which
    every remaining sentence is a citation *and* the kept part still reads as
    prose. Conservative by construction: it never trims a bare noun list or a
    prose clause that merely contains a digit (~740 trimmed, no known false
    cuts). The peeled tail joins **references**.
  - **quoted-title reunification** (`_reunite_quoted_title`) — a catch-word
    title split across the definition/notes boundary by an interior quote
    (`K553` "Wait Till I Get Fat") is stitched back together before parsing.
  - **`FORCE_BIBLIOGRAPHY` overrides** — a curated id list (~55 entries) for
    residual citation-only "definitions" the heuristics can't distinguish from
    prose — `Author Title (Place YEAR) page` citations whose English-looking
    title words (`… in Comparative Religion`) trip the prose-word guard, plus
    foreign/quoted titles with no locus. These are blanked outright; see the
    frozenset in `tmi_notes.py`.
- **cultures** — citations are tagged by a geographic/linguistic/corpus label
  (`India:`, `Irish myth:`, `Jewish:`). Anchored to a group boundary (`;`, ` --`,
  or start) so a colon inside a title is not mistaken for a label. Thompson also
  sometimes separates two labelled groups with a **comma** rather than `;`
  (`Hindu: Keith 90f., India: Thompson-Balys, Buddhist myth: Malalasekera …`,
  `A240`): `_promote_comma_labels` turns such a comma into a group boundary once a
  `Label:` has already opened the current group — so a bare comma-list of cultures
  that *share* one citation (`Mono-Alu, Fauru, Buin: Wheeler 67`) is left intact.
  A label may carry parenthetical qualifiers before its colon
  (`S. Am. Indian (Paressi):`, `Indian (Hindu):`) — these are tolerated so the
  label is still recognised (and not mistaken for a definition); a leading `--`
  bibliography dash is stripped. Nested sub-areas (`Africa (Angola): …`) stay
  inline; the canonical name drops the parens. A label is kept only if at least
  one of its citations looks source-like (a page/volume/year digit, a capitalised
  author, `*`, or `ibid.`/`cf.`); this drops prose that a capitalised word before
  a colon leaked in (`Answer:`, `Decision:`), plus a small stop-list of genre
  words that head real citations (`Fable`, `Answer`, `Countertask`). The canonical
  label maps to a broad **region** via `culture_dict._REGION` (§7).
- **references** — the bibliography split on `;` / ` --`; the general
  (non-culture-tagged) segments are shown separately on the motif page.
- **see_also** — `†` cross-references to other motifs, split into `cf`
  (Thompson's `Cf.` "compare" — the majority) and bare-`†` direct `ref`
  redirects (the minority). A single `Cf.` governs its whole list, so every
  ref after it is a compare, not just the first; the list continues across a
  comma, `and`, a range dash (`†A1--†A2`), or a `[b]` footnote marker on the
  `Cf.`, and breaks on anything else. A `†` glued to a citation as a
  bibliographic tag (`… Ursule (†B211.20)`) is dropped, not treated as a
  cross-reference. 94.8% resolve to a real id. `†` tokens are stripped from the
  text *before* definition/culture parsing so they cannot bleed into a
  neighbouring citation. (The serve layer merges `cf` + `ref` into one
  **Related motifs** list, §11.)
- **atu_inline** — inline `Type N` / `Types N, M` references to ATU tale types.

### What else lives in notes (not extracted as fields)

Significance asterisks `*`/`**` (Thompson's importance marks), `Cf.` cues,
footnote refs (`n.`, `note`), `s. v.`, `ibid.`, `passim`, quoted titles,
bracketed place/year. These remain inside the citation strings.

---

## 7. Culture dictionary (enrichment)

`src/motifs/sources/culture_dict.py` aggregates the parsed `cultures` into a
stored `culture_legend` (two layers):

- **inventory** — every distinct label with the number of motifs it tags
  (~1,090 canonical labels).
- **normalized** — variants merged to a canonical name (`Icel. → Icelandic`,
  `England → English`), a leading `Cf.` compare-prefix stripped (`Cf. Greek →
  Greek`), demonym/case variants folded (`China → Chinese`, `Irish Myth → Irish
  myth`), and the canonical tagged with a broad **region** (Europe, Near East,
  South Asia, Oceania, …). Curated for the common labels (~150 cover ~96% of
  uses); parenthetical sub-areas are collected per culture.

Common hyphenated compounds are region-mapped (`Finnish-Swedish → Europe`,
`Indo-Chinese → Southeast Asia`), `Japan` folds to `Japanese` (East Asia), and
the cross-region `Finno-Ugric` family is bucketed with **Siberia** (matching the
Volga-Finnic `Cheremis` already there and Thompson's cited *Finno-Ugric, Siberian*
source).

Exposed at `GET /api/motifs/tmi/cultures`. The long tail (~940 labels) keeps
region `""` but is still counted — mostly rare single cultures, the comma-lists of
cultures that *share* one citation (`England, U.S.`), which are not broken on
commas here (a comma is also a page-list separator), and a few genuinely
cross-region compounds (`Chinese-Persian`). Sub-areas are raw parenthetical text
and carry some noise (orthographic variants).

---

## 8. Bibliography key (external enrichment)

`scripts/build_tmi_bibliography.py` decodes the abbreviated citations into full
titles and **live book links**:

- parses the digitized *Motif-Index* bibliography at
  [folkmasa.org](https://folkmasa.org/motiv/motif_bib.htm) (English list — each
  entry already carries an archive.org / HathiTrust / Gutenberg URL);
- adds a curated supplement for the high-frequency foreign works the English
  list omits (Bolte-Polívka, Dähnhardt, Chauvin, Wesselski, **Thompson-Balys**
  — the single most-cited source at >10,000 motifs — Boberg, …) with verified
  links;
- annotates each entry with its citation count in the built TMI data.

Output: `docs/motifs/tmi-bibliography-key.md` (human) and the tracked package asset
`src/motifs/data/tmi_bibliography.json` (machine). **320 works, 236 with a book
link, covering ~71% of matched citation uses.**

The server resolves a citation by its leading author/abbreviation, disambiguating
a multi-work author by the short title (`Frazer Fire` vs `Frazer Apollodorus`).
On the motif page every recognised citation becomes a link to its source book.

Residual gaps: works cited only through a journal (`Boas BAM XV`, `Barbeau JAFL
XXIX`) link to the journal, not the specific paper; and parse-noise heads
(`Einstein`, `G.`) are not works.

---

## 9. The "substantive" heuristic

Goal: separate **substantive motifs** from building scaffolding (empty grouping
headers) and the mass of thin variations.

```
substantive(node) = notes_bytes >= 150  OR  cultures >= 3
```

Decided empirically (the full dialogue is summarised here):

- **A single absolute floor is necessary.** ~39% of root→leaf paths are entirely
  thin; a *relative* criterion ("max notes on the vertical", top-K, local
  maxima) cannot decide whether a whole branch is throwaway — every vertical has
  a max. Relative top-K either drops genuinely rich motifs (Orpheus, lost at
  K=1) or balloons to ~78% kept (junk survives at K=3). Discarding a thin branch
  *wholesale* is inherently an absolute judgement.
- **Notes size alone is not enough.** It never over-includes (it is one of the OR
  terms) but under-cuts: the `cultures ≥ 3` rescue adds ~1,142 terse-but-broad
  motifs (e.g. *God With Many Arms*, 5 cultures, 140 bytes) that size alone would
  drop. Geographic breadth is a real substance signal.
- **The ATU rescue was rejected.** `atu_inline ≥ 1` would have rescued ~1,679
  more, but median 52 bytes and 55% with zero cultures — too many thin
  tale-type kernels. Dropped to keep the core clean.
- **`T = 150` bytes** sits at the histogram shoulder (median notes is only 34
  bytes).

Result: a **substantive core of 5,344 motifs (~12%)**; ~88% is scaffolding +
variations. Major motifs are always retained (an absolute floor never drops a
big node). The boundary is intentionally a single tunable constant
(`_SUBSTANTIVE_MIN_NOTES`).

---

## 10. Browsing & overview (UI)

The Motifs section reads everything above through `GET /api/motifs/tmi/*`.

**Tree badges** carry, per motif: a **✓** when it has an extracted definition,
the **notes size**, recursive **descendant count**, and **level** — each with a
tooltip. The badge is **accent-coloured when the motif is substantive**. (So ✓ =
definition, colour = substantive — two independent signals.)

**Motif filter.** A dropdown above every main-panel tree (catalog root, chapter
browse, motif detail) offers four tiers with index-wide counts: *Full index*
(46,230), *With definitions* (8,456), *Substantive only* (5,344), *With ATU
types* (4,752). Selecting a tier lists the chapter's matching motifs at any
depth (so the list isn't empty when the broad level-0 categories have none),
and on the root/detail trees hides non-matching rows while ancestors and the
current motif stay. Root and chapter badges show the selected tier's count
(e.g. chapter A: 5,810 → 633 under *Substantive*).

**Overview dashboard.** `GET /api/motifs/{index}/stats` aggregates the index in
one cached pass; the section landing renders it as a stat-card strip plus a
responsive grid of charts on the **common chart spine** all three index overviews
share (order + title scheme defined in
[`motif-index-data-sources.md`](motif-index-data-sources.md) → *Overview
dashboards*). TMI's carrier is the **culture**, so its panels are: *Motifs by
chapter (all vs. substantive)* (the row value is the **all**-count, with a
substantive overlay bar), *Motifs by kind*, *Motifs by hierarchy level*, *Motifs
by region*, *Cultures with the most motifs*, *Cultures per motif* (breadth
histogram), *Most widespread motifs (cultures attested)*, then the TMI-specific
tail — *Motifs by note length*, *Best-documented motifs*, *Most cross-referenced
motifs (cf./†)*, and *Most-cited sources* (each work — Thompson-Balys, Cross,
Neuman, … resolved through the bibliography key, §8).

---

## 11. Cross-walks

Motif **equivalence** runs through ATU, not geography:
`tmi → atu` (Trilogy `atu_seq`) and `atu → berezkin`. A motif page merges its ATU
tale types (constituent from `atu_seq` + inline `Type` from the note) into one
**Related ATU tale types** section with ⇐/⇒/⇔ markers; inline `Type` numbers are
AaTh and are remapped to ATU 2004 where possible — see
[`atu-reference.md`](atu-reference.md) §9.

The note's own `†` cross-references (§6) are served as one **Related motifs**
list (`links.related`): the `Cf.` compares are the unmarked default and the
rarer bare-`†` redirects carry a small **see also** tag. The two are thin and
asymmetric enough that separate sections added noise, not signal, so they are
merged with the minority marked rather than split.

A **geographic** alignment (TMI cultures ↔ Berezkin areas, via a shared region
taxonomy) is possible but not built — it would be a coarse region-level overlay,
not motif-to-motif links (see the culture dictionary, §7).

---

## 12. Known limitations

- The definition / culture split is heuristic (~85–90%); short one-line
  definitions are over-flagged, and colon-less region labels (`--Oceanic Dixon …`)
  merge into the previous culture.
- Culture sub-areas carry parse noise; the region-less tail is mostly rare
  cultures plus unsplit compound labels (`England, U.S.`) — see
  `troubleshooting.md`. The broad **region** tags themselves are one of four
  non-aligned macro-region schemes (also in `troubleshooting.md`).
- Bibliography links cover ~71% of citation uses; foreign long-tail and
  author-in-journal citations are not linked to the exact edition.
- `substantive`, `definition`, region tags and citation links are interpretive
  enrichments layered on top of the source — the raw `notes` is always retained
  and shown verbatim at the end of each motif page.
