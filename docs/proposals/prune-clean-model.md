# Prune / clean model — who deletes what, when, and why (by design)

**Status: DECISION — documents current behaviour as intentional. No code change.**

Audit prompted by "should embeddings' in-`build` orphan-GC move to `driver.clean`?" The answer is
**no** — the current split is a coherent design, not tech debt. This note is the reasoning trail so
the question does not get re-opened as a "bug".

## 0. Two different animals: **stale** vs **orphan**

- **stale** — an artifact of a document *that is being rebuilt*, whose inputs changed (a shorter
  text drops its tail chunks; a re-fingerprinted book regenerates its graphs). Only `build` knows
  this delta — it is intrinsic to rebuilding that document. **Cannot live anywhere but `build`.**
- **orphan** — an artifact whose *whole document/key left the desired set* (book removed from
  config). This is `actual − desired`; the driver's `clean` is its canonical home. Some builders
  *also* reap orphans in-`build` as a safety net.

Conflating the two is the root of the confusion. Only the **orphan** case has a real "where should
it live" choice; **stale is not movable**.

## 1. Inventory — what deletes what, when

| # | Where | Removes | When | Class |
|---|---|---|---|---|
| A | `driver.clean()` L1 → `stage.delete` | orphan **keys** (doc left `desired`) | `mytho clean --apply` only | orphan |
| B | `driver.clean()` L2 → `store.delete` | whole dropped stage/model artifact (family-granular) | `mytho clean --apply` only | orphan |
| C | corpus `_prune_orphan_texts` | `.txt` of docs no longer in config | **every** `build corpus` | orphan |
| D | embeddings `orphan_chunk_ids` | chunks of docs that left the corpus | **every** `build embeddings` (full set) | orphan |
| E | embeddings `embed_plan` stale | a rebuilt doc's own dropped tail chunks | every `build embeddings`, **work-list docs only** | stale |
| F | `--force` | whole collection / extraction cache / model dir | `--force` | reset |
| — | graphs / projections / motifs | **no in-`build` orphan prune** — orphans reaped only by `clean` L1 | — | — |

`driver.build()` itself **never reaps orphans** — it only adds/updates `missing`+`stale`.

## 2. Per case — do-here / don't-here / move-it

### E — embeddings stale (non-movable)
- **Do here:** correct; an edited-down doc drops its old vectors.
- **Don't here:** **bug** — stale vectors linger, search returns outdated chunks.
- **Move?** Nowhere. Only `build` sees the per-doc chunk delta; `clean` does not rebuild. Settled.

### C — corpus prune orphan `.txt` (every build)
- **Do here:** a de-configured book's `.txt` is gone by the next build; tree + `export` stay clean.
- **Don't here:** the `.txt` lingers until `clean`. **Low harm** — serving reads `corpus.json`, and an
  orphan `.txt` is not in the catalog, so it is invisible in the UI; only disk litter + `export`.
- **Move?** To `clean` → litter until manual clean. To driver-every-pass → see §3.

### D — embeddings prune orphan chunks (every build)
- **Do here:** a removed/renamed doc's chunks are gone by the next build; search never returns an
  unresolvable `document_id`.
- **Don't here:** **user-visible bug** — orphan chunks stay in Chroma and **surface in search** with
  an unresolvable `document_id` until `mytho clean --apply`. Higher harm than C (visible, not litter).
- **Move?** To `clean`-only → exactly that search bug until manual clean. To driver-every-pass → §3.

### A / B — driver `clean` (separate command)
- **Do here:** the canonical orphan reap; family-granular; an **explicit** user action.
- **Don't here:** nothing reaps orphans except the in-`build` nets C/D — so graphs/projections/motifs
  (which have no in-`build` net) would accumulate orphans forever. `clean` is load-bearing for them.

## 3. The rejected alternative — orphan-reap in `driver.build` (every pass, all stages)

Have the driver run `plan(stage).orphans → stage.delete` after every build, uniformly.

- **Upside:** uniform; C/D leave the builders; graphs/projections self-heal too; `clean` becomes
  explicit-but-redundant.
- **Why we do NOT:** **`build` is deliberately non-destructive — it only adds/updates.** Reaping on
  every pass makes any *transiently wrong* `desired()` destructive: a config that failed to load, an
  empty catalog, a downed source collapses `desired`, and a routine `build` would **delete everything**
  as "orphans" (recomputable, but an expensive full re-embed/re-graph). Reaping is gated behind an
  explicit `clean` command precisely so a bad `desired()` cannot nuke derived data on a routine build.

**Where the driver *can* reap:** either **every pass** (uniform, but unsafe without a guard against a
suspiciously-empty/collapsed `desired()`), or **only via `clean`** (safe, but not automatic — stages
without an in-`build` net accumulate orphans until run).

## 4. Decision — keep as-is, by design

The in-`build` orphan prune (C, D) is a **deliberate, narrow exception** to "build is non-destructive",
warranted exactly where an orphan is **(a) user-visible and (b) cheap to recompute**:

- **embeddings (D):** orphan chunks are user-visible (they surface in search) → self-heal on build.
- **corpus (C):** orphan `.txt` is invisible to serving but trivially cheap to prune → harmless self-heal.
- **graphs / projections / motifs:** orphans are **invisible** (served by `document_id` / from the
  catalog, so an orphan artifact is unreachable) → no self-heal needed; `clean` suffices.

So the asymmetry **tracks orphan visibility**, and is coherent. `stale` (E) stays in `build` by
definition. Full uniformity (§3) is rejected: it trades this safe, visibility-driven split for a
build that can self-destruct on a bad `desired()`.

**Not a follow-up.** If revisited, the decision to make first is the *principle* ("is `build` ever
allowed to delete, and under what `desired()`-sanity guard?"), not the code move.
