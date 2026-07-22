# Proposal: wiring `region` into production — the plan

- **Status:** proposal — **all decisions settled** (the §3 document-identity question is resolved: D1 =
  `document_id = hash(locator)`; the file layout is decided in §6). Not implemented.
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
- **Only the region `color` is stored** (single value, `regions.md` §8) — a tradition's colour is a
  within-region **shade derived** from that base at display (OKLCH lightness/chroma gradient, `regions.md` §8.1).
- **Out of scope:** motif `theme`/`stratum`, the connectivity axis and dating (science), and **the entire
  motif-areal region system** (§2.7).

---

## 1. Current state (the problem)

The live axis is still `tradition` (free string) → `major_tradition` (derived) → `colour` (random); `region`
is not wired in.

- **Free-string identity & join.** Books hold a hand-written `tradition` string (`config/corpus.json`, 27
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

**2.6 Colour comes from the region and is not stored — including the per-tradition shade.** Only the region
node's single `colour` is stored in `config/traditions.json`. A tradition's colour is **derived at display**
as a within-region shade off that base — `tradition → region base → shade(index, region tradition-count)` —
per the OKLCH lightness/chroma rule in [`regions.md`](regions.md) §8.1 (reverses the old flat-inherit rule).
`get_tradition_color` / `random` and the colour injection in `get_catalog_documents` are removed; **no colour
— region or tradition — appears in any record.** The per-tradition shade is a pure function of `(region base,
tradition index, count)`, so it stays fully resolved, never denormalized — the same invariant as B1/D1 (colour,
like tradition and region, is computed from stable references, not written into the derived stores). The shade
is deterministic given the tree, so the front computes it from the globally-cached tree with no new payload.

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
reference) and per-document fields (`title`, `url`, counts, `description`, `dating`, `source`, and the
`document_id` = `hash(locator)`, D1) — **no `major_tradition`, no `region`, no `colour`**. Region is resolved
from the tradition via the tree; colour is the region's derived per-tradition shade (§8.1).

**2.11 Filename sanitisation.** Any name that ends up in a file path (`sanitize_filename`) is made
filesystem- and URL-safe deterministically: trim; replace every run of whitespace with a single `_`; replace
`/ \ * ? : " < > | & % # '` and control characters with `_`; collapse repeated `_`; strip leading/trailing
`_` and dots; forbid `..`. Case is preserved (the name is the key). This closes the current gap — `&` (region
names), `%`, `#`, `'` — and applies to the region/tradition/title names the decided file layout puts in the
path (`corpus/<Region>/<Tradition>/<Title>.txt` — §6).

**2.12 Fail-loud validation.** Every `corpus.tradition` must exist in the tree, and every region key must be
one of the 14 canon names — otherwise the build fails. Replaces the silent `.get(...)` degradations
(`builder.py:210`, `services/corpus.py:25`).

**2.13 Chunks carry one document reference only (B1); no re-embedding.** A chunk's metadata is exactly
`{document_id, chunk_index}` — **no** `tradition`, `major_tradition`, `region`, `url`, or `colour`. Everything
else is resolved from `document_id` at query time: `document_id → document` gives `tradition`/`url`/title (via
the catalog), and `tradition → region → colour` follows the tree. New builds stop writing
`tradition`/`major_tradition`/`region` into chunk metadata. **Dropping those fields on its own forces no
re-embed** (they are metadata, not vectors — existing chunks keep the stale fields, ignored, gone on the next
rebuild). *(Part 1 as a whole still re-embeds everything, but for a different reason — the `document_id`
re-anchor changes every chunk PK, so the §6 wipe-and-rebuild re-embeds regardless; the B1 point is only that B1
adds no re-embed cost of its own.)* Nothing name-derived is baked in: tradition,
region, and colour are all re-annotatable config, and baking any of them would force a re-embed on every
re-annotation. **This makes the cross-tradition search filter the single localized consequence** — with no
`tradition` on the chunk, `get_point` resolves tradition → documents server-side and filters
`where {document_id: {$nin: docs-of-that-tradition}}` (see §5 step 4).

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
- **`GET /api/corpus/documents`** *(renamed from `/catalog`)* → documents: `[ { document_id, title, tradition, url,
  word/sentence/char counts, description, dating, source } ]`, where `document_id = hash(locator)` (D1).
  Tradition only; region/colour resolved on the front from the tree; the front joins books from these documents.
- **`GET /api/corpus/document`** *(renamed from `/documents`)* → the raw text of one document, addressed by
  `?id=document_id` (D1, = the raw-archive key); the `major_tradition` param is dropped with §2.5.
- **`GET /api/similarity/*`** → search hits, one per chunk: `{ id, chunk_index, similarity_score, text,
  source_text }` **plus the document reference it belongs to**. `major_tradition` is removed; `tradition`,
  `url`, `region`, and `colour` are **not** carried — the front resolves them from the globally-cached
  document and tree via the reference. The per-hit payload is the smallest it can be: chunk-specific data + a
  pointer.

> **Resolved → see [`data-model-and-ids.md`](data-model-and-ids.md).** Document identity, the three registries,
> field decomposition, id minting (no slug — D8 dissolved), and the join keys are worked out there. The two load-bearing decisions:
> - **D1 (decided): `document_id = hash(locator)`** — the document id anchors on its upstream locator (URL /
>   `sources/`-path), normalized then hashed with **`blake2b`**, which is the raw-archive key
>   `corpus/raw/<blake2b(url)>` (one algorithm everywhere; the archive moves off `sha1` by a one-time re-fetch on migration, §6 — or an offline rename).
>   It is opaque, rename-/edit-stable, collision-free, and one value serving identity + archive key + the
>   incremental anchor. It is **not** `slugify(title)` — titles churn and collide (generic ones like "Creation"
>   collide at the embedding layer), and a title-slug would need the locator as a hidden match key anyway.
>   `region_id`/`tradition_id` are the **canonical name itself** (no slug — D8 dissolved); documents use `hash(locator)`. There is no `slugify` anywhere.
> - **The single stable `id`** is this `document_id`, used across `/documents` (list), `/document?id=`, the
>   search reference, and the chunk metadata — collapsing the old `(title, tradition)` locator and the
>   ephemeral `normalize_catalog_id(title)` into one persisted key.
>
> **File layout is independent of the id (a rendering, not the identity).** Because `document_id` is opaque, the
> on-disk path is free to stay fully human-readable — `corpus/<Region>/<Tradition>/<Title>.txt` — and the
> catalog bridges `document_id ↔ path`. A region/tradition/title rename is then a `git mv` of the readable path
> (or a rebuild-from-raw), touching **neither** Chroma nor graphs (both keyed by the invariant `document_id`).
> **Decided: the full nested `corpus/<Region>/<Tradition>/<Title>.txt`** (data-model §6) — it optimises the
> rendering layer for browsability, and the only cost (disk-churn on rename) is negligible and never a re-embed.

---

## 4. Data flow (target)

```
config/traditions.json   region → {color(§8), description, subdivision, strata, traditions{name:{desc,coords}}}   ← source of truth; region+color live here only
config/corpus.json       book → tradition (name)
        │  build: text files at corpus/<Region>/<Tradition>/<Title>.txt (§6, sanitize_filename); validate every book tradition ∈ tree
        │          & every region key ∈ 14 canon (fail loud). No generated traditions.json; no colour written.
        ▼
outputs/corpus/corpus.json      rows carry tradition ONLY (the reference) — no region, no colour, no major
outputs/embeddings/*            chunk metadata: document_id + chunk_index ONLY (B1); tradition/region/url resolved at query; not re-embedded
        ▼  server  (reads config/traditions.json + outputs/corpus/corpus.json)
/api/corpus/traditions   config region → traditions tree (canon order, region colour + fields); no books
/api/corpus/documents    documents list: tradition + per-doc fields; no region, no colour   (renamed from /catalog)
/api/corpus/document     one raw text, by ?id=document_id (hash(locator), D1)                (renamed from /documents)
/api/similarity/*        search hits: chunk data + document_id reference (B1); no tradition/major/region/colour
        ▼  front  (loads the tree + the documents ONCE, global cache, and composes)
group by region, attach books, colour = region base + derived per-tradition shade (regions.md §8.1); 14-region legend; reused by corpus/atlas/embeddings/search
```

---

## 5. Implementation order — **Part 1 of 4: the data-model + region migration** (the priority)

**This is the single, ordered task list for the whole migration** — not "region" alone: it ships the **id/data
model** (`document_id = hash(locator)`, name-ids, the B1 chunk, the file layout) *and* the **`region` feature**
(the 14-region tree, region-derived colour, grouping). It is self-contained — the id/data tasks are folded in
here, so `data-model` §8 only points back. The other three parts live in
[`pipeline-and-incrementality.md`](pipeline-and-incrementality.md) §7 and **do not block this one**: **Part 2**
= incrementality base, **Part 3** = the stage-protocol refactor (big; deferred), **Part 4** = manual text
curation. Each step below is shippable.

Dependency spine: silent join first (pure config) → `document_id` persisted before anything references it →
front resolution before any field is trimmed off a chunk/hit → then the trim → colour → cleanup.

1. **Author the config + validation.** Build `config/traditions.json`: 14 region nodes in canon order, each
   with its canon fields (`color` + `description`/`subdivision`/`strata`) and only its texted traditions
   (`region_id`/`tradition_id` = the canonical **name**, no slug — §6). **Reconcile the dirty corpus tradition
   strings to the canonical keys per the decided table (§6.1)** — incl. the canon extension `Euahlayi` — and
   repoint every `config/corpus.json` book at its canonical tradition; then add build-time fail-loud validation
   (unknown tradition / non-canon region; name-uniqueness). *(Highest value-to-risk — closes the silent join.)*
2. **Persist identity.** Persist `document_id = hash(locator)` in the built catalog (normalize the locator
   first, then `blake2b`; it is the raw-archive key `corpus/raw/<blake2b(url)>` — repopulated off `sha1` by the §6 re-fetch)
   and return it from the documents endpoint; mint
   `region_id`/`tradition_id` = the canonical name in the tree + as each document's `tradition` ref. `id = the
   name` verbatim — no slug, no transliteration, no new function; the boundaries already sanitise
   (`sanitize_filename` FS / `encodeURIComponent` URL / `escapeHtml` HTML) — spec in data-model §5. *(Must
   precede B1 and the `?id=` endpoint.)*
3. **Front indexes + resolution — before any trim.** Fetch `/traditions` + `/documents` once into shared state
   → `treeIndex`/`docIndex`; resolve `document_id → document → tradition → region → colour`; delete
   `bookTitleFromId`. *(Order-critical: the front must resolve from the reference before step 4 strips fields,
   or a hit loses data with nothing to resolve it.)*
4. **Retire `major_tradition`; group by region; trim chunk metadata to one reference (B1).** Re-partition the
   config tree to regions; update the code that **grouped** by `major_tradition` (`builder.py`, `iterator.py`,
   `schemas.py`, services, front) to group/resolve by `region` through the tree. Reduce **chunk metadata to a
   single document reference `{document_id, chunk_index}` (B1)** — drop `major_tradition`, `tradition`, and
   `url` as stored chunk fields (new builds; existing chunks not re-embedded). Correspondingly drop these from
   corpus rows / `CorpusFileInfo`; delete `SearchResult.major_tradition` and trim search hits to chunk data +
   the document reference. **Cross-tradition search filter (B1):** `get_point` resolves tradition → documents
   server-side and filters `where {document_id: {$nin: docs-of-that-tradition}}` (was a `tradition`-equality
   clause). Move the file layout to `corpus/<Region>/<Tradition>/<Title>.txt` (§6). Switch the embeddings dedup
   **anchor** from `slug(title)::i` to `document_id::i` — **rename-churn is fixed here for free**; the
   content-`fingerprint` *staleness* gate that completes the key (chunk `fingerprint` = `hash(doc fingerprint, model, transform_v)`) is **Part 2**
   (pipeline §7 item 1), not this step. **Rename the
   endpoints** (§3): `/catalog` → `/documents` (list), `/documents` → `/document` (one text) by `?id=document_id`.
5. **Colour from region; serve the config, drop the generated file.** Remove `_update_traditions` and
   `get_tradition_color`; `/api/corpus/traditions` serves the config tree directly (region tree, region
   colour + fields, no books); strip `region` and `colour` from the `corpus.json` rows and `/documents`.
   **Implement the per-tradition shade function** (new work — regions.md §8.1): OKLCH, fix `H`/`C`, vary `L`
   on the safe band, grow-then-clamp centred on the base, order by longitude, L×C lattice for N > 12,
   light/dark bands. Pure function of `(region base, tradition index, region count)`, computed at display —
   nothing stored. The front then colours by this derived shade.
6. **Cleanup.** One `UNASSIGNED` across `schemas.py`, `iterator.py`, the front; graphs — unify build/serve on
   the stored `document_id` + traversal guard.

**Tests — rewrite to the new model, and pin the invariants the migration exists to protect.** The suite (36
files) is written against the *old* model (`text_id = slug(title)`, `tradition`/`major_tradition` on the chunk),
so "rewrite as each step lands" is not enough on its own — the point of the migration is a set of behaviours that
must not silently regress, so name them as regressions rather than trusting green tests written to the old shape:

- **id stability** — a `title`/`tradition`/`region` rename leaves `document_id` (and the Chroma PKs, graph dir)
  byte-identical; a `url`/`sources`-path change *does* move it (D1);
- **locator normalization** — the two cosmetic-variant URLs of data-model §5 (host case, trailing slash,
  `%7E`≡`~`, dropped fragment) hash to the **same** id; a query-string or path-case difference does **not**;
- **the fp gate (the original bug)** — editing `content_start/end` or the cleaned text **re-embeds** the doc's
  chunks (flaw 2 fixed); a pure rename does **not** re-embed (flaw 1 fixed);
- **B1 resolution** — `document_id → tradition → region → colour` resolves correctly with **nothing**
  tradition/region/colour on the chunk; a tradition re-annotation changes the resolved colour with **zero**
  Chroma writes;
- **cross-tradition filter** — `get_point` returns the `document_id $nin` set equivalent to the old
  `tradition != X` clause;
- **fail-loud** — an unknown `corpus.tradition`, a non-canon region key, or a duplicate name **fails the build**
  (not a silent `.get()` default).

---

## 6. Migration & data integrity

**Prerequisite decisions.** The document-identity anchor and its knock-ons live in
[`data-model-and-ids.md`](data-model-and-ids.md) §9. **Decided:** **D1** `document_id = hash(locator)` (the
raw key `corpus/raw/<blake2b(url)>`; opaque, rename-stable; *not* `slugify(title)`); **`region_id`/`tradition_id` = the
canonical name** (kept verbatim, at most the existing `normalize_catalog_id` for whitespace; no slug, no
transliteration, no new function — boundaries already sanitise via `sanitize_filename`/`encodeURIComponent`/`escapeHtml` — `data-model` §5; **D8
dissolved**); the **tradition reconciliation** table (§6.1 below); and the **file layout** — **decided: full
nested `corpus/<Region>/<Tradition>/<Title>.txt`** (`sanitize_filename`-cleaned names; opaque `document_id`
stays out of the path, the catalog bridges id ↔ path). The `.txt` tree is a pure human-rendering layer —
identity is decoupled (Chroma/graphs key on `document_id`, never move on rename), so the path optimises for
browsability; churn is negligible (27 files, regenerable, `git mv`) and the 14-region canon is stable. Flat-by-id
and tradition-only were rejected (`data-model` §6). **Nothing left open.**

### 6.1 Tradition reconciliation (decided 2026-07)

The corpus carries 22 dirty `tradition` strings across 27 books; the current `config/traditions.json` is the
*old* 12-group scheme. Each book is repointed to a **canonical tradition** under the **14-region canon**
(`regions.md` §5 / the 194-tradition list). The canon **is a mix** — ethnolinguistic where natural, but with
religion-level nodes (Christian, Islamic, Jewish, Hindu, Vedic, Buddhist, Jain, Sikh, Zoroastrian) — so most
religion strings map **directly**; only **East Asia** is religion-free, which is why the Confucian/Taoist/
Japanese-Buddhist strings collapse to their ethnolinguistic node.

| corpus `tradition` (books) | → canonical tradition | region | kind |
|---|---|---|---|
| Ancient Egyptian | **Egyptian** | Near East & N. Africa | rename |
| Babylonian ×2 | Babylonian | Near East & N. Africa | direct |
| Greek ×2, Norse, Roman, Celtic, Finnish, Anglo-Saxon | *(unchanged)* | Europe | direct |
| Germanic (Nibelungenlied) | **Continental Germanic** | Europe | rename |
| Chinese | Chinese | East Asia | direct |
| Maori | Maori | Austronesia | direct |
| Maya | Maya | Mesoamerica & the Andes | direct |
| Christianity (KJV Bible) | **Christian** | Near East & N. Africa | religion → canon religion |
| Islam (Koran) | **Islamic** | Near East & N. Africa | religion → canon religion |
| Buddhism (Dhammapada) | **Buddhist** | South Asia | religion → canon religion |
| Hinduism ×4 | **Hindu** | South Asia | religion → canon (all 4; **not** split Vedic) |
| Confucianism (Analects) | **Chinese** | East Asia | **collapse** (no canon Confucian node) |
| Taoism (Tao Teh King) | **Chinese** | East Asia | **collapse** |
| Japanese Buddhism (Buddhist Psalms) | **Japanese** | East Asia | **collapse** to ethnolinguistic |
| West African (Anansi tales) | **Akan/Ashanti** | Sub-Saharan Africa | Gold-Coast/Anansi source |
| Polynesian (Westervelt, Māui) | **Hawaiian** | Austronesia | pan-Polynesian text; Hawaiian-dominant |
| Australian Aboriginal (K.L. Parker) | **Euahlayi** | Papua & Aboriginal Australia | source = Euahlayi (NSW) |

**Canon extension:** `Euahlayi` is **added** to the 14-region canon (Papua & Aboriginal Australia) — the
Parker tales are specifically Euahlayi/Noongahburrah and no existing node fits. This grows that region's
tradition list (and the 194→195 count); update `regions.md` §5 and the canon tradition list accordingly when
the config is authored. (`Confucianism`+`Taoism`+`Chinese` collapsing to one `Chinese` node, and `Japanese
Buddhism`→`Japanese`, are deliberate — East Asia is modelled ethnolinguistically.)

**Integrity principle.** Everything under `outputs/` is **derived and regenerable**. The committed sources of
truth are **`config/` and `sources/`** (local `file:` inputs); **`corpus/raw/` is a cache** — authoritative
on disk while present, but re-fetchable from `config` (a `--caches`-only export, never committed). Coherence
after the migration is *restored by a clean rebuild* off the re-keyed raw, not by in-place metadata surgery. At
~27 documents this is cheap.

**Why this migration re-keys offline (no re-fetch).** D1 re-keys the raw archive `sha1(url) → blake2b(locator)`.
Since **raw is a cache, never committed** (decided — raw is `--caches`-only in export, held on disk, not in git),
there is no committed fallback to restore from, so the migration does **not** re-fetch: it **re-keys the existing
on-disk raw in place** — for each config document compute `old = sha1(url)`, `new = blake2b(normalized-locator)`,
and `mv old new`. The bytes are identical; only the key changes. This needs no network, so a dead/404 source
during migration **cannot lose data** (nothing is re-downloaded). Only a genuinely-**missing** doc (new in
config, no raw) is fetched — ordinary acquire-on-miss. `--force` is not needed.

**Procedure — full rebuild off the re-keyed (not re-fetched) blake2b archive:**

1. **Commit `config/` + code** (the only committed sources of truth). **Do not commit `corpus/raw/`** — raw is a
   cache (never committed, `--caches`-only in export). The rollback is git for config/code; the raw bytes are
   preserved simply by *not deleting* them (the re-key renames them in place — step 4).
2. **Author + reconcile:** write the new `config/traditions.json` (14 regions, canon order, texted traditions
   with coordinates); repoint every `config/corpus.json` book at its canonical `tradition`.
3. **Blanket-wipe the derived artifacts.** Delete the `.txt` tree + `corpus.json`, `outputs/embeddings/`,
   `outputs/graphs/`, `outputs/projections/`, `outputs/preprocessed/`. **Leave `corpus/raw/` in place** — it is
   about to be re-keyed, not wiped.
4. **Re-key the raw in place, then plain `build`.** For each `config/corpus.json` document rename its raw file
   `sha1(url) → blake2b(normalized-locator)` (normalize per data-model §5, then hash) — same bytes, new key, no
   network. Then `build`: `fetch_to_cache(force=False)` now **finds the re-keyed raw present** (offline), re-cleans,
   re-embeds (chunk metadata = `{document_id, chunk_index}` only — B1; no `tradition`/`major_tradition`), and
   re-graphs from the new config. Local `sources/` files re-read from disk. Only a doc **new in config** (no raw)
   is fetched — ordinary acquire-on-miss; a dead source there is a normal flag, not data loss (nothing existing
   is re-fetched). **Fail-loud validation** (every corpus tradition ∈ tree; every region ∈ the 14 canon;
   name-uniqueness across region/tradition + a `document_id` collision check) is the integrity gate.
5. **Front in lockstep** with the API change (endpoint renames, dropped fields, `treeIndex`/`docIndex`, remove
   `bookTitleFromId`) — or the UI breaks.
6. **Verify with `status`** — orphan detection should report zero (nothing was left behind, since the derived
   tree was wiped before the rebuild).

Because the rebuild derives everything from the intact (re-keyed) `raw/` under fail-loud validation, the
post-migration state is coherent by construction. The only things that must be protected in **git** are
**`config/` and `sources/`**; `corpus/raw/` is a cache (protect on disk / `--caches` backup if you want to avoid
a re-fetch, but it is regenerable from `config`).

---

## 7. Out of scope

Motif `theme`/`stratum`; the connectivity axis, dating, the residual (science); the motif-areal region system
(§2.7); any facet (`family`/`subsistence`/`theme_profile`); catalogue imports/joins; re-validation of the
frozen 12-area analyses.
