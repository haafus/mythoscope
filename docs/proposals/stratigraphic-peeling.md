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

1. **Matrix + seriation (coverage-corrected).** Motif × tradition attestation matrix, coverage-weighted;
   seriate/cluster and read the **first bifurcation** — how many large blocks there are is an *empirical*
   question, not an assumption.
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
2. **Coverage confound.** The leading split can be driven by **cataloguing intensity**, not deep history.
   **Coverage-correct before reading the split** (bias weights, mockup 24) — otherwise you peel a sampling
   artefact.
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
/ or a cataloguing-effort artefact (Western Europe is the most intensely catalogued zone) — exactly guard
#2. Takeaways: **(a)** the data-driven instinct is vindicated — an imposed Laurasia/Gondwana `a/b` would have
been the *wrong* top seam here; **(b)** the method already yields a concrete first layer to peel and a clean
residual to recurse on; **(c)** guard #2 is live, so **proper coverage correction is the gating next step**
before trusting layer 1.

## Roadmap

1. **Coverage-correct** the matrix (mockup 24 weights), re-read the first bifurcation, confirm the block
   count and whether the W-Eurasian seam survives correction or a different (older) seam emerges.
2. **Full recursion** with all five guards — cores → maps → dated ages (gated) → declared subtraction →
   residual re-clustering → null-model check.
3. Ship as a new mockup (e.g. `45-stratigraphic-peeling`) and a section in
   [`stratum-derivation.md`](stratum-derivation.md); feed the dated layers back into the tradition
   `stratum-stack` of [`macro-area-facets.md`](macro-area-facets.md).

*Status: proposal + one exploratory probe. The method is specified and its first step is run; the full
recursion and its guards are not yet built.*
