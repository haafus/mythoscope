# Fetch & refresh — the acquire / re-check boundary, staging, and flags

The **canonical model** for how the pipeline acquires raw from upstream and how it reconciles already-fetched raw
with a changing upstream — independent of any one source. The driver/CLI doc
([`pipeline-and-incrementality.md`](pipeline-and-incrementality.md)) and the motif-source application
([`motifs-fetch-stabilization.md`](motifs-fetch-stabilization.md)) both refer here for the fetch/refresh/flag
model; those docs carry the wiring and the source-specific specifics respectively.

**In one paragraph.** We **never delete already-fetched content**. Automatically we **only add new content**. A
**change to existing content** is adopted only through **review + explicit confirmation** (`refresh --apply`). On
a **degradation** we report *what happened* in detail (a durable flag); **finding the cause and deciding is on
the user** — fix it as **temporary** (the world recovers, or you patch the code) or **accept and pin it as
permanent** (`refresh --rebaseline` / a config edit). The automatic layer's whole job is to **never lose or
poison data**; every judgement call is surfaced, never silently made.

**Building the corpus/DB is fundamentally *iterative*, not a one-shot job — this is the base premise the whole
model serves.** Concretely:

- the **sources are inherently external, unstable, and expanding** — new ones get added over time;
- the **delivery path is itself technologically unstable** — many *transient* failures are normal, not
  exceptional;
- **integrating and processing each source is complex and iterative** — the working loop is *debug → add →
  verify*, repeated;
- so **corpus/DB growth is a long-running process measured in years**, not a single build — and the
  **already-built part must stay in a stable, coherent state across every update**.

**Best-effort, not fail-fast** falls out of that premise. A build **degrades rather than aborts**: a source
down / degraded / unparsed yields a *smaller but coherent* output plus a flag, never a failed build — because
the built part must survive the next flaky increment untouched. A partial result beats no result here. The
opposite (**fail-fast** — abort so a degraded artifact never exists) fits a *one-shot* pipeline whose downstream
needs guaranteed-complete data (a release artifact, a payment flow); it is not this one. This is why flags
**never block** the build, why we **never delete pinned raw**, and why every change is **staged and reviewed**:
all of it keeps the standing corpus stable while it grows and is fixed incrementally, perhaps for years.

---

## 1. Fetch is the DAG boundary, not a stage

A build **stage** must be a function whose staleness is **decidable offline from fingerprints**: `desired()` is
computed from the inputs' fingerprints, and "rebuild?" is answered **without going to the network**. Network I/O
inside a stage is fine *to produce* the output — the graphs stage calls an LLM — because the output is
**content-addressed by its input** (`hash(chunk, pinned model)`) and its staleness is still decided offline.

**Fetch fails that test.** Its "output" (the bytes at a URL) is **not** a function of the input's fingerprint —
the same URL yields different bytes over time. "Is my cached copy still current vs upstream?" is **undecidable
offline**; only the network knows. So fetch cannot participate in the fingerprint-driven build graph.

Therefore **raw is an *input* to the pipeline, and fetch sits on the input boundary, above the DAG:**

- **acquire-if-missing** (part of `build`, automatic) fills a missing raw input — a purely *local* decision
  (does the file exist?);
- **refresh** (manual, networked) re-checks an already-present raw against upstream.

**The deeper distinction — a stage decides automatically; the boundary never does.** A build stage is *fully
automatic*: the fingerprint decides "rebuild?", orphans are reaped, nothing waits on a human. Fetch/refresh is
the **one place the system deliberately does *not* auto-decide** — a changed/gone/degraded upstream is **never
adopted automatically**; it is surfaced and **the human reviews and decides** (adopt / remove / fix / wait). That
is precisely why fetch is a *boundary*, not a *node*: nodes are automatic, the boundary is where human judgement
enters the pipeline.

**And the reason human judgement must enter *here* is to prevent data loss.** Ordinary stages are **purely
transforming** — they turn raw into derived, and the derived is **always re-derivable** from the raw that remains
on disk. A wrong automatic decision in a stage costs only recompute; **data loss is impossible there**. Fetch is
the *only* step that touches **raw itself — the one irreplaceable input** (upstream may be gone tomorrow). An
automatic decision that overwrote or dropped raw could destroy it **forever**. So the human gate sits exactly
where, and only where, an automatic mistake is *irreversible*. (The offline-vs-network test above is *why* the
machine cannot decide here; the irreversibility is *why* it must not.)

`refresh` **generalises** via an `upstream` capability on stages, not by hard-coding targets: a stage that has a
network source implements a `refresh()` (`corpus`, `motifs:source`); `embeddings` / `projections` / `graphs` do
not, and `refresh` skips them. It reuses the driver's stage/scope addressing, but is **not in the topological
build order** — it is a boundary operation on the DAG's input edge.

```python
def refresh(scope=None, *, apply=False):
    for s in _selected(scope):
        fn = getattr(s, "refresh", None)   # "upstream capability" = the method exists
        if fn:                             # no upstream -> no method -> skipped
            fn(apply=apply)
```

---

## 2. The two fetch paths (why `refresh` is not just `force=True`)

**`build` = acquire-if-missing** — a purely *local* decision, no network for what is already present (this is
real today, `fetch_cache.py:32`):

```python
def build_fetch(url, cache):
    if cache.exists() and cache.size() > 0:
        return cache.read()               # present -> use it, NO network
    return fetch_to_cache(url, cache)     # absent -> download once, pin it
```

**`refresh` = re-check present raw against upstream** — *networked, manual*, and **much more than a boolean
`force`**: it stages, validates, diffs, classifies, and by default keeps pinned:

```python
def refresh(source, *, apply=False):          # --check (preview) is apply=False
    for url, cache in source.fetchables():
        try:
            staged = download(url)                       # ALWAYS hit the net, into <cache>.partial
        except Exception as e:
            record(cache, outcome_or_flag(e))            # gone(F)/transient(G): keep pinned, discard staged
            continue
        if not cache.exists():                           # first acquire happened via refresh
            commit(cache, staged); continue              # os.replace(.partial -> cache)
        if staged == cache.read():                       # D: unchanged
            discard(staged); continue
        if not source.validate(staged):                  # H/J: degraded / no-parse
            flag(cache, "degraded" | "no-parse"); discard(staged); continue   # reject, keep pinned
        # E: valid AND changed — the only adopt case, and only on confirmation
        if apply:
            commit(cache, staged)                        # os.replace -> fp-cascade re-derives
        else:
            keep(staged); flag(cache, "changed")         # keep pinned + .partial for the diff, await --apply
```

Contrast: today's crude `force=True` **blindly overwrites** the cache; `refresh` never does. The difference is
not a flag — it is the whole staging / validate / diff / classify / keep-pinned machinery.

**In one phrase: `refresh` is a *diff/merge against the existing data*, not an overwrite** — the git-`fetch → diff
→ merge` shape. Fetch lands in staging (`.partial`), the diff against the pinned copy classifies the change
(`D`/`E`/`H`/`J`), and the *merge* (adopt) happens only on `--apply`. Blind overwrite is the one thing it never
does.

---

## 3. Staging: `.partial` + `os.replace` (validate-before-commit)

A fetch downloads into a sibling **`<cache>.partial`**, never the live cache, so the live copy is untouched
until the new bytes are proven good:

- **commit** = **`os.replace(<cache>.partial, <cache>)`** — an atomic **rename**, not copy-then-delete. Rename
  *consumes* the staging file (it *becomes* the cache) in one atomic op: a successful commit needs no cleanup and
  has no window where both exist.
- **reject** (fetch raised, or `validate()` returned `False`) → discard `<cache>.partial`, the live cache is
  **untouched** — nothing to undo. (Today the degraded check runs *after* the cache was already overwritten,
  which is why the current code `unlink`s to roll back, losing the good copy.)
- **crash** between write and rename → a stray `.partial` is **inert**: `actual()` never reads it, the
  deterministic path self-overwrites on the next fetch, and export excludes `*.partial`.

---

## 4. Situations and the single auto-reaction

Relative to the pinned cache (present/absent) × upstream state, a fetch meets one of:

| | situation |
|---|---|
| **A** | no cache, fetch OK → new raw |
| **B** | no cache, fetch failed (transport/timeout) |
| **C** | no cache, 404 / name never existed |
| **D** | cache, upstream identical → no-op |
| **E** | cache, **upstream changed** (valid, differs) |
| **F** | cache, **upstream gone** (404) |
| **G** | cache, transient fetch failure |
| **H** | cache, 200 but **degraded** (fails the health invariant) |
| **I** | **precondition absent** (e.g. no credentials) |
| **J** | fetched OK but **no longer parses** |

**One auto-reaction** for every trouble case (E/F/H/J): **keep the pinned artifact unchanged, commit nothing new,
raise a flag** (`url — what happened`). "Reject" is built into commit (validate-before-commit discards the
arriving bytes); where nothing arrived (a 404) the reject is vacuous. The only thing that varies is the flag's
**diagnosis** — attribution for the human, not a different mechanism. The rest are silent (A/C/D acquire /
absent / no-op) or logged outcomes (B/G/I, §6).

**Two nets, two moments** — both feed the same flag:
- **validate-before-commit** (fetch-time, per self-contained payload — *this* page/response is
  broken/degraded/changed);
- **baseline / discovery diff** (build-time, aggregate — every payload is individually fine but the whole yield
  or the fan-out shrank, which no per-payload check can see).

Distinguishing **H (degraded)** from **J (no-parse)** cannot be done automatically from the bytes — the
validator collapses both into "keep pinned + flag"; the human splits them by inspecting the raw (degraded =
valid-but-thin, transient; no-parse = structure changed, needs a code fix). "Transient" is **not** a kind — it
is a `degraded` flag that auto-clears next build.

---

## 5. Flags

A **flag is a durable "needs-review" record**, not a one-shot log line (a log line scrolls away; a flag lives
until its cause is gone). This is the persistent form of *surface, don't swallow*.

**Record** — stored in the stage's metadata (e.g. `meta.flags`), one per incident, plus a loud `WARNING`:
```python
{"source": "atu_wikidata",
 "key": "https://query.wikidata.org/sparql",   # url / page / slug
 "kind": "degraded",                            # per-payload: changed|gone|degraded|no-parse
                                                # aggregate:   yield-drop|discovery-shrank
 "detail": "rows=200 sitelinks=0",
 "auto_action": "kept-pinned",
 "first_seen": "<build-id>"}
```

**Six kinds.** Per-payload (fetch-time): `changed` · `gone` · `degraded` · `no-parse`. Aggregate (build-time,
durable off a high-water mark): `yield-drop` · `discovery-shrank`.

**Stateful lifecycle** — like a linter's open findings, **no free-form dismiss** (a still-true condition can
never be hidden). A flag is *"a divergence from the current definition of normal"* and clears exactly two ways,
which force the human to say **which**:

- **auto-clear = "the world returned to normal."** The trouble was **technical/transient** (a transient
  recovered) or we **fixed it** (repaired the parser, shrank the query) and upstream again yields what it used
  to — **nothing permanent changed**, the baseline does not move.
- **move-the-baseline = "normal changed."** The condition will not self-clear because this is a **new stable
  state accepted as correct**: the source really updated (`adopt`), really disappeared (`remove-from-config`),
  or the yield is legitimately lower (`reset the mark`). The human shifts the definition of normal to reality.

**Three resolution semantics** — the `kind` narrows which, but often only time/investigation determines it
(hence no blanket accept):

| # | semantics | flags | human action | effect |
|---|---|---|---|---|
| **1. new data, normal** | a valid update arrived — review and bring it in | `changed` | review diff → `refresh --apply` | baseline **up** — promote to pinned raw, fp-cascade re-derives |
| **2. temporary malfunction** | a fault — cannot be accepted or rejected | `degraded`, `no-parse` (+ outcomes `G`/`B`) | **wait** or **fix** | resolved **outside the pipeline** — world self-restores (auto-clear) or you fix code/config; baseline **never** moves to a malfunction |
| **3. permanent divergence** | a real new stable state — legitimize it | `gone`, `yield-drop`, `discovery-shrank` | `remove-from-config` / `reset the mark` | baseline **down** — only where you cannot fix and must reconcile counters |

The same `kind` (`gone`/`yield-drop`/`discovery-shrank`) can be **(2) transient** or **(3) permanent** and you
often cannot tell at flag-time — so the default bias is **wait** (auto-clear is free and safe). Only (1) and (3)
move the baseline; (2) never does.

**Aggregate flags are durable off a high-water mark** (not a one-shot delta vs the previous build): pin each
counter's max-ever in `meta.highwater`; a flag stays while `current < max` and clears on recovery. For the
**discovery set** the mark is the **accumulated union** of every link ever discovered; **flag only a shrink**
(`current ⊊ accumulated`; growth just extends the mark). *Risk:* a spurious high poisons the mark → advance it
**only on a trusted build** (no active per-payload flags).

**Non-decision outcomes are logged, not flagged** — `B` (fail, no cache) → log + retry; `G` (transient, cache
present) → retry in-pass, else `served-pinned-transient`; `I` (precondition absent) → `skipped-<reason>`. They
sit in the log + a per-source `fetch_outcome`, not the flag list — nothing to decide.

---

## 6. Everything reduces to two `refresh` knobs

The only baseline moves that happen **inside** the pipeline:

- **`refresh <src> --apply`** — accept **new content** (semantics 1, `changed`): promote the fetched bytes to the
  pinned raw (`os.replace`), fp-cascade re-derives. A **fetch-level** act.
- **`refresh <src> --rebaseline`** — reconcile the **counter marks** (the counter half of semantics 3,
  `yield-drop` / `discovery-shrank`): write `meta.highwater[counter] = current` and the discovery union `=
  current`. A **build-level** act (marks are set post-build).

Everything else is resolved **outside the pipeline**, regardless of whether it is (2) or (3): `gone` → edit the
config (remove the expected entry); `degraded` / `no-parse` → wait for recovery or fix the query/parser code.
