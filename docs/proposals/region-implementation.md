# Proposal: wiring `region` into production — the plan

- **Status:** proposal (open, decisions settled; one item flagged to discuss — §3). Not implemented.
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
  motif-areal region system** (§2.7).

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
  `traditions.json` (`builder.py:160-181`); carried but unread on `SearchResult.major_tradition`
  (`schemas.py:30`).
- **`colour`** — `random.randint` unseeded (`utils.py:93-104`), reshuffles each build; stored on
  `traditions.json` **and** copied onto `/catalog` rows (`services/corpus.py:29`).
- **`region`** — no such field in `config/` or `src/`. Every `region` in `src/` is the separate Berezkin/
  ATU/TMI *motif-areal* system (`services/motifs.py`, `sources/atu_regions.py`, `sources/culture_dict.py`,
  `page-motifs.js::REGION_COLORS`) — untouched by this work (§2.7).
- **Divergent defaults** — `""` / `"unknown"` / `"Unknown"` / `"Other"` / `"#6b7280"`; no
  `CATEGORY_NONE`/`UNASSIGNED` in the backend.
- **Filename sanitisation** — `sanitize_filename` (`utils.py:17-20`) replaces spaces and `\ / * ? : " < > |`
  with `_`; **`&` (and `%`, `#`, `'`) pass through**. Region names carry `&` ("Near East & North Africa",
  "Mesoamerica & the Andes"); tradition names do not.

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
regions (Greek/Norse/Celtic → `Europe`; `Mesopotamian` + `Abrahamic` → `Near East & North Africa`; …).

**2.6 Colour comes from the region and is not stored.** A tradition's colour is its region node's `colour`
in `config/traditions.json`, computed `tradition → region → colour` at display. `get_tradition_color` /
`random` and the colour injection in `get_catalog_documents` are removed; colour appears in no record.

**2.7 The motif-index region system is untouched.** Berezkin/ATU/TMI regions and their palette
(`services/motifs.py`, `sources/atu_regions.py`, `sources/culture_dict.py`, `page-motifs.js::REGION_COLORS`)
stay exactly as they are. This is a different entity (motif areas, not tradition regions).

**2.8 Backend owns structure + order; the front composes views.** The backend serves two things: the
`region → traditions` **tree** (canon order, from the config) and the **raw documents**. The front does the
composition — grouping by region, attaching each tradition's books (from the documents), colouring by region.
Books are **not** baked into the traditions payload; the client-side `groupDocuments` reconstruction is
removed (structure and order come from the served tree).

**2.9 Serve the config directly; no generated `traditions.json`.** `config/traditions.json` is the source of
truth; `/api/corpus/traditions` returns its tree as-is. `_update_traditions` and the built
`outputs/corpus/traditions.json` are removed.

**2.10 The catalog carries the tradition only.** `/api/corpus/catalog` documents carry `tradition` (the
reference) and per-document fields (`id`, `title`, `url`, counts, `description`, `source`) — **no
`major_tradition`, no `region`, no `colour`**. Region is resolved from the tradition via the tree; colour
from the region.

**2.11 Region leaves the file path.** Text files live at `corpus/<tradition>/<title>.txt` — keyed by the
tradition (a stable, disambiguating owner), with the region only in the config. Re-annotating a tradition's
region never moves files. The `<region>` segment is dropped, so region names' `&` never reach the filesystem;
only tradition/title names are sanitised (`sanitize_filename`).

**2.12 Fail-loud validation.** Every `corpus.tradition` must exist in the tree, and every region key must be
one of the 14 canon names — otherwise the build fails. Replaces the silent `.get(...)` degradations
(`builder.py:210`, `services/corpus.py:25`).

**2.13 Embeddings untouched.** `region` is resolved from a chunk's `tradition` via the tree at query time; no
chunk-metadata change, no re-embedding.

**2.14 One `UNASSIGNED`** id/label across `schemas.py`, `iterator.py`, and the front end (extend the front's
`CATEGORY_NONE` down to the value layer).

**2.15 Accept the `stratum`/`Strata` overload.** The motif `stratum` field and `regions.md` §5's authored
`strata` share a name; no rename.

---

## 3. Target API surface (corpus ↔ front)

Two data endpoints (two projections) plus one text fetch; overlap trimmed to the `tradition` key.

- **`GET /api/corpus/traditions`** → the `region → traditions` tree, canon order:
  `region → { colour, description, subdivision, strata, traditions: [ { name, coordinates, description } ] }`.
  No books, no per-tradition colour. Consumers: atlas (coordinates + book-join), embeddings (colour via
  region + coordinates), corpus browser (grouping skeleton + order).
- **`GET /api/corpus/catalog`** → documents: `[ { id, title, tradition, url, word/sentence/char counts,
  description, source } ]`. Tradition only; region/colour resolved on the front from the tree. Also the source
  the front joins books from.
- **`GET /api/corpus/documents`** → the raw text of one document. Today it is located by `(title, tradition)`
  (the `major_tradition` query param is dropped with §2.5).

The front loads the tree (structure + order + region colour) and the documents, and composes every view
(group by region, attach books, colour by region).

> **To discuss — unify document identity to one stable `id`.** Today a document is addressed by a
> multi-field tuple in `/documents` while an embedding chunk is one id (`normalize_catalog_id(title)`). A
> single stable `id`, used by `/catalog`, `/documents?id=`, and the chunk metadata, would collapse the
> multi-param file locator and align identity across catalog / documents / embeddings. **Not decided.**

---

## 4. Data flow (target)

```
config/traditions.json   region → {colour(base §8), description, subdivision, strata, traditions{name:{desc,coords}}}   ← source of truth; region+colour live here only
config/corpus.json       book → tradition (name)
        │  build: text files at corpus/<tradition>/<title>.txt; validate every book tradition ∈ tree
        │          & every region key ∈ 14 canon (fail loud). No generated traditions.json; no colour written.
        ▼
outputs/corpus/corpus.json      rows carry tradition ONLY (the reference) — no region, no colour, no major
outputs/embeddings/*            chunk metadata: tradition, url; region resolved at query; not re-embedded
        ▼  server  (reads config/traditions.json + outputs/corpus/corpus.json)
/api/corpus/traditions   config region → traditions tree (canon order, region colour + fields); no books
/api/corpus/catalog      documents: tradition + per-doc fields; no region, no colour
/api/corpus/documents    raw text, located by (title, tradition)
        ▼  front  (composes)
loads the tree + the documents → group by region, attach books, colour by region; one 14-region legend
```

---

## 5. Migration order (region-only; each phase shippable)

1. **Author the config + validation.** Build `config/traditions.json`: 14 region nodes in canon order, each
   with its canon fields (`colour` base + `description`/`subdivision`/`strata`) and only its texted
   traditions; `config/corpus.json` books reference the tradition by name; build-time fail-loud validation
   (unknown tradition / non-canon region). *(Highest value-to-risk — closes the silent join.)*
2. **`major_tradition` → `region`; drop it from records and the path.** Rename the field across `builder.py`,
   `iterator.py`, `CorpusFileInfo`, `schemas.py`, services, and the front; values come from the re-partitioned
   tree. Remove `SearchResult.major_tradition`. Stop writing `major`/`region` onto document rows. Move the
   file layout to `corpus/<tradition>/<title>.txt`; `/documents` located by `(title, tradition)`.
3. **Colour from region; serve the config, drop the generated file.** Remove `_update_traditions` and
   `get_tradition_color`; `/api/corpus/traditions` serves the config tree directly (region tree, region
   colour + fields, no books); a tradition's colour is its region's, computed at display; strip `region` and
   `colour` from the `corpus.json` rows and `/catalog`.
4. **Front composes.** Remove the client-side `groupDocuments`; render the `region → traditions` tree in canon
   order; attach books from the documents; colour = region base.
5. **One `UNASSIGNED`** across `schemas.py`, `iterator.py`, and the front end.

Tests are rewritten to the new model as each phase lands.

---

## 6. Out of scope

Motif `theme`/`stratum`; the connectivity axis, dating, the residual (science); the motif-areal region system
(§2.7); any facet (`family`/`subsistence`/`theme_profile`); catalogue imports/joins; re-validation of the
frozen 12-area analyses.
