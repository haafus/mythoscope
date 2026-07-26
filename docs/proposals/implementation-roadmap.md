# Implementation roadmap — order across the five proposals

> ### ⚠️ OPEN FOLLOW-UPS — still to fix (do not forget)
> Flagged items with a settled design but **not yet implemented**. Full write-ups linked; the
> register is [`known-issues.md`](../known-issues.md).
>
> 1. **Embeddings completeness** (HIGH, data-integrity). `EmbeddingsStage.actual()` reports a
>    **partially-embedded document as clean**. Fix: store `n_chunks` per chunk; a doc is built iff
>    `count(fp) == n_chunks`; backward-compat fallback ⇒ **no rebuild**. Reasoning + checklist:
>    [`embeddings-completeness.md`](embeddings-completeness.md).
> 2. **Discovery-on-refresh** (narrow). New **base motifs** (TMI/ATU/Berezkin index) *are* caught by
>    `refresh --apply` + `build` (each index is a single pinned file) — no `--force`. The real gap:
>    new **enrichment** pages on self-index-crawling sources (a new ashliman type page, a mapsofmyths
>    node) for an unchanged base entry lag until a forced re-crawl — only the secondary annotation,
>    not the motif. Fix: recursive `expand: bytes -> [Fetchable]` descriptor so the engine owns
>    enrichment discovery (also retires `MYTHO_OFFLINE`'s load-bearing role). Audit + mechanism:
>    [`motifs-atomisation.md`](motifs-atomisation.md) ("Guarantees & gaps", §8).
> 3. **No `fsync` in the raw write path**. `commit_bytes` is atomic (`os.replace`) but not
>    power-loss durable. Fix (if wanted): `fsync` temp + parent dir before/after replace.
> 4. **Lenient validators**. A structured HTML/`200` error page can be **adopted over good pinned
>    data** on `refresh --apply`. Fix: per-source semantic validator as the adopt gate.
>
> Items 2–4 are detailed in [`known-issues.md`](../known-issues.md); item 2 is the headline
> "won't see all updates" gap.

The consolidated build order for the pipeline/data/fetch redesign. It sequences every phase of every proposal
by the **reversibility ladder**: code and additive data first (freely revertible), the heaviest step (the Part 1
§6 rebuild) as late as possible and only once the code around it is proven. Source of truth for *what* each phase
does stays in the individual proposals linked below; this doc owns *the order and why*.

Guiding rule: **the fear is proportional to irreversibility — and after the re-key decision, nothing here is
truly one-way.** The Part 1 §6 migration is the *heaviest* step (a full re-embed/re-graph), but **reversible**:
raw is **re-keyed in place** (a `sha1→blake2b` rename, no re-fetch — reverse it by renaming back), derived is
wiped and recomputable, and `config`/code roll back via git. Nothing pre-existing can be lost (no network in the
migration; a dead source only bites a *genuinely-new* doc, as a normal flag). The pre-migration snapshot is a
*convenience* — it saves re-paying the GPU rebuild on a rollback, not a guard against data loss. Everything else
is `git revert` or a recompute.

---

## All phases (source proposals)

- **[`motifs-fetch-stabilization.md`](motifs-fetch-stabilization.md)** — Phase 0 remove the two `unlink`s ·
  1 staging+validator in `fetch_cache.py` · 2 fix the two deleters · 3 surface degradation (yield / discovery /
  high-water) · 4 flags (`meta.flags`) · 5 tests. *(Applies the canonical
  [`fetch-and-refresh.md`](fetch-and-refresh.md) model.)*
- **[`region-implementation.md`](region-implementation.md) — Part 1** (§5 + §6) — 1 `config/traditions.json` +
  validation · 2 `document_id = hash(locator)` · 3 front indexes before the trim · 4 retire `major_tradition` →
  region + B1 chunk · 5 colour from region, serve the config · 6 cleanup + graphs build/serve unify · **§6 the
  data migration** (wipe derived → offline re-key raw `sha1→blake2b` → plain build rebuild → front in lockstep → verify
  `status`).
- **[`pipeline-and-incrementality.md`](pipeline-and-incrementality.md) — Part 2** (incrementality base) —
  1 embeddings content-fp gate · 2 `transform_version` · 3 atomicity (`os.replace`) · 4 fetch/build split +
  refresh + pin raw · 5 graphs build/serve unify + traversal guard.
- **Part 3** (stage-protocol refactor) — 1 atomise stages · 2 generic driver + retire `pipeline_inspect` /
  `cli._clean` · 3 DVC/Dagster re-eval (decision only) · 4 scope · 5 rewire `export_bundle`.
- **Part 4** (manual text curation) — override layer + `curate`. **⏸ PAUSED — not now.**

---

## The order — by the reversibility ladder

### Stage I — Motifs stabilization *(isolated · code + additive data · nothing irreversible)* — ✅ DONE

The confidence starter: motifs are **independent of the corpus data**, so the whole `fetch-and-refresh` model is
proven on low-stakes territory first.

1. motifs **Phase 0** — remove the two `unlink`s ← *first safe move; zero functional change, one-command revert*
2. motifs **Phase 1** — staging + validator in `fetch_cache.py` *(also hardens the shared layer corpus uses)*
3. motifs **Phase 2** — fix the two deleters (keep pinned + flag)
4. motifs **Phase 3 + 4** — surface degradation + durable flags
5. motifs **Phase 5** — tests

**Verify** — **build:** `build motifs` (cheap, from the raw cache — no re-scrape). **Check:** the Motifs section
renders; index/cross-walk counts are sane; degradation/flag machinery writes to the log + `meta.flags` /
`meta.highwater` and self-initialises (no spurious `yield-drop` on first run); tests + lint green. *Front: the
Motifs section only.*
**Validate:** *covered by tests* — the Phase 5 `test_motifs.py` cases (kept-cache-on-404, degraded-keeps-cache,
`yield-drop` fires) **are** the acceptance gate; no separate script.
**Review:** light — `/code-review` on the stage diff + green tests.

### Stage II — Part 2 incrementality base *(code + fp sidecars · before the migration)* — ✅ DONE

Land the fingerprint + atomicity machinery **before** the data migration, so the rebuild writes fingerprints in
one pass (no separate backfill — this is the "Part 1 + 2 together" optimisation).

6. Part 2 **item 3** atomicity (`os.replace`) *(reuses the staging pattern from motifs Phase 1)* — ✅ `corpus.json`
   via the atomic `save_json`; `.fp`-bearing writes already atomic.
7. Part 2 **item 2** `transform_version` — ✅ `embeddings/transform.py` (param-hash + manual `EMBED_ALGO_VERSION`),
   folded into the chunk fingerprint.
8. Part 2 **item 1** embeddings content-fp gate — ✅ stored per-chunk fingerprint compared vs
   `hash(doc fingerprint, transform_version)`; doc `fingerprint` = `blake2b(cleaned text)` in the catalog; the
   decision is the pure `embed_plan()`. *(rename-churn half still awaits Part 1's `document_id` anchor.)*
9. Part 2 **item 4** fetch/build split + `refresh` + pin raw — ✅ `--force` no longer re-fetches (raw pinned);
   new `mytho refresh [documents|motifs]` (staged diff, keep-pinned, `--apply`). *(Documents are fully staged;
   `refresh motifs` is still a crude wholesale re-scrape — the per-source staged refresh / source-unit layer
   rides the motifs source-stage split, tracked as task 7 in [`motifs-atomisation.md`](motifs-atomisation.md).)*
10. Part 2 **item 5 = Part 1 step 6** graphs build/serve unify + traversal guard — ✅ one `graphs.store.graph_dir`
    used by build + serve, with `sanitize` + `is_relative_to` confinement.

**Verify** — **build:** tests + a tiny end-to-end (embed 2–3 docs on the *current* scheme — the old data is
still in place). **Check:** the fp gate behaves — editing a doc's text re-embeds it, an unchanged doc is
skipped; `transform_version` bump re-embeds; `os.replace` writes are atomic (no half-written catalog on a kill);
graphs build == serve. *Front: unchanged — smoke-check it still loads; no data-model change yet.*
**Validate:** *covered by tests* — the fp-gate behaviour tests (edit→re-embed, unchanged→skip, version→re-embed)
are the acceptance gate; no separate script.
**Review:** light — `/code-review` on the stage diff + green tests.

### Stage III — Part 1 data-model + region migration *(the heaviest step — but reversible via the re-key)* — code ✅ DONE; §6 migration = scripted, user-run

Now, with the code proven on motifs and fingerprints+atomicity in place.

11. Part 1 **steps 1–6** — ✅ **DONE** (code, committed): config + fail-loud validation · `document_id =
    blake2b(locator)` (+ corpus raw re-keyed to it) · front `treeIndex`/`docIndex` + resolution · region regroup
    + B1 chunk + endpoint renames + `$nin` filter · region-derived OKLCH colour · cleanup (graphs on
    `document_id`, one `UNASSIGNED`). Validated by 526 py + 17 JS tests and a live Playwright pass (9/9).
12. Part 1 **§6 migration** — ✅ **SCRIPTED** (`scripts/migrate_region.py` orchestrates: baseline → wipe derived
    → `scripts/rekey_raw.py --apply` config-driven `sha1(url) → blake2b(locator)` rename in place, no network) →
    plain `mytho build` (finds the re-keyed raw present, rebuilds **no re-fetch**) → `scripts/validate_migration.py`
    (gates a–d) → `status` zero orphans. Tested end-to-end on real data (offline rebuild succeeded). **Run by the
    user on their data** (the heavy GPU/LLM rebuild is never triggered silently). Reversible — raw re-keyed in
    place, derived recomputable, config/code via git. See [`../../scripts/README.md`](../../scripts/README.md).

**Verify** — **build:** the full rebuild of step 12 (offline re-key + re-embed + re-graph — no re-fetch). **Check (the deep one —
this is the only front-affecting stage):** region grouping and per-region colours; document resolution
(`document_id = hash(locator)`, titles, links); the renamed endpoints + dropped fields with `treeIndex` /
`docIndex`; every view that touched `major_tradition`; one `UNASSIGNED`; `status` = **zero orphans**; counts
match expectation. *Front: full, in lockstep with the API change.*
**Validate (script — high value, one-shot migration):** write `scripts/validate_migration.py` that gates the
transition: **(a) re-key byte-identity** — for each config doc, the renamed raw file's content hash is unchanged
(proves the re-key lost nothing and is invertible); **(b) the §6 fail-loud gate** — every corpus tradition ∈
tree, every region ∈ the 14 canon, name-uniqueness across region/tradition, `document_id` collision check;
**(c) counts vs a pre-migration baseline** — documents / chunks / graphs match (modulo intended changes);
**(d)** `status` = zero orphans. Run it right after step 12, before trusting the state.
**Review:** deep — `/code-review` the re-key script + `validate_migration.py` **before running step 12** (a bug wastes a full rebuild).
**Dead code:** `ruff` + `vulture` sweep after the step-6 removals (`_update_traditions`, `bookTitleFromId`, generated file); confirm dynamic refs before deleting.

### Stage IV — Part 3 stage-protocol refactor *(code-only · no data)* — ✅ DONE

Consumes Part 2's fp base; presupposes Part 1. Reverts via `git`.

13. Part 3 **items 1–2** — atomise stages + generic driver + retire `pipeline_inspect` / `cli._clean`
    *(✅ done: corpus/embeddings/graphs/projections **and motifs** on the driver — the motifs granular
    per-source split ([`motifs-atomisation.md`](motifs-atomisation.md)) shipped: 7 `motifs:*` stages
    with per-source fps, staged per-source `refresh`, the coarse `MotifsStage`/`motifs_fingerprint`
    and the `build_motifs` orchestrator retired, golden-diff byte-identical)*
14. Part 3 **item 5** — rewire `export_bundle` onto the driver *(done: `orphan_summary` on the driver; `mytho export [scope]`)*
15. Part 3 **item 4** — scope (stage / variant) *(done: positional `scope` on build/status/clean/export — force-rebuilds exactly the named stage)*
16. Part 3 **item 3** — DVC/Dagster re-eval *(done: **keep build-your-own** — [`pipeline-engine-comparison.md`](pipeline-engine-comparison.md) § Post-Part-3 decision)*

**Verify** — **build:** `status` then a `build` that should be a **no-op** (nothing stale after step 12), plus a
one-off cheap fp-init for anything Part 2 didn't fingerprint (projection refit / motif reassembly — no re-fetch,
no re-LLM). **Check:** `status` / `clean --dry-run` = zero orphans; the driver reproduces the *same* artifacts
(diff the outputs — a code refactor must not change data); `export` still bundles correctly; tests green. *Front:
unchanged — smoke-check.*
**Validate (script — high value, the refactor's one guard):** write `scripts/golden_diff.py` — hash **every
artifact** (`corpus.json` + `.txt` tree, Chroma vectors + metadata, `projections/*`, `graphs/*`, `motifs/*`)
**before** the Part 3 refactor, then **assert byte-identical after** (allowing only the intended fp-init
additions). An orchestration refactor **must not change data**; this single diff catches any drift the per-key
`status` cannot. **The exact snapshot → build → assert → reset → build → assert runbook (two passes, one
baseline) is in [`../stage-iv-validation.md`](../stage-iv-validation.md).**
**Review:** architectural — `/code-review` the stage diff for stage-protocol/design conformance; `golden_diff` guards behaviour.
**Dead code:** `ruff` + `vulture` sweep (biggest here — the driver retires `pipeline_inspect` + `cli._clean`); confirm the driver's dynamic `getattr(stage, "refresh")`-style refs before deleting.

### Stage V — Part 4 manual curation *(editorial · independent · last)*

**⏸ PAUSED — not now.** Blocks nothing; resume only when explicitly un-paused.

---

## Why this order

- **The heaviest step (12) is exactly one, and last-but-one** — after the code is proven on motifs (I) and the
  fp + atomicity rails are in place (II). Heaviest ≠ irreversible: the re-key makes it undoable.
- **Motifs first** — isolated from the corpus, cheap, and it proves the whole fetch/refresh/flag model before
  any corpus risk.
- **Part 2 before Part 1** — so the migration's rebuild writes fingerprints directly (no separate backfill).
- **graphs build/serve unify** appears in both Part 1 step 6 and Part 2 item 5 → done once, at step 10.
- **Nothing is truly one-way** — step 12 is reversible (raw re-key renames back, derived recomputes,
  config/code via git); the snapshot only saves re-paying the rebuild.

## Reversibility ladder (increasing commitment)

1. **code-only** (motifs Phase 0; Part 3) — revert in one command
2. **additive data** (flags in `meta`, `.fp` sidecars) — does not touch existing artifacts
3. **metadata backfill** (Part 2 fingerprints) — recomputable, loses nothing
4. **heavy but reversible rebuild** (Part 1 §6) — raw re-keyed in place (rename back to undo), derived
   recomputed; snapshot first only to skip re-paying the GPU rebuild on a rollback
