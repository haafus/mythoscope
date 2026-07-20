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
| 1 | **Corpus** | corpus.json + traditions.json + sources | `corpus/raw/<sha1(url)>` (raw snapshot; `sha1(url) = document_id`, D1), `corpus/<Region>/<Tradition>/<Title>.txt` (cleaned text — decided layout, data-model §6), `corpus/corpus.json` (catalog + counts + md5) | raw-fetch (sha1 url), extraction | network (~s/doc); clean/trim CPU-cheap |
| 1.5 | **Preprocess** (variant, optional) | cleaned text + variant config | `preprocessed/…` | preprocessing | **always an LLM transform when present** (`preprocess.py` → `LLMProcessor`, per-chunk) = **$$, rate-limited**. There is no cheap preprocess: a variant either enables it (LLM) or skips it entirely (embeds the base cleaned text) |
| 2 | **Embeddings** | cleaned text (+ variant) + models.json | `embeddings/` (Chroma collections per model) | chunk-cache; the collection itself is a store (dedup by chunk_id) | **GPU — dominant**; per-chunk |
| 3 | **Projections** | vectors (embeddings) + method | `projections/<model>/<method>.json` | — | moderate; **UMAP is global** (over all points), not per-chunk |
| 4 | **Graphs** | cleaned text + prompts.json + LLM | `graphs/<document_id>/…` (`document_id = hash(locator)`, D1) | chunk-cache (LLM responses) | **LLM — $$, rate-limited**; per-chunk |
| 5 | **Motifs** (a 5-step sub-pipeline) | motif sources (TMI/ATU/Berezkin) | `motifs/*.json` | motif raw-scrape | scrape sources → crosswalk → inline relations → lexical parallels → semantic/reasoned parallels → store. **Independent** of the corpus. CPU-moderate **only because** the one GPU part — BGE-M3 *semantic* parallels — is **precomputed offline** (`scripts/build_semantic_parallels.py`) + committed, and the build just copies it |
| S | **Serve** | traditions.json + corpus.json + embeddings + projections + graphs + motifs | (runtime) | front load-once indexes | — |

**No separate `download`/`fetch` stage** — network fetch is folded *inside* Corpus (`corpus` = "Download and
build") and Motifs (`build_motifs` scrapes/downloads its sources), cached by `sha1(url)` / raw-scrape. §5
(fetch-vs-build) is exactly the proposal to split it into a first-class stage (Part 2 item 6).

### 1.2 Dependency DAG

```
config/corpus.json ─┐
sources/           ─┼─► raw ─► clean/trim ─► [text .txt] ─► corpus.json (catalog)
config/traditions ──┘                          │
(serve-time only: color/tree/grouping)         ├─► preprocess ─► EMBEDDINGS ─► PROJECTIONS (global per model)
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
its artifact family (no separate `ArtifactFamily` type). A module exposes `stages()`; the driver flattens all
modules into one topological list. Interface (validated against the real stages):

```python
class Stage:
    def inputs(self) -> list[Stage]: ...    # upstream STAGES → topological order + wiring
    def desired(self) -> dict[key, fp]: ...  # what SHOULD exist + the fp each should have (config + inputs)
    def actual(self)  -> dict[key, fp]: ...  # what IS in the store + the fp it was built with (sidecars)
    def build(self, keys: set) -> None: ...  # BATCHED — the stage owns GPU batching / the pool
    def delete(self, keys: set) -> None: ...

def stages() -> list[Stage]: ...            # per module; grouping for the CLI (`mytho embeddings` …)
```

The two maps are the **same shape** (`{key → fp}`) and named by the *state* they describe, not an action:
**`desired()`** = the spec (from config: which keys should exist, and what fp each should hash to now);
**`actual()`** = reality (from the store: which keys are there, and the fp they were built with). A single key's
fp is never exposed on its own — the driver always works with the whole map.

**How dependencies flow — a stage reads its inputs' `desired()` maps, nothing more.** A dependent's target fp
folds in its inputs' target fps. So a dependent builds *its* `desired()` by *looking up* the entries it needs
in its inputs' `desired()` maps — no recursion, no recompute; topological order means an input's map is ready
first. Example (`corpus → embeddings`, "Iliad"): corpus's `desired()` is `{"iliad": "abc", …}`, so embeddings'
`desired()["iliad"] = hash("abc" + model + version)`. Fan-in is the same shape — a projection's single entry is
`hash(⊕ embeddings:M.desired().values() + method_v)`. If corpus's text changes, its `"iliad"` fp changes →
embeddings' does too → embeddings is stale (its `desired` ≠ its `actual`).

**Wiring** is a small `build_pipeline()` factory that constructs the stages and passes each its upstream as
constructor arguments, so `inputs()` returns held references — the parameterised fan-out (per variant / per
model) is just a loop:

```python
def build_pipeline(config) -> list[Stage]:
    corpus = CorpusStage()
    emb = {v.model: EmbeddingsStage(variant=v, corpus=corpus) for v in config.embedding_variants}
    return [corpus, GraphsStage(corpus=corpus), *emb.values(),
            *(ProjectionStage(model=m, plot=p, embeddings=emb[m]) for m, p in config.projection_plots),
            *motif_stages(config)]
```

> **Refs vs names is *not* load-bearing.** Object refs (above) and string-name `inputs()` resolved by the
> driver both fail loud on a *non-existent* dependency (a `NameError` at the factory vs a driver "unknown
> stage" at startup — both before any real work), and *neither* catches a wired-to-the-wrong-but-valid stage.
> Since fp flow is via each stage's `desired()` map (stages no longer reach through refs to compute anything),
> `inputs()` only needs to *identify* dependencies. Refs avoid a parallel name-space; that is the
> whole (weak) preference — a Part-4 implementation detail, not a principle.

The factory is the single, explicit home of the topology — not duplicated anywhere, the opposite
of the rotting external inspector.

**Atomisation of the current blocks.** "Atomise" = split each code module into the smallest
independently-buildable **stages**, so that within one stage *every artifact is keyed the same way*. A **key**
is the identity of one buildable/checkable item inside a stage, derived from config — it comes in two shapes:

- **`document_id`** — the stage has **one artifact per document**, so it has *many* keys, one per book listed in
  `config/corpus.json` (`document_id = hash(url)`). Build and staleness are decided per document
  (`build({doc_ids})`, `actual() -> {document_id: fp}`).
- **singleton** — the stage produces **one artifact total** (a *global reduce* over all its inputs), so it has
  exactly one key; `build` regenerates the whole thing.

A module's `stages()` may return one stage or several (e.g. one per embedding variant). The table:

| module → `stages()` | how many | key | what one build does |
|---|---|---|---|
| **`corpus`** | 1 | `document_id` | fetch→clean→trim→write one `.txt` per document. `corpus.json` (the catalog) is **not** a second stage — it is *where this stage stores* each doc's metadata + fp, i.e. its sidecar, which `actual()` reads. |
| **`embeddings:<variant>`** | one **per variant** in `models.json` | `document_id` | each variant is its own Chroma collection → its own stage. `build({docs})` chunks those docs and **GPU-batches** the encode; the per-chunk rows share one per-doc `doc_md5` (D2), so the unit is the document, not the chunk. |
| **`projections:<model>:<plot>`** | one **per (model × plot × method)** | **singleton** | UMAP/heatmap/distribution run over **all** of a model's points to emit one file — it can't be built "per document," so its whole output is a single key; `build` = full refit (D3). |
| **`graphs`** | 1 | `document_id` | one knowledge-graph per document; `build({docs})` assembles them. The expensive per-chunk LLM step keeps its own **internal** `chunk_hash` cache (a resumable GC tier, §3) — deliberately *not* a driver stage, else a content-addressed key drags in orphan-GC + refcounting. |
| **`motifs:source:<tmi/atu/berezkin>`, `motifs:crosswalk`, `motifs:parallels`, `motifs:semantic`** | several | **singleton** each | motifs is a mini-pipeline; each step emits one artifact. Atomising it makes the internal order explicit via `inputs()` (crosswalk depends on the sources, parallels on the crosswalk, …) — which the current monolithic `build_motifs` hides. |

So after atomisation **every stage has a single key shape** (per-doc or singleton) → the `Stage` *is* the family
and no `ArtifactFamily` wrapper is needed. Bonus: adding an embedding variant, a projection method, or a motif
source is just *adding a stage* — it shows up in `status`/`clean`/`build` for free.

Two shapes the atomic interface still must respect: **`build(keys)` is batched** (no expensive stage is
one-item-at-a-time — GPU / pool / global), and **`actual()` is one store pass** (not separate key + fp reads).

One generic **driver** derives every operation as a **diff of the two maps**, per stage (topological):

```
d, a = stage.desired(), stage.actual()             # {key: fp} each
missing = d.keys() - a.keys()                       # should exist, doesn't      → build
orphans = a.keys() - d.keys()                       # exists, shouldn't          → clean / GC
stale   = {k for k in d.keys() & a.keys() if d[k] != a[k]}   # exists, fp diverged → rebuild
```

`status`, `clean`, `build`, GC become **one traversal**, not four bespoke paths — the "build-your-own minimal"
engine (D6), **stateless (D7)**: the "registry" is `stages()`; the state is `actual()` (disk/store), no manifest.
**Why it can't rot:** each store's layout lives in **one** place (the stage that writes it); adding a
variant/method/source = adding a `Stage` → it appears in status/clean/build automatically.

**Sequencing (this is a big refactor — Part 4, not Part 2).** Part 2 does the small, high-ROI fp work *inside
the existing stages* (the embeddings content-fp gate, `transform_version`, `doc_md5` once per doc in the
catalog) — which **prepares the base**: the fp sidecars this protocol reads. **Part 4** is the atomisation
itself — porting `pipeline_inspect.py`'s per-store functions + `cli._clean`'s wiring into the stages and the
generic driver. It also presupposes Part 1 (content-fp dedup, `document_id` paths, colour out of the fp graph),
so it lands last.

The sections below are this protocol's pieces: §2.3 is how a stage's `desired()` fps compose, §2.6 is the
driver's topological walk, §2.7 is `actual − desired`, §2.8 is `actual()`'s stored fp (sidecars, no manifest),
§3 is orphan GC.

### 2.3 Fingerprints — how a stage's `desired()` fps compose

Each artifact gets a fingerprint:

```
fp(artifact) = hash( fp(each input)  +  transform_version(stage)  +  output-affecting params )
```

- **Inputs by content hash**, not mtime (we already have `sha1(url)`, `md5(text)`).
- **transform_version** — bumped when the stage's code/params change (§2.5). Closes "code changed → outputs
  not rebuilt".
- Rebuild **iff fp changed** (or the output is missing); else skip. Cascade is emergent (§2.6).

Granularity per stage:

| artifact | fp key | granularity |
|---|---|---|
| document text | `hash(raw_bytes + content_start/end + patch + clean_v)` | document |
| **chunk embedding** | **(document_id, doc_md5, model, preprocess_v)** — content version is **doc-level** (D2) | **per-doc decision** (a text edit re-embeds all the doc's chunks) — fixes both flaws of §1.4 |
| projection | `hash(⊕ member chunk fps + method_v)` | **global per (model, method)** — UMAP is indivisible |
| graph | `hash(text + prompt_v + llm_model)` | document/chunk |
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
where a poisoned entry is dangerous). **Standardize on one — `blake2b` (fast + strong + stdlib) or
`sha256`.** The current sha1/md5 split is legacy, not a decision. Note the *roles* differ and are meaningful:
`sha1(url)` = **identity** ("which source"); `md5(text)` = **version** ("what content") — but the algorithm
is interchangeable.

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
The projection is the special node (`fp = hash(⊕ chunk fps + method_v)`): **any** chunk change → whole
projection rebuilds (inherent to global UMAP).

### 2.7 Deletions — `actual − desired`

fp-diff catches **changed/new** inputs but **not removed** ones (they leave orphans). This is exactly the
driver's second set (§2.2) — no separate mechanism:

```
stage.actual().keys()  −  stage.desired().keys()  =  orphans → collect
```

Per deletion type it falls out for free: url/doc removed from corpus.json → its text, chunks (Chroma ids with
that `document_id`), graph dir drop out of `desired()`; model removed → its Chroma collection + projections;
method removed → its `<model>/<method>.json`. Today `pipeline_inspect` **detects** these by hand; under the
protocol each stage's own `desired()`/`actual()` supplies them, and the driver GCs behind a dry-run confirm. So:
**fp-diff for changes, `actual − desired` for removals.** (Raw snapshots are an archive tier, *not*
auto-collected — §3, §6.)

### 2.8 `actual()` — sidecars, no manifest (D7)

`stage.actual()` reads the stored fps written *beside* the artifacts last build (in `corpus.json` rows — incl.
the per-doc `doc_md5`, Chroma collection/chunk metadata, `graphs/<id>/.fp`) in **one pass** → `{key: stored_fp}`.
Sidecars are the **source of truth**: they survive partial builds, need no single write-lock, and cannot drift
from their artifact. There is **no central index** (D7 — §9.3): a manifest would only cache what `desired()` +
`actual()` already give, and a *correct* staleness check must re-hash inputs either way, so the cache
buys ~nothing while adding a thing that drifts. The stateless driver reads disk
+ sidecars each run — always current. (If lineage/audit or large-scale directory-walk cost ever justify it, a
derived `outputs/.build-state.json` index can be *added* on top without changing the sidecar source of truth.)

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
  drop, regenerable; `clean --caches`.

This matches the existing `clean` flags (`--caches`, `--apply`).

---

## 4. The embeddings key — the concrete payoff

The single highest-value change. Replace "skip if `chunk_id` exists" with a two-part key:

```
re-embed a chunk  ⇔  (stable_id, content_md5, model, preprocess_version)  not already present
```

- **stable_id** — the rename-stable `document_id` anchor, **decided as `hash(locator)`** (`data-model-and-ids.md`
  §9-D1). Because the id tracks the upstream locator, not the title, a rename leaves the key unchanged and this
  cache correctly skips the re-embed — flaw 1 is fixed. (The rejected `slugify(title)` anchor would *not* have
  fixed rename-churn; flaw 1 would have stayed. That risk is now closed.)
- **content version** — **decided (D2): document-level `md5`** (the `md5` already computed in
  `_finalize_text`). A text edit re-embeds *all* of that doc's chunks — over-embedding within a doc, but cheap
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

Separate **fetch** (network, into the immutable raw archive — non-deterministic, slow, archival) from
**build** (a pure, offline, reproducible function of raw + config + code).

- **First run** (raw missing): `build` acquires the missing raw, archives it, proceeds — automatic, no
  separate manual step (current `build_corpus` already does `fetch_to_cache(..., force=False)`).
- **Subsequent runs** (raw present): build uses it, no network; present raw is treated as immutable.
- **Upstream update**: an **explicit `refresh --check`** (occasional, human) re-fetches to a temp, diffs
  against the stored raw, reports drift/disappearance, adopts on confirm; build then sees the new raw fp and
  rebuilds downstream.

So acquire-if-missing is automatic; **upstream re-fetch is deliberately manual** — build stays offline and
deterministic.

**Escape-hatch** = `--force`: rebuild everything, ignoring fps/caches. Kept because fingerprinting can have
bugs (a forgotten `algo_version` bump), corruption/partial builds happen, or you just want a guaranteed-clean
rebuild. Every incremental system keeps one (Make `-B`, Bazel clean, Nix `--rebuild`).

---

## 6. Sources — a unified web + local model

Both a web URL and a file in `sources/` are the same thing: an **upstream locator** for a source that may
receive an updated version. They must be handled identically.

### 6.1 The unifying abstraction

```
upstream (URL | sources/-file) ──ingest──► RAW snapshot (immutable, sha1(locator))
                                                 │
                                       + override layer (shared):
                                          content_start/end, exclude (config)
                                          per-doc unified-diff patch
                                                 ▼
                                          CURATED (derived)
```

The raw key is **already unified** (`corpus/raw/<sha1(locator)>` for both; for local the "url" is the file
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
`fp = hash(content_md5, model, chunk params, prompt/algo_version)` changed:

- **(1) content_md5 in the key** — fixes the real *staleness* bug (a text edit not re-embedding). Note this
  alone does **not** fix rename *churn* — that needs the rename-stable `document_id` anchor, now decided as
  `hash(locator)` (§9.5-D1); once that anchor lands, rename-churn is fixed too (it is out of *this* minimal
  staleness-only tier, but no longer blocked on a decision).
- **(2) transform_version per stage** — code/param edits invalidate; cheap.
- **(3) stateless fp cascade** — recompute fps on the fly from sidecars for a targeted rebuild instead of
  `--force`; moderate (skippable at our size). No central manifest (D7).
- **(4)** extend `status` to "what to rebuild" (orphan detection is already there).

Full Bazel/Nix is overkill for this size — **content-addressed sidecar fps + transform versions, computed
statelessly** is the right amount.

### Implementation order — **Part 2 of 4: incrementality base** (small, high-ROI; inside the existing stages)

**Part 1 (the data-model + region migration) is the single list in
[`region-implementation.md`](region-implementation.md) §5.** Part 2 is the **small** fp work done *inside the
existing stages* — no protocol refactor yet. It **prepares the base** (the fp sidecars) that Part 4 later
harvests. None of it blocks shipping Part 1. Sub-decisions flagged *(decide Dx)*; full list in §9.5.

1. **Embeddings content-fp staleness gate** — replace the id-existence dedup with `(document_id, doc_md5,
   model, ver)`; store `doc_md5` **once per doc in the catalog** (D2, §2.3), embeddings reads it. Fixes the
   real re-embed-on-edit bug; the rename-churn half comes free from Part 1's `document_id` anchor.
2. **`transform_version`** — uniform param-hash + one manual `algo_version` per stage (D4, §2.5).
3. **Atomicity** — write the artifact *then* its fp sidecar; atomic swap for the catalog/collection — §9.4, so
   a stored fp never lies under a mid-build crash.
4. **fetch/build split** + explicit `refresh` + pin raw archive — §5, §6.5. Splits `--force`'s two meanings:
   **`--force` = rebuild derived from raw**; **`refresh` = re-fetch upstream** (today corpus conflates them).
5. Graphs build/serve unify + traversal guard (isolated bug; also in Part 1 §5 step 6 — do wherever first).

*(D3 decided — keep the full UMAP refit, no parametric work — §9.2.)*

### Implementation order — **Part 3 of 4: manual text curation** (editorial; independent)

Hand-fixing a document's text (OCR typo, an interleaved note the markers can't catch) as an **override layer**
that never mutates raw or upstream — an editorial workflow, not required to ship the migration or to make
rebuilds incremental.

1. **The override layer + `curate` workflow** — `overrides/<document_id>.patch` (**D5: unified-diff patch**);
   `curate` materialises the current curated text, the curator edits it, `curate --save` snapshots
   `difflib(base, edited)` + stamps the base-fingerprint; build applies the patch (`git apply`) — §6.2–§6.4.
   Prerequisite: the fetch/build split + `refresh` (Part 2 item 4).

### Implementation order — **Part 4 of 4: the stage-protocol refactor** (big; deferred; consumes Part 2's base)

The **self-describing-stage** architecture (§2.2): atomise each block into `stages()`, port
`pipeline_inspect.py`'s per-store `*_status`/`*_orphans` and `cli._clean`'s wiring *into* the stages, and make
`status`/`clean`/`build`/GC **one generic-driver traversal**. It ends the "external inspector rots" failure mode
structurally. Deferred because it is the **largest** refactor and touches every stage + `cli.py`; it consumes
the fp sidecars Part 2 laid, and presupposes Part 1 (content-fp dedup, `document_id` paths, colour out of the
fp graph).

1. Atomise the blocks per §2.2's table (`corpus`, `embeddings:<variant>`, `projections:<model>:<plot>`,
   `graphs`, `motifs:*`); implement `inputs/desired/actual/build(keys)/delete` on each.
2. The generic driver over `stages()`; retire `pipeline_inspect` + `cli._clean` per-store wiring.
3. Re-evaluate build-your-own vs **DVC/Dagster** at scale — §9.1 (D6); the driver already *is* build-your-own,
   so this is "when to switch," not "what to build now."

D1 is decided — `document_id = hash(locator)` — and **D8 is dissolved**, so Part 1 is fully unblocked. Decided
since: **D2** (doc-level `md5`), **D3** (full refit), **D4** (uniform param-hash + manual `algo_version`), **D5**
(unified-diff patch — Part 3), **D7** (stateless, no manifest). Still-open: **D6** (build engine) — effectively
settled by D7 (stateless in-process ⇒ build-your-own; DVC only at scale), decided formally in Part 4.

---

## 8. Coherence between builds

With content-addressing, coherence is guaranteed **at build completion** (every artifact matches its inputs).
Between builds (config edited, not yet rebuilt) the serve layer reads whatever is on disk. For a
single-user research tool the **build-then-serve** model is sufficient; if on-the-fly coherence is needed,
use atomic artifact swaps or a `status`-driven "stale" flag.

---

## 9. Weak spots, alternatives & open decisions

### 9.1 Big alternative — adopt a ready-made engine instead of building our own

Everything here (content-addressed DAG, fingerprints, cache, GC, lineage) is what existing data-pipeline
engines already do. **Selection criteria for us:** (a) content-addressed caching — the whole point; (b)
in-process Python vs shell-out (our stages are Python functions); (c) weight/dependency; (d) remote artifact
storage (raw archive + large embeddings); (e) our size (~27 docs argues against heavy tools).

| engine | class | content-cache | model | weight | notes |
|---|---|---|---|---|---|
| **DVC** | data/ML versioning | ✔ | shell-out stages | medium | `dvc.yaml` DAG, `dvc repro` = minimal rebuild, `dvc.lock` hashes, remotes for raw/embeddings. Our `cli.py` already exposes per-stage commands → wrapping is cheap. **Best off-the-shelf fit.** |
| **Dagster** (assets) | orchestrator | ✔ | Python in-process | med-heavy | software-defined assets: deps, materialization, freshness, partial re-materialize, lineage. Fits when this becomes a scheduled multi-asset product. |
| **Snakemake** | DAG runner | ✔ (content triggers) | shell-out | medium | mature file-DAG, bioinformatics-flavored/shell-oriented. |
| **Nextflow / Pachyderm** | DAG / k8s | ✔ | containers | heavy | HPC/cloud/k8s — wrong weight for us. |
| **Luigi** | orchestrator | partial | Python | light | task+target deps; older, no strong content cache. |
| **Airflow** | scheduler | ✗ | Python | heavy | scheduling, not content-caching — wrong tool. |
| **Make** | build | ✗ (mtime) | shell-out | trivial | mtime lies (appendix) — reject. |
| **build-your-own** | — | ✔ | in-process | ~few hundred LOC | full control, no heavy dep; the stage protocol + driver (§2.2) — stateless fp/GC, no manifest. |

**Recommendation:** at ~27 docs, **build-your-own minimal** (the §7 gate + a small fp sidecar) is the best
ROI — in-process, no new heavy dependency. **Adopt DVC** when the corpus/artifacts grow enough that a remote
archive + free lineage/caching outweigh the shell-out process boundary. **Dagster** only if this becomes a
scheduled product with many assets. Avoid Pachyderm/Nextflow/Airflow (weight/purpose), Make (mtime). Whatever
we pick, **the fork should be explicit** ("not DVC, because …"), not defaulted (D6).

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
- Stateless **never drifts**: out-of-band deletion/corruption, a mid-build crash, a git-branch switch, or
  concurrent builds all self-heal because it reads on-disk truth, not a cached index.

The manifest's only genuine residual edge is historical **lineage/audit** and avoiding a directory walk at
large scale — both nice-to-have, revisit if the corpus grows or lineage debugging becomes a real need.

### 9.4 Atomicity / partial-build failure (unaddressed gap)

Builds crash mid-way (network, GPU OOM, LLM rate-limit — the graph stage already handles the last). Then an
artifact and its fp can disagree. Rule: **write the artifact first, then its fp**; treat *artifact-present /
fp-absent* as "rebuild". For the catalog/collection, prefer atomic swap (write to temp, rename) so a reader
never sees a half-written index. This must be specified before the fp machinery is trusted.

### 9.5 Consolidated open decisions

| id | decision | options | blocks |
|---|---|---|---|
| ~~**D1**~~ | `document_id` anchor — **DECIDED: `hash(locator)`** | ~~`slugify(title)` vs~~ `hash(upstream-locator)` (= raw key `sha1(url)`) | doc coherence, §4 rename-stability, persist-id — *unblocked* |
| ~~**D2**~~ | embedding content-version granularity — **DECIDED: doc-level `md5`** | ~~per-chunk `hash(chunk_text)` vs~~ doc-level `md5` (cheap here; per-chunk precision illusory under positional chunking) | §2.3 / §4 |
| ~~**D3**~~ | projections incrementality — **DECIDED: full refit** | ~~parametric `.transform()` vs~~ full refit (cheap at this size, simpler, no drift) | §9.2 |
| ~~**D4**~~ | transform_version — **DECIDED: uniform** param-hash + one manual `algo_version` | ~~per-stage-by-cost auto/manual vs~~ uniform (params cover expensive-stage behaviour; split adds ~nothing) | §2.5 |
| ~~**D5**~~ | override format — **DECIDED: unified-diff patch** (Part 3) | ~~full override (near-copy, freezes on upstream update) vs~~ unified-diff patch (delta only, auto-re-applies / clean conflict) | §6.4 |
| **D6** | build engine | build-your-own vs adopt DVC | §9.1 |
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
