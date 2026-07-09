# 19 · Combined stratum (gated A × B)

Realises [`stratum-derivation.md`](../../docs/motifs/proposals/stratum-derivation.md) §12
— the integration of Method A (geography, mockup 17) and Method B (phylogeny, mockup
18) into **one gated pipeline**, not two separate scores.

For each motif: **B** (phylogenetic signal on the language tree) decides the *mode* —
descent (clustered on the tree) vs areal — and the mode picks the dating instrument:

- **descent** → dated by **clade depth** (Neolithic-era language expansions);
- **areal** → dated by **geography** — spanning both hemispheres (Indo-Pacific + New
  World) = deep Pleistocene substrate; compact single set = recent diffusion.

Output: a stratum **mode**, a depth score, and a **confidence from A/B agreement**.

## The payoff

The "broad" motifs that neither method could resolve alone **split three ways**:
`areal-deep` (480) / `descent` (32) / `areal-broad` (577). Method A alone called every
broad motif deep; Method B alone called them all areal; the gate separates them.

- **B4 fished-out earth → descent** (an Austronesian clade) — *not* the "deep disjunct"
  A would wrongly infer from its stray New-World occurrence.
- **A3 sun & moon, K25 swan-maiden → areal-deep**, but at **moderate confidence (~0.72)**:
  telling a deep substrate from a broadly-diffused motif is the irreducible residual.
- **Jonah → local** (too narrow), **Cinderella / tar-baby → areal-broad at low
  confidence (~0.3)** — correctly flagged as borderline.

## Theme is deliberately NOT an input

Feeding `theme` into the estimator would be **circular** — it would manufacture the very
`theme × stratum` correlation we want to test. So the gate is purely distributional, and
theme stays a separate axis used only as an **independent cross-check**. It corroborates
strongly: Category-A (cosmology) share falls from **64%** in `areal-deep` to **24%** in
`descent` — a real gradient, because theme was never used to build the modes. (Nor does
theme resolve the A3-vs-K25 residual: both are Category A, so that split needs external
calibration, not theme.)

## Run

```bash
python mockups/19-combined-stratum/build_data.py   # writes data.js (~10 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/19-combined-stratum/
```

`data.js` is git-ignored.
