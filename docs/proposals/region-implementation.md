# Proposal: wiring `region` into production — the plan

- **Status:** proposal (open, decisions settled). Nothing here is implemented.
- **Scope:** the **code layer only** — one config, build, serve, front — for the text-processing pipeline.
  Taxonomy and presentation are closed (§0). Supersedes the code sections of
  [`tradition-architecture-unified.md`](tradition-architecture-unified.md) §4/§6.

Grounded in the three field audits ([`../reviews/tradition-review.md`](../reviews/tradition-review.md),
[`../reviews/major-tradition-review.md`](../reviews/major-tradition-review.md),
[`../reviews/color-system-review.md`](../reviews/color-system-review.md)) and the canon
[`research/regions.md`](../../research/regions.md).

---

## 0. Closed decisions (context — not reopened)

- **`region` (14) is the sole classification axis** of a tradition. No facet layer. Canon: `regions.md`.
- **Colour lives only at the region level** — a tradition inherits its region's colour (single base colour,
  `regions.md` §8).
- **Out of scope:** motif `theme`/`stratum`, the connectivity axis and dating (science), and **the entire
  motif-areal region system** (2.7).

---

## 1. Current state (the problem)

The live axis is still `tradition` (free string) → `major_tradition` (derived) → `colour` (random); `region`
is not wired in.

- **Free-string identity & join.** Books hold a hand-written `tradition` string (`config/corpus.json`, 28
  books) joined to `config/traditions.json` by exact string equality — no validation. Misses degrade
  **silently**: `builder.py:210` → `""`; `services/corpus.py:25-26` → `{}` then colour `"#6b7280"`. Strings
  are dirty (`"Australian"` vs `"Australian Aboriginal"`).
- **`major_tradition`** — derived from the `config/traditions.json` tree (`builder.py:152-157,208-213`); the
  13 top-level nodes are an **eclectic mix** (`Indo-European`, `Mesopotamian`, `Abrahamic`, `Finno-Ugric`…),
  **not** the 14 regions. Denormalised onto rows, the file path `corpus/<major>/<tradition>/<title>.txt`
  (`utils.text_path:63-67`), and every chunk (`build_embeddings.py:177-183`); dropped from served
  `traditions.json` (asymmetry, `builder.py:160-181`); dead on `SearchResult.major_tradition`
  (`schemas.py:30`).
- **`colour`** — `random.randint` unseeded (`utils.py:93-104`), reshuffles each build; stored on
  `traditions.json` **and** denormalised onto `/catalog` rows (`services/corpus.py:29`).
- **`region`** — no such field in `config/` or `src/`. Every `region` in `src/` is the separate Berezkin/
  ATU/TMI *motif-areal* system (`services/motifs.py`, `sources/atu_regions.py`, `sources/culture_dict.py`,
  `page-motifs.js::REGION_COLORS`) — untouched by this work (2.7).
- **Divergent defaults** — `""` / `"unknown"` / `"Unknown"` / `"Other"` / `"#6b7280"`; no
  `CATEGORY_NONE`/`UNASSIGNED` in the backend.

---

## 2. Decisions

**2.1 One curated config, one file.** `config/traditions.json` is a tree; each top-level node is a **region**
(all 14, in canon order, key = the canon region name). A region node carries the canon region properties
(machine copy of `regions.md`) plus its texted traditions:

```jsonc
// config/traditions.json  — regions in canon order (out-of-Africa arc, regions.md §4); no order field
{
  "Sub-Saharan Africa": {
    "colour": "#CC503E",                 // single base colour, regions.md §8
    "description": "…",                  // regions.md §5
    "subdivision": "…",                  // regions.md §5
    "strata": "…",                       // regions.md §5
    "traditions": {                      // ONLY traditions that currently have texts
      "Yoruba": { "description": "…", "coordinates": [8, 4] }
    }
  }
  // … all 14 regions …
}
```

`regions.md` stays the human canon; this file is its machine copy for the pipeline.

**2.2 Name = id.** The region node key is the canon region name; the tradition key is the tradition name.
No slugs, no separate id field, anywhere.

**2.3 All 14 regions, only texted traditions.** Every region node is present; under each are only traditions
that currently have corpus texts. An **empty region is valid**, not a broken join.

**2.4 Curated, not derived.** The tradition list is our own curated artifact — `regions.md` §5 is the
composition reference. Nothing is imported or derived from Berezkin, `areal_path`, or any index.

**2.5 `major_tradition` → `region` = rename + re-partition.** Rename the field everywhere in code
(field / param / variable). Re-author the top-level grouping from the 13 eclectic groups into the 14 canon
regions (Greek/Norse/Celtic → `Europe`; `Mesopotamian` + `Abrahamic` → `Near East & North Africa`; …). The
`<major>` file-path segment **stays** — its value is now the region name.

**2.6 Colour comes from the region and is not stored.** A tradition's colour is its region node's `colour`
in `config/traditions.json`, computed `tradition → region → colour` at display. `region` and `colour` are
kept only there: the `outputs/corpus/corpus.json` rows, the `/api/corpus/catalog` response, and `SearchResult`
carry only the tradition; region is resolved from the tree, colour from the region. `get_tradition_color` /
`random` and the colour injection in `get_catalog_documents` are removed.

**2.7 The motif-index region system is untouched.** Berezkin/ATU/TMI regions and their palette
(`services/motifs.py`, `sources/atu_regions.py`, `sources/culture_dict.py`, `page-motifs.js::REGION_COLORS`)
stay exactly as they are. This is a different entity (motif areas, not tradition regions).

**2.8 Serve the config directly; no generated `traditions.json`.** `config/traditions.json` is the source of
truth. `/api/corpus/traditions` returns its `region → traditions` tree as-is (canon order, region colour +
fields), attaching each tradition's `books` — the list of its corpus documents — computed at request time by
grouping the `corpus.json` rows by tradition. `_update_traditions` and the built `outputs/corpus/traditions.json`
are removed. The front renders this server-provided grouping directly; the client-side `groupDocuments` is
removed.

**2.9 Fail-loud validation.** Every `corpus.tradition` must exist in the tree, and every region key must be one
of the 14 canon names — otherwise the build fails. Replaces the silent `.get(...)` degradations
(`builder.py:210`, `services/corpus.py:25`).

**2.10 Embeddings untouched.** `region` is resolved from a chunk's `tradition` via the tree at query time; no
chunk-metadata change, no re-embedding.

**2.11 One `UNASSIGNED`** id/label across `schemas.py`, `iterator.py`, and the front end (extend the front's
`CATEGORY_NONE` down to the value layer).

**2.12 Accept the `stratum`/`Strata` overload.** The motif `stratum` field and `regions.md` §5's authored
`strata` share a name; no rename.

---

## 3. Data flow (target)

```
config/traditions.json   region → {colour(base §8), description, subdivision, strata, traditions{name:{desc,coords}}}   ← source of truth; region+colour live here only
config/corpus.json       book → tradition (name)
        │  build: text files at corpus/<region>/<tradition>/<title>.txt; validate every book tradition ∈ tree
        │          & every region key ∈ 14 canon (fail loud). No generated traditions.json; no colour written.
        ▼
outputs/corpus/corpus.json      rows carry tradition ONLY (the reference) — no region, no colour, no major
outputs/embeddings/*            chunk metadata: tradition, url; region resolved at query; not re-embedded
        ▼  server  (reads config/traditions.json + outputs/corpus/corpus.json, joins at request)
/api/corpus/traditions   config region → traditions tree (canon order, region colour + fields); each tradition's books attached at request
/api/corpus/catalog      documents carry tradition ONLY; region/colour resolved by lookup; no client-side re-grouping
/api/similarity/*        SearchResult: tradition ONLY (major_tradition removed); region/colour resolved from the tree if needed
        ▼  front
one 14-region legend; render the server-provided grouping in order; colour = region base
```

---

## 4. Migration order (region-only; each phase shippable)

1. **Author the config + validation.** Build `config/traditions.json`: 14 region nodes in canon order, each
   with its canon fields (`colour` base + `description`/`subdivision`/`strata`) and only its texted
   traditions; keep `config/corpus.json` books referencing the tradition by name; add build-time fail-loud
   validation (unknown tradition / non-canon region). *(Highest value-to-risk — closes the silent join.)*
2. **`major_tradition` → `region` + remove it from records.** Rename the field across `builder.py`,
   `iterator.py`, `CorpusFileInfo`, `schemas.py`, services, and the front; values come from the re-partitioned
   tree; the `<major>` path segment keeps its place as the region name. **Remove `SearchResult.major_tradition`
   outright** (dead payload — nothing on the front reads it). Stop writing `major`/`region` onto document rows.
3. **Colour from region; serve the config, drop the generated file.** Remove `_update_traditions` and
   `get_tradition_color`; `/api/corpus/traditions` serves `config/traditions.json` directly (region tree,
   region colour + fields) with each tradition's `books` attached at request. A tradition's colour is its
   region's, computed at display; strip `region` and `colour` from the `corpus.json` rows, `/catalog`, and
   `SearchResult`.
4. **Front renders the served grouping.** Remove the client-side `groupDocuments`; render the
   `region → traditions` tree in canon order; colour = region base.
5. **One `UNASSIGNED`** across `schemas.py`, `iterator.py`, and the front end.

Tests are rewritten to the new model as each phase lands.

---

## 5. Out of scope

Motif `theme`/`stratum`; the connectivity axis, dating, the residual (science); the motif-areal region system
(2.7); any facet (`family`/`subsistence`/`theme_profile`); catalogue imports/joins; re-validation of the
frozen 12-area analyses.
