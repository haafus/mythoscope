# 24 · Effort-correction sweep (roadmap M24)

Tests **alternative-hypothesis #1** from
[`synthesis-and-directions.md`](../../docs/proposals/synthesis-and-directions.md) §4:
are our theme findings artifacts of catalogue density? Re-runs four headline results **raw
vs coverage-weighted** and gives each a verdict — *survives / weakens / flips*.

## The correction

One shared weight from [`_bias.py`](../_bias.py): `w(t) = min(2, median / a(t))` where
`a(t)` = #motifs recorded for tradition *t* (spans 1…738, median 74). It **downweights
over-catalogued corpora** and upweights thin ones (capped), moving every count toward
one-tradition-one-vote — the direct test of "do dense corpora manufacture the pattern?".

## Result — 3 of 4 survive

| Finding | raw → weighted | verdict |
|---|---|---|
| **A** · theme_profile variance explained by macro-area | 34% → **26%** | **weakens** |
| **B** · subsistence × theme (Category-A share) | forager 53→57, agrarian 39→47 (gradient holds) | survives |
| **C** · theme × area lift | Adventures×Europe 1.19→1.38, Sun&Moon×Australia 3.4→2.6 | survives |
| **D** · co-occurrence A/B blocks | within +0.29→+0.24, between −0.38→−0.34 | survives |

The one real casualty is **A**: when densely-catalogued corpora stop dominating, macro-area
explains *less* of the genre-balance variance (26%, not the ~38% mockup 16 reported). The
signal is real but was **over-stated** by sampling — exactly what the sweep exists to catch.
The subsistence gradient, the theme×area lift, and the A/B co-occurrence blocks all hold (some
even sharpen), so those findings are **not** sampling artifacts.

## What follows

Fold the weighting into the source mockups only where it matters: mockup 16's headline "38%"
should read "~26% after effort-correction". The rest keep their raw view as the default; the
corrected numbers are a robustness footnote, now backed by this sweep.

## Run

```bash
python mockups/24-bias-sweep/build_data.py   # writes data.js
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/24-bias-sweep/
```

`data.js` is git-ignored. Reads only `outputs/motifs/` + the committed D-PLACE derivative.
