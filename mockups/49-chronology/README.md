# 49 · Chronology

Can we put a **time axis** on the motifs? The interactive realisation of
[`../../docs/research/dating-and-chronology-methods.md`](../../docs/research/dating-and-chronology-methods.md).
Three linked views over one build — deliberately including the honest negative parts.

## ① Datability — which dating *route* each motif admits

Not "datable vs not". On Berezkin's areal taxonomy **99% of motifs are areal-clustered** (median NRI ≈ 11)
— coarse structure is tree-like even though *fine* geography is clinal (mockup 46). NRI (net relatedness on
the areal tree) is really a **recency** axis: it anti-correlates with the consensus age order (Spearman
−0.22), so tightly clade-local motifs are young, spread ones old. What differs between motifs is **which
route** gives a date, and the corpus splits three ways:

- **Barrier** (~1280) — crosses a biogeographic barrier → an absolute floor (view ②);
- **Tree** (~690) — clade-concentrated (NRI ≥ 3, ≤ 2 macro-areas) → language/phylogeny calibration;
- **Weak** (~1370) — spread, no clean barrier → weakly datable.

## ② Barrier floors — absolute year lower-bounds

A motif with ≥ 2 attestations on each side of a known barrier is *no younger* than the crossing:
**Sahul ≥ ~50 ka** (contested), **trans-Beringian ≥ ~15 ka**, **pan-American ≥ ~13 ka** (both solid). The map
colours each tradition by the oldest floor among its motifs; the example lists per tier are exactly the deep
celestial/cosmogonic substrate (Theft of fire, Stars are people, Sun & Moon are males, Primeval waters,
Earth grows big). These are the mockup-48 teleconnector motifs, now with *year floors* — the first real years
on the axis.
*Honest limit:* lower bounds, not ages — one ancient long-range jump is indistinguishable from deep
inheritance; and trans-Beringian sharing is so common that nearly every tradition inherits a ≥ 15 ka floor.

## ③ Pseudo-chronology — a consensus relative order, and where it fails

Four independent orderings (**CA seriation**, **diffusion-map pseudotime**, **M17 breadth**, **prevalence**)
are each rooted so the barrier anchors sit at the old end, then averaged into a consensus, with per-motif
**agreement bands**. The validation works at the coarse level: barrier-anchor motifs pile at the **old** end
(mean rank 0.69) and ATU tale motifs at the **young** end (0.33) — the polarity is real.

**But the honest catch is the point of the view.** CA seriation and diffusion pseudotime agree (0.94) only
because the **dominant ordination axis is geography, not time** — their correlation with New-World share is
**0.87 / 0.84**. The age-oriented heuristics (M17, prevalence) agree only weakly, and mean agreement across the
ribbon is just **0.63**. So:

> A defensible **coarse** chronology exists (barriers old, ATU tales young, validated), but there is **no
> robust fine-grained age order** — naive ordination recovers *space* readily and *time* only coarsely. This
> is the ceiling the research note predicted; the mockup shows it rather than hiding it.

## Why one mockup, not three

The three views share one build and **feed each other**: datability says *which* motifs to trust; the barrier
floors supply the anchors that **root the ordering's polarity** and give absolute year-floors; the
pseudo-chronology consumes both (anchors for rooting, agreement bands for reliability). Reading them
cross-wise — a motif's route, its floor, its consensus rank and its agreement — is the whole point.

## Data

`build_data.py`: binary matrix (≥ 15 motifs, coordinate); areal-taxonomy patristic distances → per-motif NRI
vs a size-matched null; barrier-floor classification; four motif orderings on motifs attested ≥ 5 times (CA
via SVD of standardised residuals, diffusion map via the graph Laplacian's 2nd eigenvector, M17 disjunction,
prevalence), barrier-rooted, consensus + agreement + Spearman method matrix + the New-World-share geography
diagnostic + barrier-old / ATU-young validation. Deterministic; writes `data.js` (~30 s).

## Run

```bash
python mockups/49-chronology/build_data.py     # writes data.js (~30 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/49-chronology/
```
