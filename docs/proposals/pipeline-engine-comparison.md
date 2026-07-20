# Pipeline engines — feature matrix & where our design sits

A side-by-side of **our build-your-own stage protocol** ([`pipeline-and-incrementality.md`](pipeline-and-incrementality.md)
§2.2) against the ready-made engines surveyed in §9.1. Purpose: see, concretely, which of our features are
**off-the-shelf standard**, which are **convergent** (we re-derived what mature tools do), and which are
**genuinely ours**. The canonical index of the whole field is
[awesome-pipeline](https://github.com/pditommaso/awesome-pipeline); this doc compares the twelve most relevant.

Legend: **✓** yes / first-class · **~** partial, opt-in, or needs user code · **✗** no · **—** n/a.

**The tools:**

| tool | one-line | lang / stage |
|---|---|---|
| **MythoScope** (ours) | the §2.2 stage protocol + stateless fp driver | Python, in-process |
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
| **MythoScope** | content hash (blake2b) | input fps + `transform_version` + output-affecting params | ~ manual `algo_version` | ✓ param-hash | ✓ fp composition |
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

**Read:** everyone serious is content-based (Luigi/Airflow/Make are the laggards). The one real *design* split
is **how a code change is caught**: **auto source-hash** (redun, targets, Hamilton — over-invalidates: a
comment/refactor re-runs) vs a **manual version bump** (Flyte `cache_version`, Dagster `code_version`, ours
`algo_version`). We landed with the manual camp (D4, §2.5) — the same choice as the two most mature orchestrators.

---

## Matrix B — state, storage, GC, lineage

| tool | state model | artifact store | remote store | orphan/stale **GC** | lineage / audit |
|---|---|---|---|---|---|
| **MythoScope** | **stateless — per-artifact sidecars, no central DB** | own stores (Chroma / files / catalog) | ✗ (raw can be committed) | ✓ **two-level: key + whole-store** (§2.7) | ~ `status` only, no history |
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
Our **two-level GC** (orphan *key* inside a live stage + orphan *whole store* from a removed stage, §2.7) is more
than most: targets/DVC/redun GC by reachability but do not distinguish "removed one item" from "removed a whole
parametrized branch," which for us is the model-removal case.

---

## Matrix C — execution model, scale, fit

| tool | dynamic fan-out | parallel / distributed | scheduling | weight | sweet spot |
|---|---|---|---|---|---|
| **MythoScope** | ✓ factory loop over config | ~ GPU-batch inside a stage | ✗ manual / CLI | **~few hundred LOC** | *this* app, ~27 docs |
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

## Matrix D — our distinctive design decisions vs the field

The follow-up axis: not "which features," but "which of our *design choices* is actually ours." For each, the
closest thing any analog does.

| our decision | what it is | any analog? | closest | verdict |
|---|---|---|---|---|
| **Provenance-addressed id** (`hash(locator)`, not `hash(content)`) | id tracks the *source*, survives a content edit → rename/edit-stable | mostly **no** — CAS tools (git/Nix/IPFS, and redun's value hashing) address by *content* → an edit is a new id | **Flyte** hashes a dataset's *storage location* by default (opt-in content hash) | **distinctive** |
| **Split identity-hash vs version-hash** | two hashes, two roles: *which* source (`hash(locator)`) vs *what* content (`doc_md5`/fp) | git/Nix/CAS **conflate** them into one content hash | **Flyte** (location vs content) | **distinctive** |
| **Stateless — sidecars, no central DB/manifest** | state = on-disk truth, re-read each run; never drifts | most keep a DB/lock (redun SQLite, targets `_targets/`, DVC `dvc.lock`, Dagster instance DB, doit `.doit.db`) | **Make** (also DB-free, but mtime) | **distinctive** (deliberate D7) |
| **Self-describing stage** (`desired()`/`actual()` owns its own hygiene) | each stage declares its spec + reality; driver diffs | **yes, convergent** | **Dagster** software-defined asset (materialization + freshness) | **convergent** (validated, not unique) |
| **Two-level orphan GC** (key **and** whole-store) | catches a removed *document* (key) *and* a removed *model/plot* (whole store) | reachability GC exists (targets/DVC/redun) but single-level | **targets** `tar_prune` (one level) | **partly distinctive** (whole-store-via-factory is ours) |
| **Transform-version = param-hash + manual `algo_version`** (reject source-hash) | precise: params catch expensive-stage behaviour, a thin manual net for pure-logic edits | split field: **auto source-hash** (redun/targets/Hamilton) vs **manual version** (Flyte/Dagster) | **Flyte** `cache_version`, **Dagster** `code_version` | **convergent** with Flyte/Dagster; **opposite** of redun/targets |
| **Doc-level content version** (coarse; positional chunks re-embed whole doc) | the incremental unit is the document, not the chunk (per-chunk precision illusory under positional chunking, D2) | most tools are file- or task-grained, not "sub-artifact but coarsened on purpose" | — | **domain-specific** |
| **Path-as-rendering** (identity decoupled from on-disk layout; catalog bridges id↔path) | files are a human view; a rename is a `git mv`, never a re-key | in **file-DAG** tools the path **is** the key (Make/Snakemake/DVC) → a rename re-keys | **Dagster** (asset key ≠ storage path, via I/O manager) | **distinctive** vs file-DAG tools |
| **Three-registry resolve-upward model** (tree / documents / chunks; resolve at serve) | normalized schema, denormalize only for a server-side filter | **not a pipeline concern** — this is app data-modeling | — (a star-schema shape) | **out of scope** for these engines |
| **Fan-out via factory; removal cascades through construction** | drop a config entry → its stage *and* its dependents vanish from `build_pipeline()` together | dynamic tasks are common; removal-then-GC semantics differ | **Dagster** (deleting an asset def) | **convergent-ish** |

---

## Verdict

- **Off-the-shelf / convergent (we re-derived the standard):** content-addressed DAG, the cache-key formula
  (`inputs + version + params`), the self-describing asset, the manual transform-version, downstream cascade by
  fp composition. Flyte and Dagster match these almost symbol-for-symbol — reassurance, not a red flag.
- **Genuinely ours:** the **provenance-addressed identity** and the **identity/version hash split**;
  **stateless-with-no-DB** (everyone content-based keeps a store); **whole-store GC via the factory**; and
  **path-as-rendering**. None of these is exotic, but no single tool packages them this way.
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
