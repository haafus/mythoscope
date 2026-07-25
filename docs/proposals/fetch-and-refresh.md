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

---

## 7. Two-layer architecture — source-units vs stages

The fetch/build split is realised as **two layers**, validated on both corpus (one generic source) and motifs
(seven bespoke sources, one shared).

**Layer 1 — fetchable source-units** own the *fetch*: a raw dir, the `key → locator` mapping, any auth, and the
**`acquire`/`refresh`** operations. `acquire(key)` **dispatches by source type** internally — `http(s)://` →
network fetch-to-cache, `file:` / bare path → local read (confined to `sources_dir`) — both landing in the same
raw cache, so the caller never sees "web vs disk". `refresh` re-checks a present source (§2 flow).

**Layer 2 — stages** own the *parse + store*: they read raw via a source-unit's `acquire`, transform (extract /
clean / parse), and write their output `store`. A stage's `store` is 1:1 with the stage (may be several
artifacts — corpus writes the `.txt` tree **and** `corpus.json`).

**No separate `RawStore` object.** The fetch capability rides on the entity that already exists — a source
module today (sources already expose `refresh()`), a **stage object in Part 3** (fetchable stages carry
`acquire`/`refresh` as methods with bound config; non-fetchable stages — `embeddings`/`graphs` — simply don't,
and read their input from a prior stage's `store`). `acquire` and `refresh` are **two faces of one `upstream`
capability**: a stage has both or neither — design them together, never as a standalone raw object beside a
separate `refresh` field.

**acquire-on-miss (auto) vs refresh (explicit)** — the divide is the core principle applied per-key:
- **new key with no raw** (cold start *or* a document newly added to config) → `acquire`: fetch + validate +
  commit. Nothing to lose → **automatic on build**. Present raw is **never re-fetched** (build stays offline for
  what is present — the invariant is "don't re-fetch present", not "never touch the network").
- **existing raw, upstream may have changed** → **`refresh`, explicit** (diff / flag / adopt). Never automatic.

**Shared sources need no driver aggregation.** Sources are a **registry deduped by id**; each stage declares
`sources = [ids]` it reads. A source used by two stages (e.g. `trilogy` → `tmi` + `atu`) is deduped for free:
- **build** — both stages call `SOURCES["trilogy"].acquire(...)`; acquire-on-miss means the network is hit
  **once** (the second is a cache hit);
- **refresh** — iterates the **set** of distinct sources in scope → `trilogy` refreshed **once**.

The driver never models sources as DAG nodes (that would put fetch back in the graph — it is the boundary). A
new source = add to the registry + name it in a stage's `sources`; sharing = one id in two lists.

```python
SOURCES = {"trilogy": Trilogy(), "wikidata": Wikidata(), "ashliman": Ashliman(), ...}   # dedup by id

class AtuStage:                       # Layer 2
    sources = ["trilogy", "wikidata", "ashliman"]
    def build(self):
        rows = SOURCES["trilogy"].acquire("atu_df")   # cache-deduped with TmiStage

def refresh(scope):
    for sid in {s for st in stages_in(scope) for s in st.sources}:   # set -> trilogy once
        SOURCES[sid].refresh()
```

Motifs map to **3 index stores** (`berezkin`/`tmi`/`atu` → one JSON each) over **~7 source-units**
(`areasofmyths` · `mapsofmyths` · `trilogy` shared · `folkmasa` · `mellmann` · `wikidata` · `ashliman`);
`crosswalk` / `parallels` / `semantic` are downstream stages with **no upstream** (they read index stores, not
raw). Corpus maps to **one generic source-unit** (scheme-dispatch, per-document keys) → the `corpus` stage →
the `.txt` tree + catalog.

## 8. Open items (pin at implementation, Part 3 era)

This architecture is the **target form** — converged and validated, not yet a code-ready spec. Still to pin:

1. **Source-unit API** — exact signatures of `acquire(key)` / `refresh(*, apply)` / the `validate` hook, and how
   `key → locator` resolves.
2. **Shared-source keys** — `trilogy`'s file-keys and how `tmi` / `atu` name what they read.
3. ~~**Motif raw in export**~~ — **DECIDED: all raw is a cache, uniformly.** Never committed (neither corpus nor
   motifs); excluded from export by default; shipped **only with `--caches`**, in all cases. No selective /
   motif-specific rule. (Consequence: the region migration re-keys raw **in place** — `sha1→blake2b` rename, no
   re-fetch, no committed fallback — see `region-implementation.md` §6.)
4. **fetch/parse split** — mechanically move parse out of the sources' current `refresh()` functions into the
   index stages' `build` (today they conflate fetch + parse).
5. **Edges not yet walked** — parse-root discovery (berezkin detail pages found by parsing the index) under the
   fetch/parse split; the `mapsofmyths` POST endpoint; per-source auth; per-source validators.

Near-term work (motifs Phases 0–5, pipeline Part 2) does **not** depend on this — it lands with the Part 3
stage-protocol refactor.

## 9. Experimental design — `refresh` on the driver (NOT a settled decision, do not build yet)

**Status:** experimental sketch. Not decided, not started. Records a direction discussed while cleaning up the
CLI; the current shape (CLI functions + the `_REFRESHERS` map in `cli.py`) stays until this is accepted.

**Idea.** Make `refresh` a driver-orchestrated operation, parallel to `build`/`status`/`clean` — but *not* a
consumer of the `desired()`/`actual()` diff. Its comparison is **fresh-download vs pinned raw** (upstream), a
different diff than spec-vs-built, so it is a separate driver pass, not another `plan()` reader.

**Shape (as sketched):**

- A capability protocol mirroring the existing `Store` (`@runtime_checkable`):
  ```python
  @runtime_checkable
  class Refreshable(Protocol):
      def refresh(self, apply: bool) -> None: ...
  ```
- `CorpusStage` / `MotifsStage` implement `refresh` (motifs = today's wholesale `build_motifs(force=True)`
  stopgap until the §7 per-source staged refresh lands). Corpus wraps `refresh_corpus` (which keeps returning
  `RefreshResult` — tests unchanged).
- `driver.refresh(stages, *, apply)` topo-traverses and dispatches to `isinstance(s, Refreshable)` stages;
  non-refreshable stages are skipped. Removes the hand-kept `_REFRESHERS` (the set derives from `build_pipeline()`).

**Decided:** **no colour** — output is plain text, not `click.style`. (Today's `_refresh_documents` colouring is
dropped in the refactor.)

**Decided — output is a three-column table**, one row per checked resource (document):

| column | contents |
|---|---|
| 1 · resource | the resource name |
| 2 · status | one exact expression, no parentheses, no explanation: `not changed` \| `changed` \| `degraded` \| `gone` \| `new` |
| 3 · action | the decision taken: `keep cached` \| `acquire on apply` \| `flagged for review` |

Status → action mapping:

- `not changed` / `degraded` / `gone` → **keep cached** (the pinned copy stands; a bad/absent upstream never overwrites it)
- `new` → **acquire on apply**
- `changed` → **flagged for review** (recorded as a §5 flag, not auto-adopted)

The "review record" is the existing **flag** (§5), not a new file: a durable needs-review entry in the stage's own
metadata (`meta.flags`) — no new path. `degraded`/`gone`/`no-parse` also raise their flag kinds there.

Footer, in order:

1. **total** resources checked;
2. how many were **flagged for review** and where the flags live (the stage's `meta.flags`, §5);
3. the **`--apply`** line (what re-running with `--apply` will do).

`degraded`/`gone` collapse the current reason detail (`empty-body`, `gone-404`) into the single status word, as
specified (no parentheses).

**Open design calls (why it's experimental):**

1. **Where the summary is produced.** Either each stage `print`s its own plain summary (domain does console IO;
   tests capture stdout — no `click`, so `src/pipeline/` stays CLI-framework-free), or the stage returns plain
   lines and the CLI prints them (cleaner layering, needs a shared shape — see below). Colour is out either way.
2. **`RefreshResult` does not generalise (today).** Its fields (`unchanged/skipped_local/changed/new/adopted/
   unreachable/degraded`, per-title, web-vs-local) are corpus's staged-per-document shape. The motifs wholesale
   stopgap cannot fill them. So `RefreshResult` stays a **corpus-internal** detail (not in the protocol); a truly
   shared result only becomes possible **after** the §7 motifs atomisation gives motifs the same per-source
   staged shape. Keeping the protocol `-> None` sidesteps this until then.

Depends on nothing already shipped; supersedes the `_REFRESHERS` map when accepted.
