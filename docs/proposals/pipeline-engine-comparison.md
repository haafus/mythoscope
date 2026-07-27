# Pipeline engines — feature matrix & where our design sits

A side-by-side of **our build-your-own stage protocol** ([`pipeline-and-incrementality.md`](pipeline-and-incrementality.md)
§2.2) against the ready-made engines surveyed in §9.1. Purpose: see, concretely, which of our features are
**off-the-shelf standard**, which are **convergent** (we re-derived what existing tools do), and which are
**genuinely ours**. The canonical index of the whole field is
[awesome-pipeline](https://github.com/pditommaso/awesome-pipeline); this doc compares the twelve most relevant.

Legend: **✓** yes / first-class · **~** partial, opt-in, or needs user code · **✗** no · **—** n/a.

**The tools:**

| tool | one-line | lang / stage |
|---|---|---|
| **Mythoscope** (ours) | the §2.2 stage protocol + stateless fp driver | Python, in-process |
| **doit** | make-in-Python, md5 file signatures | Python, in-process |
| **redun** (insitro) | Nix-model task memoization, content-addressed | Python, in-process |
| **targets** (← drake) | dependency-graph-skips-unchanged, reproducible | R, in-process |
| **DVC** | data/model versioning over git | Python, shell-out |
| **Dagster** | software-defined assets + orchestration | Python, in-process |
| **Snakemake** | file-DAG runner (bioinformatics) | Python, shell-out |
| **Flyte** | k8s-native typed workflows | Python, containers |
| **Hamilton** | function-graph dataflow / feature transforms | Python, in-process |
| **Luigi** | task+target orchestration | Python, in-process |
| **Airflow** | scheduled DAG orchestration | Python, operators |
| **Make** | the original file build tool | shell-out |

---

## Matrix A — change detection & invalidation (the core of incrementality)

| tool | change signal | cache key contents | catches **code/logic** change | catches **param** change | downstream cascade |
|---|---|---|---|---|---|
| **Mythoscope** | content hash (blake2b) | input fps + `transform_version` + output-affecting params | ~ manual `algo_version` | ✓ param-hash | ✓ fp composition |
| **doit** | md5 of `file_dep` (+ custom `uptodate`) | file signatures + your `uptodate` | ✗ unless you code it | ~ `config_changed` | ✓ task deps |
| **redun** | hash of **task source** + input hashes | task source code + args | ✓ auto source-hash | ✓ args | ✓ graph reduction |
| **targets** | hash of code + data + upstream | command + dep objects | ✓ hashes the R code | ✓ | ✓ |
| **DVC** | md5 of deps/outs | `dvc.lock` hashes + cmd string | ~ only if cmd/params change | ~ `params.yaml` | ✓ `dvc repro` |
| **Dagster** | data versions + code versions | `code_version` + input data-versions | ~ `code_version` (manual/auto) | ✓ | ✓ asset graph |
| **Snakemake** | mtime + code/params/input triggers (v7+) | input hashes/mtime + rule | ✓ (v7+ `--rerun-triggers`) | ✓ (v7+) | ✓ |
| **Flyte** | `cache_version` + signature + inputs | cache_version + task sig + input values | ~ manual `cache_version` | ✓ inputs | ✓ |
| **Hamilton** | code + input data-version hashes | fn source + input versions | ✓ | ✓ | ✓ |
| **Luigi** | **target existence only** | — (no hash) | ✗ | ✗ | ~ only via missing targets |
| **Airflow** | none (schedule/trigger) | — | ✗ | ✗ | ✗ order only, not staleness |
| **Make** | **mtime** | file times | ✗ | ✗ | ✓ via mtime prereqs |

**Read:** every content-based tool caches; the one real *design* split is **how a code change is caught**, and
it is a genuine trade with no "better" side — **auto source-hash** (redun, targets, Hamilton) is zero-bookkeeping
but *over-invalidates* (a comment or refactor re-runs an expensive stage), while a **manual version bump** (Flyte
`cache_version`, Dagster `code_version`, ours `algo_version`) has *no false triggers* but relies on the developer
remembering to bump. We took the manual side (D4, §2.5) because our stages are expensive (re-embed / re-LLM), so
a false trigger costs more than the bookkeeping; a tool with cheap stages can reasonably choose the opposite.
Luigi/Airflow/Make don't do content-caching at all.

---

## Matrix B — state, storage, GC, lineage

| tool | state model | artifact store | remote store | orphan/stale **GC** | lineage / audit |
|---|---|---|---|---|---|
| **Mythoscope** | **stateless — per-artifact sidecars, no central DB** | own stores (Chroma / files / catalog) | ✗ (raw can be committed) | ✓ **two-level: key + whole-store** (§2.7) | ~ `status` only, no history |
| **doit** | `.doit.db` (dbm signatures) | your files | ✗ | ~ manual `clean` actions, no auto-orphan | ✗ |
| **redun** | **SQLite/Postgres CallGraph DB** | own value store (+ S3) | ✓ | ~ cache in DB (prunable) | ✓ full call-graph provenance |
| **targets** | `_targets/` metadata store | own object store | ~ cloud opt-in | ✓ `tar_prune` / `tar_delete` (reachability) | ✓ metadata + `tar_visnetwork` |
| **DVC** | `dvc.lock` + `.dvc/cache` | content cache | ✓ S3/gs/azure/ssh | ✓ `dvc gc` | ✓ git-tracked versions |
| **Dagster** | instance DB (run + asset storage) | I/O managers (bring-your-own) | ✓ via I/O managers | ~ freshness; wipe via UI | ✓ asset catalog + lineage UI |
| **Snakemake** | metadata dir + file mtimes | your files | ~ remote providers | ~ `--delete-temp`, no orphan-GC | ~ report/DAG |
| **Flyte** | metadata service + blob store | blob store | ✓ | ~ cache eviction / TTL | ✓ execution lineage |
| **Hamilton** | optional cache adapter | in-memory / bring-your-own | ~ | ✗ | ✓ lineage + UI |
| **Luigi** | target existence | your files | ~ | ✗ | ✗ |
| **Airflow** | metadata DB | bring-your-own (XCom = small) | ~ | ✗ | ~ run history |
| **Make** | **none** (fs mtime) | your files | ✗ | ✗ (`make clean` manual) | ✗ |

**Read:** we are the **only content-based tool with no central state store** — everyone else keeps a DB, lock,
or metadata dir (only Make is also DB-free, and it pays with mtime). That is a deliberate trade (D7, §9.3): we
give up **remote storage** and **lineage/history**, which redun (call graph), DVC (git), Dagster (catalog), and
targets (metadata) all provide first-class. Those two gaps are exactly our §9.1 switch-triggers (a) and (b).

**On GC specifically — our "two levels" is not an edge, it is the *cost* of being stateless.** A central-store
tool (DVC, targets, redun, Dagster) GCs with **one** uniform sweep: the store records *every* artifact that was
ever built, keyed independently of the live task graph, so "garbage = recorded-in-store − reachable-from-current-config"
covers a removed *document* and a removed *whole collection/model* **identically** — the store still lists the
removed model's outputs even though its producing task is gone from the code. We have **no** such record, so our
`actual()` is computed by *asking each live stage*; a removed stage isn't there to ask, which is exactly why we
need a **second** store-scanning pass (§2.7 level 2). So the honest read is the reverse of a boast: **their
single-level reachability GC is cleaner, and it is bought by the very central store we chose not to keep.** Our
two-level scheme is what statelessness costs, not what it wins.

---

## Matrix C — execution model, scale, fit

| tool | dynamic fan-out | parallel / distributed | scheduling | weight | sweet spot |
|---|---|---|---|---|---|
| **Mythoscope** | ✓ factory loop over config | ~ GPU-batch inside a stage | ✗ manual / CLI | **~few hundred LOC** | *this* app, ~27 docs |
| **doit** | ✓ task-creators | ✓ multiprocess | ✗ | light | Python build automation |
| **redun** | ✓ | ✓ executors (local / AWS Batch / k8s) | ~ | light-med | scientific pipelines, cloud |
| **targets** | ✓ branching | ✓ `crew` / `clustermq` | ~ | medium | R reproducible research |
| **DVC** | ~ `foreach` stages | ~ | ✗ (CI-driven) | medium | ML data/model versioning |
| **Dagster** | ✓ dynamic outs | ✓ | ✓ schedules / sensors | med-heavy | scheduled data platform |
| **Snakemake** | ✓ wildcards | ✓ cluster / k8s | ~ | medium | bioinformatics file DAGs |
| **Flyte** | ✓ dynamic / map tasks | ✓ k8s | ✓ | **heavy** | enterprise k8s ML |
| **Hamilton** | ✓ `@parametrize` | ~ Ray / Dask / Spark adapters | ✗ | light | dataflow / feature transforms |
| **Luigi** | ~ | ✓ workers | ~ central scheduler | light | task orchestration (legacy) |
| **Airflow** | ~ | ✓ | ✓ (its whole point) | heavy | scheduled ETL / DAGs |
| **Make** | ~ pattern rules | ✓ `-j` | ✗ | trivial | file build automation |

**Read:** at ~27 docs, weight is the deciding axis. We sit at the far-light end with doit/Hamilton; everything
with distributed execution or a scheduler (Flyte/Airflow/Dagster) is over-built for a single-user research tool —
which is why D6 stayed build-your-own and Dagster is gated to "if this becomes a scheduled product."

---

## Matrix D — each engine's signature design decision

Not "which features," but the **one idea that defines each tool** — the choice you adopt (or reject) the whole
tool for — with its distinctive strength and its notable limitation. Ours is one row among the rest.

| engine | signature design decision | distinctive strength | notable limitation |
|---|---|---|---|
| **Mythoscope** | **provenance-addressed identity** (`hash(locator)`, not content) + **stateless** sidecars, no central DB | id survives a content edit *and* a filesystem rename; state can never drift (re-read from disk each run) | no remote store, no lineage/history, no distributed exec; identity-hash split is bespoke code |
| **doit** | **`uptodate` — arbitrary Python predicates decide staleness** (not just file times/hashes) | staleness is *programmable*: any callable, `config_changed`, `result_dep` | file-oriented; no code-change detection unless you write it; no orphan GC |
| **redun** | **expression graph + graph reduction**; a task's own **source code** is part of its content hash | "code *and* data reactivity" — edit the function, it re-runs; full call-graph provenance | over-invalidates on any source edit; requires a SQL backend DB |
| **targets** (← drake) | **targets as first-class objects** with a reproducibility *proof* — "all up to date" is evidence results match code+data | strongest reproducibility guarantee; dynamic branching; visual dep graph | R-only; single `_targets/` metadata store |
| **DVC** | **git-for-data** — data/models versioned like source (`.dvc` pointers, content cache, remotes) | data versioning + remote storage + `dvc repro` ride on the git workflow you already have | the DAG is secondary; stages shell out; heavier than a pure cache |
| **Dagster** | **software-defined assets** — you declare the *data asset* (the output), not the task | asset catalog, freshness policies, auto-materialize, lineage UI as first-class | needs an instance + DB; med-heavy for a single-user tool |
| **Snakemake** | **wildcard/pattern rules over filenames** — one rule with `{sample}` expands into a file DAG | concise implicit DAG for thousands of files; cluster/k8s submission built in | shell/file-centric; mtime heritage; rebuild logic tied to paths |
| **Flyte** | **strongly-typed, containerized, k8s-native tasks** — every task is a typed container | type-safe interfaces + hard isolation + reproducible envs at org scale | heavy; needs k8s + a control plane; wrong weight below team scale |
| **Hamilton** | **the DAG *is* the function graph** — param names of a function are its dependencies | zero explicit wiring; the code is the lineage; extremely light | scoped to in-process dataflow/transforms, not orchestration/scheduling |
| **Luigi** | **`Target` abstraction** — a task is done iff its output `Target` exists | dead-simple mental model; pluggable targets (file, S3, DB) | completion = existence, not content → stale outputs undetected; dated |
| **Airflow** | **time-based scheduling of DAGs** — the *scheduler* is the product | cron-for-DAGs, sensors, backfill, huge operator ecosystem | not a build/cache system at all — no staleness, no content-caching |
| **Make** | **mtime-based prerequisite rules** — rebuild if a prerequisite is newer | trivial, universal, declarative; the ancestor of all of this | mtime lies (git resets it); blind to code/flag changes |

---

## Verdict

- **Off-the-shelf / convergent (we re-derived the standard):** content-addressed DAG, the cache-key formula
  (`inputs + version + params`), the self-describing asset, the manual transform-version, downstream cascade by
  fp composition. Flyte and Dagster match these almost symbol-for-symbol — reassurance, not a red flag.
- **Genuinely ours:** the **provenance-addressed identity** and the **identity/version hash split**;
  **stateless-with-no-DB** (everyone content-based keeps a store); and **path-as-rendering**. None of these is
  exotic, but no single tool packages them this way. *(Our two-level GC is **not** on this list — it is the
  price of statelessness, not a feature; a central store handles collection removal in one uniform sweep, §
  Matrix B.)*
- **Not a pipeline question at all:** the **three-registry data model** — no engine addresses it because it is
  application schema, not build orchestration ([`data-model-and-ids.md`](data-model-and-ids.md)).
- **What the comparison costs us (all already flagged):** no **remote artifact store** (redun/DVC/Flyte/Dagster
  have it → §9.1 trigger a); no **lineage/history** (redun/DVC/Dagster/targets have it → trigger b); no
  **distributed execution or scheduling** (out of scope, single-user); stateless means **no output-integrity
  check** for a silent out-of-band edit (§9.3); and the **manual `algo_version`** is human bookkeeping (§2.5) —
  the exact same soft spot Flyte's `cache_version` and Dagster's `code_version` carry.

**Bottom line:** the incrementality half is a sensible point in a crowded, solved space — and `doit` (our
build-your-own, already written) or `redun` (our model, minus the D4 disagreement) could replace much of Part 3
if the hand-rolled driver ever feels heavy. The distinctive, defensible originality is on the **identity/data
model** side, not the engine side.

## Post-Part-3 decision (Stage IV item 3) — keep build-your-own

Re-evaluated now that the generic driver is **built and running** (Part 3 items 1–2/4/5:
`src/pipeline/` — the stage protocol, topological driver, two-level GC; `mytho
build`/`status`/`clean`/`export` all ride one `desired()`/`actual()` diff). **Decision:
we keep our own engine — DVC and Dagster are not adopted.**

Why, concretely:

- **They would replace what already works, and add a dependency.** The hand-rolled driver is
  ~three small modules with no runtime service. DVC brings a `.dvc/cache` + `dvc.lock` + a
  shell-out model; Dagster brings an instance + a DB. For a single-user research tool that is a
  net *cost*, not a gain — the "med-heavy" / "needs an instance" cells of Matrix C/D.
- **Their genuine added value is out of our scope.** Remote artifact store, lineage/history UI,
  schedulers/sensors (Matrix B/C) — none of which a single-user offline pipeline needs. If a
  scheduled *product* ever emerges, Dagster is the re-entry point (as already gated in Matrix C).
- **The part they'd help with, we already have.** Content-addressed change detection, the
  `inputs + version + params` cache key, downstream cascade by fp composition — our driver
  matches these symbol-for-symbol (the Verdict's "convergent" list). Adopting an engine buys no
  incrementality we lack.
- **Our distinctive design is orthogonal to the engine.** Provenance-addressed identity, the
  identity/version hash split, stateless-with-no-DB, path-as-rendering — none is an engine
  feature; an off-the-shelf engine would not carry them and would fight the no-DB choice.

The escape hatch is unchanged: if the driver ever feels heavy, `doit` (build-your-own, same
shape) or `redun` (our model minus the D4 disagreement) can replace it without touching the
identity/data model. Nothing observed while building it made it feel heavy.
