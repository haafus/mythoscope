# Motifs fetch stabilization — never destroy good raw, never degrade silently

The motif build (`src/motifs/build_motifs.py`) scrapes several third-party sources into a resumable raw
cache, then re-parses that cache into indexes + cross-walk on every run. Two failure modes make it fragile
when an upstream link dies, 404s, or silently changes shape:

1. **A `--force` re-fetch that now fails can *delete* the previously-good cached copy** — two sources call
   `cache.unlink()` on failure, so an upstream hiccup during a forced rebuild erases raw data we already had.
2. **A response that downloads but no longer *parses* degrades the output silently** — the build succeeds
   with fewer (or zero) motifs/links, logging only counts, with no comparison to the last good build.

**Goal:** a fetch that fails, 404s, degrades, or stops parsing must **never uncover or silently drop
previously-good data**; and a drop in yield must **surface**, not be swallowed. This is the motif-specific
instance of the pinned-raw / no-unconfirmed-deletion / plan-surfaces-regressions principle in
[`pipeline-and-incrementality.md`](pipeline-and-incrementality.md) §5–§6 — shippable now, without the driver
refactor.

---

## 1. Current behaviour (what actually happens today)

The single caching layer is `fetch_cache.py`: a **non-empty cached file short-circuits the request unless
`force`** (`fetch_cache.py:32`), and `corpus.downloader.download_file` does `raise_for_status()`
(`downloader.py:87`), so an HTTP error propagates as an exception. At the `fetch_to_cache` level a raised
download **skips the write**, so the old cache survives *there* — the destruction is in the callers.

By scenario:

| scenario | what happens now | verdict |
|---|---|---|
| **normal build (no `--force`), link dead** | cached copy reused, network not hit (`fetch_cache.py:32`) | ✅ persists, flows into pipeline |
| **`--force`, Ashliman page now 404** | `_fetch_page` does `cache.unlink()` + writes `.absent` (`ashliman.py:253`) → variants **fall off** | ❌ **erases good raw** |
| **`--force`, Wikidata fetch/parse fails or degrades** | `refresh` does `cache.unlink()` on any failure and on a degraded reply (`atu_wikidata.py:170,185`) | ❌ **erases good raw** |
| **`--force`, transient error elsewhere** | generic path: old cache not overwritten (raise before write); current run drops the enrichment, recovers next non-force build | ⚠️ transient-only loss |
| **downloaded but no longer parseable** | raw bytes stay on disk; parse yields nothing → `if variants:` false (`build_motifs.py`, `ashliman.py:191`) → type silently loses enrichment | ⚠️ **silent degradation** |
| **whole source unreachable** | `refresh()` returns `{"skipped": ...}` → index built without it | ⚠️ best-effort, but invisible |

The corpus downloader is already safe: `raise_for_status()` + no `unlink` anywhere in `src/corpus`, so a
forced re-fetch that fails keeps the last-good raw. Only the two motif sources actively delete.

Note the Wikidata degraded-guard (`atu_wikidata.py:181–186`) is *right* to reject a degraded reply (rows but
zero sitelinks — WDQS timing out the heavy OPTIONALs) rather than cache it and poison offline re-runs — but it
implements the rejection as `unlink`, which also discards the prior good copy. The fix keeps the rejection and
drops only the destruction.

---

## 2. Principle to encode

**In one paragraph.** We **never delete already-fetched content**. Automatically we **only add new content**.
A **change to existing content** is adopted only through **review + explicit confirmation** (`refresh --apply`).
On a **degradation** we report to the user in detail *what happened* (a durable flag: `url — what — auto-action`);
**finding the cause and deciding is on the user** — fix it as **temporary** (the world recovers, or you patch
the code) or **accept and pin it as permanent** (`refresh --rebaseline` / a config edit). The automatic layer's
whole job is to **never lose or poison data**; every judgement call is surfaced, never silently made.

- **Pinned raw.** Once written, the cache is the source of truth. An upstream problem degrades to *"serve the
  pinned copy + warn"*, never to *"delete."*
- **Validate before commit.** A fetched response replaces the live cache only after passing a validity check;
  otherwise the live cache is kept and the new (bad) bytes are discarded.
- **No silent regression.** Every build compares its yield to the last and flags drops.
- **One auto-reaction.** Every trouble case — upstream *changed* / *disappeared* / *degraded* / *no longer
  parses* — takes the **same** automatic action: **keep the pinned artifact unchanged, commit nothing new, and
  raise a flag** (`url — what happened`). "Reject" is built into commit (validate-before-commit discards the
  arriving bytes); where nothing arrived (a 404) the reject is simply vacuous. The wording variants
  (*keep / keep pinned / keep raw*) are the same act. The **only** thing that varies is the flag's **diagnosis**
  (which of the four) — attribution for the human, not a different mechanism. The human decides whether to leave
  the pinned state (adopt / remove-from-config / retry / fix-parser); the automatic layer never loses or poisons
  data.

---

## 3. The plan

### Phase 0 — Hole-only fix (no functional change, no new machinery)

The pure "stop destroying good raw" fix — remove the two `unlink`s where the failed re-fetch never overwrote
the live copy, so it is preserved with zero behaviour change on the happy path:

1. **Ashliman `_fetch_page`** (`ashliman.py:253`): on 404 with an existing cache → **keep + serve it**, do not
   `unlink`, do not write `.absent`. `.absent` + `None` only when there is no cache (never-existed derived name).
2. **atu_wikidata** (`atu_wikidata.py:170`): on a **raised** fetch (transport/HTTP) → drop the `unlink`; the
   old good copy survives (the raise skipped the overwrite anyway).

Ships alone, no `fetch_cache.py` change. *Excluded here on purpose:* the **degraded** Wikidata reply
(`atu_wikidata.py:185`) — those bytes were already written, so keeping them needs validate-before-commit → Phase 1.

### Phase 1 — Non-destructive fetch (shared layer, `fetch_cache.py`)

1. Add **staging-with-validator** to `fetch_to_cache`: download to `<cache>.partial`, run an optional
   `validate(bytes) -> bool`, then **`os.replace(<cache>.partial, <cache>)`** onto the live path **only if
   valid** — an atomic rename, not copy-then-delete, so the commit *consumes* the staging file (no apply-time
   cleanup) and never leaves a window where both exist. A **reject** is either signal — the download **raised**
   (transport/HTTP) or the **validator returned `False`** (content: unparseable / degraded / empty); on reject,
   discard `.partial` and **leave the live cache untouched**. (Today a raise skips the write, but the degraded
   check runs *after* `fetch_to_cache` already overwrote the cache — hence the `unlink` to undo. Running
   `validate` on `.partial` *before* the rename means a reject simply never renames: nothing to undo.)
2. Return the **outcome** to the caller: `fresh` / `served-pinned` (fetch failed but a cache exists → serve it)
   / `nothing` (no fetch, no cache). The "non-empty cache short-circuits unless force" rule is unchanged.

#### The two fetch paths (so `refresh` is not mistaken for `force=True`)

**`build` = acquire-if-missing** — a purely *local* decision, no network for what is already present (real today,
`fetch_cache.py:32`):
```python
def build_fetch(url, cache):
    if cache.exists() and cache.size() > 0:
        return cache.read()               # present -> use it, NO network
    return fetch_to_cache(url, cache)     # absent -> download once, pin it
```

**`refresh` = re-check present raw against upstream** — a *networked, manual* operation, and **much more than a
boolean `force`**: it stages, validates, diffs, classifies, and by default keeps pinned:
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
            commit(cache, staged)                        # os.replace(.partial -> cache) -> fp-cascade
        else:
            keep(staged); flag(cache, "changed")         # keep pinned + .partial for the diff, await --apply
```
So `refresh` never blindly overwrites (today's crude `force=True` does — the very thing this replaces). `commit`
is the atomic `os.replace(<cache>.partial, <cache>)` of Phase 1. The **aggregate** flags (`yield-drop` /
`discovery-shrank`) are not in this loop — they are computed post-build and reconciled by `--rebaseline`, a
separate build-level act.

### Phase 2 — Fix the two deleters

3. **Ashliman `_fetch_page`** (`ashliman.py:246–256`):
   - Remove `cache.unlink()` on 404.
   - Rule: **if a cache exists** → keep it, serve it, warn "upstream 404 — serving pinned copy", and do **not**
     write `.absent`.
   - Write `.absent` + return `None` **only when there is no cache** (a derived filename like `type0778J.html`
     that never existed) — this preserves the "don't re-probe non-existent pages" optimisation.
   - Transient (non-404) error: unchanged (keep cache; `None` only if no cache).
4. **atu_wikidata** (`atu_wikidata.py:158–186`):
   - Switch to the validated fetch (Phase 1) with a validator = *"parses as JSON **and** (`rows < 50` **or** at
     least one sitelink present)."*
   - On failure/degraded → do **not** `unlink`; keep the previous cache; return `{"skipped": reason}`
     (enrichment skipped this run, good copy intact for offline / next run).
   - Remove both `cache.unlink()` calls (lines 170, 185).

### Phase 3 — Surface silent degradation (`build_motifs.py`)

5. Before `save_json(store.meta_path(), meta)` (`build_motifs.py:266`), **load the previous `meta.json`** if
   present and capture prior `counts` + `enrichment`.
6. After building, compute the **delta** for each index count and each enrichment field vs the prior build.
7. Raise a **`yield-drop` flag** when a count drops **below its high-water mark** (item 13 — *not* merely below
   the previous build). Log it loudly (`REGRESSION: Ashliman variants 0 (was 340)`); the durable record lives in
   `meta.flags` (§Phase 4), not a separate block.
   **How a `yield-drop` even arises** (it is the backstop for losses the per-payload nets miss): a payload that
   **passes the deliberately-loose invariant but contributes fewer records** (a page edited from 20 variants to
   2 still clears `≥1`); a **skipped source's aggregate consequence** (mapsofmyths without creds → its English /
   TMI / tradition counts fall); a **derive/crosswalk code change**; a **cross-source cascade** (trilogy yields
   fewer ATU ids → wikidata/ashliman match fewer); or an intentional **config change** (you confirm it). Most of
   this is downstream of fetch (in crosswalk) or in cross-source aggregation — which no single payload sees.
8. **Root-discovery set — iterate the union; the diff is diagnostic only.** For a *parse-root* (an index page
   whose parse yields the sub-page links: Ashliman `folktexts*.html`, berezkin index, mapsofmyths
   `/motifs_full`), a source builds over **`cached ∪ discovered`**, not just the current discovery. This makes
   the two behaviours *fall out of the general rules* with no special-casing:
   - a **newly-appeared** link is just an un-cached member of the union → acquire-if-missing fetches it;
   - a link that **vanished from the root** is still in `cached`, its pinned page **kept and still contributing**
     to the output (we do not trust "the root dropped it" as authoritative — same E/F caution, never lose data).

   So there is **no fetch/keep logic to write** — the union iteration + acquire-if-missing + never-delete already
   do it. Persist the **discovered set** in `meta.enrichment[source].discovered`. **Only a shrink is flagged** —
   `now ⊋ prev` (the root gained links) is additive, auto-fetched, no concern; `now ⊊ accumulated` (the root
   dropped links it used to list) is the signal. Its value is **attribution** — the general count-drop flag
   (item 7) says *"variants fell"*, the discovery shrink says *whether the root shrank* vs *pages degraded
   individually* — the one signal per-sub-page health checks cannot see.

   **Why it fires even though we build over the union:** the flag is *not* raised from the run (the union never
   shrinks, so the output never loses anything). It is a **separate** comparison — the current root parse vs the
   accumulated mark — and is a signal about the **health of the live root**, orthogonal to the output. This
   matters precisely *because* the union **masks** root degradation: the output stays full off the pinned copies
   while the live source quietly rots, so without this watch a dying source would be invisible until the root
   returns nothing (or the pinned copies themselves go stale). discovery-shrank un-masks it early.

### Phase 4 — Flags (observability of state needing review)

A **flag is a durable "needs-review" record**, not a one-shot log line (a log line scrolls away and is lost; a
flag lives until its cause is gone). This is the persistent form of *surface, don't swallow*.

9. **Store flags in `meta.json`** (`meta.flags`), one record per incident, plus a loud `WARNING` when raised:
   ```python
   {"source": "atu_wikidata",
    "key": "https://query.wikidata.org/sparql",   # url / page / slug
    "kind": "degraded",                            # per-payload: changed|gone|degraded|no-parse; aggregate: yield-drop|discovery-shrank
    "detail": "rows=200 sitelinks=0",              # human-readable cause
    "auto_action": "kept-pinned",                  # what the system already did
    "first_seen": "<build-id>"}
   ```
10. **Stateful lifecycle**, like a linter's open findings — **no free-form dismiss** (a still-true condition
    can never be hidden, or a real problem gets silenced). A flag is *"a divergence from the current definition
    of normal"* and clears exactly two ways, which force the human to say **which**:
    - **raise** — the condition is detected (invariant failed / hash changed / discovery shrank / count dropped)
      → record created; **persist** — every build re-checks; still true → the flag stays (`first_seen` untouched).
    - **auto-clear = "the world returned to normal."** The trouble was **technical/transient** (a transient
      recovered) or we **fixed it** (repaired the parser, shrank the query) and upstream again yields what it
      used to — **nothing permanent changed**, the baseline does not move.
    - **move-the-baseline = "normal changed."** The condition will *not* self-clear because this is a **new
      stable state we accept as correct**: the source really updated (`adopt`), really disappeared
      (`remove-from-config`), or the yield is legitimately lower (`reset the high-water / union mark`). The human
      shifts the definition of normal to reality, and the flag then clears against the new normal.

    So a flag is closed only by resolving *which category the divergence is* — a technical glitch (world
    recovers, auto) or a new system state (baseline moves, manual) — never by hiding it.
11. **Surfaced** three ways: the build-time `WARNING`, a list in `status` / `mytho flags`, and the `refresh
    --check` preview. **Never blocking** — a flag never aborts the build (best-effort); the build proceeds on
    the pinned state, the flag just makes the situation visible and un-losable.

**Three resolution semantics.** Every flag resolves as exactly one of three — the `kind` *narrows* which, but
often only time/investigation *determines* it (which is why there is no blanket accept):

| # | semantics | flags | human action | what actually happens |
|---|---|---|---|---|
| **1. new data, all normal** | a valid update arrived — review it and bring it in | `changed` | review the diff, `refresh <src> --apply` | **move baseline *up*** — promote new bytes to pinned raw, fp-cascade re-derives. Has reviewable content. |
| **2. temporary malfunction** | a fault — cannot be accepted or rejected | `degraded`, `no-parse` (+ outcomes `G`/`B`) | **wait** (transient) **or fix** | **resolved *outside the pipeline*** — either technical conditions self-restore (→ auto-clear), or you update code/config to the new reality. The baseline is **never** moved to a malfunction. |
| **3. permanent divergence** | a real new stable state — legitimize it | `gone` (permanent), `yield-drop`, `discovery-shrank` | `remove-from-config` / `reset the mark` | **move baseline *down*** — needed **only where you cannot fix and must reconcile the counters/expectations**. Legitimizes an absence/reduction (nothing to "adopt"). |

The trap that forbids a blanket `--apply`: the same `kind` (`gone` / `yield-drop` / `discovery-shrank`) can be
**(2) transient — wait** *or* **(3) permanent — legitimize**, and at flag-time you often cannot tell. So the
default bias is **wait** (auto-clear is free and safe); (1) is a per-reviewed-source `adopt`; (3) is a
deliberate single act. Only (1) and (3) move the baseline; (2) never does — it is fixed by the world recovering
or by you changing code/config.

**Everything reduces to two `refresh` knobs** — the only baseline moves that happen *inside* the pipeline:

- **`refresh <src> --apply`** — accept **new content** (semantics 1, `changed`): promote the fetched bytes to the
  pinned raw (`os.replace`), fp-cascade re-derives. A **fetch-level** act.
- **`refresh <src> --rebaseline`** — reconcile the **counter marks** (the counter half of semantics 3,
  `yield-drop` / `discovery-shrank`): write `meta.highwater[counter] = current` and the discovery union `=
  current`. A **build-level** act (the marks are set post-build). Legitimizes a lower yield / a reorganized root
  when you have confirmed it is real.

Everything else is resolved **outside the pipeline**, regardless of whether it is (2) or (3): `gone` → edit the
config (remove the expected entry); `degraded` / `no-parse` → wait for recovery or fix the query/parser code.
(The two knobs are different layers — fetch vs build — but both live on `refresh` as the one "reconcile the
pipeline with reality" verb.)

*Two trigger points feed the same flag* (§2's single auto-reaction, seen at two layers): **validate-before-commit**
(fetch-time, per self-contained payload — this page/response is broken/degraded/changed) and the
**baseline/discovery diff** (build-time, aggregate — every payload is individually fine but the whole yield or
the fan-out shrank, which no per-payload check can see).

12. **Non-decision outcomes are logged, not flagged.** Situations with nothing for a human to *decide* never
    become one of the six review-flags — they are a `WARNING`/`INFO` line **and** a per-source `fetch_outcome`
    in `meta.enrichment`, so they are visible and greppable without cluttering the flag list:
    - **`B`** (fetch failed, no cache) → log + retry next build;
    - **`G`** (transient failure, cache present) → **retry in-pass**; if unrecovered → `served-pinned-transient`
      + log (serve the pinned copy, just wait for the source — no decision);
    - **`I`** (precondition absent, e.g. mapsofmyths without credentials) → `skipped-<reason>` + log **must**
      appear (it already does: `mapsofmyths.py` warns, `build_motifs` logs `SKIPPED`).
    Only if such an outcome *persists across many builds* (long-stale pinned data) is durable awareness useful —
    still an observability line, not a per-pass decision.
13. **Aggregate flags are durable off a high-water mark** — not a one-shot delta vs the previous build. Pin each
    aggregate counter's **max ever seen** in `meta.highwater`; a flag stays raised while `current < max` and
    **auto-clears only when the counter recovers to the mark**:
    ```python
    if current < mx:  flag("below-high-water", detail=f"{counter}: {current} < max {mx}")
    ```
    For the **discovery set** (not a number) the high-water is the **accumulated union** of every link ever
    discovered; **flag only a shrink** — `current ⊊ accumulated` (growth just extends the mark, never flags).
    This makes `yield-drop` / `discovery-shrank` persist until
    the source actually recovers, instead of clearing the next build just because the (now-lower) value stopped
    changing.
    - **Risk — a spurious high poisons the mark** (a dedup bug counts double → `max` sticks, everything flags
      below it forever). Mitigation: **advance the mark only on a trusted build** (no active per-payload flags);
      a dirty spike does not move it.

### Phase 5 — Tests & verification (`tests/test_motifs.py`)

14. Add cases:
    - forced re-fetch with a 404 and an existing cache → cache kept and served (no `unlink`, no `.absent`);
    - 404 with no cache → `.absent` written, `None` returned (optimisation preserved);
    - degraded Wikidata reply → previous cache kept (no `unlink`);
    - `yield-drop` flag fires when a count falls below its high-water mark.
15. Run the existing motif tests + lint; a small end-to-end build to confirm counts are unchanged when nothing
    changed.

---

## 4. Sequencing

- **Phase 0** ships first, alone — the pure hole-only deletion fix, zero functional change.
- **Phases 1–2** complete the non-destructive fetch (staging-with-validator + the degraded case) — the live
  foot-gun is fully closed here.
- **Phases 3–4** are a separable degradation / flag guard.
- **Phase 5** covers all of it.

All of this is **code**. The **core (Phases 0–3: stop deleting, validate-before-commit, surface degradation)**
does **not** require the `refresh` / plan-apply machinery — it is the same principle applied locally to the
motif sources, and it hardens the shared `fetch_cache.py` layer the corpus downloader also uses. The flag
**resolution** verbs — `refresh --apply` (adopt) / `refresh --rebaseline` (reconcile marks), §Phase 4 — are the
same ones proposed in [`pipeline-and-incrementality.md`](pipeline-and-incrementality.md); the motif flags slot
into them when they land. Until then a flag is resolved by a plain re-fetch (adopt) or a manual `meta.highwater`
edit (rebaseline).

**Export note:** the Phase-1 `<cache>.partial` staging files must be excluded from `export_bundle.py` (the same
`*.partial` temp-exclusion Part 2's atomicity needs — see that doc's *Export impact*). The `.absent` markers
already sit under `motifs/raw/`, which export excludes as cache (`export_bundle.py:62`).
