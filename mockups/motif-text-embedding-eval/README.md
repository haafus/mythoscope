# Motif ↔ source-text embedding — grid experiment

Answers, on real data, two design questions for embedding motifs to match them
against source texts:

- **What goes in the motif embedding?** name only / name + summary / name + summary
  + hierarchy path.
- **How is the text represented?** whole tale (one vector) / passage chunks
  (max-similarity over chunks).

## Gold set

Ashliman's *Folktexts* pages: each cached `type{N}.html` is a set of real tales that
instantiate **ATU type N**. Every anchor-delimited tale becomes one `(atu_id, text)`
pair; label leakage ("Aarne-Thompson type N", editor boilerplate) is stripped. About
**1,500 tales across ~165 types**. For each tale we rank *all* ~2,240 ATU types by
embedding similarity and score whether the true type lands near the top.

No labels are in the tale text, so this is an honest retrieval eval — not a lookup.

## Run

```bash
PYTHONPATH=src .venv/bin/python mockups/motif-text-embedding-eval/run.py \
    --model BAAI/bge-m3 --max-tales 400
```

- `--model` — any sentence-transformers backbone. Default `BAAI/bge-m3` (the one the
  app already uses); swap in a small model (e.g.
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) for a fast pass.
- `--max-tales` — deterministic stride subsample of the gold for speed.

Prints a grid of **recall@1/5/10, MRR, median rank** and writes `results.json`.

## What it measures / caveats

- Metric is single-label (a tale's page-type). A tale often instantiates several types,
  so absolute recall is modest by construction — read the numbers **relatively**
  (which composition wins), which is the point.
- Candidates are all ATU types (realistic distractors), not just the 165 with gold.
- The **LLM-decomposition axis** from the design discussion (decompose a tale into
  per-scene motif-like statements, embed those) is *not* wired here — it needs an API
  key and the project's LLM config. It's the natural next stage: use these embedding
  configs for high-recall candidate retrieval, then an LLM layer for precision.

## Early finding (small-model pass)

`name + summary` beats `name` alone by a wide margin; **adding the hierarchy path
hurts** (it pulls the vector toward abstract classificatory space, away from the
narrative); chunks edge out the whole-tale vector. See `results.json` for the run's
numbers and the repo discussion for the reasoning.
