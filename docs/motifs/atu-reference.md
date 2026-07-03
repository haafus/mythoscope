# The Aarne-Thompson-Uther Tale-Type Index in MythoScope

How the Aarne-Thompson-Uther (ATU) tale-type index is sourced, parsed,
interpreted, enriched, and cross-walked in this project. Overview and licensing:
[`motif-index-data-sources.md`](motif-index-data-sources.md); the Thompson side:
[`tmi-reference.md`](tmi-reference.md).

---

## 1. Source

ATU comes from the **Trilogy dataset**
([j-hagedorn/trilogy](https://github.com/j-hagedorn/trilogy), CC-BY-SA) as five
CSVs (`config/motifs.json → trilogy.files`): `atu_df` (tale types), `atu_seq`
(type → constituent TMI motifs), `atu_combos` (frequently combined types), `aft`
(example folktales), and the shared `tmi.csv`. Parsing lives in
`src/motifs/sources/trilogy.py`; Wikidata enrichment in `atu_wikidata.py`.

**Ultimate origin.** Trilogy's `fetch/fetch_taletypes.R` does not scrape a site —
it parses a local text file `ATU.Master.Hels.txt` (**Hels = Helsinki**), i.e. a
plain-text extraction of the printed catalogue:

> Hans-Jörg Uther, *The Types of International Folktales* (Helsinki: Academia
> Scientiarum Fennica, 2004), **FF Communications 284–286**.

So the tale names, plot summaries and the whole scholarly apparatus
(`litvar`/`provenance`/`remarks`) are **verbatim Uther**. There is no open,
machine-readable clean release of these fields — only the copyrighted book — which
is why several defects below (§5) trace to that text extraction, not to us.

Source columns in `atu_df.csv`:
`chapter, division, sub_division, atu_id, tale_name, litvar, provenance,
tale_type, remarks, combos`.

---

## 2. Structure (four-level hierarchy)

An ATU id is a **number**, optional **letter suffix(es)**, optional **`*`**:
`313`, `313A`, `1861*`, `1525A*`. The `*` marks a regional/supplementary type
(667 of 2,247 ids, ~30%). Ids sort by `(number, suffix)` so `313 < 313A < 313A* <
1861`.

The catalogue nests **chapter → division → sub_division → type**:

- **chapter** — 7 canonical top-level classes (Animal Tales, Tales Of Magic,
  Religious Tales, Realistic Tales, Tales Of The Stupid Ogre, Anecdotes And
  Jokes, Formula Tales; plus an *Unclassified* 2400–2499 bucket). **Derived from
  the type number**, not the CSV column — see §5.
- **division** — 43 named ranges (`Supernatural Adversaries 300-399`); every type
  gets one (§5 fills the gaps).
- **sub_division** — an optional 4th level (24 groups, 833/2,247 types), e.g.
  `The Clever Man 1525-1639` inside `Stories About A Man`.
- **subtype families** — a lettered subtype (`313A`) hangs off its base number
  type (`313`) when that base exists: `parent` + natural-sorted `subtypes`
  (970 types have a parent, 412 head a family).

The read service exposes the `divisions`/`subdivisions` trees for the browse
dropdown (nested by chapter, ascending by number range).

The **plot summary is linkified** on the type page (`_atu_summary_html`): after
escaping the prose, `[B261]`-style TMI motif tokens and `Type N` ATU references
are turned into links — but only for ids that actually exist in the index (a
missing one stays plain text).

---

## 3. Composition

| | |
|---|---|
| Tale types | 2,247 |
| Starred (`*`) types | 667 |
| Chapters | 7 (+ Unclassified) |
| Divisions / sub-divisions | 43 / 24 |
| Subtype families (base types) | 412 |
| With a plot summary | 2,242 |
| With Uther literature (`references`) | 1,773 |
| With attestations (`provenance`) | 2,220 |
| With remarks | 923 |
| With constituent TMI motifs (`atu_seq`) | 1,642 types / 4,573 links |
| With combinations (`combos`) | 729 types / 4,696 links |
| With Wikidata names / Wikipedia / image | 481 / 265 / 176 |
| With catalogue concordances | 328 |
| With example tales (Ashliman AFT) | 182 types / 1,518 tales |

The atu_df rows are ordered alphabetically by chapter name, so the raw file
"starts" mid-index (`Anecdotes…` 1850–1874); we re-sort types ascending by id.

---

## 4. Record fields

Each stored type (`outputs/motifs/atu.json → types[]`):

| field | meaning |
|---|---|
| `id` / `num` | tale-type id / its leading number |
| `chapter` | canonical chapter, derived from `num` (§5) |
| `division` / `division_range` | division name / `[start, end]` |
| `sub_division` / `sub_division_range` | optional finer level |
| `parent` / `subtypes` | subtype family links |
| `name` / `summary` | tale name / plot summary (both repaired, §5) |
| `references` | Uther key literature (`litvar`, mojibake-healed §5) |
| `attestations` | attestations by tradition (`provenance`) |
| `attestations_grouped` | the same, parsed into peoples & macro-regions (§7) |
| `remarks` | historical/textual notes |
| `motifs` | constituent TMI motif codes (`atu_seq`) |
| `combos` | frequently combined type ids |
| `tales` | example folktales (AFT metadata, §8) |
| `names` / `wikipedia` / `wikidata` / `image` / `concordances` | Wikidata (§6) |

Index-level keys: `label, long_label, attribution, homepage, divisions,
subdivisions, types`.

---

## 5. Build-time interpretation decisions & source defects

The apparatus is verbatim Uther, but the *text extraction* Trilogy parsed it from
introduced several defects. Each is repaired at build time (`trilogy.py`).

- **Chapter from the number, not the CSV.** The CSV `chapter` column is
  unreliable — it promotes sub-groups (`Other Animals And Objects`) to chapters
  for only half their tales, and lumps Religious + Realistic + Stupid-Ogre into
  one. We instead derive the chapter from the type number via the canonical
  Uther ranges (`_ATU_CHAPTERS`), giving exactly 7 chapters.
- **Division-gap fill.** The extraction omitted two division headers, leaving
  **126 types with no division** (700–749 in Tales Of Magic, 750–779 in Religious
  Tales). Empty divisions are filled from the range containing the type — first
  from the CSV's own labelled ranges, then from a canonical fallback
  (`700–749 Other Tales Of The Supernatural`, `750–779 God Rewards And Punishes`).
- **Tale name truncated mid-bracket.** Trilogy split `tale_name` at the first
  period, which for **54 types** lands inside a bracketed aside (`402`: *The Mouse
  [Cat, Frog, etc.] as Bride*) — cutting the name at `etc` and leaking the tail
  into the summary. When a name has an unbalanced `[`/`(`, we rejoin name +
  summary and re-split at the first period **outside all brackets** (fixes 52/54;
  2 have a closing bracket missing in the source itself, left untouched).
- **Baked-in mojibake `ï¿½`.** A lost character shows up as the 3-char sequence
  `ï¿½`. **Proven upstream** (our cached CSV is byte-identical to GitHub, and the
  file is valid UTF-8): the original diacritic → `U+FFFD` → latin1-decoded → `ï¿½`
  → re-UTF-8-encoded, all in Trilogy's extraction. The original char is destroyed
  in the published file, so no re-download helps. We heal in three passes:
  1. a **curated dictionary** (~140 entries) of the recurring folklore-scholar
     names and journals it corrupts (`Ténèze`, `Köhler`, `Polívka`,
     `Ó Súilleabháin`, `Bârlea`, `Pitrè`, `Röhrich`, `Béaloideas`, `Pañcatantra`…);
  2. **range → en-dash**: numbers/pages (`998ï¿½1005`), letter-suffixed type
     ranges (`400Aï¿½C`) and roman numerals (`XIï¿½XXVIII`) — both sides must be a
     proper range endpoint so a diacritic inside a name (`Rï¿½hle`) is never turned
     into a dash;
  3. the residue → a single `�` (a genuinely lost diacritic we won't guess).
  Result: **~94%** of occurrences healed. The remainder (~900) is a long tail of
  rare or genuinely ambiguous names (`Böcker`, `Führmann`), plus just 19 standalone
  `ï¿½`.
- **Dropped leading capital.** A related corruption deletes a name's leading
  diacritic capital outright, no marker (`Ėrgis → rgis`, `Čajkanović → ajkanovi`).
  These surface as a lowercase-initial surname in citation position and are
  repaired as **whole words only** (6 curated names) so a fragment inside a real
  word is never touched.
- **`tale_variant` is not used.** `atu_seq` carries a `tale_variant` column, but
  the data dictionary defines it as *"the specific permutation of the tale type"* —
  synthetic permutations, not documented variants. Two catch-all types (`875`,
  `650A`) alone expand to ~542k of the file's 593k rows. So per-motif variant
  frequency is not a trustworthy salience signal; we collapse across variants and
  keep only the **ordered unique motif set** per type.

Defects are logged at build time.

---

## 6. Wikidata enrichment

`atu_wikidata.py` best-effort enriches each type via SPARQL (open, cached in
`raw/wikidata/atu.json`; network failure skips the step). By the ATU-number
property **P2540** it attaches, per type:

- **multilingual names** of the *tale-type* items (`P31 = Q47451145`, so a
  specific tale isn't mistaken for the type name);
- **Wikipedia** articles (en/ru/de/fr), a Commons **image** (`P18`);
- **concordances** to other catalogues — Grimm/**KHM**, Aarne-Thompson (**AaTh**),
  Aesop (**Perry**), Child ballads — from `P528` (+ `P972`) and `P1852`.

Cyrillic homoglyphs in ids are folded (`283В* → 283B*`). The AaTh concordance is
also **inverted** to remap old AaTh numbers cited in TMI notes (§9).

---

## 7. The Uther apparatus (per-type bibliography)

`litvar → references`, `provenance → attestations`, `remarks → remarks` carry
Uther's scholarly apparatus (key literature, attestations by tradition/language,
historical notes). There is **no author-year key** for ATU (unlike TMI/folkmasa),
so individual citations are shown as-is. But on the type page:

- recurring **reference-work / journal / catalogue abbreviations** (`EM`, `BP`,
  `Tubach`, `Perry`, `HDA`, `SUS`, `BFP`, `JAFL`, `ZDMG`, `RTP`…) and **famous
  named collections/authors** (Gesta Romanorum, Decameron, Pentamerone, Roman de
  Renart, Pauli, Bebel, Aesop, 1001 Nights, Ovid…) are decoded by a curated
  mini-key into a **tooltip** with the full name and, where one exists, a **link
  to the work** (full text preferred: Wikisource, Gutenberg, Fordham, ruthenia;
  else De Gruyter/Google Books/Cambridge Core/Wikipedia). Multi-word titles match
  as phrases; word boundaries prevent false hits (`\bGrimm\b` ≠ *Grimms*).
- Ambiguous abbreviations (`Speculum` journal vs work; `Facetiae` for two
  authors) are deliberately **not** linked.

### Attestations by people & region

The `provenance` prose is `People: citation; People, People: citation; …` — a
nationality/ethnonym before each colon. `atu_regions.py` parses it into
`(people, citation)` entries, canonicalises the people label (folding spelling
variants — `Iclandic → Icelandic`, `Indian → India`), and maps it to a
**macro-region**. A head that glues two peoples with a period (`Palestinian.
Iraqi`) is split into both — but only when *both* halves are region-mapped, so
citation noise (`No. 65`) is never torn apart. Nothing is discarded: the handful
of stray fragments that leak into a people slot (`No. 65`, `György 1934`) are
kept as unmapped entries in the "—" bucket rather than dropped, so the section
stays faithful to the source. The region set matches
TMI/Berezkin plus **Central Asia** (ATU carries a real mass of Uzbek/Tadzhik/
Kazakh… material the other two don't distinguish); ~260 curated labels cover
~100% of the ~45k people-mentions, the rest landing in a "—" bucket.

Stored per type as `attestations_grouped` (`{total, regions: [{region, count,
entries}]}`) and aggregated across the index into `culture_legend` (people →
types-attesting, region). On the type page the section renders as a region
accordion; the overview gains **Types by region** (types present per region,
each type counted once — matching TMI/Berezkin "Motifs by region"), **Top
peoples**, and a
**regional-breadth** histogram. This is illustrative-free — every count is real,
parsed from Uther's own apparatus. The one caveat is the region map itself: a
first-pass curation (e.g. Maghreb folded into "Near East", Volga-Finnic into
"Europe") that can be refined.

---

## 8. Example tales (Ashliman AFT)

`aft.csv` (Ashliman's *Annotated Folk Tales*) is 1,518 folktale texts labelled
with an ATU type. We ingest **metadata only** — `title`, `provenance`, `source`,
`notes` — and deliberately **drop the full `text`**: the Ashliman texts carry
their own licence separate from the repo's CC-BY-SA, and it keeps the index lean.
The type page shows an "Example tales" section (present for 182 types) with a
per-tale title, provenance chip and bibliographic source, plus one corpus-level
attribution link to Ashliman's Folktexts (no per-tale URLs exist in the data).

---

## 9. Cross-walks

- **ATU ↔ TMI** — `atu_seq` gives each type's constituent motif codes (the bridge
  that powers the whole cross-walk); inverted, it tells a TMI motif which types it
  builds.
- **ATU → Berezkin** — from `atu_refs` parsed in Berezkin titles (see
  `berezkin-reference.md`).
- **Combinations** — `atu_combos.csv` is Uther's own "Combinations" field, parsed
  and range-expanded into individual type ids (informative, not derived); 4,667 of
  4,696 resolve, 29 overshoot the range expansion (shown grey).

### AaTh vs ATU numbering (the broken-link problem)

Inline `Type N` references in **TMI notes are AaTh numbers** — Thompson wrote them
~50 years before ATU 2004 (this is inferred from provenance; the data has no
label). Of these, **540 don't resolve** against ATU 2004 (337 distinct types),
because Uther split many into letter variants (`650 → 650A/B/C`) or renumbered /
deleted them. On the read side each ref is resolved:

- straight through if the number still exists in ATU;
- else remapped via the **Wikidata AaTh→ATU concordance** (55/337 types;
  `330A → ATU 330`), keeping an `AaTh 330A` provenance badge — this can be
  one-to-many (`553 → 303 · 554`, a split type);
- else left grey with a tooltip ("AaTh number, no ATU 2004 equivalent"). Family
  and deleted types are **not guessed**.

The reverse direction (ATU → TMI, `atu_seq`) has **36 broken** constituent motif
links — codes absent from Trilogy's tidy `tmi.csv` — also shown grey with a
tooltip. Parent-trim / a fuller TMI source were considered and skipped as
over-engineering for 14–22 links.

### Merged relations on the motif page

On a TMI motif page the two ATU relations are one deduplicated section, **Related
ATU tale types**, with a direction marker from the motif's viewpoint: **⇐**
constituent (from `atu_seq`), **⇒** referenced (named in the note, AaTh-resolved),
**⇔** both. Ordered ⇔ first (corroborated by two independent sources), then
ascending by tale-type number. Max 48 types on one motif (`L161`); ~97% of motifs
have 1–3.

---

## 10. Known limitations

- The scholarly apparatus is only partly decoded: series abbreviations and famous
  works get names/links, but individual author-year citations cannot be expanded
  without Uther's full bibliography (copyrighted, not machine-readable).
- Mojibake healing is ~94%; the residual `�` marks a genuinely lost diacritic, and
  a few ambiguous names (`Böcker`, `Führmann`, `Hüllen`) are left as markers
  rather than guessed.
- AaTh→ATU remaps only ~16% of the orphaned TMI-note references; the rest are
  types ATU deleted or renumbered with no Wikidata concordance.
- Example tales are metadata only (no full text); coverage is 182/2,247 types.
- All repairs (chapter, division fill, name split, mojibake, name dictionaries)
  and enrichments (Wikidata, abbreviation/work links, AaTh remap) are interpretive
  layers on top of the source; the raw fields remain the source of truth.
