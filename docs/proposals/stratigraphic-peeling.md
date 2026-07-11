# Recursive layer-peeling — data-driven stratigraphy

> One of the core methodological ideas of the project. Stage 3→4 (**classify → explain**) of the arc in
> [`analysis-program.md`](analysis-program.md), and the recursive generalisation of the per-motif depth
> score ([`stratum-derivation.md`](stratum-derivation.md), mockup 17).

## The idea, in one line

Let the **statistics**, not a priori categories, define the top-level structure of the motif corpus;
extract each large data-driven block's **shared core**, characterise and **date** it as a layer, **subtract**
it, and **recurse** on the residual — producing a **bottom-up, dated stratigraphy** of world mythology.

This is the data-driven answer to "what if we subtract the signal from the two super-areas?": we do **not**
impose Laurasia/Gondwana (Witzel) or any Berezkin macro-category as the top seam. We let the heatmap draw
its own leading split, peel it, and see what finer structure the residual reveals — the same logic as
removing the leading principal component to expose sub-structure, and the same discipline Berezkin urges
("do not count the corpus as one pool").

## The method

0. **Coverage normalisation — a precondition, not a later guard.** The correction for cataloguing effort
   must happen **before the first bifurcation is even read**, because the leading split is precisely where
   coverage bites hardest (the most-catalogued zone peels first — see the probe below). Reading a
   bifurcation off an uncorrected matrix is invalid: the split you read *is* the artefact. So coverage
   correction (bias weights, mockup 24) is **step 0** — an admissibility gate on the matrix — not one guard
   among five. **Caveat:** weighting cannot fully separate a genuinely distinct region from a merely
   over-catalogued one (they are confounded — Western Europe is both a real märchen zone *and* the most
   intensely recorded). Step 0 is necessary but not sufficient; a surviving seam must be re-checked against
   a coverage-*independent* signal (rarefaction to equal motif counts; the crosswalk-replicated core, M37),
   not weights alone.
1. **Seriation on the corrected matrix.** Seriate/cluster and read the **first bifurcation** — how many
   large blocks there are is an *empirical* question, not an assumption.
2. **Core / substrate of each block** = its **consensus signature**: motifs broadly shared *within* the
   block and characteristic of it (lift, not raw share).
3. **Draw each core as a named nucleus** — map + motif list + theme profile.
4. **Date the core** — from the shape of its distribution (depth score, mockup 17) and, where the block
   tracks a language family, clade depth (Method B). **Dating is a gate, not an assumption**: a *young* core
   is a diffusion front, not a substrate, and must not be peeled as a deep layer.
5. **Subtract the core** (by a **declared** operator — remove the core motifs, or residualise the block's
   per-motif prevalence, or down-weight) and **recurse** on the residual until no stable large block remains
   (an explicit stopping rule).

**Output:** a dated stratigraphy — each peel is a layer with an age estimate; the residual exposes the next
layer. It generalises the depth score from *per motif* to *per layer*, and does it bottom-up.

## Guards — where the method self-deceives (these do not vanish by going data-driven)

1. **Circularity / double-dipping (the main one).** The core is defined from the same matrix it is then
   subtracted from and re-clustered — so part of the residual structure is an artefact of the subtraction
   operator. Require a **null model** (permutation) or out-of-sample validation to show residual clusters are
   real, not induced by peeling.
2. **Coverage confound — promoted to step 0 (precondition), not a guard applied after.** The leading split
   can be driven by **cataloguing intensity**, not deep history, and it corrupts the *very first* thing the
   method reads — so correction precedes step 1 (see step 0). Listed here only for completeness; and even
   step 0 cannot fully disentangle a real region from an over-catalogued one, so the surviving seam needs a
   coverage-independent cross-check.
3. **Core ≠ substrate.** A block's most-shared motifs are its consensus, but "shared" can be recent
   diffusion. Calling a core a *substrate* requires it to independently pass the depth test (disjunctness +
   banality control) — hence dating as a gate (step 4).
4. **The subtraction operator is a modelling choice** with different residuals; declare which and why.
5. **Recursion stability.** A stopping rule, plus a check that peel order (block 1 first vs block 2 first)
   converges to the same stratigraphy rather than a path-dependent artefact.

## How it fits the existing code

A **nested, sampling-corrected block model** over the existing biclustering (mockups 06 / 15), using the
depth score (mockup 17) as the dating gate and the bias weights (mockup 24) as the coverage control. Not a
new paradigm — a recursive wrapper on machinery that exists.

## Initial evidence (exploratory probe — coverage NOT yet properly corrected)

A first-bifurcation probe on the 948 traditions with ≥15 motifs (idf down-weighting as a partial coverage
control, Ward linkage) already says something sharp:

**The data-driven top split is *not* Gondwana/Laurasia.** It peels off a compact **Western/Central-Eurasian
block** — Western Europe + Northern & Eastern Europe + SW/Central Asia (+ Siberia at k=3), i.e. the
literate/märchen + Near-Eastern belt — from a large "everything else" residual (the Americas + Sub-Saharan
Africa + SE-Asia/Oceania + Australia together). Under this control **Sub-Saharan Africa and Australia do not
form a top-level Gondwanan block**; Africa sits with the Americas/rest.

| First cut | Peeled block | Residual |
|---|---|---|
| Ward k=2 | 94: W.Europe/N.Africa + N&E Europe + SW/C.Asia | 854: Americas 325 · Eurasia-rest 347 · Africa 129 · Austronesia 46 · Australia 7 |
| KMeans k=2 | 226: W.Eurasia + Near East + Siberia | 722: Americas 325 · Eurasia-rest 239 · Africa 105 · Oceania 46 · Australia 7 |

Two readings, **not yet separable**: the young European fairy-tale / descent layer standing out (real), and
/ or a cataloguing-effort artefact (Western Europe is the most intensely catalogued zone). This probe
**skipped step 0** (only idf down-weighting, not the real bias weights), so its seam is **provisional and
probably partly artefactual** — which is the whole point: the very first read is coverage-corrupted, so
step 0 must run *before* any bifurcation is trusted. Takeaways: **(a)** the data-driven instinct is
vindicated — an imposed Laurasia/Gondwana `a/b` would have been the *wrong* top seam here; **(b)** the method
already yields a concrete first layer to peel and a clean residual to recurse on; **(c)** coverage
correction is not a later fix but the **precondition (step 0)** on which layer 1's validity depends.

### Step 0 applied — the seam changes (this is the point)

Running step 0 confirms the uncorrected seam was largely an artefact and **changes the answer**:

- **Direct confound (smoking gun).** The peeled 94-tradition W-Eurasian block has mean coverage **391.7
  motifs/tradition** (median 380) vs **91.3** (median 74) for the residual and **121** overall — it is
  simply the **richly-catalogued tail**, so the uncorrected seam tracks cataloguing effort.
- **Coverage-equalised (rarefaction to 20 motifs/tradition, and L1-normalised profiles).** The W-Eurasian
  seam **disappears**. The corrected top split becomes **New World ↔ Old World** — the **Americas** are the
  distinct pole (≈290 American traditions separating), with the Old-World residual being Eurasia + Africa +
  Oceania together. (Some seed instability: the bipartition flips between "Americas out" and "Old World out",
  but the Americas are the distinctive block either way.)
- **Still not Gondwana/Laurasia:** Africa groups with **Eurasia** (the Old World), not with Australia — so
  neither the imposed `a/b` nor the uncorrected W-Eurasian seam is the real layer 1; the data-driven,
  coverage-corrected answer is **Americas vs the Old World**, consistent with Berezkin's New-World peopling
  work.

The lesson is exactly the step-0 argument made concrete: **correcting before the first read changed the
top seam** — from an artefactual Western Europe to a defensible New-World/Old-World contrast. Firming it up
needs the real bias weights (mockup 24) and several rarefaction depths; the qualitative result (effort
artefact gone, Americas the distinct pole) is already stable across both corrections.

### Recursion to depth 3 — the emergent stratigraphy

Running the peel recursively (coverage-corrected L1+idf, Ward k=2 per node, depth 3) yields a
geographically and thematically coherent tree, bottom-up, with no imposed labels — and each block's **core**
(top motifs by lift) reads as its known folklore:

```
948  ROOT
├─432  NEW WORLD (Ame323 Eur100)          core: paramour-animal, monster-fight, theft-of-fire
│   ├─192  deep pan-American cosmology (Ame182)   core: incestuous Moon, rainbow serpent, deluge
│   │   ├─51   Meso/N-American (buzzard-husband ×15, Moon-rabbit, first sunrise)
│   │   └─141  S-American/Amazonian (jaguar, sky-of-birds)
│   └─240  BERINGIAN / circum-Pacific bridge (Ame141 + Eur99)   core: two-sisters, thunderbirds, false-burial
└─516  OLD WORLD (Eur299 Afr169 Oce46)    core: dragon-slayer, ungrateful-one, strange-son
    ├─92   Sub-Saharan Africa (Afr91)      core: hyena-fails, death-and-chameleon, demonic-wife
    └─424  Eurasian-Oceanian märchen (Eur298 Afr78 Oce46)   core: Cinderella, helpful-cow, quest
        ├─163  Indo-Pacific cosmology (Eur114 + Oce46)   core: brother-sister cosmogony, shed-skin
        └─261  W-Eurasian + N-African tale belt (Eur184 Afr77)   core: Bremen-animals, averted-incest
```

**What emerges** — a recognisable genetic-geographic stratigraphy: L1 New/Old World; L2 a **Beringian /
circum-Pacific bridge** (Americas + N-Eurasia together — Berezkin's deep trans-Beringian signal) and a
**clean Sub-Saharan Africa** peel; L3 a North/South-America split and the Eurasian märchen dividing into an
**Indo-Pacific cosmology** cluster (Oceania joins here) and the **Western-Eurasian + North-African ATU tale
belt** (Bremen musicians, Cinderella).

**Honest gates on this tree:**
- **Silhouettes are weak** (L1 +0.03, L2 +0.04 / +0.11) → the structure is **clinal** (isolation-by-distance),
  not crisp modules; peeling imposes hard cuts on a soft gradient. This is consistent with the programme's
  own "geography is primary, areal" finding — the tree is a useful discretisation, not a claim of sharp
  blocks.
- **Singleton / tiny outlier peels** (e.g. an n=1 leaf with lift ×158) are **outliers, not layers**; the
  subtraction operator needs a minimum block size that routes them aside (guards #4/#5).
- **The null model (guard #1) is not yet run** — the blocks are geographically coherent (a strong sign they
  are real, not peel-induced), but not yet permutation-tested.
- Still L1+idf, not the full mockup-24 bias weights.

Even so, the recursion demonstrates the method's payoff: coverage-corrected peeling reconstructs a plausible,
interpretable stratigraphy of world mythology from the bare attestation matrix.

## Roadmap

1. **Run step 0 first — coverage-correct** the matrix (mockup 24 weights) *and* a rarefaction /
   crosswalk-replicated cross-check, then read the first bifurcation on the corrected matrix: does the
   W-Eurasian seam survive, or does a different (older) seam emerge once cataloguing effort is removed?
   Everything downstream is conditional on this.
2. **Full recursion** with all five guards — cores → maps → dated ages (gated) → declared subtraction →
   residual re-clustering → null-model check.
3. Ship as a new mockup (e.g. `45-stratigraphic-peeling`) and a section in
   [`stratum-derivation.md`](stratum-derivation.md); feed the dated layers back into the tradition
   `stratum-stack` of [`macro-area-facets.md`](macro-area-facets.md).

*Status: proposal + one exploratory probe. The method is specified and its first step is run; the full
recursion and its guards are not yet built.*
