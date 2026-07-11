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

### Stopping rule — why internal criteria fail (the structure is clinal)

Attempting a principled bottom (the natural next step) produced a **more important negative result than a
tree**:

- **Significance does not stop.** A permutation test (Ward + a column-shuffle null that breaks co-occurrence
  while keeping motif prevalence, 150 perms) returns **p ≈ 0.007 at *every* split — the floor** — including a
  split whose silhouette is **−0.000** (fully overlapping clusters). The null is too weak: any structure
  beyond marginal prevalence, even a clinal gradient, beats it. **Significance ≠ meaningfulness**; the tree
  only ever stopped on the size floor.
- **Effect size has no natural gap.** Silhouettes are **~0.03–0.11 at *every* level, including the top**
  (the New/Old-World root itself is only ≈ 0.03–0.09). Any silhouette floor therefore either kills the whole
  tree (a 0.05 floor stops at the root) or nothing.
- **Why:** mythological similarity is a **smooth geographic gradient** (isolation-by-distance), not a
  hierarchy of crisp modules — the programme's own "geography is primary, areal" thesis. Peeling
  **discretises a continuum**; it does not recover true discrete strata. So *"have we exhausted the levels?"*
  is the wrong question — there is **no discrete bottom**, only a gradient, and depth is a **discretisation
  choice** (how finely to cut), not a discoverable truth. (Fittingly, the root treated as one block has a
  **pan-global celestial-substrate** core — male-sun/female-moon, eclipses, man-in-the-moon — the universal
  layer shared by all.)

**Consequence for guards #1/#5.** Internal cluster criteria (p-value, silhouette) validate neither the
stopping point nor "how many layers are real." Depth must be validated **externally**: (a) **stability** —
does a split reproduce under bootstrap resampling; (b) the **dating gate** — a layer is real only if its core
**dates coherently** (mockup 17); (c) **clade correspondence** — does a block map to a dated linguistic /
genetic group. The tree stays **interpretable and useful** (its blocks are geographically coherent and match
known mythology geography) — but it is a *discretisation of a continuum*, to be trusted per-block by external
anchoring, not a crisp modular hierarchy read off internal separation.

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

## Recommendation — what to do with this

The experiments settle the method's role. **Do not force hard recursive peeling deeper on clinal data** —
there is no discrete bottom to find, and perfecting the stopping rule is a dead end (internal criteria
provably fail). Instead:

1. **Fix the discretisation at 2–3 layers** and stop; the top layers are meaningful and match known
   geography.
2. **Shift the payoff from "the tree" to "dated cores."** The value is the ~5–6 coherent blocks (the
   pan-global celestial substrate, the Beringian bridge, Sub-Saharan Africa, Indo-Pacific cosmology, the
   Western-Eurasian tale belt, the New World) — **date each core** via the depth score (mockup 17) and clade
   anchoring, turning the tree into a *dated stratigraphy* (the Element ch. 6 goal).
3. **Use a soft decomposition as the real layer model.** Clinal, overlapping layers are exactly what the
   existing **joint Poisson factorisation (M38)** represents — latent components a tradition loads on
   *several* at once (as reality demands: one tradition carries many strata). Make the *scientific* layers
   the soft factors; keep peeling as the intuitive **discovery / naming / cross-check** tool over them.
4. **Validate blocks externally, cheaply:** bootstrap stability (does a split reproduce under resampling)
   and clade correspondence (does a block map to a dated linguistic/genetic group) — the only criteria that
   still bite on clinal data.

In one line: **peeling is right for *seeing and naming* layers; dating and counting them belongs to the
soft factorisation that already exists — not to a deeper hard tree.**

This recommendation is realised as an interactive mockup —
[`45-stratigraphic-peeling`](../../mockups/45-stratigraphic-peeling/) — visualising the layers, their
geography, motif composition, proxy dating, bootstrap stability, and the soft-factor cross-check.

### The payoff realised — dated soft layers

Recommendation 2+3 is now done in mockup 45: an **M38-style effort-corrected Poisson factorisation**
(`P[t,m] ~ Poisson(a(t)·(WH)[t,m])`) into six **overlapping** soft layers, each **dated by the M17
disjunction depth score** of its motifs — a **dated stratigraphy**, the result the hard clinal tree could
not give:

| Layer | depth (M17) | geography | core motifs |
|---|--:|---|---|
| F1 | 81 | Americas | Sun & Moon · Theft of fire · Magic wife · Stars-are-people |
| F2 | 72 | Americas + Eurasia | Earth-grows-big · Primeval waters · thunderbirds |
| F3 | 63 | Eurasia + Africa | Magic wife · primeval sky · trickster-hare |
| F4 | 62 | Eurasia | Man-in-the-Moon · Cosmic hunt · lunar-disc figure |
| F5 | 33 | Eurasia + Africa | trickster-fox · external soul · nestlings |
| F6 | 30 | Eurasia + Africa | dragon-slayer · kind-and-unkind · personified Death |

The deep layers (F1–F4) are cosmogonic/celestial and New-World-endemic; the shallow layers (F5–F6) are the
young Eurasian/African **märchen** (ATU dragon-slayer, kind-and-unkind). This is a proof-of-concept that
soft, overlapping, datable layers can be built where the hard discrete tree could not — but see the honest
conclusions below on how *new* this actually is.

## Conclusions — what this arc did and did not produce

Assessed plainly, without inflation:

- **No genuinely new scientific result.** The dated soft layers are a **synthesis of things that already
  existed**, not a discovery: (a) the depth axis is **literally M17** — each layer's age is the M17
  per-motif disjunction score averaged over its motifs, so nothing is added to the dating; (b) the layers
  themselves are the **same coarse components** the existing factor / theme work already recovers (mockups
  16 / 23 / 38); (c) the pattern *deep = cosmology/celestial + New-World-endemic, shallow = Eurasian
  märchen* is the **already-established** finding (Element ch. 6 / 8: the celestial substrate is deep,
  European tales are young, theme and stratum are orthogonal). So the earlier "content-ful new finding"
  claim was an **overstatement**; this is a re-presentation, not a new result.
- **It is the same as the previous per-motif-prevalence approach.** M17 dated motifs from the shape of their
  distribution; this dates *groups* of motifs by the same M17 scores. The stratigraphy's depth axis *is*
  M17 — grouping-then-averaging adds presentation, not depth information.
- **PCA would get close.** M17's own score is a PCA (PC1) of distributional features; a PCA of the
  tradition × motif matrix would recover the same coarse components (prevalence, New/Old World, …) and the
  same clinal signature (a scree plot with no elbow). The factorisation's only advantages over PCA are
  **interpretability** (non-negative, parts-based "layers" a motif positively belongs to) and the **coverage
  offset** `a(t)` in the Poisson variant — not a different result.
- **The one real, if modest, takeaway is methodological and negative:** the corpus is **clinal**
  (isolation-by-distance), so it has **no discrete strata** — hard recursive peeling is a dead end, and any
  "layers" are a *discretisation of a continuum*, to be trusted per-block by external anchoring
  (bootstrap stability, dated clades), not read off internal cluster metrics. That adds **rigour** (don't
  over-claim layers), not a finding. A minor side-note: coverage correction *dissolves* the clean
  Austronesian factor (NMF isolates it, the effort-corrected Poisson distributes it).

> **"Clinal"** = a continuous gradient, not discrete groups. Motif similarity falls off *smoothly* with
> geographic distance (neighbours always similar, no sharp seam where one "group" ends) — like a colour
> gradient or a dialect continuum, versus distinct blocks. It is the same thing as the programme's
> "geography is primary, areal" thesis, and it is *why* clustering here imposes cuts rather than finding
> them.

*Status: proposal + probes + recommendation + mockup 45 (two dated soft-factor models). Value delivered:
a visualisation and a clean negative result (clinal → no discrete strata). No new scientific finding;
production wiring (real M38 output, calibrated M17/clade ages, external validation) remains — and would be
the only path here to an actual new result (dated layers with real ages).*
