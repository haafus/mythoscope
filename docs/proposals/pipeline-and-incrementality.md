# Pipeline & incrementality — build graph, fingerprints, caches, GC, sources

How the build pipeline is structured, what each stage produces and depends on, how changes should
propagate, and how sources (web + local) are archived and curated. Companion to
[`data-model-and-ids.md`](data-model-and-ids.md) (which covers the three registries, ids and joins); this
doc covers *when things rebuild* and *how source data is managed*.

Guiding goal: **any change at any stage automatically invalidates exactly the dependent part of the
pipeline and nothing more; the result is always coherent; ideally with no human bookkeeping.**

---

## 1. The pipeline map

### 1.1 Stages, artifacts, caches, cost

Build order (`cli.py`): Corpus → Embeddings → Projections → Graphs → Motifs.

| # | stage | inputs | artifacts (`outputs/`) | caches | cost |
|---|---|---|---|---|---|
| 0 | **config** (hand-authored) | `config/corpus.json` (title, tradition, url, content_start/end, exclude), `config/traditions.json` (tree), `config/models.json`, `config/prompts.json`, `sources/` | — | — | — |
| 1 | **Corpus** | corpus.json + traditions.json + sources | `corpus/raw/<hash(locator)>` raw snapshot (**today `sha1(url)`; D1 target `blake2b(normalized-locator)` = `document_id`**), `corpus/<Region>/<Tradition>/<Title>.txt` (cleaned text — decided layout, data-model §6), `corpus/corpus.json` (catalog + counts + per-doc `fingerprint`) | raw-fetch (locator hash), extraction | network (~s/doc); clean/trim CPU-cheap |
| 1.5 | **Preprocess** (variant, optional) | cleaned text + variant config | *(no first-class artifact — an internal step of the embeddings variant)* | preprocessing (**resumable cache**) | **always an LLM transform when present** (`preprocess.py` → `LLMProcessor`, per-chunk) = **$$, rate-limited**. **Not a separate driver stage** — it is folded into `embeddings:<variant>` (§2.2) as a resumable cache tier (§3); a variant either enables it (LLM) or skips it (embeds the base cleaned text) |
| 2 | **Embeddings** | cleaned text (+ variant) + models.json | `embeddings/` (Chroma collections per model) | chunk-cache; the collection itself is a store (dedup by chunk_id) | **GPU — dominant**; per-chunk |
| 3 | **Projections** | vectors (embeddings) + plot | `projections/<model>/<plot>.json` | — | moderate; **UMAP is global** (over all points), not per-chunk |
| 4 | **Graphs** | cleaned text + prompts.json + LLM | `graphs/<document_id>/…` (`document_id = hash(locator)`, D1) | chunk-cache (LLM responses) | **LLM — $$, rate-limited**; per-chunk |
| 5 | **Motifs** (a 5-step sub-pipeline) | motif sources (TMI/ATU/Berezkin) | `motifs/*.json` | motif raw-scrape | scrape sources → crosswalk → inline relations → lexical parallels → semantic/reasoned parallels → store. **Independent** of the corpus. CPU-moderate **only because** the one GPU part — BGE-M3 *semantic* parallels — is **precomputed offline** (`scripts/build_semantic_parallels.py`) + committed, and the build just copies it |
| S | **Serve** | traditions.json + corpus.json + embeddings + projections + graphs + motifs | (runtime) | front load-once indexes | — |

**No separate `download`/`fetch` stage** — network fetch is folded *inside* Corpus (`corpus` = "Download and
build") and Motifs (`build_motifs` scrapes/downloads its sources), cached by `sha1(url)` / raw-scrape. §5
(fetch-vs-build) is exactly the proposal to split it into a first-class stage (Part 2 item 4).

### 1.2 Dependency DAG

```
config/corpus.json ─┐
sources/           ─┼─► raw ─► clean/trim ─► [text .txt] ─► corpus.json (catalog)
config/traditions ──┘                          │
(serve-time only: color/tree/grouping)         ├─► [preprocess: internal to embeddings] ─► EMBEDDINGS ─► PROJECTIONS (global per model)
                                               └─► + prompts.json ─► GRAPHS (per doc)
motif sources ───────────────────────────────────────────────► MOTIFS (independent branch)
```

Resolution runs **upward** at serve time: `chunk → document → tradition → region` (see
`data-model-and-ids.md`). Tree edits (region/color/name/coordinates) touch only the **serve-time resolve**,
never a built artifact.

### 1.3 How data changes (what triggers what)

| change source | example | should invalidate |
|---|---|---|
| **config/corpus.json** | add/remove doc | that doc's whole branch |
| | change `url` | raw → text → embeddings(its chunks) → projection(whole model) → graph(doc) |
| | edit `content_start/end` | text → embeddings(chunks) → projection → graph |
| | rename `title` | *today:* everything below (title-anchored); *should:* nothing if content is unchanged |
| | change `tradition` | path rendering + catalog ref only; embeddings **never** touched (tradition isn't on the chunk — B1) |
| | `exclude` on/off | add/remove from everything below |
| **traditions.json** | rename/re-annotate region, color, coordinates | **serve-resolve only** — no artifact rebuild |
| **sources/** local file | byte edit / new version delivered | raw(hash) → below |
| **external URL** upstream | Gutenberg re-release | raw → below (not detected without a re-fetch) |
| **models.json** | add/change model | embeddings(model) → projections(model) |
| **prompts.json** | change prompt | graphs(all) |
| **stage CODE** | clean/trim, `chunk_size/overlap`, projection method | **all outputs of that stage — today not detected at all** |
| **motif sources** | new crosswalk | motifs |

### 1.4 What incrementality exists today (and its two flaws)

- **raw-fetch** — content-addressed by `sha1(url)` (rename-proof). ✔
- **Corpus reuse** — keyed by `title` (`_load_existing_metadata` → `{row["title"]: row}`; reuse if the output
  file is present / for local, if the raw-snapshot hash is unchanged). ✖ rename-fragile.
- **Embeddings dedup** — by `chunk_id = normalize_catalog_id(title)::i` (title-anchored today), on **id
  existence, not content**. ✖  *(target: `document_id::i` with `document_id = hash(locator)`.)*
- **Projections/Graphs** — coarse reuse (file/dir presence).
- **`status` / orphan detection** (`pipeline_inspect`: `corpus_orphans`, `embeddings_orphan_chunks/collections`,
  `projections_orphans`, graphs) — detects drift, but does not auto-fix or cascade.

**Two concrete flaws in the current keys:**

1. **Title-anchored → needless re-embed on rename.** Rename a book → chunk ids change → re-embed all its
   chunks though the vectors are identical.
2. **Dedup by "id exists", not content → missed re-embed on a text edit.** Fix `content_start/end` or clean
   the text while keeping the title → same `chunk_id` → already in `existing_ids` → **chunks are NOT
   re-embedded → vectors go stale** (without `--force`). `md5` is computed in `_finalize_text` but unused for
   the embeddings decision.

**The deeper systemic gap:** there is **no transform-version** — a change to a stage's *code* (cleaning,
chunker, method) invalidates nothing. Flaw 2 is a special case of this.

---

## 2. Incrementality: a content-addressed build graph

### 2.1 The model (Make / Bazel / Nix)

All three treat a build as a **DAG of targets**, each a pure function of its inputs, rebuilt only when
inputs change. They differ in *how* they detect change:

- **Make** — by **file mtime**: rebuild if an input is newer than the output. Coarse, fast, fragile (see the
  appendix on why mtime lies).
- **Bazel** — by **action content**: key = hash(input contents + the exact rule/command + toolchain);
  matching key ⇒ reuse the result (even from a shared remote cache). Catches content and rule changes.
- **Nix / Guix** — **purely functional, content-addressed**: every output's store path is derived from a hash
  of its whole transitive input closure. Immutable store; identical inputs ⇒ same path ⇒ reuse; any change ⇒
  new path. Gives rollback and reproducibility.

Our target is the common denominator: **a target is a pure function of its inputs; cache/reuse keyed by a
hash of (inputs + transform); rebuild on hash change; propagate down the DAG.**

### 2.2 The stage as a self-describing asset — the spine

The organising idea the rest of §2 hangs off. Today hygiene is **external and hand-coded per store**:
`pipeline_inspect.py` has a `*_status`/`*_orphans` pair for each of corpus / embeddings / projections / graphs
/ motifs, and `cli._clean` wires them one by one. That **duplicates each store's layout knowledge** (the
builder writes it, the inspector re-derives it) so the two drift, and it **silently rots** when a naming scheme
changes ("`clean` won't find files that fell out of the scheme").

Instead, **each stage carries its own hygiene**, and a stage is **atomic** — one key-space, so the stage *is*
its artifact family (no separate `ArtifactFamily` type). A single `build_pipeline()` factory (below) constructs
and wires every stage — it is **the one registry**; the driver flattens its output into a topological list, and
CLI scope (`mytho build embeddings`) matches on the stage's name prefix (`embeddings:*`), not a separate per-module
list. Interface (validated against the real stages):

```python
class Stage:
    # store/id are CLASS-level and only on fan-out / singleton stages (embeddings, projections, motifs), for L2 GC (§2.7).
    # Per-document stages (corpus, graphs) set store = None and rely wholly on L1 (their per-doc desired/actual).
    store: Store | None = None               # WHICH backend its artifact lives in — a *shared* ChromaStore/FileStore (§2.7)
    id: str                                  # this stage's id in that store (collection name / relative path) — from config (§2.7)
    def inputs(self) -> list[Stage]: ...    # upstream STAGES → topological order + wiring
    def desired(self) -> dict[key, fp]: ...  # what SHOULD exist + the fp each should have (config + inputs)
    def actual(self)  -> dict[key, fp]: ...  # what IS built (artifact + its fp sidecar both present) → its stored fp
    def build(self, keys: set) -> None: ...  # BATCHED — the stage owns GPU batching / the pool
    def delete(self, keys: set) -> None: ...  # L1: drop these KEYS within its own store (chunk rows / doc files) — ≠ Store.delete(id), which drops one whole fan-out artifact (a collection/file), L2 §2.7
```

The two maps are the **same shape** (`{key → fp}`) and named by the *state* they describe, not an action:
**`desired()`** = the spec (from config: which keys should exist, and what fp each should hash to now);
**`actual()`** = reality (from the store: which keys are built, and the fp they were built with). A key is in
`actual()` only if **both** its artifact *and* its fp sidecar are present — a build that crashed after writing
the artifact but before its fp leaves the key *out* of `actual()`, so it shows up as `missing` and is rebuilt
(that is how the crash-recovery rule of §9.4 falls out of the model). A single key's fp is never exposed on its
own — the driver always works with the whole map.

**How dependencies flow — a stage reads its inputs' `desired()` maps, nothing more.** A dependent's target fp
folds in its inputs' target fps. So a dependent builds *its* `desired()` by *looking up* the entries it needs
in its inputs' `desired()` maps — no recursion, no recompute; topological order means an input's map is ready
first. Example (`corpus → embeddings`, "Iliad"): corpus's `desired()` is `{"iliad": "abc", …}`, so embeddings'
`desired()["iliad"] = hash("abc" + model + version)`. Fan-in is the same shape — a projection's single entry is
`hash(⊕ embeddings:M.desired().values() + plot_v)`, where `⊕` folds the `desired()` entries **sorted by key**
(a defined order → the fp is deterministic across runs). If corpus's text changes, its `"iliad"` fp changes →
embeddings' does too → embeddings is stale (its `desired` ≠ its `actual`).

**Wiring** is a small `build_pipeline()` factory that constructs the stages and passes each its upstream as
constructor arguments, so `inputs()` returns held references — the parameterised fan-out (per variant / per
model) is just a loop:

```python
def build_pipeline(config) -> list[Stage]:
    corpus = CorpusStage()
    emb = {v.model: EmbeddingsStage(variant=v, corpus=corpus) for v in config.embedding_variants}
    return [corpus, GraphsStage(corpus=corpus), *emb.values(),
            *(ProjectionStage(model=m, plot=p, embeddings=emb[m]) for m in emb for p in PROJECTION_PLOTS),
            *motif_stages(config)]   # PROJECTION_PLOTS: code constants (umap/tsne/pca…); models: from config
```

> **Refs vs names is *not* load-bearing.** Object refs (above) and string-name `inputs()` resolved by the
> driver both fail loud on a *non-existent* dependency (a `NameError` at the factory vs a driver "unknown
> stage" at startup — both before any real work), and *neither* catches a wired-to-the-wrong-but-valid stage.
> A stage *does* reach into its inputs — it calls each input's `desired()` to fold their fingerprints into its
> own — but the *only* thing it needs from an input is that one call, so `inputs()` just has to hand it
> something to call `desired()` on (a held object, or a name the driver resolves to one). Refs avoid a parallel
> name-space; that is the whole (weak) preference — a Part-3 implementation detail, not a principle.

Concretely, who depends on whom:

- **corpus** depends on nothing — its inputs are the config and the raw files, not another stage (because fetch
  is still folded into it, below).
- each **embeddings** stage, and **graphs**, depend on **corpus** — they read its cleaned texts.
- each **projection** depends on the embeddings of *its own model* — it reduces those vectors to a 2-D layout.
- inside **motifs**: the source stages depend on nothing (they scrape external sites); the **crosswalk** depends
  on the sources; the **parallels** depend on the crosswalk and the sources; the **semantic** layer **also
  depends on the sources** (the source motifs — *not* on corpus documents). That dependency is **real and
  permanent**. What is *temporary* is only how `build()` is implemented: the semantic step is a GPU BGE-M3 pass
  that is expensive and non-deterministic in-build, so — exactly like fetch for corpus (§5) — it is **currently
  pulled out to a manual offline step** (`scripts/build_semantic_parallels.py`, run + committed by hand) and the
  pipeline **copies the committed result**. In this copy-in mode the source→semantic edge is *mediated* by that
  manual regen: `desired()` keys on the committed file, and a source change is adopted only after an offline
  re-run + commit (the deliberate-manual pattern of §5 — not a spurious in-build rebuild). **Drop the shortcut
  and `motifs:semantic` becomes an ordinary source-dependent stage**: `build()` re-runs BGE-M3, `desired()` folds
  the sources + model version, a source change re-runs it — the same shape as graphs.

This whole map of who-feeds-whom lives in **one** place — the factory — instead of being re-derived in an
external checker that drifts.

**Fan-out — one stage per config entry.** Some blocks are a single stage; others produce a *variable* number,
driven by config. `corpus` and `graphs` are one stage each. **Embeddings is one stage per embedding model**
listed in `config/models.json` — three models means three stages, all reading the same corpus. **Projections
fan out further** — one stage per (model × **plot**), each wired to the embeddings of its own model. Motifs
is a fixed handful. The fan-out is nothing clever: it's a loop in the factory over the models in the config
(the projection **plots** — the reduction/chart kinds — are code constants, not config) that makes one stage object per entry. Add a
model to the config and a new stage appears on the next build (its
whole collection is "missing", so it embeds all the books just for that model, leaving the others alone);
remove a model and its stage — and its now-orphaned collection — is cleaned.

**Fetch is the one step still bundled in.** Right now the `corpus` stage does two different jobs at once: it
**downloads** each book's raw file (from a web address, or copies it from a local `sources/` folder) *and then*
**cleans** that text into the readable form. Because it downloads its own inputs, it doesn't depend on any
earlier stage — that's why `corpus.inputs()` is empty.

But downloading is a different *kind* of work from building. Downloading hits the network: it's slow, it can
fail, and its result is an archive you want to keep forever. Building is pure and offline — from the same raw
files it always produces the same output. Bundling the two means you can't rebuild without risking a
re-download.

So Part 2 (item 4) pulls fetch out into its own stage that sits *above* corpus. Fetch's only job is to get each
book's raw file and drop it in the archive folder (`corpus/raw/`), one per book listed in the config. After
that, `corpus` depends on fetch, reads the already-downloaded raw, and never touches the network itself. This
split is also what lets `--force` mean "rebuild from the raw I already have" while a separate `refresh` means
"go download fresh from the web" — today the single corpus command muddles both (§5).

**Atomisation of the current blocks.** "Atomise" = split each code module into the smallest
independently-buildable **stages**, so that within one stage *every artifact is keyed the same way*. A **key**
is the identity of one buildable/checkable item inside a stage, derived from config — it comes in two shapes:

- **`document_id`** — the stage has **one artifact per document**, so it has *many* keys, one per book listed in
  `config/corpus.json` (`document_id = hash(locator)`). Build and staleness are decided per document
  (`build({doc_ids})`, `actual() -> {document_id: fp}`).
- **singleton** — the stage produces **one artifact total** (a *global reduce* over all its inputs), so it has
  exactly one key; `build` regenerates the whole thing.

A module's `stages()` may return one stage or several (e.g. one per embedding variant). The table:

| module → `stages()` | how many | key | what one build does |
|---|---|---|---|
| **`corpus`** | 1 | `document_id` | fetch→clean→trim→write one `.txt` per document. `corpus.json` (the catalog) is **not** a second stage — it is *where this stage stores* each doc's metadata + fp, i.e. its sidecar, which `actual()` reads. |
| **`embeddings:<variant>`** | one **per variant** in `models.json` | `document_id` | each variant is its own Chroma collection → its own stage. `build({docs})` chunks those docs and **GPU-batches** the encode; the per-chunk rows share one per-doc `fingerprint` (D2), so the unit is the document, not the chunk. |
| **`projections:<model>:<plot>`** | one **per (model × plot)** — `plot` = the reduction/chart kind (umap/tsne/pca…), a code constant | **singleton** | the reduction runs over **all** of a model's points to emit one `<model>/<plot>.json` — it can't be built "per document," so its whole output is a single key; `build` = full refit (D3). |
| **`graphs`** | 1 | `document_id` | one knowledge-graph per document; `build({docs})` assembles them. The expensive per-chunk LLM step keeps its own **internal** `chunk_hash` cache (a resumable GC tier, §3) — deliberately *not* a driver stage, else a content-addressed key drags in orphan-GC + refcounting. |
| **`motifs:source:<tmi/atu/berezkin>`, `motifs:crosswalk`, `motifs:parallels`, `motifs:semantic`** | several | **singleton** each | motifs is a mini-pipeline; each step emits one artifact. Atomising it makes the internal order explicit via `inputs()` (crosswalk depends on the sources, parallels on the crosswalk, …) — which the former monolithic `build_motifs` hid (now shipped — see [`motifs-atomisation.md`](motifs-atomisation.md)). **`motifs:semantic` depends on the sources** (source motifs, not corpus), but its GPU BGE-M3 step is **temporarily offline + committed** (§5-style deliberate-manual): `build()` copies the committed file and `desired()` keys on it, so a source change is adopted only via an offline re-run + commit. Drop the shortcut → a normal source-dependent stage (`build()` re-runs BGE-M3, `desired()` folds the sources). |

So after atomisation **every stage has a single key shape** (per-doc or singleton) → the `Stage` *is* the family
and no `ArtifactFamily` wrapper is needed. Bonus: adding an embedding variant, a projection method, or a motif
source is just *adding a stage* — it shows up in `status`/`clean`/`build` for free.

Two shapes the atomic interface still must respect: **`build(keys)` is batched** (no expensive stage is
one-item-at-a-time — GPU / pool / global), and **`actual()` is one store pass** (not separate key + fp reads).

A third: **`build(keys)` isolates per-key failure.** One document failing (a 404, a bad decode, an LLM
rate-limit) must **not** abort the rest of the batch — it builds the keys it can, logs the ones it can't, and
simply **does not write their fp sidecar**. That is not a special error path: a key with no sidecar is absent
from `actual()`, so it stays `missing` and is retried on the next run — the same self-healing that covers a
mid-build crash (§9.4). `build_corpus` already behaves this way (`_download_and_process` returns `None` on
failure and the loop continues); the protocol just makes "partial success leaves the failed keys rebuildable"
an explicit contract for every stage, not an accident of one.

One generic **driver** derives every operation as a **diff of the two maps**. It first puts the stages in
**topological order** — each stage after all of its `inputs()` — by a plain topological sort of the `inputs()`
edges (repeatedly take a stage whose inputs are all already placed; if some stages remain but none can be
placed, that's a dependency cycle, and it errors). This ordering is what guarantees an input's `desired()` map
is already computed before a dependent asks for it. Then, per stage in that order:

```
d, a = stage.desired(), stage.actual()             # {key: fp} each
missing = d.keys() - a.keys()                       # should exist, doesn't      → build
orphans = a.keys() - d.keys()                       # exists, shouldn't          → clean / GC
stale   = {k for k in d.keys() & a.keys() if d[k] != a[k]}   # exists, fp diverged → rebuild
```

This per-stage `orphans` set catches only orphan *keys inside a surviving stage* (a removed document). Removing a
whole stage (a model / plot / motif source) makes it vanish from `build_pipeline()`, so it never enters this
traversal at all — its now-unowned store is caught by a **second, store-level orphan pass** (§2.7, level 2).

`status`, `clean`, `build`, GC become **one traversal**, not four bespoke paths — the "build-your-own minimal"
engine (D6), **stateless (D7)**: the "registry" is `build_pipeline()`'s output; the state is `actual()` (disk/store), no manifest.
**Why it can't rot:** each store's layout lives in **one** place (the stage that writes it); adding a
variant/method/source = adding a `Stage` → it appears in status/clean/build automatically.

**Sequencing (this is a big refactor — Part 3, not Part 2).** Part 2 does the small, high-ROI fp work *inside
the existing stages* (the embeddings content-fp gate, `transform_version`, the per-doc `fingerprint` once in the
catalog) — which **prepares the base**: the fp sidecars this protocol reads. **Part 3** is the atomisation
itself — porting `pipeline_inspect.py`'s per-store functions + `cli._clean`'s wiring into the stages and the
generic driver. It also presupposes Part 1 (content-fp dedup, `document_id` paths, colour out of the fp graph).

The sections below are this protocol's pieces: §2.3 is how a stage's `desired()` fps compose, §2.6 is the
driver's topological walk, §2.7 is `actual − desired`, §2.8 is `actual()`'s stored fp (sidecars, no manifest),
§3 is orphan GC.

### 2.3 Fingerprints — how a stage's `desired()` fps compose

Each artifact gets a fingerprint:

```
fp(artifact) = hash( fp(each input)  +  transform_version(stage)  +  output-affecting params )
```

- **Inputs by content hash**, not mtime (we already hash content — the raw file and the cleaned text).
- **transform_version** — bumped when the stage's code/params change (§2.5). Closes "code changed → outputs
  not rebuilt".
- Rebuild **iff fp changed** (or the output is missing); else skip. Cascade is emergent (§2.6).

Granularity per stage:

| artifact | fp key | granularity |
|---|---|---|
| document text | `hash(raw_bytes + content_start/end + patch + clean_v)` | document |
| **chunk embedding** | `fingerprint = hash(doc_fingerprint, model, transform_v)`, stored **in each chunk's Chroma metadata** (so it is written atomically *with* the vector by the same `upsert` — §4); the doc fingerprint = `blake2b(cleaned text)` is **doc-level** (D2, same algorithm everywhere — §2.4), and `transform_v` (the full `transform_version`, §2.5) **covers `chunk_size`/`overlap`, the pinned model lib, and the preprocess prompt** — so a chunk-param change re-embeds | **per-doc decision** (a text edit re-embeds all the doc's chunks) — fixes both flaws of §1.4 |
| projection | `hash(⊕ that model's embeddings `desired()` values + plot_v)` — `⊕` = a fold over `desired()` entries **sorted by key** (deterministic; per-doc fps, D2 — not per-chunk) | **global per (model, plot)** — UMAP is indivisible |
| graph | `fingerprint = hash(doc fingerprint + prompt_v + llm_model)` — **one `graphs/<document_id>/.fp` per document**, covering the whole graph (all sub-graphs: beings/relations/locations/time) | **document** — distinct from the internal **per-chunk** LLM cache (`chunk_hash`, many per doc; a resumable tier §3, *not* the `.fp`) |
| serve-resolve (tree + colour, incl. per-tradition shade) | — | **not an artifact** — region colour *and* its derived per-tradition OKLCH shade (regions.md §8.1) are computed at runtime → tree/colour edits are free |

### 2.4 Hash choice

| | bits | crypto strength | speed |
|---|---|---|---|
| md5 | 128 | **broken** | fast |
| sha1 | 160 | **broken** (SHAttered) | fast |
| sha256 | 256 | strong | slower |
| blake2b | 256/512 | strong | **fastest, in stdlib** |

For change-detection / cache keys (non-adversarial) **any works** — accidental collision is astronomically
unlikely at our scale. Crypto strength matters only if fps become a trust boundary (a shared/remote cache
where a poisoned entry is dangerous). **Decided: `blake2b` everywhere, `digest_size=16` (32 hex)** (fastest +
strong + stdlib; 128 bits is ample collision margin here and keeps raw filenames short) — across **all three
roles**: `document_id` / the raw-archive key (`corpus/raw/<blake2b(locator)>`), every **fingerprint**, *and* the
per-doc **content version** (the doc `fingerprint` = `blake2b(cleaned text)`, D2 — replacing the old `md5` that
`_finalize_text` computed; a one-line swap). This drops **both** broken hashes (`sha1` *and* `md5`) from every
persistent key and leaves genuinely **one algorithm, one length** to reason about. The cost of moving the raw
key off `sha1` is only a **one-time re-key** of the ~27 raw files — the D1 migration **renames them offline**
`sha1(url) → blake2b(locator)` from config (same bytes, no network, no re-fetch; region §6), and it rides that
same migration, which
rebuilds all derived artifacts on the new key anyway. Note the *roles* are still distinct even under one algorithm: `blake2b(url)` = **identity**
("which source"); a content hash = **version** ("what content").

### 2.5 Transform version — where it lives, how it is bumped

A module-level constant per stage, beside the code it versions, folded into that stage's `desired()` fps:

```python
# corpus/clean_gutenberg.py
CLEAN_ALGO_VERSION = 3   # bump when the cleaning/trimming LOGIC changes
```

**Bumped manually** by the developer on a *behavioural* change (not comments/refactors). It lives in git, so
the bump appears in the same diff as the logic change. A forgotten bump is caught by `--force` (§5).

Two rejected auto-alternatives:

- **Timestamp of the `.py` files** — the mtime problem, made fatal by git: `checkout`/`clone`/`pull` reset all
  file mtimes to now ⇒ **every fresh clone or branch switch looks like "all code changed" → full rebuild of
  the whole pipeline**; `cp -p`/rsync/tar preserve old mtimes ⇒ a real change can look older than its output ⇒
  missed rebuild; non-reproducible across machines. **Do not use.**
- **Hash of the `.py` source** — content-addressed (reproducible, git-robust, automatic), but **over-
  invalidates**: a comment, docstring, `black` reformat, or unrelated rename bumps the hash ⇒ needless
  expensive rebuilds (re-embed, re-LLM). Also a **scope problem**: hash only the stage file and you miss
  changes in imported helpers (`utils.normalize_text`) and third-party libs (a `torch`/`sentence-transformers`
  upgrade *does* change embeddings); hash the transitive closure and you over-invalidate even more. Better than
  timestamp, but blunt for expensive stages.

**Chosen: hybrid.** Hash the **output-affecting parameters** (chunk_size/overlap, model id + pinned lib
version, prompt text, content markers) — these are *data*, precise, no false triggers — **plus
a small manual `algo_version`** for pure-logic changes. Middle grounds if fuller automation is wanted:
AST-hash (ignores comments/format, still triggers on no-op refactors), or scope the code-hash to the stage's
core function(s) + pinned dep versions.

> **Caveat — the manual bump reintroduces the human-bookkeeping this doc set out to avoid.** A forgotten
> `algo_version` bump = silent staleness (the very bug we fix), "caught by `--force`" only if someone runs it.
> A *per-stage-by-cost* split (auto code-hash on cheap stages, manual on expensive) was considered as a
> mitigation and **rejected (D4): use the uniform hybrid everywhere.** It adds ~nothing here: the expensive
> stages' behaviour is already a **parameter** the param-hash catches for free (embeddings = model id + pinned
> lib version; graphs = prompt text; preprocess = `preprocess_prompt`), so the manual bump is only a thin net
> for rare pure-logic edits; auto-hash on cheap stages saves only a cheap rebuild and carries a scope trap
> (misses changed helpers/libs); and cost isn't even per-stage (preprocess flips cheap↔$$ by variant config).
> One mechanism, applied the same way to every stage.

### 2.6 Downstream invalidation via fp composition

The driver's topological walk (§2.2), using each stage's `inputs()`. Because an artifact's fp *includes its
inputs' fps*, cascade is emergent — no per-edge "invalidate downstream" logic:

```
in topological order (stage.inputs()); d = stage.desired(); a = stage.actual():
  for key: if d[key] ≠ a[key] (or key missing from a): build, write new fp sidecar
           else: skip
```

A rebuilt node gets a new fp → it is an input to its dependents → they see a changed input fp → they rebuild.
The projection is the special node (`fp = hash(⊕ its model's per-doc embedding fps + plot_v)`, `⊕` sorted by key): **any**
document change → whole projection rebuilds (inherent to global UMAP).

### 2.7 Deletions — `actual − desired`

fp-diff catches **changed/new** inputs but **not removed** ones (they leave orphans). This is exactly the
driver's second set (§2.2) — no separate mechanism:

```
stage.actual().keys()  −  stage.desired().keys()  =  orphans → collect
```

But there are **two kinds of removal**, and the per-stage key-diff above catches only the first:

- **an orphan *key* inside a stage that is still alive** — remove a **document** from `corpus.json`: its text,
  its chunks (Chroma ids carrying that `document_id`), and its graph dir drop out of the *surviving* corpus /
  embeddings / graphs stages' `desired()` while staying in their `actual()`. This is exactly `actual − desired`
  above.
- **an orphan *whole stage (store)*** — remove an **embedding model**, a **projection plot**, or a **motif
  source**: the entire stage vanishes from `build_pipeline()`, so there is **no live stage object to call
  `.actual()` on** — a dead stage enumerates nothing, and the key-diff never sees its Chroma collection or its
  `projections/<model>/` files. **This removal cascades through the *factory*, not the fp graph:** dropping model
  `M` from the config removes `EmbeddingsStage(M)` *and*, in the same construction loop, every `ProjectionStage(M,
  *)` (projections fan out over the *live* models), so the stage and its dependents disappear together — their
  artifacts are now stores **owned by no live stage**.

So orphan detection is **two levels**, because "what physically exists" is known at two granularities:

```
level 1 (key):    live_stage.actual().keys() − live_stage.desired().keys()   # removed document (within a live store)
level 2 (store):  store.list() − {id of every live stage on that store}      # removed model / plot / source (a whole store)
```

**The store abstraction (level 2).** There are exactly **two storage backends** — files on disk and Chroma
collections — so the mechanics live in two small `*Store` objects that stages hold by **composition** (a stage
*has-a* store; it is not a subclass of one). Each `*Store` knows how to **enumerate** its scope and **delete by
id**; neither needs a stage instance:

```python
class ChromaStore:
    def list(self):        return {c.name for c in chroma_manager.list_collections()}
    def delete(self, id):  chroma_manager.delete_collection(id)

class FileStore:
    def __init__(self, root, glob): self.root, self.glob = Path(root), glob
    def list(self):        return {rel_to_root(p) for p in self.root.glob(self.glob)}   # scoped to THIS root
    def delete(self, id):  rmtree_or_unlink(self.root / id)

CHROMA      = ChromaStore()
PROJECTIONS = FileStore("outputs/projections", "*/*.json")      # one store object per file-family
```

A stage carries only its **`id`** in that store — its collection name or relative path — assigned by the factory
from the very config value it fanned out on (`variant.key`, `f"{model}/{plot}.json"`), so `id` needs no new
naming rule:

```python
class EmbeddingsStage(Stage):
    store = CHROMA
    def __init__(self, variant, corpus): self.id = variant.key; ...
class ProjectionStage(Stage):
    store = PROJECTIONS
    def __init__(self, model, plot, embeddings): self.id = f"{model}/{plot}.json"; ...
```

The reaper groups live stages by their shared store and reconciles **per store**:

```python
def reap(stages, *, apply=False):
    live = {}                                     # store → {ids of live stages on it}
    for s in stages:
        if getattr(s, "store", None):
            live.setdefault(s.store, set()).add(s.id)
    for store, live_ids in live.items():
        for orphan in store.list() - live_ids:    # scan THIS store's scope only
            if apply: store.delete(orphan)        # delete by id — the orphan's stage is gone
```

Three properties, each a constraint we hit along the way:

- **Delete is by `id`, not `self`.** An orphan's stage no longer exists (it left the factory), so deletion
  cannot route through an instance; it is a store operation parameterised by the id the scan returned.
- **The scan is scoped per store, never a blanket walk of `outputs/`.** `raw/` (the pinned archive) and the
  resumable caches have **no `*Store`**, so they are never enumerated and never collected — safety *by
  construction*, not by an exclude-list. A single "delete everything under `outputs/` not claimed" would nuke
  the archive.
- **Naming is single-sourced.** `list()`/`delete()` live once on the shared `*Store`; the stage contributes only
  its `id`. No per-instance duplication of namespace knowledge (a lone collection can't and shouldn't know its
  siblings; the reaper aggregates them).

This is deliberately **not** a "reaper *stage*." L2's unit is the **store** (a family/namespace), not a stage
instance, so a GC-only pseudo-stage would sit at the wrong altitude and abuse the `Stage` contract
(`build`/`missing`/`stale` all degenerate). It is an **explicit pass**, fed by the live stages' own `store`+`id`
declarations — which is why it can't rot (each store's layout lives in one place) yet stays outside the per-stage
`desired/actual` loop. It is also what `pipeline_inspect.embeddings_orphan_collections` already does today
(`list_collections()` minus configured variants); the protocol ports that scan into the reaper instead of a
hand-wired per-store checker.

So: **fp-diff for changes; `actual − desired` for removed keys (level 1); `store.list() − live ids` for removed
stores (level 2).** (Raw snapshots are an archive tier, *not* auto-collected — §3, §6.)

Worked example — **drop model `M`**: its `CHROMA` collection and its `PROJECTIONS` files (`M/*.json`) are ids no
live stage claims → orphans on their stores; `status` reports them, `clean --apply` deletes them **by id**; the
raw archive is untouched (no store; keyed by document, not model), no other model re-embeds (their stages are
live, `desired = actual`), and `M`'s preprocess cache is a resumable tier dropped only by `--caches` (§3).
Removing a single *document* instead stays entirely at level 1.

**Why level 2 is inherent, not a wart.** Both sides of the difference need the same two inputs: the **reachable
set** (the live stages' ids, from `build_pipeline()`) and **what physically exists** — only the second differs
from level 1. To learn "collection `M` exists" after `M`'s stage is gone, *something* must either **(a) scan the
store** (`store.list()`) or **(b) read a persistent record of `M` not tied to `M`'s stage** (a manifest). There
is no third way, so **statelessness logically entails the scan**: you cannot be stateless *and* find removed
stores without scanning. Scan and manifest yield the **same** orphan set for a local store; the scan reads
**ground truth** (can't drift; self-heals across crashes / branch-switches / manual `rm`), a manifest is
**faster but drifts** and needs an fsck-scan to be trusted (§9.3). A manifest only reaches what a scan cannot — a
**remote** store or **history** — which are §9.1's growth triggers (a)/(b). At our ~dozen stores the scan is
instant, so it wins now.

### 2.8 `actual()` — sidecars, no manifest (D7)

`stage.actual()` reads the stored fps written *beside* the artifacts last build (in `corpus.json` rows — incl.
the per-doc `fingerprint`, Chroma collection/chunk metadata, `graphs/<id>/.fp`) in **one pass** → `{key: stored fingerprint}`.
Sidecars are the **source of truth**: they survive partial builds, need no single write-lock, and cannot drift
from their artifact. There is **no central index** (D7 — §9.3): a manifest would only cache what `desired()` +
`actual()` already give, and a *correct* staleness check must re-hash inputs either way, so the cache
buys ~nothing while adding a thing that drifts. The stateless driver reads disk
+ sidecars each run — always current. (If lineage/audit or large-scale directory-walk cost ever justify it, a
derived `outputs/.build-state.json` index can be *added* on top without changing the sidecar source of truth —
but note a *derived* index is only a **cache of the level-2 store scan** (§2.7): it must itself be built *by*
scanning, so it speeds up the walk (trigger c) but does **not** remove the scan or make the GC one-level. True
one-level GC needs a *persistent, build-maintained* inventory — which is stateful, i.e. what D7 rejected.)

---

## 3. Garbage collection — the driver's `orphans` set

GC is not a separate subsystem: it is the driver's `actual − desired` (§2.2/§2.7), collected
behind a dry-run confirm.

**Immutable vs overwrite.** Nix-style immutability (new fp = new path, old kept) accumulates stale artifacts
and needs GC; overwrite-in-place (current) accumulates nothing but gives no rollback and a mid-build failure
leaves inconsistency. **For our size, overwrite + orphan-GC suffices**; adopt immutability only if rollback /
A-B model comparison is wanted, and then GC by reachability from the stages' `desired()` (no manifest root).

**Policy catalog:** reachability (delete what's unreachable from the root — our orphan detection); TTL by
age; keep-last-N (for versioned stores); pinning (never-collect); tiered (per class); manual + dry-run
(`clean --apply`).

**Tiered, for us:**

- **derived** (text, chunks, projections, graphs) → **reachability GC**: orphan = not in the expected set →
  collect behind `--apply` dry-run. Half-built already in `pipeline_inspect`.
- **raw archive** → **pin / keep-forever** (durability, provenance); explicit `purge` only — *not* auto-
  deleted even when its doc leaves the config (retired ≠ purged).
- **resumable caches** (extraction/preprocess/LLM chunk-cache/motif scrape) → **TTL or reachability**, safe to
  drop, regenerable; `clean --caches`. **`--force` does *not* touch these** — only `--caches` does (§5), so a
  forced rebuild never re-pays for LLM/scrape work whose inputs are unchanged.

**The tier is a property of the artifact *class*, not the stage — one stage can span tiers.** So GC policy is
applied per artifact class *within* a stage, not per stage wholesale, and the three escape-hatches map one-to-one
onto the three tiers: `--force` rebuilds derived (keeps resumable), `--caches` also drops resumable (the only
thing that re-pays for `$$`), `purge` touches raw. How each stage's outputs land in the tiers:

| stage | derived — reachability GC, `clean --apply` | raw archive — pin, `purge` only | resumable cache — `clean --caches`, `--force` skips |
|---|---|---|---|
| **corpus** | `.txt` tree + `corpus.json` | `corpus/raw/<blake2b(url)>` | extraction |
| **embeddings:M** | the Chroma collection — at **both** granularities: whole collection (level 2, model removed) and chunks within (level 1, doc removed / count shrank) | — | preprocess (LLM variant) |
| **projections:M:plot** | the JSON (singleton; level-2 reachability on removal, else stale-rebuild) | — | — |
| **graphs** | `graphs/<document_id>/` (reachability, per-doc) | — | the internal per-chunk LLM `chunk_hash` cache — **deliberately not a driver stage** (§2.2): a cache tier, dropped only by `--caches`, never by orphan-GC |
| **motifs:\*** | motif JSONs (singleton; reachability when a source stage is removed) | — | motif raw-scrape |

This matches the existing `clean` flags (`--caches`, `--apply`).

---

## 4. The embeddings key — the concrete payoff

The single highest-value change. Replace "skip if `chunk_id` exists" with a **positional id + a stored
`fingerprint`**, compared (not a content-keyed tuple checked by set-membership — that would strand old rows, the
very orphan problem positional ids avoid, below):

```
chunk id  =  document_id::chunk_index                 # positional PK — UPSERTED, never content-keyed
re-embed a chunk  ⇔  its stored fingerprint  ≠  hash(doc fingerprint, model, transform_version)   # else skip
```

The chunk's `fingerprint` lives **in its own Chroma metadata**, so a single `upsert` writes the vector *and*
its fingerprint together — **one atomic row-write, no "artifact-then-fp" window** (that separation applies only
where the two are distinct writes, e.g. graphs' dir + `.fp` file, §9.4). A crash mid-document leaves some chunks
upserted and the rest absent; the next `build` re-embeds exactly the absent-or-stale ones (upsert overwrites the
present ones by their positional id — **never a duplicate**), then drops any trailing `document_id::i` for
`i ≥ new_count` (the only deletion case).

- **document_id** — the rename-stable anchor, **decided as `hash(locator)`** (`data-model-and-ids.md`
  §9-D1). Because the id tracks the upstream locator, not the title, a rename leaves the key unchanged and this
  cache correctly skips the re-embed — flaw 1 is fixed. (The rejected `slugify(title)` anchor would *not* have
  fixed rename-churn; flaw 1 would have stayed. That risk is now closed.)
- **content version** — the **doc `fingerprint`**, **decided (D2): document-level `blake2b(cleaned text)`** (the
  same one algorithm — §2.4; a one-line swap of the `md5` `_finalize_text` computes today). A text edit re-embeds
  *all* of that doc's chunks — over-embedding within a doc, but cheap
  at our scale (tens of chunks = seconds), and the per-chunk alternative's precision is largely illusory anyway
  (positional chunking → an insert shifts every downstream chunk's text, so most chunk hashes change regardless).

Correct on all cases (D1 = `hash(locator)` + a content version): rename (same content) → same key → **skip**
(fixes flaw 1); text edit → new version → **re-embed** (fixes flaw 2); new doc → new id → embed. The non-buzzword value of
ids is precisely this: **`(id, version)` as the incremental cache key.**

**The chunk id stays positional (`document_id::chunk_index`), not content-addressed.** A content-addressed
chunk id (`hash(chunk_text)`) would dedup identical chunks, but it buys an orphan-GC problem — a text edit
mints a *new* id and strands the old one, so you must enumerate a doc's chunks (`where document_id == X`),
diff stored vs new, and delete the difference — plus **reference counting**, because identical chunks can be
shared across documents (delete only when no doc still references the id). Positional ids avoid both: an edit
at position *i* re-uses the same id → **upsert overwrites** (no orphan), and deletion is needed **only when the
chunk count shrinks** → drop trailing `document_id::i` for `i ≥ new_count`. This is why the content lives in a
metadata **version field**, not in the id (see "the chunk id is a bare PK", `data-model-and-ids.md` §5): the
`document_id` metadata is the handle both for this truncation and for deleting a removed document's chunks.

---

## 5. Fetch vs build; the escape-hatch

**CLI surface — decided: four verbs** over one content-addressed diff. `status [scope]` (read-only view of
what's stale/missing/orphaned), `build [scope] [--force]` (make current; `--force` = ignore fingerprints in
that scope), `refresh [documents|motifs]` (re-fetch upstream; preview → `--apply`), `clean [scope] [--apply]
[--caches]` (orphans / cache tier, preview → `--apply`). Destructive/overwrite ops default to preview and
require `--apply`; `build` is non-destructive and runs directly. `scope` is the optional stage/variant escape
(Part 3 item 4).

**Fetch is the DAG boundary, not a stage** — and the full fetch/refresh/flag model lives in its own canonical
doc, [`fetch-and-refresh.md`](fetch-and-refresh.md) (referenced here and from `motifs-fetch-stabilization.md`).
Why a boundary: a stage's staleness is decidable *offline from fingerprints* (network *to produce* an output is
fine — the LLM graph stage — because the output is content-addressed by its input); a fetch's "is my copy still
current vs upstream?" is **undecidable offline**, so it cannot be a build node. The deeper reason it is a
**human-gated** boundary rather than an automatic node: ordinary stages are **purely transforming** — their
output is always re-derivable from the raw on disk, so an automatic mistake costs only recompute and **data loss
is impossible**. Fetch is the only step that touches **raw itself, the one irreplaceable input**; an automatic
overwrite/drop there could destroy it forever. So the human gate sits exactly where an automatic mistake would be
*irreversible*. `refresh` generalises via an `upstream` capability on stages (`corpus`, `motifs:source` have it;
`embeddings`/`projections`/`graphs` do not) and is **not in the topological build order**.

Separate **fetch** (network, into the immutable raw archive — non-deterministic, slow, archival) from
**build** (a pure, offline, reproducible function of raw + config + code).

- **First run** (raw missing): `build` acquires the missing raw, archives it, proceeds — automatic, no
  separate manual step (current `build_corpus` already does `fetch_to_cache(..., force=False)`).
- **Subsequent runs** (raw present): build uses it, no network; present raw is treated as immutable.
- **Upstream update**: an **explicit `refresh --check`** (occasional, human) re-fetches to a temp, diffs
  against the stored raw, reports drift/disappearance, adopts on confirm; build then sees the new raw fp and
  rebuilds downstream.

So acquire-if-missing is automatic; **upstream re-fetch is deliberately manual** — build stays offline and
deterministic. **Motif source stages behave the same way**: they scrape fixed sites once into a cache and
restage only when their config/`algo_version` changes; a changed upstream site is picked up only by the same
explicit `refresh` (or `--caches`), never auto-detected.

**Escape-hatch, in two levels** (they are *not* the same):

- **`--force`** = rebuild every derived artifact from the raw, **ignoring fingerprints** — but the **resumable
  caches stay** (the LLM chunk-cache, extraction cache). So graphs reassemble from the cache, embeddings
  re-encode, projections refit; the expensive LLM calls are **not** re-paid when their input chunks are
  unchanged. This is for "my fp logic might be buggy / partial build — rebuild the tree."
- **`--caches`** = also drop the resumable caches → re-run the LLM / re-scrape. This is the only thing that
  re-pays for `$$` work. (Today `graphs --force` conflates these by clearing the cache; the split fixes that.)

Kept because fingerprinting can have bugs (a forgotten `algo_version` bump) or you just want a guaranteed-clean
rebuild. Every incremental system keeps one (Make `-B`, Bazel clean, Nix `--rebuild`).

---

## 6. Sources — a unified web + local model

Both a web URL and a file in `sources/` are the same thing: an **upstream locator** for a source that may
receive an updated version. They must be handled identically.

### 6.1 The unifying abstraction

```
upstream (URL | sources/-file) ──ingest──► RAW snapshot (immutable, blake2b(locator))
                                                 │
                                       + override layer (shared):
                                          content_start/end, exclude (config)
                                          per-doc unified-diff patch
                                                 ▼
                                          CURATED (derived)
```

The raw key is **unified** (`corpus/raw/<blake2b(locator)>` for both; for local the "url" is the file
locator). Only the *policy* differs today (local auto-re-ingests on hash change; web fetch-once), and neither
has a manual-edit layer.

### 6.2 Manual edits = the override layer only

**Manual curation never mutates the raw and never mutates the upstream (URL or `sources/`-file). It lives only
in the override layer** — identically for both:

- structural trims / skip → `content_start/end`, `exclude` (config);
- arbitrary text fixes (OCR typo, an interleaved note the markers cannot catch) → `overrides/<document_id>.patch`
  (unified diff).

If local edits were made directly in the `sources/`-file, an "upstream update" could not be distinguished
from "my hand-tweak" — the same trap as editing web raw. So `sources/` is reserved for the **authoritative
upstream version** (replaceable by a newer delivered file); all divergence is the patch.

### 6.3 Updates flow identically; the one principled difference

A new version — a web re-fetch **or** a new `sources/`-file delivered — takes one path:

```
new upstream ─► candidate RAW ─► diff against archived RAW
   changed? ─► adopt ─► re-apply override layer ─► rebuild CURATED
                       patch fails to apply ⇒ re-curate signal (like a git conflict)
```

Because edits live in a separate layer, **an upstream update never clobbers them** (unlike today's local
auto-re-ingest, which would). This fixes both web and local with one mechanism.

The **only** difference is the *adopt trigger*, and it follows a principle, not an ad-hoc rule — **checking
upstream is free for local (a file read) and costly for web (a network GET):**

| | read upstream | when to check |
|---|---|---|
| **local** | `sources/`-file read (free) | **every build** — auto-detect hash change |
| **web** | network GET (costly, upstream stable) | **explicit `refresh`** — keep build offline |

The adopt path (diff → adopt → re-apply override) is shared.

### 6.4 Override format

- **config markers** (`content_start/end`, `exclude`) — for structural trims/skip. Structured, tiny,
  git-friendly.
- **per-doc text override** — for point text fixes. **Decided (D5): the unified-diff patch**
  (`overrides/<document_id>.patch`). It stores only the delta (not a near-copy of the derived text), shows
  exactly what diverged in git, re-applies deterministically, and a patch that no longer applies after a
  `refresh` **is** the merge-conflict / re-curate signal. The rejected **full override**
  (`overrides/<document_id>.txt`) stores the whole curated text — a ~99 % copy of the derived text per doc, and
  it *freezes*: on an upstream update it cannot merge, so the fix must be re-done by hand. The patch's only
  extra cost is an **apply** step (`git apply` — git is already the repo — or `patch-ng`); the `curate`
  edit-then-snapshot workflow is needed either way, so it is shared, not a patch-only tax.

Layer order: `curated = trim(clean(apply_patch(base)), content_start/end)`. The patch base is best the
*cleaned* text (boilerplate stripped — what a curator reads); if `clean_version` bumps and the patch fails,
that is a re-curate signal.

**Curator workflow (the curator never writes a diff — a tool does).** Edit-then-snapshot:

```
curate <document_id>          # materialize the current curated text (raw→clean→trim→[+prior patch])
                              # into a working file; the curator edits it in their editor
curate --save <document_id>   # store difflib(base, edited) → overrides/<id>.patch; also stamp a
                              # base-fingerprint (hash of the cleaned base at edit time)
```

On build, `curated = trim(clean(apply_patch(base)), content_start/end)`, and the base-fingerprint is compared
to the current base; if the base moved (new upstream / bumped `clean_version`) and the patch no longer applies,
that failure **is** the merge / re-curate signal.

### 6.5 Web-specific priority

Upstream (e.g. Gutenberg) is near-immutable; the real risk is **disappearance (404)**, not change. So
priorities are **archive (keep the raw copy) ≫ preserve curation ≫ track upstream** (low value — upstream is
stable). Since these texts are public-domain, **committing the raw snapshots** (or backing them up) is a clean
archival + reproducibility strategy.

---

## 7. Strategy / policy catalog

| strategy | essence | fit here |
|---|---|---|
| **Full rebuild (`--force`)** | nuke & rebuild | keep as escape-hatch |
| **Timestamp (Make)** | input mtime > output mtime | reject (mtime lies; git resets mtimes) |
| **Content-addressed (Bazel/Nix)** | fp = hash(inputs + transform) | **target** — catches content *and* code |
| **Event-sourcing / CDC** | config edits as an event stream → targeted invalidation | optional sugar over content-addressing for interactive edits |
| **Immutable / versioned (Nix)** | never mutate; new version = new artifact | only if rollback / A-B models wanted |
| **Manual + audit (current)** | human runs build; `status` shows orphans | as a check, not the policy |

Minimal path, by value — items (1) and (2) collapse into **one per-document fingerprint gate on the
expensive stages** (embeddings, graphs): re-run a document's chunks/graph iff its
`fingerprint = hash(doc fingerprint, model, chunk params, prompt/algo_version)` changed:

- **(1) the doc `fingerprint` in the key** — fixes the real *staleness* bug (a text edit not re-embedding). Note this
  alone does **not** fix rename *churn* — that needs the rename-stable `document_id` anchor, now decided as
  `hash(locator)` (§9.5-D1); once that anchor lands, rename-churn is fixed too (it is out of *this* minimal
  staleness-only tier, but no longer blocked on a decision).
- **(2) transform_version per stage** — code/param edits invalidate; cheap.
- **(3) stateless fp cascade** — recompute fps on the fly from sidecars for a targeted rebuild instead of
  `--force`; moderate (skippable at our size). No central manifest (D7).
- **(4)** extend `status` to "what to rebuild" (orphan detection is already there).

Full Bazel/Nix is overkill for this size — **content-addressed sidecar fps + transform versions, computed
statelessly** is the right amount. (This minimal path is exactly what **Part 2** below implements; the
protocol/driver of §2.2 is the later **Part 3** generalisation of it.)

### Implementation order — **Part 2 of 4: incrementality base** (small, high-ROI; inside the existing stages) — ✅ DONE

> **Status: shipped (Stage II).** Items 1–5 below are implemented inside the existing stages, tests are the
> acceptance gate (`test_embeddings_transform.py`'s `embed_plan` cases = edit→re-embed / unchanged→skip /
> version-bump→re-embed / shrink→drop-trailing; `test_corpus_refresh.py`; `test_graphs_store.py`). Two things
> are **deliberately deferred to Part 3**, not skipped: the **rename-churn** half of item 1 (needs Part 1's
> `document_id` anchor — today's anchor is still `slug(title)`), and the **generalised per-source staged
> `refresh`** / source-unit layer of item 4 (`fetch-and-refresh.md` §7 — `refresh motifs` currently re-scrapes
> wholesale rather than per-source-diffing). The fingerprints are written in the shape Part 3's `actual()` reads.

**Part 1 (the data-model + region migration) is the single list in
[`region-implementation.md`](region-implementation.md) §5.** Part 2 is the **small** fp work done *inside the
existing stages* — no protocol refactor yet. It **prepares the base** (the fp sidecars) that Part 3 later
harvests, so it must write each fp in the shape Part 3's `actual()` will read it back — `blake2b`, stored per
doc in the `corpus.json` row / per collection in Chroma metadata / `graphs/<id>/.fp` — or Part 3 reworks it.
None of it blocks shipping Part 1. Each item references its (already-decided) Dx; full list in §9.5.

1. **Embeddings content-fp staleness gate** — replace the id-existence dedup with a stored chunk `fingerprint`
   = `hash(doc fingerprint, model, ver)`; store the per-doc `fingerprint` = `blake2b(text)` **once in the
   catalog** (D2, §2.3; the `blake2b` swap of today's `_finalize_text` md5), embeddings reads it. Fixes the
   real re-embed-on-edit bug; the rename-churn half comes free from Part 1's `document_id` anchor.
2. **`transform_version`** — uniform param-hash + one manual `algo_version` per stage (D4, §2.5).
3. **Atomicity** — write the artifact *then* its fp sidecar; atomic swap for the catalog/collection — §9.4, so
   a stored fp never lies under a mid-build crash. **The swap is `os.replace(<target>.partial, <target>)` — an
   atomic rename, never copy-then-delete.** Rename *consumes* the staging file (it *becomes* the target), so a
   successful commit needs no apply-time cleanup and leaves no window where both exist; a rejected write instead
   discards `<target>.partial`, leaving the live file untouched. (Export consequence: `.fp` sidecars must ride
   along in the bundle, `*.partial`/`*.tmp` staging must not — see Part 3's *Export impact*.)
4. **fetch/build split** + explicit `refresh` + pin raw archive — §5, §6.5. Splits `--force`'s two meanings:
   **`--force` = rebuild derived from raw**; **`refresh` = re-fetch upstream** (today corpus conflates them).
5. Graphs build/serve unify + traversal guard (isolated bug; also in Part 1 §5 step 6 — do wherever first).

**Migration story — Part 2 does NOT re-fetch, and needs no rebuild-from-raw.** Part 1's migration itself does not
re-fetch either (it re-keys the raw in place, region §6); the raw archive is already in its blake2b form and Part
2 touches neither the raw keys nor the sources. Part 2 changes the **staleness-decision** machinery, not artifact
**content** (vectors,
graphs, text are unchanged), so its transition is only to give the Part-1 artifacts the `fingerprint`s they lack:

- **land Part 1 + Part 2 together** → the single Part-1 rebuild writes the fingerprints from the start → **no
  separate Part-2 migration at all**;
- **land Part 2 after Part 1** → a **metadata-only backfill** (no network / GPU / LLM): compute the per-doc
  `fingerprint` from the on-disk `.txt` into the catalog; add each chunk's `fingerprint` via a Chroma
  **metadata update** (no re-encode); write each graph's `.fp`. Or, if you skip the backfill, the first plain
  `build` sees "no fingerprint" everywhere and **re-embeds once** (GPU, still no network) — acceptable at ~27
  docs, avoidable via the backfill. **Either way there is no re-fetch — not in Part 1, not here.**

*(D3 decided — keep the full UMAP refit, no parametric work — §9.2.)*

### Implementation order — **Part 3 of 4: the stage-protocol refactor** (big; deferred; consumes Part 2's base)

The **self-describing-stage** architecture (§2.2): atomise each block into `stages()`, port
`pipeline_inspect.py`'s per-store `*_status`/`*_orphans` and `cli._clean`'s wiring *into* the stages, and make
`status`/`clean`/`build`/GC **one generic-driver traversal**. It ends the "external inspector rots" failure mode
structurally. Deferred because it is the **largest** refactor and touches every stage + `cli.py`; it consumes
the fp sidecars Part 2 laid, and presupposes Part 1 (content-fp dedup, `document_id` paths, colour out of the
fp graph).

1. Atomise the blocks per §2.2's table (`corpus`, `embeddings:<variant>`, `projections:<model>:<plot>`,
   `graphs`, `motifs:*`); implement `inputs/desired/actual/build(keys)/delete` on each, and declare `store` +
   `id` on the fan-out/singleton stages (per-doc `corpus`/`graphs` set `store = None`) for the level-2 reaper (§2.7).
2. The generic driver over `stages()`; **retire `pipeline_inspect`'s per-key scans into each stage's
   `desired()`/`actual()` (level-1 orphans), but *port* its store-level scans — `embeddings_orphan_collections`
   and the `projections/*/` listing — as the driver's level-2 pass (store-vs-live-stages, §2.7): they catch a
   *removed whole stage*, which the per-stage key-diff structurally cannot.** Retire `cli._clean`'s per-store
   wiring.
3. (D6 decided — build-your-own.) Re-evaluate **DVC/Dagster** only if one of §9.1's explicit triggers fires
   (remote store / lineage / walk cost); the driver already *is* build-your-own, so this is "when to switch,"
   not "what to build now."
4. **Optional `scope` on `status`/`build`/`clean`** — a **stage** (`embeddings`) or **variant**
   (`embeddings:bge-m3`) token, matched by prefix over `stages()` (`id == token or id.startswith(token + ":")`).
   Not needed for correctness (full incrementality already rebuilds exactly the stale set) — it is the rare
   manual escape for **deferring an expensive stage** or a **scoped `--force`**. Separator `:` (uniform across
   filesystem and Chroma stores). No key-level / `--doc` / wildcard. Ships thin or last.
5. **Rewire `export_bundle.py` onto the driver** — it is the one *other* consumer of the retired
   `pipeline_inspect`. Today `orphan_summary()` imports `corpus_orphans` / `embeddings_orphan_chunks` /
   `embeddings_orphan_collections` / `projections_orphans` / `graphs_orphans` (`export_bundle.py:27–35`) and
   `_is_cache` hardcodes the cache filenames (`export_bundle.py:41,60`). Retiring `pipeline_inspect` **breaks
   these imports**, so: point `orphan_summary()` at the driver's `clean --dry-run` plan (same set-reconciliation),
   and drive cache-exclusion from each stage's declared cache tier (§3) instead of the hardcoded list.

**Export impact across the parts** — `export_bundle.py` bundles `outputs/` and reports the orphans it would
carry. It is affected at every part, but only Part 3 *breaks* it:

| part | export effect |
|---|---|
| **Part 1** | layout changes (`corpus/<Region>/…`, `graphs/<document_id>/`, blake2b raw) are **auto-absorbed** — export `rglob`s each dir. **Decided (uniform, all sources):** **all raw is a cache** — `corpus/raw/` **and** `motifs/raw/` are excluded by default and shipped **only with `--caches`** (extend `_is_cache` to `corpus/raw/**`, matching the existing `motifs/raw` rule, `export_bundle.py:62`; both then honour the existing `include_caches` flag). Raw is never committed; the bundle ships cleaned corpus + derived artifacts, raw is rebuild-fuel re-fetchable from `config`. |
| **Part 2** | **`.fp` sidecars ride along automatically** (`rglob`, not treated as cache) — **required for a coherent bundle** (else the target's first `status` sees no fingerprints → all stale). **New:** exclude `*.partial` / `*.tmp` (the atomic-write staging, item 3) so staging junk never travels. |
| **Part 3** | **breaks the `pipeline_inspect` imports → item 5 above** (rewire `orphan_summary` + cache-exclusion onto the driver). |
| **motifs** | `.partial` staging covered by Part 2's temp-exclusion; `.absent` markers already sit under the excluded `motifs/raw`. |

Principle: **a bundle must carry each artifact together with its fingerprint** so the target's `status` reads
"current", not "all stale" — already true today (Chroma copied file-for-file carries the metadata fp; `.fp`
files ride along) and must survive the temp-exclusion.

**Migration story — Part 3 needs no data migration; it is code-only.** It changes *how the pipeline is
orchestrated* (a generic driver over self-describing stages), not artifact content, fingerprints, or their
location: the fingerprints are already on disk in the shape Part 3's `actual()` reads (Part 2 wrote them; the
formula is unchanged, so the values match), and atomisation is a code split — the Chroma collections,
`projections/*/`, `graphs/`, and the `corpus/` tree stay put; `store`/`id` merely *name* them. So no re-fetch, no
re-embed, no re-LLM, no artifact move. The only possible one-time cost: any artifact Part 2 did not fingerprint
(e.g. projections, motif sub-steps if out of Part 2's scope) is recomputed once on the first driver run — cheap
(UMAP refit / motif reassembly, no network, not GPU-dominant), and avoidable if Part 2 fingerprinted it.

### Implementation order — **Part 4 of 4: manual text curation** (editorial; independent; last)

> **⏸ PAUSED — not now.** Deferred deliberately; do not start until explicitly resumed. It is editorial and
> fully independent (blocks nothing else), so pausing it costs nothing to the other parts.

Hand-fixing a document's text (OCR typo, an interleaved note the markers can't catch) as an **override layer**
that never mutates raw or upstream — an editorial workflow, not required to ship the migration or to make
rebuilds incremental, so it goes last.

1. **The override layer + `curate` workflow** — `overrides/<document_id>.patch` (**D5: unified-diff patch**);
   `curate` materialises the current curated text, the curator edits it, `curate --save` snapshots
   `difflib(base, edited)` + stamps the base-fingerprint; build applies the patch (`git apply`) — §6.2–§6.4.
   Prerequisite: the fetch/build split + `refresh` (Part 2 item 4).

**Migration story — Part 4 is additive; it touches no existing artifact.** It only *adds* `overrides/*.patch`
files; existing raw, text, embeddings, and graphs are unchanged. Applying a new patch re-derives that one
document on the next build (cheap, offline). No re-fetch, no bulk re-embed.

### Migration cost across the four parts

**All the heavy work — the one full rebuild — is Part 1, and it is GPU/LLM, not network: the migration re-keys
the raw in place (no re-fetch). Nothing re-fetches or bulk-re-embeds after it.** (Rows are *incremental* cost if
the parts land in sequence; landing Part 1+2 together folds Part 2's backfill into Part 1's rebuild.)

| part | network (re-fetch) | GPU (re-embed) | LLM (graphs) | what the transition actually is |
|---|---|---|---|---|
| **Part 1** | **none** (raw re-keyed in place) | full | full | the heavy migration: rename raw `sha1→blake2b` offline, then full rebuild off it (region §6) |
| **Part 2** | — | — (backfill) / once if lazy | — | **metadata-only** fingerprint backfill onto Part-1 artifacts |
| **Part 3** | — | — (rare one-off*) | — | **code-only** refactor; reads Part 2's fingerprints (*maybe a one-off refit of un-fingerprinted projections/motifs) |
| **Part 4** | — | — | — (per edited doc) | **additive**: new `overrides/*.patch`; re-derives only the edited document |

D1 is decided — `document_id = hash(locator)` — and **D8 is dissolved**, so Part 1 is fully unblocked. Decided
since: **D2** (doc-level `fingerprint` = `blake2b`), **D3** (full refit), **D4** (uniform param-hash + manual `algo_version`), **D5**
(unified-diff patch — Part 4), **D7** (stateless, no manifest), **D6** (build engine — **build-your-own**, the
§2.2 protocol; DVC only when §9.1's explicit trigger fires). **No open decisions remain.**

---

## 8. Coherence between builds

With content-addressing, coherence is guaranteed **at build completion** (every artifact matches its inputs).
Between builds (config edited, not yet rebuilt) the serve layer reads whatever is on disk. For a
single-user research tool the **build-then-serve** model is sufficient; if on-the-fly coherence is needed,
use atomic artifact swaps or a `status`-driven "stale" flag.

**Stated assumption — one builder at a time.** This whole design assumes a **single-user, single-build**
setting: at most one `build` runs at a time, and serving reads the last completed build. That is what lets
`actual()` trust on-disk sidecars and the driver stay stateless (§9.3). It is an *assumption*, not a guarantee —
§9.3's "concurrent builds self-heal" holds only in the weak sense that each run re-reads truth, **not** that two
`build` processes may safely race on the same store (the `corpus.json` atomic swap serialises one writer, but two
concurrent writers to the same collection are out of scope, and `test_concurrency.py` covers the LLM
`map_concurrent` fan-out *within* a build, not competing builds). If this ever becomes multi-writer (a scheduled
service, a shared remote cache), add a per-store build lock — but that is a different product than the one
these docs spec.

---

## 9. Weak spots, alternatives & open decisions

### 9.1 Big alternative — adopt a ready-made engine instead of building our own

Everything here (content-addressed DAG, fingerprints, cache, GC, lineage) is what existing data-pipeline
engines already do — the field is large and well-mapped; the canonical index is
**[awesome-pipeline](https://github.com/pditommaso/awesome-pipeline)** (a curated list of workflow/pipeline
frameworks — the tools compared below and dozens more). A full feature-by-feature matrix of our design against
the twelve most relevant engines (incl. our distinctive design decisions) is in
**[`pipeline-engine-comparison.md`](pipeline-engine-comparison.md)**; the table below is the summary. **Selection criteria for us:** (a) content-addressed
caching — the whole point; (b) in-process Python vs shell-out (our stages are Python functions); (c)
weight/dependency; (d) remote artifact storage (raw archive + large embeddings); (e) our size (~27 docs argues
against heavy tools).

| engine | class | content-cache | model | weight | notes |
|---|---|---|---|---|---|
| **DVC** | data/ML versioning | ✔ | shell-out stages | medium | `dvc.yaml` DAG, `dvc repro` = minimal rebuild, `dvc.lock` hashes, remotes for raw/embeddings. Our `cli.py` already exposes per-stage commands → wrapping is cheap. **Best off-the-shelf fit.** |
| **Dagster** (assets) | orchestrator | ✔ | Python in-process | med-heavy | software-defined assets: deps, materialization, freshness, partial re-materialize, lineage. Fits when this becomes a scheduled multi-asset product. |
| **Snakemake** | DAG runner | ✔ (content triggers) | shell-out | medium | mature file-DAG, bioinformatics-flavored/shell-oriented. |
| **Nextflow / Pachyderm** | DAG / k8s | ✔ | containers | heavy | HPC/cloud/k8s — wrong weight for us. |
| **Luigi** | orchestrator | partial | Python | light | task+target deps; older, no strong content cache. |
| **Airflow** | scheduler | ✗ | Python | heavy | scheduling, not content-caching — wrong tool. |
| **Make** | build | ✗ (mtime) | shell-out | trivial | mtime lies (appendix) — reject. |
| **doit** | build (Python) | ✔ (md5) | Python in-process | light | make-in-Python: `file_dep` checked by **md5 content signature** (not mtime), `uptodate` callables for *computed* staleness, DAG, signatures in a small `.doit.db`. **This is essentially our "build-your-own" already written** — the §7 gate + sidecar store, packaged. |
| **redun** (insitro) | task memoization | ✔ (content) | Python in-process | light-med | **Nix-model in Python**: hashes each task by name + **source code** + input hashes → content-addressed value store; near-1:1 with our `fp = hash(inputs + transform)`. Note it **auto-hashes the task source** — exactly the D4 alternative we *rejected* as over-invalidating (§2.5); we chose param-hash + manual `algo_version`. |
| **targets** (R; ← drake) | pipeline | ✔ (content) | R in-process | medium | the **canonical** dependency-graph-skips-unchanged tool: skips targets whose "code, data, and upstream" are unchanged — our `desired/actual` + cascade, in R. Wrong language for us, but the reference implementation of this exact idea. |
| **build-your-own** | — | ✔ | in-process | ~few hundred LOC | full control, no heavy dep; the stage protocol + driver (§2.2) — stateless fp/GC, no manifest. **But see `doit`/`redun` above — much of this is off-the-shelf.** |

**Decided (D6): build-your-own** — at ~27 docs the §2.2 stage protocol + driver (the §7 gate + small fp
sidecars, stateless fp/GC, no manifest) is the best ROI: in-process, no new heavy dependency, and it follows
directly from D7 (stateless in-process ⇒ no reason to take on DVC's shell-out process boundary and `dvc.lock`
state). The fork is thus **explicit, not defaulted**, in *both* directions — and so is the reverse fork:
**reevaluate DVC when, and only when, one of these triggers fires** —

- **(a) remote artifact store** — the raw archive + embeddings outgrow the git repo / local disk and need an
  S3-style remote (DVC's remotes are its main draw; build-your-own has none);
- **(b) cross-run lineage/audit** becomes a recurring debugging need — the one thing stateless deliberately
  gives up (§9.3);
- **(c) directory-walk cost** — the corpus grows large enough that re-scanning every store per run is felt.

Until one fires, build-your-own is strictly better here. **Dagster** only if this becomes a scheduled
multi-asset product. Avoid Pachyderm/Nextflow/Airflow (weight/purpose), Make (mtime).

**"Build-your-own" ≠ "from scratch" — the explicit fork against `doit`/`redun`.** Both are Python, in-process,
content-addressed, and light; either could *be* the engine instead of hand-rolled code. The fork:

- **not `doit`, because** its `uptodate`/`file_dep` model is file-oriented and would still need our two-shape
  key layer (per-`document_id` vs singleton), the two-level orphan GC (§2.7), and the Chroma-collection /
  projections store adapters written on top — it saves the *driver skeleton*, not the parts that are actually
  ours. Reasonable to lift its md5-signature-store idea rather than reimplement it, though.
- **not `redun`, because** it auto-hashes each task's **source code** — the D4 alternative we rejected as
  over-invalidating (a comment/refactor re-embeds); adopting it would re-open a decision we closed. It also
  wants its own value store, duplicating Chroma/the catalog as the artifact home.

So D6 stays build-your-own, but the honest framing is **"a thin driver over our own stores, borrowing `doit`'s
content-signature trick,"** not "a novel engine." If Part 3's driver ever feels heavy, `doit` is the first
off-the-shelf fallback to reconsider.

**Cross-tool validation of the model.** The design is not exotic — mature engines use the *same* shapes, which
is reassurance, not a gap: **Flyte**'s cache key = `Cache Version + Task Signature + Task Input Values` is our
`hash(transform_version + params + input fps)` almost symbol-for-symbol, and its default **"hash the storage
location, opt into a content hash"** is exactly our split of `hash(locator)` (identity) vs the doc `fingerprint` (version).
**Dagster**'s "software-defined asset" with materialization + freshness is our "stage as a self-describing
asset." We re-derived a standard content-addressed pipeline; the only genuinely non-standard piece is the
*identity* layer (see the provenance-addressed note in `data-model-and-ids.md` §5).

### 9.2 Projections defeat "minimal rebuild"

A global UMAP means **any** chunk change rebuilds the *whole* projection (all points). Alternative:
**parametric projection** — `fit` once, `.transform()` new/changed points into the existing space (UMAP
supports this). *Pros:* incremental, cheap. *Cons:* the embedding drifts vs the original fit → a periodic full
refit is still needed; not all methods transform. **Decided (D3): full refit** — at this corpus size a refit
is cheap, it is simpler, method-agnostic, and avoids drift; the parametric path is not worth its complexity
here.

### 9.3 Manifest vs stateless — DECIDED (D7): stateless

**Decided: stateless** — no central index; each build/`status` compares the config-expected set vs on-disk and
recomputes fps on the fly (fps live in per-artifact sidecars). Why it wins here:

- A **correct** "what's stale" must hash the current inputs either way (you can't know content changed without
  hashing it — mtime lies), so the manifest saves only *reading previous fps from one file vs N sidecars* —
  trivial. A "fast" manifest that skips re-hashing is fast only by **trusting a possibly-stale cache** — which
  sacrifices the currency we care about.
- "What depends on X" is a **static** fact of this pipeline (graphs ← prompts, etc. — known from the code), not
  something needing stored edges; the manifest only pays off for dynamic, fine-grained dependency graphs we
  don't have.
- Stateless doesn't carry a stale index: an out-of-band **deletion**, a mid-build crash, a git-branch switch, or
  concurrent builds all self-heal because it reads on-disk truth each run. *(Caveat: `actual()` reads the fp
  the artifact was **built with**, not a re-hash of the artifact's current bytes — so a silent out-of-band
  **edit** of an already-built artifact is **not** detected. That is out of scope for input-based staleness;
  `--force` is the recovery, or a separate output-integrity check if it ever matters.)*

The manifest's only genuine residual edge is historical **lineage/audit** and avoiding a directory walk at
large scale — both nice-to-have, revisit if the corpus grows or lineage debugging becomes a real need.

**Two manifest flavours, don't conflate them (they answer different questions):**

- a ***derived* manifest** is regenerated from on-disk truth — i.e. **built by the level-2 store scan** (§2.7).
  It is a **cache of the scan**, so it can only *speed up* the directory walk; it does not remove the scan and
  does not make GC one-level. Safe (rebuildable, can't drift), because it never claims to know more than disk.
- a ***persistent, build-maintained* manifest** is mutated **incrementally by builds** — append `M`'s store
  address the moment `M` is built, remove it only when GC collects it — and **never touched by config edits**.
  *This* is what removes level 2: because the record of `M` survives the config forgetting `M`, GC finds the
  removed collection by `recorded − reachable` with **no scan**. But it is **stateful** — a crash between
  writing `M` and appending its entry leaves the manifest lying (the exact drift D7 weighed and rejected).

So one-level GC is not free: it is bought with the persistent stateful manifest. **Stateless ⇔ two-level GC** is
an *implication*, not a coincidence — the scan is the price, and the only thing that buys it away is the state we
declined.

> **Not now — neither manifest is built.** The **shipped** mechanism is the stateless scan (§2.7): decided
> stateless (D7), and at our ~dozen stores the scan is instant. A manifest — derived (a scan cache, for
> directory-walk cost) or persistent build-maintained (for one-level GC / remote / lineage) — is a **growth-trigger
> option only**, added *if and when* a §9.1 trigger (a)/(b)/(c) fires. Until then there is no manifest to build,
> maintain, or fsck.

### 9.4 Atomicity / partial-build failure — ADDRESSED (Part 2 item 3 + §2.2)

Builds crash mid-way (network, GPU OOM, LLM rate-limit — the graph stage already handles the last). Then an
artifact and its fp can disagree. Rule: **write the artifact first, then its fp**; treat *artifact-present /
fp-absent* as "rebuild" (a key with no fp sidecar is absent from `actual()` → shows as `missing` → rebuilt).
For the catalog/collection, prefer atomic swap (write to temp, rename) so a reader never sees a half-written
index. This is now a shipped step — **Part 2 item 3** specifies it before the fp machinery is trusted — and its
per-key counterpart, **`build(keys)` failure isolation**, is the explicit contract in §2.2 (one failed key
writes no sidecar and is retried next run, the rest of the batch proceeds).

### 9.5 Consolidated open decisions

| id | decision | options | blocks |
|---|---|---|---|
| ~~**D1**~~ | `document_id` anchor — **DECIDED: `hash(locator)`** | ~~`slugify(title)` vs~~ `blake2b(upstream-locator)` (= raw key `corpus/raw/<blake2b(url)>`) | doc coherence, §4 rename-stability, persist-id — *unblocked* |
| ~~**D2**~~ | embedding content-version granularity — **DECIDED: doc-level `fingerprint` = `blake2b(text)`** | ~~per-chunk `hash(chunk_text)` vs~~ doc-level (cheap here; per-chunk precision illusory under positional chunking); algorithm = `blake2b`, one hash everywhere (§2.4) | §2.3 / §4 |
| ~~**D3**~~ | projections incrementality — **DECIDED: full refit** | ~~parametric `.transform()` vs~~ full refit (cheap at this size, simpler, no drift) | §9.2 |
| ~~**D4**~~ | transform_version — **DECIDED: uniform** param-hash + one manual `algo_version` | ~~per-stage-by-cost auto/manual vs~~ uniform (params cover expensive-stage behaviour; split adds ~nothing) | §2.5 |
| ~~**D5**~~ | override format — **DECIDED: unified-diff patch** (Part 4) | ~~full override (near-copy, freezes on upstream update) vs~~ unified-diff patch (delta only, auto-re-applies / clean conflict) | §6.4 |
| ~~**D6**~~ | build engine — **DECIDED: build-your-own** (the §2.2 protocol) | ~~adopt DVC now vs~~ build-your-own in-process (follows from D7 + ~27-doc scale); DVC only when the **explicit trigger** in §9.1 fires | §9.1 |
| ~~**D7**~~ | manifest vs stateless — **DECIDED: stateless** | ~~central index vs~~ recompute-on-the-fly from sidecars (never drifts; correct staleness needs re-hashing either way) | §9.3 |
| ~~**D8**~~ | ~~`slugify` transliteration~~ — **DISSOLVED** | there is no slug: `region_id`/`tradition_id` = the canonical name (data-model §5), documents = `hash(locator)` | — |

**Proportionality.** This is a spec for ~27 documents. The immediate, high-ROI work is small: the §4
embeddings key (D1 + D2 both decided) + the graphs build/serve fix. The stateless fp cascade and GC tiers
are "when it grows" — do not read the whole doc as "build now".

## Appendix — why mtime lies

mtime is an unreliable proxy for "content changed":

- **Touch without change** — `touch`, `git checkout` (rewrites files with new mtimes, identical content),
  re-writing identical output ⇒ spurious rebuilds.
- **Change without an mtime advance** — clock skew (NFS/VM/multi-machine); tools that preserve times
  (`cp -p`, `rsync --times`, tar extraction, git sets mtime to checkout time, not commit time) ⇒ an input can
  be *older* than the output it changed ⇒ missed rebuild (staleness).
- **Coarse resolution** on some filesystems (1–2 s) ⇒ two edits in the window look identical.
- **Blind to the transform** — mtime compares file times only; it cannot see that the *rule/code* changed
  (Make famously will not rebuild on a flag/logic change without manual wiring).

Content hashing compares *what the bytes are*, not *when they were touched* — which is why Bazel/Nix moved to
content-addressing.
