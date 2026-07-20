# Corpus data model — registries, ids & joins

How corpus data is split across three registries, how the pieces address and join each other, and how
identifiers are minted. This resolves the document-identity question left open in
[`region-implementation.md`](region-implementation.md) §3 — settled as **`document_id = hash(locator)`** (D1).
Companion:
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
| **documents** | catalog `outputs/corpus/corpus.json` → the documents list | `document_id` (= `hash(locator)`, D1) | title, url, counts, description, source |
| **embeddings** | Chroma collection | Chroma PK (opaque, see §5) | the vectors + per-chunk text |

**Invariant: resolution always runs upward** — `chunk → document → tradition → region` — and each hop is an
O(1) look-up into a load-once index. Cardinality grows downward, so **duplicating a field costs more the
lower it lives** (a field on the chunk is multiplied by tens of thousands).

---

## 2. Join keys

Distilled from every frontend section (corpus browser, atlas, embeddings scatter, graphs, search;
`motifs` is a separate domain and does not join this triple):

- **`tradition_id` is the universal presentational join.** Color, geography, grouping, attribution — every
  section keys on it. It lives on the **tree (PK)** and the **document (ref)** — **not** on the chunk.
- **`document_id` (= `hash(locator)`, D1) is the document key.** Corpus text fetch, graphs, and chunk→document
  all use it. It is a **single key, not a composite** (see §5), opaque and rename-stable, and *is* the
  raw-archive key `corpus/raw/<sha1(url)>`.
- **A chunk carries exactly ONE upward reference: `document_id`** (+ `chunk_index` and its intrinsic
  text/vector). Everything else — `tradition`, region, color, url, title — is resolved from `document_id`
  through the load-once catalog + tree (§4).

> **Decided (B1): no `tradition_id` on the chunk.** The chunk's only ref is `document_id`. The one thing that
> seemed to need `tradition` on the chunk — the server-side cross-tradition `where`-filter — instead resolves
> the clicked point's tradition and its document set from the catalog (server-side) and filters
> `where {document_id: {$nin: docs-of-that-tradition}}`. So `tradition` is never denormalized onto the chunk,
> and a tradition **rename or re-annotation touches nothing in Chroma** (it is resolved from `document_id` at
> query time). See §3.

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
| `tradition_id` (ref) | document→tree | **no** (B1) | resolved from `document_id` via the catalog; the cross-tradition filter uses `document_id $nin` (§3 below) |
| title | document | no | resolve via `docIndex[document_id]` — exact, no reconstruction |
| url | document | no | document-level; resolve on demand from the catalog |
| counts, description, source | document | no | corpus browser reads them from the catalog |
| region_id | tree (via tradition) | no | volatile (re-annotation); resolve `tradition_id → region` |
| **color** | tree (via region) | no | pure function of region + volatile (palette) — always resolve |
| coordinates, dating, subdivision, strata | tree | no | tree-only |

**`tradition` is not stored on the chunk at all (B1).** Two candidate justifications both fall away:

- *1-hop `chunk→region/color` resolve* — **does not survive §2.8**: the front loads the tree *and* the
  catalog once globally, so region/color are reached from `document_id → docIndex → tradition → treeIndex` for
  free (one extra Map lookup). Nothing needs `tradition` inlined on the front (the scatter, hits, atlas all
  resolve from `document_id`).
- *server-side cross-tradition `where`-filter* — the only thing that seemed to force a stored field. But it,
  too, can key on `document_id`: the server resolves the clicked point's tradition and that tradition's
  document set from the catalog, then filters `where {document_id: {$nin: docs-of-that-tradition}}`. The
  `$nin` list is bounded by books-per-tradition (small), the resolution is an in-memory catalog lookup.

So the chunk is the pure minimum `{document_id, chunk_index}` (+ text/vector). `tradition` lives only on the
tree and the document; a tradition rename/re-annotation touches **nothing** in Chroma or the projections —
it is resolved from `document_id` at query time. The single localized change is the cross-tradition query in
`get_point` (from `where {tradition != X}` to `where {document_id $nin …}`).

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

**The projection view is the exemplar of the right pattern.** The projection stores every chunk as
`{ id (=document_id), chunk_index, x, y, text(preview) }` — pointer + coords only, **no** tradition / url /
title / region / **color**. The front resolves tradition (→ region → color) from `id` via `docIndex` +
`treeIndex` at render, so a palette swap, a region re-annotation, or a **tradition rename never touches the
projection** (`document_id` is invariant). *(The current code inlines `tradition` because the embeddings page
loads only the tree, not the catalog; under §2.8 that inline is a pre-target crutch and is dropped — same
rationale as B1.)*

---

## 5. Identifiers

### Two ids from names via `slugify`; the document id is `hash(locator)`

**Region and tradition** names are **free-form display strings** — they may contain `&`, spaces, non-ASCII,
`/`, apostrophes (`Near East & North Africa`, `Tupí/Guaraní`, `Selk'nam`). They are **not** constrained.
Instead **one shared `slugify(name) → id`** derives a Chroma-, filesystem- and URL-safe id (transliterate
non-ASCII, lowercase, `&`→`and`, collapse the rest to `-`). It is **total** — it always *produces* a safe id
by construction, so there is no charset validator gate. The only build-time check is **uniqueness: fail loud
if two distinct names slug to the same id** (verified today: the 194 traditions slug without collision). This
replaces `normalize_catalog_id` (whitespace-only, misnamed, not fs-safe).

Two mint sites: `region_id = slugify(region name)`, `tradition_id = slugify(tradition name)`.

**The document id is *not* slugified — `document_id = hash(locator)` (Decided, D1).** The locator is the
document's upstream address (the URL, or the `sources/` path), normalized (scheme/host/trailing-slash/%-decode)
then hashed — which is **already the raw-archive key `corpus/raw/<sha1(url)>`**, so `document_id` *is* that key,
reused with zero new code. This deliberately keeps documents off `slugify`: a hash is fixed-length,
always fs/url/Chroma-safe, collision-free, and — crucially — **invariant under any title/tradition/region
rename** (the id tracks the source, not the display string). Titles are free to churn and collide; the id does
not. See §5 and §9-D1 for the full rationale.

> The model registry (`model_registry.py`) uses the inverse pattern — an **authored** safe key plus a
> `key → label` humanizer — because its keys are hand-written. That does not fit free-form names, so we do
> not reuse its key regex as a validator; we write a name→id transform instead.

### `document_id` is a single key, not composite

`document_id` is a **single key** (not a `(tradition, title)` composite), and it is the chunk's **only**
upward reference (B1, §2/§3): `tradition` is not stored on the chunk — it, region and color all resolve from
`document_id` through the catalog + tree, including the cross-tradition filter (via `document_id $nin`).

> **Decided (D1): `document_id = hash(locator)`.** The id anchors on the document's upstream locator (the URL /
> `sources/`-path), normalized then hashed — **not** on the title. This is **rename- and edit-stable**
> (a title/tradition/region change never moves the id), collision-free, and unifies identity + raw-archive key
> + the incremental anchor in one value ([`pipeline-and-incrementality.md`](pipeline-and-incrementality.md) §4
> assumes exactly this). It is already the raw key `corpus/raw/<sha1(url)>`, so `document_id` reuses it with
> zero new code. The rejected alternative, `slugify(title)`, was **not rename-stable** (a title edit changes
> the id) and collided when two documents share a title — and it needed the locator as a hidden second match
> key anyway (§9-D1). The only cost — an opaque id — is a non-issue: navigability lives in the file path (a
> rendering bridged by the catalog), never in the id.

### Store the ids; never regenerate

Ids are **minted once at build and persisted** (`region_id`/`tradition_id` in the tree, `document_id` in the
catalog and as the chunk's `document_id` ref). They are **not** recomputed on the fly. This matters because
**ids are durable external keys** — Chroma PKs and graph-directory names, written with a specific value:

- if `slugify` improves (region/tradition) or the locator-normalization rule changes (documents),
  *recomputing* silently changes the id → reads miss the writes (orphaned vectors, lost graph folders).
  *Storing* freezes the id at write time so reads always match. This is the concrete content of "populate
  once" — it is load-bearing only because ids persist. (Note `document_id = hash(locator)` is already immune to
  the common driver — a title/tradition rename — since the locator is unchanged; the residual risk is only a
  change to the normalization rule itself.)

For **joins**, pass the **stored** ids; do not regenerate — especially not on the front (that would
reimplement `slugify` in JS and diverge from Python, the same class of bug as build/serve divergence in the
graphs path). **`slugify` lives in one place, runs once, and its output is data.**

### The chunk id is a mandatory PK with no meaningful content

Chroma requires a unique id per vector, so a chunk id must exist. But **nothing resolves *by* it from
outside**: the front holds `(document_id, chunk_index)`; the only look-up (`get_point`) *reconstructs*
`f"{document_id}::{chunk_index}"` internally, and could equally query `where {document_id, chunk_index}` —
both fields are stored metadata. So the chunk id's **content is not a contract**; nothing should parse it. It
may be `document_id::chunk_index` (free, debuggable) or an opaque uuid — either way it is a bare PK, and all
real addressing is via the stored `document_id` and `chunk_index` fields (the only chunk metadata, B1).

---

## 6. On-disk layout

The file tree is kept **for human navigation** (browse, grep, git diffs). It is a *rendering*, not the
identity: the path segments are a regenerable mirror of the tree, not part of any id.

**The cleaned-text path can be fully human-readable — including the book title — precisely because
`document_id` is opaque.** Since the path never doubles as the id (identity = `document_id = hash(locator)`,
§9-D1), it carries no id constraints (uniqueness, lowercase, URL/Chroma-safe charset); it needs only mild
**fs-safety**. So the layout is `corpus/<Region Name>/<Tradition Name>/<Book Title>.txt` with only
`sanitize_filename` (keeps spaces/case/`&`, strips `/ : * ? < > |`) — readable, not slugged (e.g.
`Europe/Norse/The Poetic Edda.txt`). The current `text_path` already does this. An opaque id thus *liberates*
the path to be prettier, not the reverse. Consequences:

- **The catalog is the id↔path bridge.** Reads go `document_id → catalog row → path`; the path is **never
  parsed** for identity.
- **The path is not guaranteed unique.** Two books sharing `(tradition, title)` render to one path, though
  `document_id` (by locator) does not collide — so **disambiguate the file** (append a short suffix, e.g.
  `…-9f3a.txt`), since a path clash is cosmetic, not an identity clash. Rare.
- **The graph directory is a rendering too — it can be human-readable the same way.** A graph is keyed by
  `document_id`, so its on-disk path is a *rendering*, not the address: it may stay opaque
  (`graphs/<document_id>/`) or mirror the text tree (`graphs/<Region>/<Tradition>/<Title>/`) via the same
  catalog bridge. Crucially, a region/tradition/title rename then **relocates the graph dir with a `git mv`,
  not an LLM re-run** — the expensive graph *content* is invariant (keyed by the unchanged `document_id`);
  only the path rendering moves. Opaque path → zero disk-touch on rename; readable path → a cheap move. Same
  trade as the text tree (§6 above), never a recompute.
- The remaining stores stay opaque by design: raw at `corpus/raw/<hash(locator)>` (an archive, not browsed for
  content) and chunks keyed by `document_id` in Chroma.
- Path segments may use the pretty region/tradition **names** (fs-sanitized) for max readability, or the slug
  ids — a minor sub-choice; the catalog bridges either way.

**A region/tradition rename *does* touch disk — but only the cheap layer.** If the path embeds `region_id` /
`tradition_id`, renaming or re-annotating one moves the cleaned-text folders (detect + relocate). That is
real, but bounded: it touches only the **regenerable cleaned-text tree** (a rebuild-from-raw or `git mv` —
CPU) and a tree key. It does **not** touch Chroma at all — under B1 the chunk carries no `tradition`, so there
is no metadata field to update — and it does **not** touch the **expensive stores** (embeddings, graphs),
because those are keyed by `document_id` — and with the `hash(locator)` anchor (§9-D1), `document_id` is
**invariant** under any region/tradition/title rename. So the re-layout is absorbed by a normal rebuild (new
paths written, old GC'd); an explicit `git mv` is only needed for an *incremental* rename without a rebuild.

**The disk-touch on rename is the price of on-disk navigability — an explicit layout sub-fork:**

| layout | region rename | tradition rename | on-disk navigability |
|---|---|---|---|
| `region_id/tradition_id/<title>.txt` | relocate all under the region | relocate the tradition folder | ✔ full |
| `tradition_id/<title>.txt` | **nothing** | relocate the tradition folder | ✔ by tradition |
| `document_id.txt` (flat) | **nothing** | **nothing** | ✖ (navigate via app / catalog) |

Want zero disk-touch on rename → drop region/tradition from the path (flat by `document_id`), losing on-disk
navigability. Want navigability → pay the cheap text-tree re-layout on rename (never a re-embed). This is a
sub-decision of the file-layout choice (region-implementation §6 prerequisites).

### Rename operations (the operational payoff)

Because `document_id = hash(locator)` is invariant under every name change **and** no name is denormalized
onto the chunk or the projection (B1, §2/§3), a rename touches **neither Chroma nor the projections at all** —
only config, the tree, and the `git mv`'d path renderings.

| rename | config edit | Chroma chunks | projection files | text file | graph dir | re-embed / re-fit UMAP |
|---|---|---|---|---|---|---|
| **region** | tree (region node) | — | — | `git mv` region folder * | `git mv` * | no |
| **tradition** | tree + repoint `corpus.json` books | — (no `tradition` on chunk, B1) | — | `git mv` tradition folder * | `git mv` * | no |
| **book (title)** | `corpus.json` `title` | — | — | `git mv` the file * | `git mv` the dir * | no |

\* only where that path segment is in the readable layout; opaque path → nothing.

**The rule:** every *denormalized copy* of the renamed value must be rewritten — and after B1 there are **no
denormalized copies** of `tradition`/region/title in the derived stores. `tradition` lives only on the tree
and the catalog; the cross-tradition filter resolves it from `document_id` at query time (§3). So a rename is
pure config + `git mv`.

**Unified incremental procedure:** (1) edit config (tree for region/tradition; `corpus.json` for
repoint/title); (2) `git mv` the changed path segment (region folder / tradition folder / file + graph dir);
(3) rebuild the catalog + front `treeIndex`/`docIndex`; (4) **never re-embed / re-fit UMAP / re-LLM / touch
Chroma** (`document_id` invariant, nothing name-derived on the chunk); (5) re-run fail-loud uniqueness +
`status`.

The once-feared case — a **book rename** — is a `title` edit + a `git mv`, nothing else. This is only for a
*single* incremental rename; a full wipe-rebuild (region-implementation §6) is for large scheme migrations,
not one rename.

---

## 7. What this changes vs today

Part formalization, part one real anchor change: today the code derives `text_id = slug(title)` and addresses
chunks/graphs by it; the target **re-anchors the document id to `hash(locator)`** (D1) — which is already the
raw-archive key — so identity stops tracking the title. The deltas:

| # | today | target |
|---|---|---|
| 0 | document identity = `text_id = slug(title)` (title-anchored, churns on rename, collides on shared titles) | `document_id = hash(locator)` (D1) — the existing raw key `corpus/raw/<sha1(url)>`; opaque, rename-stable, collision-free |
| 1 | `text_id` is ephemeral (computed in `iterator`, in-memory, absent from `corpus.json`) | **persist** `document_id` in the catalog ("populate once") |
| 2 | `tradition` stored raw (unsafe for paths); region has no id | give tradition & region their own **slugified ids** |
| 3 | `normalize_catalog_id` (whitespace-only, misnamed, not fs-safe) mints the document id | retired for documents (id = `hash(locator)`); **one shared `slugify`** mints only `region_id`/`tradition_id` |
| 4 | chunk carries `text_id, tradition, major_tradition, url` | chunk = **one ref** `document_id` (+ `chunk_index`); drop `tradition`/`major_tradition`/`url` (B1) |
| 5 | graphs: build writes raw `text_id`, serve re-normalizes it (idempotent today, latent divergence; not a traversal guard) | **unify** build/serve on the stored id + a real `sanitize`+`is_relative_to` guard |
| 6 | front reconstructs the title (`bookTitleFromId`, lossy) | resolve exact title from `docIndex[document_id]` |
| 7 | no id validity/uniqueness check | build-time **fail-loud uniqueness** check |

Order matters: build the front indexes and resolution **before** trimming `url`/`major_tradition` off the
chunk, or a hit loses the data with nothing to resolve it.

---

## 8. Follow-ups (concrete tasks)

1. Persist `document_id = hash(locator)` (D1) in the built catalog — the existing raw key `sha1(url)`, now
   surfaced as the document identity; return it from the documents endpoint. Normalize the locator
   (scheme/host/trailing-slash/%-decode) before hashing.
2. Mint `region_id` / `tradition_id` in the tree (and as the document's `tradition` ref in the catalog); the
   chunk carries **no** `tradition` (B1).
3. Write one `slugify` (transliterate/lowercase/collapse) for `region_id`/`tradition_id` **only**; retire
   `normalize_catalog_id` (documents no longer need a name-slug — the id is `hash(locator)`); add the fail-loud
   uniqueness check (slug-collision for region/tradition; distinct-locator for documents).
4. Chunk metadata → `{document_id, chunk_index}` (B1); drop `tradition`/`url`/`major_tradition`. Change the
   `get_point` cross-tradition filter from `where {tradition != X}` to `where {document_id $nin …}` (server
   resolves the tradition's document set from the catalog).
5. Graphs: unify build/serve on the stored id; add the traversal guard.
6. Front: `treeIndex` + `docIndex`; delete `bookTitleFromId`; resolve title/url/color from the indexes.

---

## 9. Weak spots & open decisions

- **D1 — `document_id` anchor — DECIDED: `hash(locator)`.** `slugify(title)` vs `hash(upstream-locator)` is
  settled in favour of the locator hash (see §4/§5). It decides rename/edit stability, unifies identity with
  the raw-archive key and the incremental anchor (pipeline §4), and makes `graphs/<document_id>/` dirs
  rename-invariant. The rationale below is retained as the justification, not an open question.
  - *The governing principle: **identity = provenance**, not the label.* A **title is a label** — it churns,
    collides, and says nothing about *what* the text is; anchoring identity on it is the mistake D1 fixes. A
    **locator is what the text *is*** — where it was drawn from. So the two axes separate cleanly and each does
    the right thing: a **rename** (label changed) leaves the id fixed → the expensive stores are reused (free);
    a **re-source** (URL / `sources/`-path changed) *is* a different provenance → the id changes → the
    document re-derives (re-fetch, re-embed, re-graph). **That re-derive is the intended behaviour, not a
    cost** — you changed where the text comes from, so a fresh derivation is exactly what you want; the old
    id's artifacts orphan and GC. The only degenerate case — an *identical-bytes* move (a mirror / upstream
    re-release at a new URL) — costs one idempotent re-embed (same vectors) plus a re-graph of unchanged text;
    rare, cheap at this scale, and avoidable by keeping the URL pinned or remapping the catalog `locator → old
    id` by hand. No schema complexity is worth buying that edge case out.
  - *Match-key argument (strengthens the locator anchor).* Stability across rebuilds is not about what the id
    *looks like* but about the **match key** used to decide "same document, reuse its id". A *stored*
    `slugify(title)` is rename-stable only if you separately match entries by their **locator** (url/path) —
    because matching by title breaks on rename. So a stored title-slug needs the locator as a hidden second
    key anyway (and it then drifts from the current title and can collide). `hash(locator)` collapses id +
    match-key + raw-archive key into one; a stored title-slug adds a redundant, drift- and collision-prone id
    on top of a locator match you already need.
  - *`slug` vs `hash` for the locator (the form of the anchor).* `hash(locator)` beats `slug(locator)`:
    fixed-length, always fs/url/Chroma-safe (no slugify for documents at all), unique, and **it is already the
    raw-archive key** (`corpus/raw/<sha1(url)>`) → `document_id` = raw key with zero new code. `slug(locator)`
    only adds mnemonic value, which is weak (URLs slug long and unreadable) and which the file path already
    carries. Opacity is fine — the catalog is the `id → {title, url}` lookup. Keep `sha1(url)` to avoid
    re-keying the archive; normalize the locator (scheme/host/trailing-slash/%-decode) before hashing. (Both
    slug and hash need that normalization.)
  - *Why `slug` is fine for `tradition_id`/`region_id` but feared for `document_id`.* The fear is not the slug
    mechanism (identical for all three) but **what the id primary-keys** × **how churny/collision-prone the
    name is**. `document_id` primary-keys the **expensive, persisted, content-addressed** per-document
    artifacts (chunk ids `document_id::i`, `graphs/<document_id>/`, the raw anchor), and titles churn and
    collide → changing it re-embeds/re-graphs + orphans. `tradition_id`/`region_id` are a **tree key** on a small
    closed **curated** vocabulary (14 + ~194, unique by fiat, renamed ~never), never stored on the chunk (B1) —
    changing one touches only the cheap regenerable layer (the text-tree re-layout, §6; no Chroma update),
    never the expensive stores. With `document_id = hash(locator)`, those stores are shielded from *every*
    human-name rename, which is exactly what makes region/tradition/title all cheap to rename.
- **`slugify` transliteration is under-specified (D8) — but D1 shrinks it.** "Transliterate non-ASCII" needs a
  concrete library/rules (Python has no stdlib transliteration — `unidecode` or hand rules); it is lossy and
  can itself collide. **D1 narrows this to region/tradition names only** — documents no longer slug (id =
  `hash(locator)`), so the surface is now a **small closed curated vocabulary** (14 regions + ~194 traditions,
  unique by fiat), not the open-ended, growing document-title set. The fail-loud uniqueness check *detects* a
  collision but does not *resolve* it; confirm collision-freedom over that closed set (already verified for the
  194 traditions). Locators — the document key — need normalization, not transliteration, and are exact.
- **B1 depends on the server resolving `tradition ↔ documents` for the cross-tradition filter.** `get_point`
  must load (or cache) the catalog server-side to build the `document_id $nin` set. Cheap (an in-memory map,
  small lists), but it is the one new server-side dependency B1 introduces; a re-annotation is then picked up
  *automatically* at query time (nothing stored on the chunk to update).
  - *This is the **only** cost of B1, and it serves an **experimental** feature — "search only within other
    traditions".* If that feature does not survive, B1 becomes **unconditional**: the chunk is a pure
    `{document_id, chunk_index}` pointer and no query resolves `tradition` at all. In that case the
    store-`slug(tradition)`-on-chunk alternative would instead leave a **dead denormalized field** on every
    chunk — read by nothing, still needing a strip-migration or left to rot and drift. B1 keeps the entire
    footprint of this experiment in **one server function**: adding *or* removing it is a `get_point` edit with
    **zero data migration**, whereas store-on-chunk couples the feature's on/off to a Chroma backfill/strip. So
    B1 is precisely the design that respects the feature's provisional status.
- **The front resolves title/url/tradition from `docIndex`, so the embeddings/search pages must load the full
  catalog** (§2.8). Fine at book scale; if the catalog grows large, prefer a lean `id → {title, url,
  tradition}` projection over shipping every per-document field. Not urgent.
- **Proportionality.** This is a spec for a corpus of ~27 documents. The single high-value, low-cost change is
  making the chunk carry only `document_id` (B1) and dropping `tradition`/`url`/`major_tradition`; the rest is
  formalization. Do not read the whole doc as "must build now".
