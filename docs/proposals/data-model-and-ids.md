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
  raw-archive key `corpus/raw/<blake2b(url)>`.
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

### The region/tradition id **is the canonical name**; the document id is `hash(locator)`

**Decided: `region_id` / `tradition_id` are the canonical name itself** — no slug, no transliteration, and
**no new function**. The earlier plan (a `slugify` to a lowercase, `-`-collapsed, transliterated token) was
**over-built**: the two hard constraints that motivated it are gone, *and* the boundaries that stay are already
defended by existing, in-use code.

The constraints that fell away:

- **Chroma-safe** — moot under **B1**: `tradition`/`region` are never stored on the chunk (nor in graphs or
  projections, which key on `document_id`). The id never enters an embedding store.
- **Filesystem-safe** — moot under **path-is-a-rendering**: on-disk paths are built from the **name**, never
  the id (below).

**The boundaries are already filtered by existing code — reuse it, don't pre-mangle the id:**

| boundary | existing filter (in use today) |
|---|---|
| **filesystem** | `sanitize_filename` (`corpus/utils.py:17`) — `/`→`_`, space→`_`, `\ * ? : " < > |`→`_`, `..`→`_`; already applied per path segment in `text_path` (`utils.py:63`) + an `is_relative_to` traversal guard in `read_document` |
| **URL** | `encodeURIComponent` / `URLSearchParams` — already used everywhere the front builds a query/path (`page-geography.js:98` `?tradition=${encodeURIComponent(...)}`, `page-graphs.js`, `search-utils.js`, …); handles `&`, `/`, spaces |
| **HTML** | `escapeHtml` — already on `data-tradition` attrs (`tree-traditions.js:19`, `tree-sources.js:34`) |

So the id is simply the **canonical name**, at most whitespace-canonicalized with the *existing*
`normalize_catalog_id` (`utils.py:28`, `\s+`→`_`) to prevent silent double-space join misses. It **keeps case,
accents, apostrophes, `&`, `/`** verbatim (`Near East & North Africa`, `Tupí/Guaraní`, `Akan/Ashanti`,
`Selk'nam`). Two mint sites: `region_id`, `tradition_id`. **There is no `slugify` and no transliteration**
(dissolves D8 — see §9).

> **The one invariant (already satisfied in the codebase):** never splice a raw `region_id`/`tradition_id`
> into a path or route — use `sanitize_filename`(FS) / `encodeURIComponent`(URL) / `escapeHtml`(HTML). All three
> are already in place and consistently used, so keeping `&`/`/` in the id is safe *by existing construction*,
> not by new discipline. (This closes the earlier A-vs-B sub-choice: no gentle `&→and`/`/→-` transform is
> needed — the boundaries already neutralize those chars.)

The **uniqueness check** still runs but is now near-vacuous: distinct canonical names are distinct ids by
construction (unique by fiat in the curated 14 + ~194 vocabulary); it only catches a name listed twice or two
whitespace-variants of one name. Rename = edit the config string + repoint books (cheap, validated; touches no
Chroma, no re-embed — B1/D1).

**The document id is *not* a name and *not* a slug — `document_id = hash(locator)` (Decided, D1).** The locator
is the document's upstream address (the URL, or the `sources/` path), **normalized** (rule below) then hashed
(`blake2b`) — which is the raw-archive key `corpus/raw/<blake2b(url)>`, so `document_id` *is* that key, reused
with zero new code. A hash is fixed-length, always fs/url/Chroma-safe, collision-free, and — crucially —
**invariant under any title/tradition/region rename** (the id tracks the source, not the display string).
Titles are free to churn and collide; the id does not. See §9-D1 for the full rationale.

> **The locator-normalization rule — the identity boundary.** Because `document_id = hash(locator)`, *what we
> hash* **is** the definition of "the same document," so the rule must be pinned, not hand-waved. Today the raw
> key is `sha1(url)` over the **raw** config string, with **no** normalization (`fetch_cache.cache_path`,
> `hashlib.sha1(url.encode())`); the target adds one canonical pass **before** hashing. The design intent is
> narrow: **fold only cosmetic edits to the locator** (so a trivial re-typing of the config URL does not
> re-mint the id and orphan every derived artifact), and **never merge two genuinely distinct sources.** So the
> rule is conservative — it touches only the parts of a URL that RFC 3986 defines as case-insensitive or
> non-identifying:
>
> - **Web locator** (`http`/`https`): strip surrounding whitespace; lowercase the **scheme** and **host** only;
>   drop the default port (`:80` for http, `:443` for https); drop the **fragment** (`#…` never names a
>   different document); percent-decode only the RFC-3986 **unreserved** set (`A–Z a–z 0–9 - . _ ~`, so `%7E`≡`~`);
>   collapse a **single trailing `/`** on the path. **Keep verbatim:** the **path case** (paths are
>   case-sensitive) and the **entire query string** (it can select a real resource). Nothing else is altered.
> - **Local locator** (a `sources/` file): the locator is the file path **relative to `sources/`**,
>   whitespace-trimmed and POSIX-normalized (forward slashes, drop `./` and redundant separators); **case is
>   preserved** (the config path is authoritative). No percent/scheme handling.
>
> Whatever the exact rule, it is **frozen once ids are minted** — it feeds the durable Chroma PKs and graph
> dir names, so changing it later silently re-mints and orphans (exactly the "Store the ids; never regenerate"
> hazard below). A future rule change is therefore a *migration* (re-mint + rebuild-from-raw), not a hot edit.

> **Provenance-addressed, not content-addressed — the one genuinely non-standard choice.** Classic
> content-addressed stores — **git** blobs, **Nix** store paths, **IPFS** CIDs — hash the *content*, so
> identical bytes get one id (deduplication is the goal). We deliberately hash the **locator**, so the *same
> source* keeps one id **even after its content is edited** (rename-/edit-stability is the goal). The two are
> not the same axis, and mixing them up is the mistake D1 avoids: we want identity to survive a text fix, which
> content-addressing at the identity layer would break (every edit = new id = re-embed + orphan). So the system
> is **provenance-addressed at the identity layer** (`document_id = hash(locator)`) and **content-addressed
> only at the version layer** (`doc_md5`, the fingerprints of pipeline §2.3) — the design splits the single
> hash that git/Nix/CAS conflate into the two roles it actually plays here (which is *which* source vs *what*
> content). Mature pipeline engines make the same split under other names — e.g. Flyte hashes a dataset's
> **storage location** by default and lets you opt into a **content hash** (pipeline §9.1). There is no library
> that hands you this data model; it is application schema design (a star-schema-shaped registry split) plus
> this provenance-addressed id.

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
> assumes exactly this). It *is* the raw key `corpus/raw/<blake2b(url)>` (hash = `blake2b`, one algorithm
> everywhere — the archive moves off `sha1` by a one-time rename, §9-D1). The rejected alternative,
> `slugify(title)`, was **not rename-stable** (a title edit changes
> the id) and collided when two documents share a title — and it needed the locator as a hidden second match
> key anyway (§9-D1). The only cost — an opaque id — is a non-issue: navigability lives in the file path (a
> rendering bridged by the catalog), never in the id.

### Store the ids; never regenerate

Ids are **minted once at build and persisted** (`region_id`/`tradition_id` in the tree, `document_id` in the
catalog and as the chunk's `document_id` ref). They are **not** recomputed on the fly. This matters because
**ids are durable external keys** — Chroma PKs and graph-directory names, written with a specific value:

- if the locator-normalization rule changes (documents) or the name-canonicalization rule changes
  (region/tradition), *recomputing* silently changes the id → reads miss the writes (orphaned vectors, lost
  graph folders). *Storing* freezes the id at write time so reads always match. This is the concrete content of
  "populate once" — it is load-bearing only because ids persist. (`document_id = hash(locator)` is already
  immune to the common driver — a title/tradition rename — since the locator is unchanged; and the
  region/tradition id being the raw name means there is barely a rule to drift.)

For **joins**, pass the **stored** ids; do not regenerate — especially not on the front (recomputing a
canonicalization in JS could diverge from Python, the same class of bug as build/serve divergence in the graphs
path). **The id is minted once and its output is data.**

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
- Path segments use the region/tradition **names**, `sanitize_filename`-cleaned, for max readability. (Since
  the id now *is* the name, "name vs id in the path" is no longer a real sub-choice — only the fs-sanitization
  differs; the catalog bridges either way.)

**A region/tradition rename *does* touch disk — but only the cheap layer.** If the path embeds `region_id` /
`tradition_id`, renaming or re-annotating one moves the cleaned-text folders (detect + relocate). That is
real, but bounded: it touches only the **regenerable cleaned-text tree** (a rebuild-from-raw or `git mv` —
CPU) and a tree key. It does **not** touch Chroma at all — under B1 the chunk carries no `tradition`, so there
is no metadata field to update — and it does **not** touch the **expensive stores** (embeddings, graphs),
because those are keyed by `document_id` — and with the `hash(locator)` anchor (§9-D1), `document_id` is
**invariant** under any region/tradition/title rename. So the re-layout is absorbed by a normal rebuild (new
paths written, old GC'd); an explicit `git mv` is only needed for an *incremental* rename without a rebuild.

**The disk-touch on rename is the price of on-disk navigability — decided in favour of navigability:**

| layout | region rename | tradition rename | on-disk navigability |
|---|---|---|---|
| **`<Region>/<Tradition>/<Title>.txt` — DECIDED** | relocate under the region | relocate the tradition folder | ✔ full |
| `<Tradition>/<Title>.txt` | **nothing** | relocate the tradition folder | ✔ by tradition |
| `<document_id>.txt` (flat) | **nothing** | **nothing** | ✖ (navigate via app / catalog) |

**Decided: full nested `corpus/<Region>/<Tradition>/<Title>.txt`** (names, `sanitize_filename`-cleaned; the
opaque `document_id` is *not* in the path — the catalog bridges id ↔ path). Rationale: the `.txt` tree is a
**pure human-rendering layer** — identity is already fully decoupled (`document_id = hash(locator)`; Chroma and
graphs never move on any rename), so the path is free to be the most browsable thing, which is the full nested
tree. The disk-churn against it is negligible (27 files, regenerable from raw + catalog, `git mv` for an
incremental rename, never a re-embed), and the 14-region canon is closed/stable so region re-annotation rarely
fires. The flat-by-id option was rejected: it throws away the one purpose of the cleaned-text tree — being the
readable layer — to save a churn cost that is already absorbed elsewhere; `<Tradition>/…` was rejected as a
muddle (pays tradition/title churn while giving up region grouping). *(If region re-annotation ever became
frequent, drop region from the path → `<Tradition>/…`; the catalog makes that a cheap, reversible re-render.)*

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
| 0 | document identity = `text_id = slug(title)` (title-anchored, churns on rename, collides on shared titles) | `document_id = hash(locator)` (D1) — the raw key `corpus/raw/<blake2b(url)>`; opaque, rename-stable, collision-free |
| 1 | `text_id` is ephemeral (computed in `iterator`, in-memory, absent from `corpus.json`) | **persist** `document_id` in the catalog ("populate once") |
| 2 | `tradition` stored raw; region has no id | `region_id`/`tradition_id` = **the canonical name** (kept verbatim; boundaries already sanitise — `sanitize_filename`/`encodeURIComponent`/`escapeHtml`) |
| 3 | `normalize_catalog_id` mints the document `text_id` (`\s+`→`_`) | **repurposed, not retired**: documents drop it (id = `hash(locator)`); it now just whitespace-canonicalises `region_id`/`tradition_id`. **No `slugify`, no transliteration.** |
| 4 | chunk carries `text_id, tradition, major_tradition, url` | chunk = **one ref** `document_id` (+ `chunk_index`); drop `tradition`/`major_tradition`/`url` (B1) |
| 5 | graphs: build writes raw `text_id`, serve re-normalizes it (idempotent today, latent divergence; not a traversal guard) | **unify** build/serve on the stored id + a real `sanitize`+`is_relative_to` guard |
| 6 | front reconstructs the title (`bookTitleFromId`, lossy) | resolve exact title from `docIndex[document_id]` |
| 7 | no id validity/uniqueness check | build-time **fail-loud uniqueness** check |

Order matters: build the front indexes and resolution **before** trimming `url`/`major_tradition` off the
chunk, or a hit loses the data with nothing to resolve it.

---

## 8. Follow-ups → sequenced in the single implementation list

**The concrete tasks from this spec are not listed separately here** (that only created a parallel list that
drifts). They are folded, in dependency order, into the **single implementation list —
[`region-implementation.md`](region-implementation.md) §5 (Part 1)**:

- persist `document_id = hash(locator)` + mint `region_id`/`tradition_id` = name → §5 step 2;
- front `treeIndex`/`docIndex` + resolution, delete `bookTitleFromId` → §5 step 3;
- chunk → `{document_id, chunk_index}` (B1) + the `get_point` `$nin` filter → §5 step 4;
- graphs build/serve unify + traversal guard → §5 step 6.

Incrementality tasks (embeddings key, fingerprints, GC) are Part 2 — `pipeline-and-incrementality.md` §7.

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
    fixed-length, always fs/url/Chroma-safe (no slugify for documents at all), unique, and **it is the
    raw-archive key** (`corpus/raw/<blake2b(url)>`). `slug(locator)` only adds mnemonic value, which is weak
    (URLs slug long and unreadable) and which the file path already carries. Opacity is fine — the catalog is
    the `id → {title, url}` lookup. **Hash = `blake2b`** (one algorithm across identity + fingerprints —
    pipeline §2.4; the archive was `sha1(url)`, a one-time rename to `blake2b(url)` off the config, no
    re-download). Normalize the locator before hashing per the **pinned rule in §5** (the identity boundary:
    fold only cosmetic URL variation — scheme/host case, default port, fragment, unreserved %-escapes, one
    trailing slash — keep path case + query verbatim; local = POSIX path relative to `sources/`). Both slug and
    hash need that normalization; today's `sha1(url)` does *none*, so this pass is new work landing with D1.
  - *Why a name-derived id is fine for `tradition_id`/`region_id` but was feared for `document_id`.* The issue
    is never the transform but **what the id primary-keys** × **how churny/collision-prone the name is**.
    `document_id` primary-keys the **expensive, persisted, content-addressed** per-document artifacts (chunk ids
    `document_id::i`, `graphs/<document_id>/`, the raw anchor), and titles churn and collide → a name-derived
    document id re-embeds/re-graphs + orphans (hence `hash(locator)`). `tradition_id`/`region_id` are a **tree
    key** on a small closed **curated** vocabulary (14 + ~194, unique by fiat, renamed ~never), never stored on
    the chunk (B1) — so using the name directly (no slug) is safe;
    changing one touches only the cheap regenerable layer (the text-tree re-layout, §6; no Chroma update),
    never the expensive stores. With `document_id = hash(locator)`, those stores are shielded from *every*
    human-name rename, which is exactly what makes region/tradition/title all cheap to rename.
  - *Rejected alternative — a synthetic `uuid` (identity decoupled from both title **and** locator).* The real
    axis is **derivable-from-source vs synthetic-stored**, not readability (both a uuid and a hash are opaque).
    A uuid buys exactly **one** capability — *re-source without re-identify*: change a document's URL but keep
    its id, so an identical-bytes move preserves the expensive LLM graph and you get an explicit "same document
    / new document" knob. Its costs are structural and permanent:
    - **Statefulness.** A uuid is random → it must live in a primary, **unrebuildable** `locator → uuid`
      registry (lose it → every doc re-mints → total orphaning), or be hand-authored per entry in config
      (friction + a redundant field beside the locator). `hash(locator)` needs no registry — the id is
      `f(config)`, and the catalog is a rebuildable *cache*, not a source of truth for identity.
    - **A second key.** The raw archive is locator-addressed by nature (`corpus/raw/<blake2b(url)>`), so a uuid
      identity sits *on top* and reintroduces the join uuid ↔ `blake2b(url)` — the very "two identifiers" problem
      `hash(locator)` collapses into one.
    - **Lost free dedup + a new failure mode.** Same locator listed twice → same hash (caught for free) but two
      uuids (silent duplicate). Plus a mint-once read-modify-write with its own atomicity/crash concerns.
    - **Architectural incoherence.** The pipeline is already content-addressed / derive-from-source (Nix model,
      `blake2b(url)` identity + content-hash versions, fp cascade); `hash(locator)` continues it, a uuid would be
      an island of stateful identity.

    A uuid is the **right** choice only when a document has **no stable locator** (user uploads, generated
    content, mutable primary keys) — provenance is then not a usable handle. Mythoscope's locators are stable
    and pinned in config, so that precondition fails. The one case a uuid would handle better — preserving a
    graph across an *identical-bytes* address move — is covered without going stateful by an **optional
    `alias` / `id_override` in config** (pin "treat this locator as the same identity as `<old id>`"): 99 %
    stays stateless, the rare case gets a manual knob. Prefer that escape hatch to a uuid space if the need
    ever arises.
- **~~D8 (`slugify` transliteration)~~ — DISSOLVED.** The former open question (which transliteration
  library/rules for the slug) no longer exists: **there is no slug.** `document_id = hash(locator)` (D1) never
  slugged, and `region_id`/`tradition_id` are now the **canonical name itself** (at most the existing
  `normalize_catalog_id` for whitespace), which keeps accents rather than transliterating them. Nothing to decide. The only
  residual check is the near-vacuous name-uniqueness over the closed 14 + ~194 vocabulary (verified: the 194
  names are already distinct as-is). Locators need normalization, not transliteration, and are exact.
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
