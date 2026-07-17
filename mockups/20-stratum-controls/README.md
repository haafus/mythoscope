# 20 · Stratum controls (sampling + banality)

Applies the two mandatory §5 controls from
[`stratum-derivation.md`](../../docs/proposals/archive/stratum-derivation.md) that mockups
17–19 skipped, and measures **how much the estimate moves** once they are on. It re-runs
the mockup-19 gated A × B estimator, then corrects.

## 1 · Attestation-intensity (the single biggest fix)

Tradition coverage `a(t)` = #motifs recorded — ranges **1 … 738** (median 74). A
densely-catalogued tradition records almost any motif, so a presence there is *cheap*
evidence; a presence in a thinly-covered tradition is *costly* and informative. So raw
breadth partly measures catalogue density, not age (axiom 11).

Correction: weight each present tradition by baseline-equivalent coverage
`w(t) = median / a(t)` (capped at 2), and count a macro-area toward "breadth" only where
the motif carries **≥ 1 baseline-equivalent** of evidence. Then re-gate on that effective
breadth.

> A degree-preserving **configuration null** (`q = r_m·c_t/G`) was tried first and
> **rejected**: conditioning on the motif's own frequency `r_m` is circular for our
> purpose (we *want* to keep real breadth) and it nuked genuinely broad motifs — sun & moon
> collapsed to `areal-recent`, 84% breadth shrink. The coverage weight is milder and
> non-circular.

## 2 · Banality / homoplasy

A proxy `banality = ½·(generic-definition) + ½·(singleton-scatter)` — short definitions
and motifs whose presences are lone attesters in their macro-area — flags motifs whose
"depth" is more likely independent reinvention than descent. It is a **warning, not a
re-gate**.

## What it shows

- **Breadth shrinks 31%; 504 motifs (15%) change mode.** Most of the churn is
  `areal-broad → areal-recent` (344 motifs): breadth that was catalogue density.
- **The deep, both-hemisphere class survives — 320 / 480.** It is *not* an artefact of
  sampling, because spanning Indo-Pacific **and** the New World needs real disjunct
  evidence. This is an empirical restatement of **axiom 4**: cross-barrier disjunction is
  a stronger antiquity signal than sheer breadth, which contact manufactures quickly.
- **Sun & moon (A3) and swan-maiden (K25) stay `areal-deep`** (effective macro 15/16) —
  genuinely broad. **Cinderella / tar-baby drop to `areal-recent`** — their breadth was
  partly density.
- **Banality flags the celestial "X is Y" etiologies** (Ursa-major-is-a-boat, clouds-from-
  smoke, stars-are-sparks): short, cognitively easy, scattered — exactly the homoplasy
  candidates the depth score should discount before calling them ancient.

## Takeaway for the estimator

The controls do not overturn mockup 19 — the deep-disjunct spine holds — but they thin
the "broad areal" middle by more than half and expose a homoplasy-prone celestial set.
Both belong in any production `stratum`: the sampling weight is the single biggest
correctness fix, and the banality flag keeps easy-to-reinvent motifs out of the deep tail.

## Run

```bash
python mockups/20-stratum-controls/build_data.py   # writes data.js (~10 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/20-stratum-controls/
```

`data.js` is git-ignored.
