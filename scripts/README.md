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

- **`build_tmi_bibliography.py`** — rebuild the TMI citation key standalone and
  regenerate the committed doc [`docs/motifs/tmi-bibliography-key.md`](../docs/motifs/tmi-bibliography-key.md).
  The key itself is produced by the normal pipeline
  (`motifs.sources.bibliography`, as `mytho motifs` runs); this wrapper additionally
  writes the human-readable doc. Re-fetches the folkmasa page unless already cached
  under `outputs/motifs/raw/`; needs a built `tmi.json`.
  → `python scripts/build_tmi_bibliography.py`
