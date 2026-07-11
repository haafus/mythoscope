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
