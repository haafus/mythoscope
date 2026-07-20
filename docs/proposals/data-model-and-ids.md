# Corpus data model — registries, ids & joins

How corpus data is split across three registries, how the pieces address and join each other, and how
identifiers are minted. This resolves the document-identity question left open in
[`region-implementation.md`](region-implementation.md) §3 ("To discuss"). Companion:
[`pipeline-and-incrementality.md`](pipeline-and-incrementality.md) — *when* artifacts rebuild, caches, GC and
source management.

The guiding principle throughout: **store each field at its natural owner; denormalize downward only for
a server-side need; resolve everything else upward through load-once front indexes.**

---

## 1. The three registries

```
tree (region → tradition)   low cardinality (14 regions, ~hundreds of traditions)
   ↑ tradition → region is a FUNCTION (via the tree)
document (a book)           medium (tens–hundreds)
   ↑ document → tradition is a reference
chunk (an embedded fragment)  HIGH (thousands–tens of thousands)
   ↑ chunk → document is a reference
```

| registry | source of truth | addressed by | serves |
|---|---|---|---|
| **tree** | `config/traditions.json` → `/api/corpus/traditions` | `region_id`, `tradition_id` | region/color/geo, classification, order |
| **documents** | catalog `outputs/corpus/corpus.json` → the documents list | `document_id` (= `text_id`) | title, url, counts, description, source |
| **embeddings** | Chroma collection | Chroma PK (opaque, see §5) | the vectors + per-chunk text |

**Invariant: resolution always runs upward** — `chunk → document → tradition → region` — and each hop is an
O(1) look-up into a load-once index. Cardinality grows downward, so **duplicating a field costs more the
lower it lives** (a field on the chunk is multiplied by tens of thousands).

---

## 2. Join keys

Distilled from every frontend section (corpus browser, atlas, embeddings scatter, graphs, search;
`motifs` is a separate domain and does not join this triple):

- **`tradition_id` is the universal presentational join.** Color, geography, grouping, attribution — every
  section keys on it. It lives on the tree (PK), the document (ref) and the chunk (ref + filter).
- **`document_id` (= `text_id`) is the document key.** Corpus text fetch, graphs, and chunk→document all use
  it. It is a **single key, not a composite** (see §5).
- **A chunk carries exactly two upward references: `document_id` and `tradition_id`.** Nothing else
  document- or region-level is stored on it.

`major_tradition` is **not** a join axis — it is redundant (a function of `tradition`) and is dropped.

---

## 3. Field placement (the decomposition)

**Decision rule.** A field is stored at its normalized owner. A copy is pushed **down** onto a lower entity
only if **(i)** a scenario needs it at that entity's query time **and (ii)** resolving it upward then is
infeasible/too slow. For the **chunk**, (ii) is true only for **server-side `where`-filter keys** (Chroma
filters before the client can resolve). For everything else, front-side resolution via load-once indexes
wins.

**The real drivers are volatility and single-source, not payload size.** Earlier the argument leaned on
network payload (C2), but the projection view (§4) is a *precomputed* file that does not echo Chroma
metadata, so per-chunk fields do not bloat it. The load-bearing reasons to keep a field off the chunk are:

- **Volatility** — a value that changes (palette swap, region re-annotation, title/url edit), if copied onto
  the chunk, goes stale until a rebuild.
- **Single source of truth** — a second copy drifts.

Payload size is a minor, secondary consideration (Chroma on-disk storage; small `top_k` search/points
responses).

| field | owner | on chunk? | rationale |
|---|---|---|---|
| vector, text, source_text, chunk_index | chunk | **yes** | intrinsic |
| `document_id` (ref) | chunk↔document | **yes** | irreducible upward pointer to the document |
| `tradition_id` (ref) | document→tree | **yes** | (a) Chroma `where` cross-tradition filter; (b) 1-hop `chunk→region/color` without loading the catalog |
| title | document | no | resolve via `docIndex[document_id]` — exact, no reconstruction |
| url | document | no | document-level; resolve on demand from the catalog |
| counts, description, source | document | no | corpus browser reads them from the catalog |
| region_id | tree (via tradition) | no | volatile (re-annotation); resolve `tradition_id → region` |
| **color** | tree (via region) | no | pure function of region + volatile (palette) — always resolve |
| coordinates, dating, subdivision, strata | tree | no | tree-only |

`tradition_id` earns its place on the chunk three ways, all free once it is the ref half: **`where`-filter,
1-hop region/color resolve, and the pointer needed anyway.** Because it is *stable* while region/color are
resolved *live* through the tree, a palette change or region re-annotation never stales a chunk.

---

## 4. The denormalizing layer

Denormalization belongs **not in Chroma chunk metadata**, but in two places:

1. **Front-side load-once indexes** (built once per session, rebuilt from source → never stale):
   - `treeIndex: Map<tradition_id, {region_id, color, coordinates}>` — from `/traditions`. Powers color/geo
     for every section, and the 1-hop chunk→region path.
   - `docIndex: Map<document_id, documentRow>` — from the catalog. Powers chunk→document (title, url,
     counts). Single-key, because `document_id` alone is unique (§5).
2. **Build-time materialized catalog** — `outputs/corpus/corpus.json` stores the document-level fields plus
   *expensive-but-stable* computed values (`word/sentence/char counts`, `md5`). A legitimate precompute.

**The projection view is the exemplar of the right pattern.** `projections/<model>/<method>.json` holds every
chunk as `{ id, tradition_id, chunk_index, text(preview), x, y }` — no url/title/region/**color**. Color is
resolved on the front from `treeIndex`. This is exactly why the palette swap did not require rebuilding the
projections: the *stable* key (`tradition_id`) is inlined, the *volatile* mapping (→ color) is resolved live.

---

## 5. Identifiers

### One `slugify`, three mint sites

Region, tradition and document names are **free-form display strings** — they may contain `&`, spaces,
non-ASCII, `/`, apostrophes (`Near East & North Africa`, `Tupí/Guaraní`, `Selk'nam`). They are **not**
constrained. Instead **one shared `slugify(name) → id`** derives a Chroma-, filesystem- and URL-safe id
(transliterate non-ASCII, lowercase, `&`→`and`, collapse the rest to `-`). It is **total** — it always
*produces* a safe id by construction, so there is no charset validator gate. The only build-time check is
**uniqueness: fail loud if two distinct names slug to the same id** (verified today: the 194 traditions
slug without collision). This replaces `normalize_catalog_id` (whitespace-only, misnamed, not fs-safe).

Three mint sites: `region_id = slugify(region name)`, `tradition_id = slugify(tradition name)`,
`document_id = slugify(title)`.

> The model registry (`model_registry.py`) uses the inverse pattern — an **authored** safe key plus a
> `key → label` humanizer — because its keys are hand-written. That does not fit free-form names, so we do
> not reuse its key regex as a validator; we write a name→id transform instead.

### `document_id` is a single key, not composite

`document_id` is a **single key** (not a `(tradition, title)` composite): `tradition_id` on the chunk is for
filtering and region resolution, **not** for document identity.

> **⚠ Open decision — what does `document_id` anchor on? (not resolved; see §9-D1.)** Two candidates, and this
> doc does **not** yet pick:
> - **`slugify(title)`** — human-readable, but **not rename-stable** (a title edit changes the id) and can
>   collide when two documents share a title (guard with the uniqueness check; fold `tradition_id` in only if a
>   real collision appears).
> - **`slug/hash(upstream-locator)`** (the URL / `sources/`-path — already the raw-archive key) — **rename- and
>   edit-stable**, collision-free, unifies identity + archive key + the incremental anchor
>   ([`pipeline-and-incrementality.md`](pipeline-and-incrementality.md) §4 wants exactly this), at the cost of
>   an opaque id (acceptable — navigability lives in the file path, not the id).
>
> The two docs currently lean different ways (this one wrote `slugify(title)`; pipeline §4 assumes a
> rename-stable anchor). **They must converge on one before implementation** — see §9-D1.

### Store the ids; never regenerate

Ids are **minted once at build and persisted** (`region_id`/`tradition_id` in the tree, `document_id` in the
catalog and as the chunk's `document_id` ref). They are **not** recomputed on the fly. This matters because
**ids are durable external keys** — Chroma PKs and graph-directory names, written with a specific value:

- if `slugify` improves, or a source name is edited, *recomputing* silently changes the id → reads miss the
  writes (orphaned vectors, lost graph folders). *Storing* freezes the id at write time so reads always
  match. This is the concrete content of "populate once" — it is load-bearing only because ids persist.

For **joins**, pass the **stored** ids; do not regenerate — especially not on the front (that would
reimplement `slugify` in JS and diverge from Python, the same class of bug as build/serve divergence in the
graphs path). **`slugify` lives in one place, runs once, and its output is data.**

### The chunk id is a mandatory PK with no meaningful content

Chroma requires a unique id per vector, so a chunk id must exist. But **nothing resolves *by* it from
outside**: the front holds `(document_id, chunk_index)`; the only look-up (`get_point`) *reconstructs*
`f"{document_id}::{chunk_index}"` internally, and could equally query `where {document_id, chunk_index}` —
both fields are stored metadata. So the chunk id's **content is not a contract**; nothing should parse it. It
may be `document_id::chunk_index` (free, debuggable) or an opaque uuid — either way it is a bare PK, and all
real addressing is via the `document_id` and `tradition_id` fields.

---

## 6. On-disk layout

The full folder tree `region_id/tradition_id/document_id.txt` is kept **for human navigation** (browse,
grep, git diffs). But it is a *rendering*, not the identity: `region_id` is a **regenerable mirror of the
tree**, not part of any id (region is volatile — re-annotation would otherwise move identity). Re-annotating
a document's region is a cheap `git mv`; the stored `document_id`/`tradition_id` and every reference are
**unchanged**, because they are stored keys, not path derivations.

---

## 7. What this changes vs today

This is largely formalization of what already exists — the current code already derives `text_id =
slug(title)` and addresses chunks/graphs by it. The deltas:

| # | today | target |
|---|---|---|
| 1 | `text_id` is ephemeral (computed in `iterator`, in-memory, absent from `corpus.json`) | **persist** it in the catalog ("populate once") |
| 2 | `tradition` stored raw (unsafe for paths); region has no id | give tradition & region their own **slugified ids** |
| 3 | `normalize_catalog_id` (whitespace-only, misnamed, not fs-safe) | one shared **`slugify`** |
| 4 | chunk carries `text_id, tradition, major_tradition, url` | chunk = **two refs** `(document_id, tradition_id)`; drop `url`/`major_tradition` |
| 5 | graphs: build writes raw `text_id`, serve re-normalizes it (idempotent today, latent divergence; not a traversal guard) | **unify** build/serve on the stored id + a real `sanitize`+`is_relative_to` guard |
| 6 | front reconstructs the title (`bookTitleFromId`, lossy) | resolve exact title from `docIndex[document_id]` |
| 7 | no id validity/uniqueness check | build-time **fail-loud uniqueness** check |

Order matters: build the front indexes and resolution **before** trimming `url`/`major_tradition` off the
chunk, or a hit loses the data with nothing to resolve it.

---

## 8. Follow-ups (concrete tasks)

1. Persist `document_id` in the built catalog; return it from the documents endpoint.
2. Mint `region_id` / `tradition_id` in the tree; carry `tradition_id` (not raw name) as the chunk ref.
3. Write one `slugify` (transliterate/lowercase/collapse); retire `normalize_catalog_id`; add the fail-loud
   uniqueness check.
4. Chunk metadata → `{document_id, tradition_id, chunk_index}`; drop `url`/`major_tradition`.
5. Graphs: unify build/serve on the stored id; add the traversal guard.
6. Front: `treeIndex` + `docIndex`; delete `bookTitleFromId`; resolve title/url/color from the indexes.

---

## 9. Weak spots & open decisions

- **D1 — `document_id` anchor (blocking).** `slugify(title)` vs `slug/hash(upstream-locator)` — see §5. This
  is the load-bearing open choice: it decides rename/edit stability, whether it unifies with the raw-archive
  key and the incremental anchor (pipeline §4), and how `graphs/<document_id>/` dirs behave. **Resolve first**;
  much of §8 (persist `document_id`, the embeddings key) depends on it. Leaning: the upstream-locator anchor
  (unifies more), but not decided.
- **`slugify` transliteration is under-specified.** "Transliterate non-ASCII" needs a concrete library/rules
  (Python has no stdlib transliteration — `unidecode` or hand rules); it is lossy and can itself collide as the
  corpus grows. The fail-loud uniqueness check *detects* a collision but does not *resolve* it. Decide the
  transliteration source and confirm collision-freedom on the full name set, not just the 194 traditions.
- **`tradition_id` on the chunk goes stale on a book re-annotation.** Re-annotating a *book's tradition* (not
  its region) changes `chunk.tradition_id` and forces a re-embed. We lean on "tradition is stable", which is
  true for *renames* but not for *re-annotation*; acceptable but worth stating.
- **The front resolves title/url from `docIndex`, so the embeddings/search pages must load the full catalog.**
  Fine at book scale; if the catalog grows large, prefer a lean `id → {title, url, tradition}` projection over
  shipping every per-document field. Not urgent.
- **Proportionality.** This is a spec for a corpus of ~27 documents. The single high-value, low-cost change is
  carrying `document_id` + `tradition_id` as the chunk's two refs and dropping `url`/`major_tradition`; the
  rest is formalization. Do not read the whole doc as "must build now".
