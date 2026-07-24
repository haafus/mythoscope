# scripts/

One-off / offline maintenance scripts, **separate from the `mytho` CLI pipeline**.
Run from the repo root with the project installed (`pip install -e ".[all]"`) and a
built motif DB (`mytho build motifs`) present.

- **`build_semantic_parallels.py`** — precompute the BGE-M3 semantic-parallel
  suggestion layer offline. Deliberately *not* part of `mytho build motifs` (the model is
  ~2 GB and CPU inference is slow). Embeds every motif and writes the committed
  `src/motifs/data/semantic_parallels.json`, which the app copies into
  `outputs/motifs/` on first read — so the running app needs neither the model nor
  `sentence-transformers`. Needs `sentence-transformers`; embeddings cache to
  `outputs/motifs/raw/bge_m3.npy` (the first run is the slow one).
  → `python scripts/build_semantic_parallels.py`

- **`build_tmi_bibliography.py`** — rebuild the TMI citation key standalone and
  regenerate the committed doc [`docs/motifs/tmi-bibliography-key.md`](../docs/motifs/tmi-bibliography-key.md).
  The key itself is produced by the normal pipeline
  (`motifs.sources.bibliography`, as `mytho build motifs` runs); this wrapper additionally
  writes the human-readable doc. Re-fetches the folkmasa page unless already cached
  under `outputs/motifs/raw/`; needs a built `tmi.json`.
  → `python scripts/build_tmi_bibliography.py`

- **`golden_diff.py`** — whole-corpus byte-identity guard for the Part 3 / Stage IV
  stage-protocol refactor. Hashes every build artifact (`corpus/`, `projections/`,
  `graphs/`, `motifs/` files + the pinned `raw/` caches; each Chroma collection's
  records + vectors logically) into a manifest. Snapshot **before** the refactor,
  assert **after** — the whole-corpus guarantee `mytho status` cannot give. `assert`
  fails on any changed/removed artifact; *added* files fail too unless they are
  fingerprint sidecars (`.fp` / `.input-fp`) or `--allow-added` is passed (the
  refactor's one intended fp-init). Manifest defaults to `outputs/.golden/manifest.json`
  (gitignored). Run from a built + region-migrated tree.
  → `python scripts/golden_diff.py snapshot` … refactor … `python scripts/golden_diff.py assert`

  A `reset` mode forces the **regeneration** path (not just the no-op steady state):
  it deletes the derived outputs + fp sidecars for the deterministic stages
  (`corpus`, `projections`, `graphs`, `motifs`) while **physically refusing** to touch
  the pinned caches (`raw/`, graphs' `extraction_cache.jsonl`), Chroma, or
  `preprocessed/`. A plain rebuild (no `--force`) then re-derives from those caches —
  no re-fetch, no re-LLM, and, because the embeddings fp gate still matches, **no
  re-embed**. Dry-run by default; `--apply` deletes. Scope with `--stages`.
  → `golden_diff snapshot` → `golden_diff reset --apply` → `mytho build` → `golden_diff assert`
