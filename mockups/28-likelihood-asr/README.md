# 28 · Likelihood ASR (roadmap M28)

Upgrades Method B (mockup 18) from Fitch **parsimony** gain-counting to a 2-state
continuous-time Markov (Mk) **gain/loss** model with marginal ancestral-state reconstruction
by belief propagation (inside/outside sum-product). Rates are fit globally with a **loss bias**
(Dollo-flavoured: loss ≈ 8× gain). Per motif it yields the *expected* (continuous) number of
independent 0→1 gains — a probabilistic homoplasy estimate — instead of a hard minimum.

## What it shows

- **Honest limit:** on the undated classification tree (unit branch lengths) the likelihood
  model largely **reproduces parsimony** — `corr(parsimony gains, expected gains) = 0.90`. That
  is precisely the motivation for **M30**: the real payoff (calendar ages, sharp ASR) needs a
  *dated* tree. What is new already is the *probabilistic* output.
- **The qualitative upgrade — loss vs independent gain.** For the swan-maiden (K25) parsimony
  needs **120** independent origins; the loss-biased model expects only **~20**, because it can
  explain scattered presence as **loss from a common ancestor** rather than a hundred
  reinventions — something parsimony cannot represent. Distinguishing loss from convergence is
  the genuine methodological gain (also visible for A3: 110 → 38).

## Takeaway

Likelihood ASR confirms Method B's picture and adds probabilistic ancestral states and a
loss/gain decomposition, but on an undated topology it does not move the aggregate. It is
best run **after M30** wires in branch dates; committed here so the machinery (pruning +
inside/outside, Dollo rate fit) is ready.

## Run

```bash
python mockups/28-likelihood-asr/build_data.py   # writes data.js — SLOW (~3 min: inside/outside per motif)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/28-likelihood-asr/
```

`data.js` is git-ignored. Reads only `outputs/motifs/`.
