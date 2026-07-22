# scripts/

One-off / offline maintenance scripts, **separate from the `mytho` CLI pipeline**.
Run from the repo root with the project installed (`pip install -e ".[all]"`) and a
built motif DB (`mytho motifs`) present.

- **`build_semantic_parallels.py`** — precompute the BGE-M3 semantic-parallel
  suggestion layer offline. Deliberately *not* part of `mytho motifs` (the model is
  ~2 GB and CPU inference is slow). Embeds every motif and writes the committed
  `src/motifs/data/semantic_parallels.json`, which the app copies into
  `outputs/motifs/` on first read — so the running app needs neither the model nor
  `sentence-transformers`. Needs `sentence-transformers`; embeddings cache to
  `outputs/motifs/raw/bge_m3.npy` (the first run is the slow one).
  → `python scripts/build_semantic_parallels.py`

## Region / data-model migration (region-implementation.md §6)

One-off, **offline, reversible** migration of an *existing* build to the region data-model
(`document_id = blake2b(locator)`, region tree, B1 chunk). It **re-keys the raw archive in
place — no re-fetch** — then rebuilds all derived artifacts. Raw is preserved, so a dead/404
source can't lose data, and the whole thing rolls back via `git` (config/code) + renaming raw
back. Only `config/` and `sources/` must be committed; `corpus/raw/` is a cache.

**Run order (from the repo root):**

```
python scripts/migrate_region.py            # DRY RUN — preview baseline/wipe/re-key
python scripts/migrate_region.py --apply    # baseline → wipe derived (keep raw/) → re-key raw
mytho build                                 # rebuild everything off the re-keyed raw (offline)
python scripts/validate_migration.py        # gate a–d (must all PASS)
mytho status                                # expect zero orphans
```

Want to skip re-paying the GPU/LLM rebuild on a rollback? Copy `outputs/` aside before `--apply`.

- **`migrate_region.py`** — the orchestrator. Dry-run by default; `--apply` runs the offline
  prep (baseline snapshot → wipe derived, keeping `corpus/raw/` → re-key). It never triggers
  the heavy `mytho build` itself — that stays your explicit step.
- **`rekey_raw.py`** — config-driven raw re-key `sha1(url) → blake2b(locator)`, in place,
  offline. Dry-run by default; `--apply` renames + writes `corpus/raw/.rekey-manifest.json`.
  Idempotent; a doc with no raw is left for the build's acquire-on-miss.
- **`validate_migration.py`** — the gates. `--capture-baseline` records pre-migration counts
  (the orchestrator calls it); no flag runs gates (a) re-key byte-integrity · (b) fail-loud
  model (tradition ∈ tree, region ∈ 14 canon, name-uniqueness, no `document_id` collision) ·
  (c) counts vs baseline · (d) zero orphans.

- **`build_tmi_bibliography.py`** — rebuild the TMI citation key standalone and
  regenerate the committed doc [`docs/motifs/tmi-bibliography-key.md`](../docs/motifs/tmi-bibliography-key.md).
  The key itself is produced by the normal pipeline
  (`motifs.sources.bibliography`, as `mytho motifs` runs); this wrapper additionally
  writes the human-readable doc. Re-fetches the folkmasa page unless already cached
  under `outputs/motifs/raw/`; needs a built `tmi.json`.
  → `python scripts/build_tmi_bibliography.py`
