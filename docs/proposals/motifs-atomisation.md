# Motifs atomisation — the granular per-source split (✅ SHIPPED)

**Status: done.** Motifs is now atomised onto the driver as **7 stages** — `motifs:source:{berezkin,
tmi,atu}` → `motifs:crosswalk` → `motifs:parallels` / `motifs:semantic` → `motifs:meta` — each
gating on its own fp sidecar (`.fp.<stage>`). The coarse `MotifsStage` + `motifs_fingerprint` gate
and the monolithic `build_motifs` orchestrator are **retired** (only the `_build_*` stage helpers
remain); each source has a staged per-source `refresh` (`mytho refresh motifs[:source:X]`). Every
step was validated **golden-diff byte-identical** (`scripts/validate_motifs_atomisation.py`).

The sections below are the original plan, kept as the design record; task statuses are marked inline.

## Why it was deferred (historical)

The split could not be **validated** in a network-less / raw-cache-less environment: it needs either
the network or a populated `outputs/motifs/raw/` scrape cache. With that cache present it builds
offline and the core artifacts (`berezkin/tmi/atu/crosswalk/parallels.json`) are deterministic and
golden-diffable. That prerequisite (a raw-cache snapshot) was met, and the split then landed.

## Target stages + DAG

```
source:berezkin ┐
source:tmi      ┼──► crosswalk ──► parallels ──┐
source:atu      ┘         │                    ├──► meta
       └──────────────────┴──► semantic ───────┘
```

| Stage | Builds | Enrichment (network, best-effort) | fp (offline) |
|---|---|---|---|
| `motifs:source:berezkin` | `berezkin.json` | mapsofmyths, berezkin_bibliography | raw(berezkin) + config + algo |
| `motifs:source:tmi` | `tmi.json` | bibliography | raw(trilogy-tmi) + config + algo |
| `motifs:source:atu` | `atu.json` (+ `atu_seq`) | atu_wikidata, ashliman | raw(trilogy-atu) + config + algo |
| `motifs:crosswalk` | `crosswalk.json` | — | ⊕(three source fps) + algo |
| `motifs:parallels` | `parallels.json` | — | crosswalk fp ⊕ source fps + algo |
| `motifs:semantic` | `semantic_parallels.json` | — (copies committed file) | hash(committed file) |
| `motifs:meta` | `meta.json` (counts, degradation guard) | — | derived (aggregator) |

Dependencies: sources depend on nothing (external scrapes); `crosswalk` on the three sources;
`parallels` on crosswalk + sources; `semantic` on the sources (copy-in mode keys on the
committed file); `meta` aggregates everything. Each source build is already self-contained
(`berezkin.build` / `trilogy.build_tmi` / `trilogy.build_atu` + its own enrichment refreshes),
so the sources separate cleanly at the build boundary.

## The real work (what makes it non-trivial)

The sources cannot be peeled **in isolation**: `crosswalk`/`parallels` currently receive the
sources' **in-memory** outputs directly (≈10 derived structures). As separate stages the
sources only write JSON, so the downstream stages must reload and re-derive. But most of those
structures are already **re-projectable** from the stored index JSONs — they are inline
convenience projections in `build_motifs` today:

- from `tmi.json`: `tmi_ids`, `tmi_notes` (the `atu_inline` field), `tmi_aliases`
- from `atu.json`: `atu_ids`, `atu_defining`, `atu_aliases`, `atu_summaries`, `aath_to_atu` (from `concordances`)

The **one** structure not persisted is **`atu_seq`** (tale type → ordered TMI motif codes; a
separate return of `trilogy.build_atu`, consumed only by `crosswalk.build`).

So the concrete tasks:

1. **Persist `atu_seq`** into `atu.json`. ✅ **DONE** — `sources.trilogy.build_atu` now embeds
   `atu_seq` in the returned index (still returns it separately for the monolith). It appears in
   `atu.json` on the next rebuild; older indexes read `{}` until then.
2. **`load_indexes() → derived`** — re-project the structures crosswalk/parallels need from the
   stored JSONs. ✅ **DONE** — `motifs.derive` (`derived_from_indexes` / `load_indexes`),
   validated **deep-equal** to the monolith's inline derivation on the real indexes. Not yet
   wired into `build_motifs` (that happens with the split, so it can be rebuild-validated).
3. **Persist enrichment summaries** per source (skip status + counts). ✅ **DONE** — each source
   writes a `<source>.enrichment.json` sidecar; `_aggregate_enrichment` merges them for the meta
   degradation guard (`trusted`/`fetch_outcomes`).
4. **Partition the raw cache by source** for the per-source fps. ✅ **DONE** — `fingerprint._SOURCE_RAW`
   + `source_fingerprint(source)` hash only that source's raw slice + config + algo; isolated so
   one source's change never moves another's.
5. **`meta` as a final aggregator stage**. ✅ **DONE** — `_build_meta` recomputes counts/sources from
   the indexes + config and reads crosswalk/parallels tallies from disk; no in-memory handoff.
6. **Author the stages + retire the coarse gate.** ✅ **DONE** — `SourceStage`×3 (self-contained
   `BerezkinSource`/`TmiSource`/`AtuSource`) → `CrosswalkStage` → `ParallelsStage`/`SemanticStage`
   → `MetaStage`, each gating on its own `.fp.<stage>` sidecar, wired via `motifs_stages()`. The
   coarse `MotifsStage` + `motifs_fingerprint` are removed. **Partial:** the `build_motifs`
   *orchestrator* survives as the wholesale re-fetch helper (`scripts/fetch_motifs_raw.py`) — fully
   removing it needs the parse-discovery-on-refresh edge below (§8), since it is the only path that
   fetches parse-discovered pages (berezkin details, ashliman/mapsofmyths nodes) in one pass.
7. **Per-source staged `refresh`**. ✅ **DONE** — `motifs/refresh.py` (staged diff/keep-pinned/adopt
   over `Fetchable` descriptors), each source module owns its own `fetchables()` (decentralised, so
   a module can be dropped and forgotten), each `SourceStage.refresh()` composes only the modules it
   owns, and `mytho refresh motifs[:source:X]` fans out per-source with the §9 table. Replaces the
   wholesale `build_motifs(force=True)` stopgap.

**All done.** The **ashliman** offline-determinism edge is resolved: the shared fetch layer has a
frozen-offline mode (`MYTHO_OFFLINE`, `fetch_cache.offline()`) that serves the pinned cache only —
never fetching or mutating it — and the golden validator sets it, so the rebuild is a pure function
of the pinned raw (two offline asserts byte-identical). The staged refresh is validated live
end-to-end on the `tmi` source (fetch → diff → keep-pinned → adopt-on-`--apply` → atomic commit →
self-heal). The `build_motifs` **orchestrator is now retired**: the driver-sequenced `motifs:*`
stages *are* the build, `scripts/fetch_motifs_raw.py` drives them (cold cache → each stage
acquires on miss), and the final cross-index summary moved into `motifs:meta`. Only the `_build_*`
stage helpers remain in `motifs.build_motifs`. A forced re-fetch of an already-pinned cache is
`mytho refresh motifs --apply` (the networked re-check path), not a build flag.

## Validation

With a raw cache present: `golden_diff snapshot` → refactor → `golden_diff assert`, dropping
`meta.json`'s `built_at` and the network best-effort enrichment fields (as the corpus catalog
drops `date_downloaded` / `source_fp`). The deterministic core (`berezkin/tmi/atu/crosswalk/
parallels.json`) must be byte-identical — validated byte-identical through every step above
(`scripts/validate_motifs_atomisation.py`).

## Guarantees & gaps (fetch/refresh audit)

An audit of what the fetch/refresh/build layer does and does not guarantee about corruption,
data loss, and network-update completeness. Ground truth for the "is my raw safe / am I seeing
all upstream changes" question.

### Guaranteed

- **Atomic single-file writes.** Every raw write goes through `commit_bytes` (`fetch_cache.py`):
  stage to a **unique** `.partial` (`mkstemp`) → `os.replace`. A crash mid-write leaves an inert
  `.partial`, never a half-written live file. Build-fetch and refresh-adopt share this one path,
  so a torn file is impossible.
- **Validate-before-commit.** A fresh reply must pass `validate()` + a non-empty check *before*
  it may overwrite the pinned copy (`fetch_to_cache`, `refresh_fetchables`). Empty body / HTML
  error stub / bad CSV/JSON → `FetchRejected`/`DEGRADED`, pinned copy untouched.
- **Keep-pinned-on-failure.** Transport error / 404 / degraded → the last-good pinned copy is
  kept and served; good raw is never deleted over an upstream disappearance (Phase 0). A 404 on a
  never-cached page is remembered in a `.absent` marker (not re-probed); a 404 on a *pinned* page
  keeps + serves it.
- **Build never overwrites raw.** `fetch_to_cache(..., force=False)` is hardcoded in the builder;
  `--force` only re-derives from pinned raw. A build cannot clobber raw with a bad network reply —
  it reads raw, it does not refresh it.
- **Refresh never blind-overwrites.** Keep-pinned by default; adopt only on `--apply`, via the
  same atomic `commit_bytes`. Ephemeral: a pending `changed` re-derives from upstream-vs-pinned.
- **Reproducible rebuild.** `MYTHO_OFFLINE` serves pinned only; the golden-diff validator asserts
  the deterministic core rebuilds byte-identical from pinned raw.

### Not guaranteed

- **Durability against power loss (no `fsync`).** `os.replace` gives atomicity (no torn file) but
  the write path calls no `fsync` on the file or its directory. A power cut between write and
  physical flush can lose a just-adopted byte-set (falling back to the old pinned copy — still not
  corrupt). No *corruption*, but *durability* of a fresh adoption is not guaranteed.
- **Cross-file transactionality.** Each file is atomic; there is no whole-set snapshot. An
  interrupted run leaves a mix of old + new files. Fine for independent idempotent sources, but
  not all-or-nothing.
- **Structural 200-error detection.** Validators are deliberately lenient (non-empty + has markup
  / parses as CSV/JSON). A well-formed HTML error page served with 200, or a plausibly-structured-
  but-wrong payload, passes `validate` and *can* be adopted over good pinned data on `--apply`.
  Catching it needs a per-source semantic parser (deferred).

### Will the user see all network updates?

Through `refresh` alone — **no**. Coverage by change type:

| upstream change | caught by `refresh`? |
|---|---|
| content of an **already-pinned** page changed | ✅ yes (`changed` → adopt on `--apply`) |
| a page **404s** | ✅ yes (`gone`, pinned kept) |
| a **new** page on a parse-discovered source (new ATU type, berezkin detail, mapsofmyths node) | ❌ no |
| a page **de-linked from the index but still 200** | ❌ no (re-checks as `not changed`) |

The refresh resource set = whatever is already pinned (`walk_fetchables`); refresh has no
discovery. A never-pinned new page is invisible to it. New pages are found only by re-crawling the
index — which lives in build, and a plain build reads the *pinned* index (`force=False`) so it
surfaces the same old set. New members appear only under a **forced wholesale re-scrape**
(`force=True` → `scripts/fetch_motifs_raw.py`), which re-fetches and re-parses the index. So:

- changes **within the known set** (content edits, disappearances) — refresh covers fully;
- changes to **set membership** on discovery sources (new pages, de-links) — no routine path
  covers them; only a forced re-scrape does.

This is exactly the discovery-on-refresh edge (§8): closing it (the `expand`-descriptor design)
would let `refresh` own discovery, at which point the forced re-scrape — and `MYTHO_OFFLINE`'s
load-bearing role — both retire.
