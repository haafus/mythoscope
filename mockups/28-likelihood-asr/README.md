# 28 · Likelihood ASR (roadmap M28)

Upgrades Method B (mockup 18) from Fitch **parsimony** gain-counting to a 2-state
continuous-time Markov (Mk) **gain/loss** model with marginal ancestral-state reconstruction
by belief propagation (inside/outside sum-product). Rates are fit globally with a **loss bias**
(Dollo-flavoured). Per motif it yields the *expected* (continuous) number of independent 0→1
gains — a probabilistic homoplasy estimate — instead of a hard minimum.

The model is run **twice**: on the *undated* tree (unit branches) and on a **family-scaled
dated tree** wired from mockup 30 (the M30→M28 payoff).

## What it shows

- **Undated ≈ parsimony.** On unit branch lengths the likelihood model largely **reproduces
  parsimony** — `corr(parsimony gains, expected gains) = 0.91`. The genuinely new thing here is
  the *probabilistic* output and the loss-vs-gain split (K25 swan-maiden: parsimony needs **120**
  independent origins; the loss-biased model expects far fewer, explaining scattered presence as
  **loss from a common ancestor** — something parsimony cannot represent).

- **Dating (M30) turns family ceilings into node ages — for concentrated motifs.** Each
  top-level family is given a calendar root age from mockup 30's `FAMILY_DATES` (matched via the
  modal Glottolog family of its traditions; 95% tradition coverage, undated families take a
  3.5 kyr default), internal branches are scaled by node height, and `P(t) = expm(Q·t)` runs per
  branch. Result: **778 motifs concentrated in their dominant family (conc ≥ 0.5) get a
  node-level origin age, median ≈ 1833 BP, and every one sits BELOW its family-root ceiling** —
  exactly what mockup 31 predicted an RRW would find (the within-family spread is younger than
  the family root). Examples: **B4** (fished-out earth) → **1733 BP** node age vs the **5200 BP**
  Austronesian ceiling; **Cinderella (K57)** → **3667 BP** vs proto-IE 5500; **tar-baby** →
  **4000 BP** vs 6000.

## Honest limit — read the node age *with* concentration

The node age is a real origin **only for a motif concentrated in its dominant family**. For
areal, low-concentration motifs (K25 swan-maiden, A3 sun & moon — conc ≈ 0.15) the model returns
the **proto-family age of the inherited sliver only** (both → 5500 BP, proto-Indo-European) —
*not* the origin of the whole, mostly-areal motif. A tree-only ASR can date an inherited core
but is **blind to the diffuse tail**; long deep branches + the Dollo loss-bias even pull areal
motifs toward spurious "deep-present-then-lost" (their expected gains drop, e.g. K25 45 → 10).
This is precisely the deep-vs-diffuse conflation that the areal channel (mockups 19 / 31) and the
connectivity layer (roadmap **M34**) exist to resolve. The `conc` column is the honesty guard.

Also: the branch scaling is a **topology-proportional proxy**, not real divergence times; a
genuine relaxed-random-walk (BEAST) on a truly dated tree with an uncertainty cloud stays future
work (mockup 31's limit).

## Run

```bash
python mockups/28-likelihood-asr/build_data.py   # writes data.js — SLOW (~6 min: inside/outside per motif, ×2 modes)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/28-likelihood-asr/
```

`data.js` is git-ignored. Reads `outputs/motifs/` + mockup 30's `FAMILY_DATES` and
`glottolog_join.json`.
