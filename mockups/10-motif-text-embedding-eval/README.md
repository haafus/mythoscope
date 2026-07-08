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

## Result

Realistic pass — `paraphrase-multilingual-MiniLM-L12-v2`, 250 tales, all 2,242 types
as candidates (recall@k / MRR / median rank):

| config | r@1 | r@5 | r@10 | MRR | med.rank |
|---|---|---|---|---|---|
| **name+summary × chunks** | 0.164 | **0.30** | 0.364 | 0.228 | 36 |
| name+summary × whole | 0.164 | 0.276 | 0.332 | 0.221 | 49 |
| name+summary+hierarchy × chunks | 0.10 | 0.232 | 0.284 | 0.170 | 51 |
| name+summary+hierarchy × whole | 0.132 | 0.228 | 0.28 | 0.184 | 79 |
| name × whole | 0.072 | 0.156 | 0.204 | 0.118 | 301 |
| name × chunks | 0.072 | 0.14 | 0.216 | 0.118 | 137 |

Reading:
1. **The summary is the big win** — `+summary` roughly doubles recall over `name`
   alone. Include the definition/summary whenever it exists.
2. **The hierarchy path hurts** — it pulls the vector toward abstract classificatory
   space, away from the narrative surface the text lives in.
3. **Chunks edge out the whole-tale vector** (and give a much better median rank) —
   one vector per tale blurs its many motifs together.

Numbers are single-label recall, so read them **relatively**; the ordering is a
property of the composition and is expected to hold across backbones.

### On BGE-M3

`--model BAAI/bge-m3` is the app's real backbone, but it's an XLM-Roberta-large and
**too slow to finish this grid on CPU** (encoding 2,242×3 candidates times out; memory
is fine, it's compute). Run it on a GPU box — it will raise the absolutes but is very
unlikely to flip the ordering above. `--max-candidates` shrinks the distractor pool to
let a heavy model finish, at the cost of eval realism.
