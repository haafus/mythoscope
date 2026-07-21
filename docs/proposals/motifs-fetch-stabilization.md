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

- **Pinned raw.** Once written, the cache is the source of truth. An upstream problem degrades to *"serve the
  pinned copy + warn"*, never to *"delete."*
- **Validate before commit.** A fetched response replaces the live cache only after passing a validity check;
  otherwise the live cache is kept and the new (bad) bytes are discarded.
- **No silent regression.** Every build compares its yield to the last and flags drops.

---

## 3. The plan

### Phase 1 — Non-destructive fetch (shared layer, `fetch_cache.py`)

1. Add **staging-with-validator** to `fetch_to_cache`: download to `<cache>.partial`, run an optional
   `validate(bytes) -> bool`, then `os.replace` onto the live path **only if valid**; on exception or invalid,
   discard `.partial` and **leave the live cache untouched**. (Today a raise skips the write — this makes the
   atomicity explicit *and* covers "downloaded but degraded", which the current code can only fix by deleting.)
2. Return the **outcome** to the caller: `fresh` / `served-pinned` (fetch failed but a cache exists → serve it)
   / `nothing` (no fetch, no cache). The "non-empty cache short-circuits unless force" rule is unchanged.

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
7. Flag a **regression** when a count drops beyond a threshold (to 0, or by more than ~10%). Log it loudly
   (`REGRESSION: Ashliman variants 0 (was 340)`) and record a `regressions` block in `meta.json`.
8. Add a `--strict` flag (`build_motifs` + CLI): exit non-zero if any regression is flagged. Default off
   (best-effort), so CI/automation can opt in while interactive builds stay lenient.

### Phase 4 — Observability of degraded state

9. Record the per-source **fetch outcome** in `meta.enrichment`: `ok` / `served-pinned-upstream-404` /
   `skipped-<reason>` / `degraded-kept-previous`. Then the log, `meta`, and (later) `status` / `refresh
   --preview` show **which sources are serving pinned/stale data** rather than live.

### Phase 5 — Tests & verification (`tests/test_motifs.py`)

10. Add cases:
    - forced re-fetch with a 404 and an existing cache → cache kept and served (no `unlink`, no `.absent`);
    - 404 with no cache → `.absent` written, `None` returned (optimisation preserved);
    - degraded Wikidata reply → previous cache kept (no `unlink`);
    - regression detector fires when counts drop.
11. Run the existing motif tests + lint; a small end-to-end build to confirm counts are unchanged when nothing
    changed.

---

## 4. Sequencing

- **Phases 1–2** are the urgent, self-contained fix for the live deletion foot-gun — one PR.
- **Phases 3–4** are a separable degradation guard.
- **Phase 5** covers both.

All of this is **code**, independent of the CLI/driver design decisions in
[`pipeline-and-incrementality.md`](pipeline-and-incrementality.md). It does not require the `refresh` / plan-apply
machinery — it is the same principle applied locally to the motif sources, and it hardens the shared
`fetch_cache.py` layer that the corpus downloader also uses.
