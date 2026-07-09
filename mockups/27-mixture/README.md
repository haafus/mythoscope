# 27 · Descent / areal / reinvention mixture (roadmap M27)

Tests **alternative-hypothesis #2** (synthesis §4): maybe `stratum` isn't one ordinal axis —
a motif is a *mixture* of inheritance, areal diffusion and reinvention. Replaces mockup 19's
binary descent-vs-areal **gate** with a per-motif continuous decomposition into three shares
that sum to 1.

## Method — and one honest rejection

A per-tradition EM was tried first and **rejected**: for a broad motif "has a same-family
relative present" is trivially satisfied (Galton), so descent and areal are unidentifiable and
the mixture over-attributes to descent. Instead the decomposition is **motif-level**, anchored
in the *chance-corrected* phylogenetic signal (mockup 18), which does not saturate with breadth:

- **reinvention** = fraction of present traditions isolated (no same-family relative, no
  neighbour within 1500 km);
- **descent** = (1 − reinvention) · phylo_signal;
- **areal** = (1 − reinvention) · (1 − phylo_signal).

## What it shows

- **Most motifs are areal-dominant** (2311 of 2775), 460 descent-dominant, 4 reinvention — the
  continuum confirms "geography is primary" and puts numbers on it. Category B (tales) is
  slightly **more inheritable** (mean descent 35%) than Category A (cosmology, 28%), as the
  proposal claimed — tales ride language expansions more.
- **The tracked motifs come out right:** B4 fished-earth → descent 0.61 (Austronesian clade);
  Cinderella → 50/50 (a genuine descent-tracking European tale); trickster and the broad
  cosmology motifs → areal-dominant.
- **The continuum works but the residual does not dissolve.** A3 (sun & moon) and K25
  (swan-maiden) get **near-identical mixtures** (descent ≈ 0.16, areal ≈ 0.84) — the
  decomposition cannot separate "deep substrate" from "wide diffusion" *within* the areal
  share. That residual (stratum-derivation §12) is confirmed irreducible here too; it needs
  external calibration (a dated tree, M30/M31), not a finer distributional model.

## Takeaway

Replacing the gate with a continuum is the right move — it is honest about the ~50/50 tales and
about breadth — but it does not manufacture a resolution the data can't support. Alt-hypothesis
#2 is **partly upheld**: stratum is better modelled as a continuous mixture than a hard mode,
yet the deep-vs-diffuse ambiguity persists inside the areal component.

## Run

```bash
python mockups/27-mixture/build_data.py   # writes data.js (~5 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/27-mixture/
```

`data.js` is git-ignored. Reads only `outputs/motifs/`.
