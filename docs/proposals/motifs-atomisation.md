# Motifs atomisation — the granular per-source split (deferred)

Stage IV atomised corpus / embeddings / graphs / projections onto the driver. **Motifs is
still a monolith** (`build_motifs`), fronted by a coarse input-fp gate (`motifs:` singleton,
`motifs_fingerprint` = raw cache + config + `MOTIFS_ALGO_VERSION`, stamped to
`outputs/motifs/.fp`). That already stops it rebuilding every run. This document is the plan
for the full granular split into the stages the pipeline spec (§2.2) describes.

## Why it is deferred

The split cannot be **validated** in a network-less / raw-cache-less environment: `build_motifs`
needs either the network or a populated `outputs/motifs/raw/` scrape cache. With that cache
present it builds offline and the core artifacts (`berezkin/tmi/atu/crosswalk/parallels.json`)
are deterministic and golden-diffable (excluding `meta.json`'s `built_at` + the network
best-effort enrichment fields). **Prerequisite: a raw-cache snapshot in the build environment.**

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

**All done.** Remaining edge (§8, `fetch-and-refresh.md`): the golden validator's rebuild is not
fully offline for **ashliman** (its `discover_site_types` fetches discovery pages live and writes
them into the "pinned" cache, so `atu.json` can drift across network conditions — re-snapshot after
the cache settles). Fully retiring the `build_motifs` orchestrator waits on making parse-discovered
fetch fully pinnable so refresh alone can cold-acquire a source.

## Validation

With a raw cache present: `golden_diff snapshot` → refactor → `golden_diff assert`, dropping
`meta.json`'s `built_at` and the network best-effort enrichment fields (as the corpus catalog
drops `date_downloaded` / `source_fp`). The deterministic core (`berezkin/tmi/atu/crosswalk/
parallels.json`) must be byte-identical — validated byte-identical through every step above
(`scripts/validate_motifs_atomisation.py`).
