# Proposal: wiring `region` into production — the plan

- **Status:** proposal (open, decisions settled; one item flagged to discuss — §3). Not implemented.
- **Scope:** the **code layer only** — one config, build, serve, front — for the text-processing pipeline.
  Taxonomy and presentation are closed (§0). Supersedes the code sections of
  [`tradition-architecture-unified.md`](archive/tradition-architecture-unified.md) §4/§6.

Grounded in the three field audits ([`../reviews/archive/tradition-review.md`](../reviews/archive/tradition-review.md),
[`../reviews/archive/major-tradition-review.md`](../reviews/archive/major-tradition-review.md),
[`../reviews/archive/color-system-review.md`](../reviews/archive/color-system-review.md)) and the canon
[`regions.md`](regions.md).

---

## 0. Closed decisions (context — not reopened)

- **`region` (14) is the sole classification axis** of a tradition. No facet layer. Canon: `regions.md`.
- **Colour lives only at the region level** — a tradition inherits its region's colour (single `color`,
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
    "color": "#CC503E",                  // single color, regions.md §8
    "description": "…",                  // regions.md §5
    "subdivision": "…",                  // regions.md §5
    "strata": "…",                       // regions.md §5
    "traditions": {                      // ONLY traditions that currently have texts
      "Yoruba": { "description": "…", "coordinates": [8, 4], "dating": "…" }
    }
  }
  // … all 14 regions …
}
```

`regions.md` stays the human canon; this file is its machine copy for the pipeline.

**`description` carries *what*; a separate field carries *when* — both optional at every level, and the date
never goes in `description`.**

| Entity | *what* → `description` | *when* → its own field |
|---|---|---|
| **region** | why the region is one unit (taxonomy rationale) | `strata` — dated historical layers |
| **tradition** | what the mythology is (the subject) | `dating` — culture + fixation |
| **document** (`config/corpus.json`) | what the specific text/edition is (the source) | `dating` — source composition + edition/translation |

`dating` is **free text** — ranges, `~`, BCE/CE — for example:
- tradition `"Culture ~8th–13th c. CE (Viking Age); written down (Eddas) ~13th c. CE"` (culture and fixation
  often diverge for oral traditions; they nearly coincide for early-literate ones like Sumerian/Egyptian);
- document `"OT ~1200–165 BCE, NT ~50–120 CE; KJV translation 1611"` (a text's composition and the edition we
  hold are two dates).

`region.subdivision`, `region.strata`, and every `description` / `dating` field are optional.

**2.2 Name = id.** The region node key is the canon region name; the tradition key is the tradition name.
No slugs, no separate id field, anywhere.

**2.3 All 14 regions, only texted traditions.** Every region node is present; under each are only traditions
that currently have corpus texts. An **empty region is valid**, not a broken join. *(Consequence: the atlas and
any tradition map show only texted traditions — fewer points than the ~194-tradition mockup, by design.)*

**2.4 Curated, not derived.** The tradition list is our own curated artifact — `regions.md` §5 is the
composition reference. Nothing is imported or derived from Berezkin, `areal_path`, or any index.

**2.5 `major_tradition` → `region` = re-partition + remove from records.** In the **config tree**, the
top-level grouping is re-authored from the 13 eclectic groups into the 14 canon regions (Greek/Norse/Celtic →
`Europe`; `Mesopotamian` + `Abrahamic` → `Near East & North Africa`; …). In **code**, `major_tradition` is
retired: where it was a **stored field** (corpus rows, chunk metadata, `SearchResult`, the `/documents` query
param) it is **removed** — region is resolved from the tradition via the tree, never persisted on a record;
where code **grouped** by it, grouping is now by `region` through the tree. It is a renamed *concept*, not a
field that survives on records.

**2.6 Colour comes from the region and is not stored.** A tradition's colour is its region node's `colour`
in `config/traditions.json`, computed `tradition → region → colour` at display. `get_tradition_color` /
`random` and the colour injection in `get_catalog_documents` are removed; colour appears in no record.

**2.7 The motif-index region system is untouched.** Berezkin/ATU/TMI regions and their palette
(`services/motifs.py`, `sources/atu_regions.py`, `sources/culture_dict.py`, `page-motifs.js::REGION_COLORS`)
stay exactly as they are. This is a different entity (motif areas, not tradition regions).

**2.8 Backend owns structure + order; the front composes views, from one global load.** The backend serves two
things: the `region → traditions` **tree** (canon order, from the config) and the **raw documents**. The front
fetches both **once, globally, into shared state**, and every section (corpus, atlas, embeddings, search)
composes its view from that one cache — grouping by region, attaching each tradition's books (from the
documents), colouring by region. Books are **not** baked into the traditions payload; the client-side
`groupDocuments` reconstruction is removed (structure and order come from the served tree).

**2.9 Serve the config directly; no generated `traditions.json`.** `config/traditions.json` is the source of
truth; `/api/corpus/traditions` returns its tree as-is. `_update_traditions` and the built
`outputs/corpus/traditions.json` are removed.

**2.10 The documents list carries the tradition only.** `/api/corpus/documents` (renamed from `/catalog`) documents carry `tradition` (the
reference) and per-document fields (`title`, `url`, counts, `description`, `dating`, `source`, and a document
`id` — pending §3 to-discuss) — **no `major_tradition`, no `region`, no `colour`**. Region is resolved from
the tradition via the tree; colour from the region.

**2.11 Filename sanitisation.** Any name that ends up in a file path (`sanitize_filename`) is made
filesystem- and URL-safe deterministically: trim; replace every run of whitespace with a single `_`; replace
`/ \ * ? : " < > | & % # '` and control characters with `_`; collapse repeated `_`; strip leading/trailing
`_` and dots; forbid `..`. Case is preserved (the name is the key). This closes the current gap — `&` (region
names), `%`, `#`, `'` — and applies to whichever names the chosen file layout puts in the path (§3
to-discuss).

**2.12 Fail-loud validation.** Every `corpus.tradition` must exist in the tree, and every region key must be
one of the 14 canon names — otherwise the build fails. Replaces the silent `.get(...)` degradations
(`builder.py:210`, `services/corpus.py:25`).

**2.13 Chunks carry the tradition only; no re-embedding.** A chunk's metadata keeps the `tradition` reference
(FK) and `url`; `region` is resolved from `tradition` via the tree at query time and is **not** stored on the
chunk. New builds stop writing `major_tradition`/`region` into chunk metadata; existing chunks keep their stale
`major_tradition` (ignored, gone on the next natural rebuild) — nothing is re-embedded. `region` is
deliberately not baked in: a tradition's region is re-annotatable, and baking it would force a re-embed on
every re-annotation.

**2.14 One `UNASSIGNED`** id/label across `schemas.py`, `iterator.py`, and the front end (extend the front's
`CATEGORY_NONE` down to the value layer).

**2.15 Accept the `stratum`/`Strata` overload.** The motif `stratum` field and `regions.md` §5's authored
`strata` share a name; no rename.

---

## 3. Target API surface (corpus ↔ front)

Two data endpoints (two projections) + one text fetch + search; the front loads the tree and the documents
once (globally, cached, §2.8) and composes every view. Overlap is trimmed to the `tradition` key.

> **Endpoint rename (planned).** `/catalog` → **`/documents`** (the documents list) and the old one-text
> `/documents` → **`/document`** (one text, by `?id=`). This aligns with the codebase's single-item idiom
> `GET /api/motifs/{index}/motif?id=` — **plural = the collection, singular + `?id=` = one item.** Throughout
> this doc: `/documents` is the list, `/document?id=` is one raw text. (Any lingering `/catalog` / one-text
> `/documents` below reads under this mapping.)

- **`GET /api/corpus/traditions`** → the `region → traditions` tree, canon order:
  `region → { colour, description, subdivision, strata, traditions: [ { name, coordinates, description, dating } ] }`.
  No books, no per-tradition colour. Consumers: atlas (coordinates + book-join), embeddings (colour via
  region + coordinates), corpus browser (grouping skeleton + order).
- **`GET /api/corpus/documents`** *(renamed from `/catalog`)* → documents: `[ { title, tradition, url, word/sentence/char counts,
  description, dating, source } ]` (+ a document `id`, pending — see “To discuss”). Tradition only; region/colour
  resolved on the front from the tree; the front joins books from these documents.
- **`GET /api/corpus/document`** *(renamed from `/documents`)* → the raw text of one document, addressed by
  `?id=` once the stable id lands (working default: `(title, tradition)`); the `major_tradition` param is
  dropped with §2.5.
- **`GET /api/similarity/*`** → search hits, one per chunk: `{ id, chunk_index, similarity_score, text,
  source_text }` **plus the document reference it belongs to**. `major_tradition` is removed; `tradition`,
  `url`, `region`, and `colour` are **not** carried — the front resolves them from the globally-cached
  document and tree via the reference. The per-hit payload is the smallest it can be: chunk-specific data + a
  pointer.

> **Resolved → see [`data-model-and-ids.md`](data-model-and-ids.md).** Document identity, the three
> registries, field decomposition, `slugify` and the join keys are worked out there: `document_id =
> slugify(title)` (single key, not composite; uniqueness-checked), ids minted once and stored, `slugify`
> run only on the backend. The original open questions are kept below for the reasoning trail.
>
> **To discuss — document identity & location (one connected decision, items 1/2/4).** Three entangled
> questions, answered together:
> 1. **A single stable document `id`.** Today a document is addressed by the tuple `(title, tradition)` in
>    the one-text endpoint, while an embedding chunk is one id (`normalize_catalog_id(title)`). One stable `id`, used
>    by `/documents` (list), `/document?id=`, the search reference, and the chunk metadata, collapses the multi-param
>    locator and aligns identity across list / document / embeddings / search.
> 2. **File layout — follows from (1).** `corpus/<region>/<tradition>/<title>.txt` (region in the path),
>    `corpus/<tradition>/<title>.txt` (region out, keyed by the stable tradition), or `corpus/<id>.txt` (keyed
>    by the id, no classification in the path). More decoupling ⇢ fewer file moves on re-annotation, less
>    on-disk navigability. `sanitize_filename` (§2.11) covers whatever names the chosen layout puts in the
>    path.
> 3. **The catalog `id` field and the search reference** both presuppose (1).
>
> **The underlying question — name-as-id vs a stable id, per level.** `name = id` (§2.2) makes the display
> string the identity, which fails in known ways: renaming a name breaks every reference (config caught by
> validation, but chunks go stale → re-embed); two distinct names that sanitise to the same path collide; and,
> at the **document** level, the chunk id is `normalize_catalog_id(title)` — **title only** — so two books that
> share a title (generic ones like "Creation", "Folk Tales") collide at the embedding layer already. These bite
> unevenly:
> - **tradition / region** — names are short, unique, and rarely renamed; `name = id` is tolerable (the main
>   risk — a rename forcing a re-embed — is a rare deliberate edit).
> - **document** — `title = id` is the weakest: generic-title collisions are real, not hypothetical, and it is
>   the id that reaches `/documents`, the catalog, the search reference, and the chunk metadata.
>
> **Leaning:** keep `name = id` for **tradition / region**; give the **document** a separate stable `id` (not
> the title). That id is then the one used across `/documents` (list), `/document?id=`, the search reference, and the
> chunk metadata (settles 1 and 3), and it narrows the layout (2) to `corpus/<id>.txt` or
> `corpus/<tradition>/<title>.txt`. Open sub-question: how the document id is minted (slug of
> `tradition + title`, or a synthetic stable key).
>
> **Not decided.** Working default until then: `/document` and the path use `(title, tradition)` with region
> out of the path; search carries `id` = `normalize_catalog_id(title)`.

---

## 4. Data flow (target)

```
config/traditions.json   region → {color(§8), description, subdivision, strata, traditions{name:{desc,coords}}}   ← source of truth; region+color live here only
config/corpus.json       book → tradition (name)
        │  build: text files under corpus/… (layout pending — §3); validate every book tradition ∈ tree
        │          & every region key ∈ 14 canon (fail loud). No generated traditions.json; no colour written.
        ▼
outputs/corpus/corpus.json      rows carry tradition ONLY (the reference) — no region, no colour, no major
outputs/embeddings/*            chunk metadata: tradition, url; region resolved at query; not re-embedded
        ▼  server  (reads config/traditions.json + outputs/corpus/corpus.json)
/api/corpus/traditions   config region → traditions tree (canon order, region colour + fields); no books
/api/corpus/documents    documents list: tradition + per-doc fields; no region, no colour   (renamed from /catalog)
/api/corpus/document     one raw text, by ?id= (working default (title, tradition))          (renamed from /documents)
/api/similarity/*        search hits: chunk data + document reference; no major/region/colour
        ▼  front  (loads the tree + the documents ONCE, global cache, and composes)
group by region, attach books, colour by region; one 14-region legend; reused by corpus/atlas/embeddings/search
```

---

## 5. Migration order (region-only; each phase shippable)

1. **Author the config + validation.** Build `config/traditions.json`: 14 region nodes in canon order, each
   with its canon fields (`color` + `description`/`subdivision`/`strata`) and only its texted
   traditions. **Reconcile the dirty corpus tradition strings to canonical keys** (e.g. `"Australian"` vs
   `"Australian Aboriginal"` → one canonical name) and repoint every `config/corpus.json` book at its
   canonical tradition; then add build-time fail-loud validation (unknown tradition / non-canon region).
   *(Highest value-to-risk — closes the silent join.)*
2. **Retire `major_tradition`; group by region; trim search.** Re-partition the config tree to regions; update
   the code that **grouped** by `major_tradition` (`builder.py`, `iterator.py`, `schemas.py`, services, front)
   to group/resolve by `region` through the tree. Remove `major_tradition` as a **stored field**: from corpus
   rows, from `CorpusFileInfo`/chunk metadata (new builds; existing chunks not re-embedded), from the
   one-text endpoint's query param; delete `SearchResult.major_tradition` and trim search hits to chunk data + a
   document reference (`tradition`/`url`/`region`/`colour` resolved on the front). Move the file layout per the
   §3 identity decision (working default `corpus/<tradition>/<title>.txt`). **Rename the endpoints** (§3):
   `/catalog` → `/documents` (list), `/documents` → `/document` (one text) located by `(title, tradition)`.
3. **Colour from region; serve the config, drop the generated file.** Remove `_update_traditions` and
   `get_tradition_color`; `/api/corpus/traditions` serves the config tree directly (region tree, region
   colour + fields, no books); a tradition's colour is its region's, computed at display; strip `region` and
   `colour` from the `corpus.json` rows and `/documents` (the renamed list).
4. **Front composes from one global load.** Fetch `/traditions` + `/documents` once into shared state; remove the
   client-side `groupDocuments`; render the `region → traditions` tree in canon order; attach books from the
   documents; color = region `color`; reuse the cache in corpus/atlas/embeddings/search.
5. **One `UNASSIGNED`** across `schemas.py`, `iterator.py`, and the front end.

Tests are rewritten to the new model as each phase lands.

---

## 6. Out of scope

Motif `theme`/`stratum`; the connectivity axis, dating, the residual (science); the motif-areal region system
(§2.7); any facet (`family`/`subsistence`/`theme_profile`); catalogue imports/joins; re-validation of the
frozen 12-area analyses.
