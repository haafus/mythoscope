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

Uther also lists a tale's variant **forms inline as `(1)…(N)`** (175 types, e.g.
"exists chiefly in four different forms: (1)… (2)…"). `_summary_blocks` renders a
leading strictly-sequential `1..K` run as an `<ol>` (the preamble stays a
paragraph before it), **losing nothing**: the `(k)` markers just become the list
numbering and each item keeps all its text — motif links and any per-form
`(Previously Type X)` provenance included. Lone or non-sequential `(k)` (e.g. a
stray `(7)`) stay inline as text; the run is 100 % sequential across all 175, so
there are no false lists.

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
| With Wikidata names / Wikipedia | 481 / 265 |
| With catalogue concordances | 328 |
| With example tales (crawled from Ashliman) | ~172 types / ~1,457 variants |

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
| `former_name` | pre-2004 Uther name, from a `(previously …)` block (§5) |
| `former_ids` | old ATU numbers renumbered from / absorbed (`previously Type X` + `Including Type X`) |
| `defining_motifs` | the defining TMI motif(s) Uther names at the label (distinct from `motifs`) |
| `references` | Uther key literature (`litvar`, mojibake-healed §5) |
| `attestations` | attestations by tradition (`provenance`) |
| `attestations_grouped` | the same, parsed into peoples & macro-regions (§7) |
| `remarks` | historical/textual notes |
| `motifs` | constituent TMI motif codes (`atu_seq`) |
| `combos` | frequently combined type ids |
| `tales` | example tales `{title, url}`, crawled from Ashliman (§8) |
| `names` / `wikipedia` / `wikidata` / `concordances` | Wikidata (§6) |

Index-level keys: `label, long_label, attribution, homepage, divisions,
subdivisions, aliases, types`. `aliases` is `{old ATU number: current type id}` —
built from every type's `former_ids` (dead-only, ambiguous ones dropped) plus the
five folded `See/Cf Type X` pointer stubs, which are removed as pages. The server
resolves an unknown id through it (`redirected_from`), and search matches
`former_name`/`former_ids`.

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
- **Title/description boundary.** Trilogy split Uther's single
  `<title>. <description>` run-on into `tale_name`/`tale_type` at the **first
  period** (`tale_name` provably never keeps a real sentence period). That period
  often falls *inside* the title, leaking one side into the other:
  - an **abbreviation** — `St. Peter…` cut down to `St`;
  - a **bracketed aside** — `The Mouse [Cat, Frog, etc.] as Bride` cut at `etc`;
  - deep in the **prose**, for quoted catch-phrase titles (jokes/anecdotes/formula
    tales, `1200–2200`) whose name is a spoken line — `'The Barn is Burning!'`
    swallowing the plot summary; when the line ends in a period the closing quote
    is orphaned to the front of the summary instead (`'No` | `' A king…`).

  We rejoin the two columns (re-inserting the consumed period; a space only where
  the seam is a real word boundary, not inside a `[code]` or a token) and re-split
  with one boundary rule: a leading `'…'` catch-phrase, else the first period at
  bracket-depth 0 that is neither an abbreviation (`St., etc., e.g.…`) nor a
  decimal in a code (`X1030.1`). This **subsumes** the old unbalanced-bracket
  patch. Trailing apparatus — `(previously …)`, `(Including … Type …)`, `[codes]`
  — is left wherever the boundary puts it (not pulled back onto the title). A
  **doubled apostrophe** (`''`, a source artifact: a doubled quote mark or a lost
  accent — 8 records) is collapsed first so quote detection is reliable. Net on
  rebuild: ~86 titles change, all in these classes.
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
- **Wikipedia** articles (en/ru/de/fr);
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

## 8. Example tales (crawled from Ashliman's Folktexts)

Tales are **sourced live from Ashliman's site**, not from the `aft.csv` dataset
(dropped — a 2021 snapshot with no per-tale URLs). The type page shows an
"Ashliman" section: a plain **list of links to each variant's text**, each a deep
link to its in-page anchor. Tale records store only `{title, url}`.

**`ashliman.refresh` (best-effort, §9-style enrichment).**
1. **Discover** every ATU type the site carries (`discover_site_types`): walk the
   index/contents pages (type-numbered page links + types declared on themed
   pages) **and** add the curated `_TYPE_PAGES` set — the numbered pages a one-time
   full probe of every catalogue code found, kept so no per-build brute-force is
   needed (`probe=True` re-runs it to regenerate the set). ATU range only (<3000;
   higher = Christiansen migratory legends). Pages cached under `raw/ashliman/`.
2. **Map** each site type to a catalogue type: itself when present, else a parent
   or lowest sibling sharing its base number (`attach_target`, hierarchical — so a
   site-only subtype like `333A` folds into `333`); genuine orphans (`676`, `828`,
   `1066`, `2033`) are dropped.
3. **Parse** each mapped page's table of contents into `{title, url}` variants
   (`parse_variants`), removing nav/footnote/cross-type-link noise (~5% of TOC
   entries), and set them as the type's `tales`, deduped by title.

A curated `_PAGE_OVERRIDES` handles types living on a themed slug page instead of
a numbered one — but only pages that **list variants**: `954→alibaba`,
`325→magicbook`, `958E*→hand`, `1408→tradingplaces`. Single-text / edition-
comparison pages are excluded (`440`/frogking.html, `779J*`/friday.html), so those
types get no tales. A full pass yields ~**172 types / ~1,457 variants** from ~183
pages (vs the dataset's 182 types / 1,518 — trading a few dead-page types for
live-site growth and folded-in subtypes).

---

## 9. Cross-walks

*The complete cross-index reference — all six relations, both directions, the
repair machinery and storage keys — is in [`cross-walk.md`](cross-walk.md); this
section summarises the ATU end.*

- **ATU ↔ TMI** — `atu_seq` gives each type's constituent motif codes (the bridge
  that powers the whole cross-walk); inverted, it tells a TMI motif which types it
  builds.
- **ATU ↔ TMI (defining)** — a *separate* map from the defining motif(s) Uther
  names at the label (`defining_motifs` → `atu_to_tmi_defining` and its inverse
  `tmi_to_atu_defining`). Kept apart from the constituent link above because the
  two relationships barely overlap: a TMI motif page surfaces it as **Defines ATU
  tale type(s)**, distinct from *Related ATU tale types*. Only codes present in
  the TMI index are linked.
- **ATU ↔ TMI (inline)** — two free-text relations (a TMI note citing `Type N`;
  a TMI code named in an ATU summary), each stored both ways so the edge shows on
  both pages. See *Symmetric inline relations* below.
- **ATU → Berezkin** — from `atu_refs` parsed in Berezkin titles (see
  `berezkin-reference.md`). A cited number that is a pre-2004 (renumbered/merged)
  type is resolved to the current type through the ATU `aliases` map before the
  link is stored.
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

### Symmetric inline relations

The two *inline* free-text relations used to show on one index's page only; they
are now stored in both directions (`crosswalk.build`) so each edge appears on both
pages:

- **TMI note → ATU** (`tmi_to_atu_note` / `atu_to_tmi_note`) — the ⇒ "cited"
  half above. The tale-type page gains **Referenced by TMI motifs (via notes)**,
  the inverse of a note's resolved `Type N` citations (straight-through, else via
  the AaTh→ATU concordance; orphan AaTh numbers produce no edge). ~800 types.
- **ATU summary → TMI** (`atu_to_tmi_summary` / `tmi_to_atu_summary`) — the TMI
  codes the summary prose names and renders as links. The motif page gains **Named
  in ATU summaries**, listing the types whose summary cites it. ~1,665 types.

The curated structural links (constituent `atu_seq`, `defining_motifs`) were
already symmetric — each is stored with its inverse.

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
- Example tales are titles + resolved deep links (no full text); coverage is
  182/2,247 types, and ~13 star/absent types resolve no Ashliman page.
- All repairs (chapter, division fill, name split, mojibake, name dictionaries)
  and enrichments (Wikidata, abbreviation/work links, AaTh remap) are interpretive
  layers on top of the source; the raw fields remain the source of truth.
