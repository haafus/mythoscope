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
| 1 | **Corpus** | corpus.json + traditions.json + sources | `corpus/raw/<sha1(url)>` (raw snapshot), `corpus/<major>/<trad>/<title>.txt` (cleaned text), `corpus/corpus.json` (catalog + counts + md5) | raw-fetch (sha1 url), extraction | network (~s/doc); clean/trim CPU-cheap |
| 1.5 | **Preprocess** (variants) | cleaned text + variant config | `preprocessed/…` | preprocessing | CPU cheap–moderate |
| 2 | **Embeddings** | cleaned text (+ variant) + models.json | `embeddings/` (Chroma collections per model) | chunk-cache; the collection itself is a store (dedup by chunk_id) | **GPU — dominant**; per-chunk |
| 3 | **Projections** | vectors (embeddings) + method | `projections/<model>/<method>.json` | — | moderate; **UMAP is global** (over all points), not per-chunk |
| 4 | **Graphs** | cleaned text + prompts.json + LLM | `graphs/<text_id>/…` | chunk-cache (LLM responses) | **LLM — $$, rate-limited**; per-chunk |
| 5 | **Motifs** | motif sources (TMI/ATU/Berezkin) | `motifs/*.json` | motif raw-scrape | CPU moderate; **independent** of the corpus |
| S | **Serve** | traditions.json + corpus.json + embeddings + projections + graphs + motifs | (runtime) | front load-once indexes | — |

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
| | change `tradition` | paths/refs; embeddings need not (content unchanged) |
| | `exclude` on/off | add/remove from everything below |
| **traditions.json** | rename/re-annotate region, color, coordinates | **serve-resolve only** — no artifact rebuild |
| **sources/** local file | byte edit / new version delivered | raw(hash) → below |
| **external URL** upstream | Gutenberg re-release | raw → below (not detected without a re-fetch) |
| **models.json** | add/change model | embeddings(model) → projections(model) |
| **prompts.json** | change prompt | graphs(all) |
| **stage CODE** | clean/trim, `chunk_size/overlap`, projection method, slugify | **all outputs of that stage — today not detected at all** |
| **motif sources** | new crosswalk | motifs |

### 1.4 What incrementality exists today (and its two flaws)

- **raw-fetch** — content-addressed by `sha1(url)` (rename-proof). ✔
- **Corpus reuse** — keyed by `title` (`_load_existing_metadata` → `{row["title"]: row}`; reuse if the output
  file is present / for local, if the raw-snapshot hash is unchanged). ✖ rename-fragile.
- **Embeddings dedup** — by `chunk_id = slug(title)::i`, on **id existence, not content**. ✖
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

### 2.2 Fingerprints

Each artifact gets a fingerprint:

```
fp(artifact) = hash( fp(each input)  +  transform_version(stage)  +  output-affecting params )
```

- **Inputs by content hash**, not mtime (we already have `sha1(url)`, `md5(text)`).
- **transform_version** — bumped when the stage's code/params change (§2.4). Closes "code changed → outputs
  not rebuilt".
- Rebuild **iff fp changed** (or the output is missing); else skip. Cascade is emergent (§2.5).

Granularity per stage:

| artifact | fp key | granularity |
|---|---|---|
| document text | `hash(raw_bytes + content_start/end + patch + clean_v)` | document |
| **chunk embedding** | `hash(chunk_text + model + preprocess_v)` = **(stable_id, md5, model, ver)** | **chunk** — fixes both flaws of §1.4 |
| projection | `hash(⊕ member chunk fps + method_v)` | **global per (model, method)** — UMAP is indivisible |
| graph | `hash(text + prompt_v + llm_model)` | document/chunk |
| serve-resolve (color/tree) | — | **not an artifact** — resolved at runtime → tree edits are free |

### 2.3 Hash choice

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

### 2.4 Transform version — where it lives, how it is bumped

A module-level constant per stage, beside the code it versions, included in that stage's fp:

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
version, prompt text, content markers, slugify rules) — these are *data*, precise, no false triggers — **plus
a small manual `algo_version`** for pure-logic changes. Middle grounds if fuller automation is wanted:
AST-hash (ignores comments/format, still triggers on no-op refactors), or scope the code-hash to the stage's
core function(s) + pinned dep versions.

### 2.5 Downstream invalidation via fp composition

Because an artifact's fp *includes its inputs' fps*, cascade is emergent — no per-edge "invalidate
downstream" logic:

```
in topological order:
  new_fp = hash(current input fps + transform_version)
  if new_fp ≠ stored fp (or output missing): rebuild, store new_fp
  else: skip
```

A rebuilt node gets a new fp → it is an input to its dependents → they see a changed input fp → they rebuild.
The projection is the special node (`fp = hash(⊕ chunk fps + method_v)`): **any** chunk change → whole
projection rebuilds (inherent to global UMAP).

### 2.6 Deletions

fp-diff catches **changed/new** inputs but **not removed** ones (they leave orphans). A second mechanism —
**set reconciliation** — is needed:

```
expected artifacts (from config)  −  present on disk  =  orphans → collect
```

Per deletion type: url/doc removed from corpus.json → its text, chunks (Chroma ids with that `document_id`),
graph dir orphan; local file removed → same; model removed from models.json → its Chroma collection +
projections orphan; projection method removed → its `<model>/<method>.json` orphan. `pipeline_inspect`
already **detects** these; the missing piece is linking the *expected set* to auto-GC (behind a dry-run
confirm). So: **fp-diff for changes, set-diff for removals.** (Raw snapshots are an archive tier and are
*not* auto-collected — §3, §6.)

### 2.7 Manifest & sidecars

Two complementary stores; the index is derivable from the sidecars:

- **Sidecars** (fp *with* the artifact — in `corpus.json` rows, in Chroma chunk metadata, `graphs/<id>/.fp`)
  = **source of truth**: survive partial builds, no single write-lock, cannot drift from their artifact. Lose
  the index → rebuild it by walking sidecars.
- **Central index** (`outputs/.build-state.json`, optional) = a **derived cache for fast global queries**
  ("what's stale", "what depends on X", "what to rebuild") + the **GC root** (expected-key set). Contents:
  `artifact_key → {fp, input_fps, transform_version, path, ts}` + the expected-key set.

**"Small"** = one entry per *artifact* (document, per-model collection, projection, graph) storing *hashes and
paths, not content*; per-chunk fp lives in Chroma metadata and is rolled up into a document fp. O(artifact
count) × a few short fields ≈ hundreds of KB even for a large corpus, vs GB of artifacts.

For our scale **sidecars alone suffice for correctness**; the central index is an optional speed layer — adopt
it only when global-status queries get slow.

---

## 3. Garbage collection

**Immutable vs overwrite.** Nix-style immutability (new fp = new path, old kept) accumulates stale artifacts
and needs GC; overwrite-in-place (current) accumulates nothing but gives no rollback and a mid-build failure
leaves inconsistency. **For our size, overwrite + orphan-GC suffices**; adopt immutability only if rollback /
A-B model comparison is wanted, and then GC by reachability from the manifest root.

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

- **stable_id** — see §6/`data-model-and-ids.md`; anchored so a rename does not churn it.
- **content_md5** — already computed in `_finalize_text`, just unused here.

Correct on all cases: rename (same content) → same key → **skip** (fixes flaw 1); text edit (same title) →
new md5 → **re-embed** (fixes flaw 2); new doc → new id → embed. The non-buzzword value of ids is precisely
this: **`(id, version)` as the incremental cache key.**

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
- **per-doc unified-diff patch** (`overrides/<document_id>.patch`) — for point text fixes. **Diff beats a full
  override file**: it stores only the changes (small), shows exactly what diverged (provenance), reviews in
  git, and re-applies deterministically. A patch that no longer applies after `refresh` is the merge/conflict
  signal → re-curate.

Layer order: `curated = trim(clean(apply_patch(base)), content_start/end)`. The patch base is best the
*cleaned* text (boilerplate stripped — what a curator reads); if `clean_version` bumps and the patch fails,
that is a re-curate signal.

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

Minimal path, by value: **(1) content_md5 in the embeddings key** (fixes the real staleness bug + rename
churn; cheap, high value); **(2) transform_version per stage** (code edits invalidate; cheap); **(3) fp
manifest + DAG cascade** (targeted rebuild instead of `--force`; moderate); **(4)** extend `status` to "what to
rebuild" (orphan detection is already there). Full Bazel/Nix is overkill for this size — **a small
content-addressed manifest + transform versions** is the right amount.

---

## 8. Coherence between builds

With content-addressing, coherence is guaranteed **at build completion** (every artifact matches its inputs).
Between builds (config edited, not yet rebuilt) the serve layer reads whatever is on disk. For a
single-user research tool the **build-then-serve** model is sufficient; if on-the-fly coherence is needed,
use atomic artifact swaps or a `status`-driven "stale" flag.

---

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
