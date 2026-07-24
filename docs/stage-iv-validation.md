# Stage IV validation runbook — golden_diff

How to prove the Part 3 / Stage IV stage-protocol refactor **did not change any data**.
Run on a **built + region-migrated** tree. Tool: [`scripts/golden_diff.py`](../scripts/golden_diff.py).

Two properties, two passes, **one shared baseline**:

- **Pass A — steady state:** the refactored driver leaves a fresh tree untouched (no spurious rewrites; correct staleness decision on the all-fresh case).
- **Pass B — regeneration fidelity:** when the driver *does* recompute a stale stage, it reproduces the same bytes — exercised from pinned caches, so **no re-fetch, no re-LLM, no re-embed**.

## The exact sequence

```sh
git pull                                         # bring in the refactor

# 1. Baseline — BEFORE any build or reset. The single baseline for BOTH passes.
python scripts/golden_diff.py snapshot

# --- Pass A: steady state ---
mytho build                                      # 2. must be a NO-OP (nothing stale)
python scripts/golden_diff.py assert             # 3. expect: OK — byte-identical

# --- Pass B: regeneration ---
python scripts/golden_diff.py reset --apply      # 4. delete derived outputs + fp sidecars (caches kept)
mytho build                                      # 5. deterministic re-derive from caches (no re-embed)
python scripts/golden_diff.py assert             # 6. expect: OK — byte-identical (fp-init additions allowed)
```

## Why this order

- **Snapshot first — before `build` AND before `reset`.** `build` is what could change data; `reset` deletes
  derived files. The baseline must capture the full pre-build, pre-reset state. Snapshot after either → a smeared
  comparison (deleted/regenerated files show up as added/removed).
- **One snapshot for both passes.** Pass A's `build` is a no-op, so the tree still equals the baseline when Pass B
  starts. The manifest lives at `outputs/.golden/manifest.json`, which is **not** under any stage root, so
  `reset` never deletes it — the baseline survives into Pass B.
- **Before vs after the refactor commit does not matter** — only *before the build* does. The on-disk data is the
  same old data either way, and the file hashes are code-independent. Snapshotting after the refactor is in fact
  marginally safer: `snapshot` and `assert` then use the identical Chroma reader (`load_data`), isolating pure
  data drift. (`load_data` is out of the refactor's scope regardless — one caller, `projections/analyzer`.)

## Hard rules

- **Never `mytho build --force`.** `--force` re-embeds the whole corpus (a full day), re-runs graph LLM extraction
  (non-deterministic, metered) and re-fetches motifs (non-deterministic). It is "rebuild at any cost", not
  "reproduce" — useless as an identity check. `reset` + plain `build` is the deterministic path.
- **`reset` is dry-run by default.** Run it once without `--apply` to preview what it deletes; add `--apply` to
  act. Scope with `--stages corpus,projections,graphs,motifs` (default: all four deterministic stages).
- **`reset` never touches** `raw/` caches, graphs' `extraction_cache.jsonl`, Chroma, or `preprocessed/` — that
  is what keeps the rebuild free of re-fetch / re-LLM / re-embed (the embeddings fp gate stays matched → no-op).

## Reading the verdict

`assert` exit codes: **0** = OK (byte-identical), **1** = DRIFT (a `CHANGED`/`REMOVED`/unexpected `ADDED`), **2** =
baseline manifest missing. On DRIFT: an orchestration refactor must not change data — investigate before trusting
the state. `added (allowed: fp-init)` lines are fine: they are the refactor's one intended fingerprint init
(`.fp` / `.input-fp` sidecars); pass `--allow-added` only to permit *any* new file.

## Manifest location

`outputs/.golden/manifest.json` (gitignored, so it never reaches the repo; wiped by `mytho clean`). Override with
`snapshot --out <path>` and, symmetrically, `assert --before <path>`.
