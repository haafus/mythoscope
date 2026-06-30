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
| Motifs | 46,230 |
| Chapters (letters) | 23 (`A`–`Z`, skipping `I`/`O`/`Y`) |
| With non-empty notes | 41,959 (90.8%) |
| With an extracted definition | 10,230 (22%) |
| With culture-tagged citations | 30,426 |
| With `†` motif cross-references | 7,017 |
| With inline ATU `Type` references | 2,912 |

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

Index-level keys: `label, long_label, attribution, homepage, chapters,
culture_legend` (§7).

The read service (`src/server/services/motifs.py`) adds **derived** fields at
serve time — never stored: `notes_size`, `has_definition`, `substantive` (§9),
`descendant_count`, `leaf`, `breadcrumbs`, `children`, and resolved cross-walk
links.

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
- **Duplicate codes.** 8 source codes are reused for distinct motifs
  (`B172.2, E755.2.8, K1352, K561.1.1, M202.1, N591, S222, Z64`). The first
  keeps the bare code; the rest get a lowercase suffix (`S222 → S222b`). All
  occurrences are flagged `duplicate`; `code` preserves the original. (16 records
  total are flagged.)
- **Notes run-on (defect).** Motif **`A736.1.1`** has an unclosed `notes` cell
  in the source that swallows the serialized text of ~4,200 later rows. We cut
  the note at the first `<code>. †<code>.` row-start marker (which never appears
  in a genuine note). 467,200 → 428 bytes; no data lost — the bled-in rows all
  exist in full as their own records.

These are logged at build time as `TMI defect: …` warnings.

---

## 6. Notes decomposition

A `notes` string packs several layers; `src/motifs/sources/tmi_notes.py`
separates them, keeping the raw `notes` as the source of truth.

- **definition** — the leading prose, taken up to the first bibliography marker
  (` --`, `†`, `Type`, a `*Author`, or a culture label). Heuristic, ~85%
  reliable; short one-line "definitions" are the noisy edge.
- **cultures** — citations are tagged by a geographic/linguistic/corpus label
  (`India:`, `Irish myth:`, `Jewish:`). Anchored to a group boundary so a colon
  inside a title is not mistaken for a label. Nested sub-areas
  (`Africa (Angola): …`) stay inline.
- **references** — the bibliography split on `;` / ` --`; the general
  (non-culture-tagged) segments are shown separately on the motif page.
- **see_also** — `†` cross-references to other motifs, split into direct `ref`
  and softer `cf` ("compare"). 94.8% resolve to a real id. `†` tokens are
  stripped from the text *before* definition/culture parsing so they cannot
  bleed into a neighbouring citation.
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
  (868 canonical labels).
- **normalized** — obvious variants merged to a canonical name (`Icel. →
  Icelandic`, `England → English`) and tagged with a broad **region**
  (Europe, Near East, South Asia, Oceania, …). Curated for the common labels
  (~110 cover ~94% of uses); parenthetical sub-areas are collected per culture.

Exposed at `GET /api/motifs/tmi/cultures`. The long tail (763 labels) keeps
region `""` but is still counted. Sub-areas are raw parenthetical text and carry
some noise (orthographic variants, multi-ethnos strings).

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

Output: `docs/tmi-bibliography-key.md` (human) and the tracked package asset
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

Result: a **substantive core of 5,322 motifs (~12%)**; ~88% is scaffolding +
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
(46,230), *With definitions* (10,230), *Substantive only* (5,322), *With ATU
types* (4,752). Selecting a tier hides the non-matching filterable rows
(children, chapter contents, and whole chapters with none of that tier), while
ancestors and the current motif always stay. Root and chapter badges show the
selected tier's count (e.g. chapter A: 5,810 → 627 under *Substantive*).

**Overview dashboard.** `GET /api/motifs/{index}/stats` aggregates the index in
one cached pass; the section landing renders it as a stat-card strip plus a
responsive grid of charts: composition, nodes per level, notes-size histogram,
motifs per chapter (all vs substantive), motifs by region, top cultures,
cultural breadth, most-documented motifs, most-referenced motifs (see_also
in-degree), and top sources (motifs citing each work — Thompson-Balys, Cross,
Neuman, … resolved through the bibliography key, §8).

---

## 11. Cross-walks

Motif **equivalence** runs through ATU, not geography:
`tmi → atu` (Trilogy `atu_seq`) and `atu → berezkin`. A motif page shows its ATU
tale types (crosswalk + inline `Type`), and from ATU the Berezkin areal motifs.

A **geographic** alignment (TMI cultures ↔ Berezkin areas, via a shared region
taxonomy) is possible but not built — it would be a coarse region-level overlay,
not motif-to-motif links (see the culture dictionary, §7).

---

## 12. Known limitations

- The definition / culture split is heuristic (~85–90%); short one-line
  definitions are over-flagged, colon-less region labels (`--Oceanic Dixon …`)
  merge into the previous culture.
- Culture sub-areas and the 763-label tail carry parse noise.
- Bibliography links cover ~71% of citation uses; foreign long-tail and
  author-in-journal citations are not linked to the exact edition.
- `substantive`, `definition`, region tags and citation links are interpretive
  enrichments layered on top of the source — the raw `notes` is always retained
  and shown verbatim at the end of each motif page.
