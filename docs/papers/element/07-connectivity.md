# 7 · Connectivity: what the facets miss

*Computational Comparative Mythology: A Natural History of the Motif — Chapter 7 of 10. Draft.*

---

Chapter 5 measured a hole and Chapter 6 sharpened its edges. A tradition's four describable facets
recover only about a third of why traditions share the motifs they do, and the depth analysis, having
resolved a descent minority and a small deep substrate, left the great areal majority explained by
nothing more specific than "neighbourhood and distance." Two-thirds of the structure is a **convergence
residual** — real, cross-continental motif sharing that area, family, subsistence, and theme together
do not account for. This chapter takes that residual seriously as an object in its own right and asks
whether it can be closed by modelling the *channels* along which motifs actually travelled: the
physical landscape, and the historical polities that carried culture across it. The answer is
instructive precisely because it is mostly negative — one candidate fails a test set in advance, and
the other succeeds only weakly and only where it should.

## 7.1 The residual, measured in one fit

Before testing what might close the residual, it is worth seeing it emerge cleanly from a single model
rather than from the piecemeal analyses of Chapter 5. A joint Poisson factorization of the whole
motif × tradition matrix — with attestation-intensity built in as an exposure offset and cross-index
replication as weights — does in one fit what the earlier systematics did in several, and does it
de-confounded. It **removes sampling**: the share of a component explained by catalogue richness falls
to η² = 0.34, against 0.67 for a naïve k-means and around 0.80 for naïve co-clustering. And it
**recovers geography**: its twelve emergent components turn out to be the twelve macro-areas, each with
its own theme profile, at a block agreement of ARI 0.37 against 0.08 for the naïve baseline (Figure
7.1, panel a). This is the systematics of Chapter 5 vindicated in a single principled model — the
structure is regional and it survives de-confounding. But the same fit quantifies the shortfall: the
regional components account for the areal majority and leave the cross-continental sharing unexplained.
The residual is not an artefact of using too many small models; it is there in the cleanest single
model too. That is what makes it worth trying to close.

## 7.2 Landscape permeability fails its gate

The first candidate is physical. The analyses so far have measured distance as the crow flies —
isotropic great-circle distance — but the world is not isotropic. Oceans are barriers to land peoples
and highways to maritime ones; mountains and ice block movement; coastlines and open plains channel it.
A motif's reach should perhaps be governed not by raw distance but by **resistance distance** — the
least-cost path across a friction surface that makes seaways cheap or dear depending on the people and
makes the Himalaya and the Andes expensive. If isolation is really "by resistance" rather than "by
distance," a connectivity model built on such a surface should predict tradition-to-tradition motif
sharing better than plain distance does.

This is exactly the kind of attractive upgrade Chapter 3's discipline of the falsifiable gate exists to
discipline. The friction surface is built procedurally: land and ocean rasterised from the committed
coastline, a latitude penalty for ice and tundra above about 60°, two explicit mountain barriers at the
Himalaya–Tibet massif and the Andes, and — crucially chosen *a priori* rather than tuned to the
outcome — three physically-motivated sea regimes: a *realistic* one in which coasts are easy and open
ocean is a costly but crossable barrier, a *maritime* one in which the whole sea is a cheap highway, and
a *terrestrial* one in which the sea is a near-wall. Least-cost distance between traditions is then a
shortest-path computation over a one-degree grid. The claim was pre-registered as a test the model had to
pass *out of sample*: resistance distance must beat great-circle distance on held-out tradition pairs, or
it does not earn adoption. It does not pass. Across **all three** sea regimes — barrier, highway, and
wall — great-circle distance wins on held-out data, with a held-out R² of 0.158 against 0.110 or less for
resistance, and adding resistance distance on top of great-circle distance adds nothing (Figure 7.2).
That the negative holds even in the maritime regime, which was built to be generous to sea travel, is
what makes it convincing rather than an artefact of one arbitrary setting. Either isolation-by-distance
genuinely dominates at this global scale, or the coarse, procedural friction surface — a first cut, not
a fine terrain-and-ecoregion raster — is too blunt to capture the real corridors. The honest conclusion is that
this particular upgrade is not warranted by this evidence, and the clean negative is reported rather
than buried. A finer GIS friction raster with real terrain and ecoregions might revisit the question;
until it does, the model keeps plain distance. Reporting a negative that a less disciplined analysis
would have quietly dropped is the point of setting the gate in the first place.

## 7.3 Historical empires: a weak but real cross-area channel

The second candidate is historical rather than physical. Motifs move with people, and people moved in
bulk through empires — Rome, the Mongol world, the great agrarian states that briefly stitched distant
regions into single political fabrics. If a pre-colonial empire ever spanned two macro-areas, the
traditions it enclosed had a channel for sharing motifs that distance alone would not predict. Joining
the corpus to pre-colonial political boundaries lets this be tested directly.

The test needs two scoping decisions, both of which matter. Colonial-era boundaries are excluded, because
they blanket the globe administratively — the British Empire would link India to Australia, which is not
a folk-motif corridor — leaving four pre-colonial snapshots that capture Rome and Han, then Byzantium,
the Caliphate and Song, then the Mongol khanates, then the Ottomans and Ming. And because the boundary
data tessellates the world, so that nearly every point falls inside *some* named region (including
culture-region catch-alls), a "real" empire is defined as a polity spanning at least three macro-areas —
the filter that keeps Rome and the Mongol world and drops the tessellation cells.

With that filter, the global effect is small, and honestly so. Only about 32% of traditions were ever
inside a multi-area empire at all, and the coverage is starkly Old-World and Mongol-belt biased —
Eurasia and Africa run 40–54%, but South America sits at 0%, Aboriginal Australia at 0%, and Oceania at
1%, because small-scale societies sat *outside* the great empires by definition. Empire cannot, then, be
a general explanation for cross-continental sharing; most of the world was never in one, and added as a
covariate across the whole corpus it contributes a mere ΔR² of +0.011. But the sharp, targeted test is
positive, and positive exactly where the theory says it should be: traditions in **different**
macro-areas that once shared an empire share about **2.6 times** more motifs than distance-matched pairs
that did not, a distance-matched increment of +0.029 (Figure 7.3). Rome and the Mongol world genuinely
moved motifs across boundaries that distance would otherwise have kept closed. The result is a model of what a real but minor channel looks like: negligible on average
because it touched only part of the world, yet unmistakable in the cross-area cases it did touch. It
closes a sliver of the residual, not the bulk of it.

## 7.4 The back-migration critique

The last test in this chapter is not an attempt to close the residual but a check on one of the deep
substrate's most seductive interpretations — and it matters because it disciplines a claim the previous
chapter came close to. It is tempting to read the deep, Africa-touching layer as an African substratum
that is *therefore* the oldest, a stratum carried out of Africa with the first modern humans. But motifs
also flowed *back* into Africa across the Eurasian corridor, and if apparent African-Eurasian sharing
is really the residue of back-migration rather than of an out-of-Africa inheritance, the "African =
oldest" equation weakens.

A tree cannot answer this, because a deep out-of-Africa inheritance and a recent back-migration both
produce the same Africa-plus-Eurasia co-occurrence. The direction has to come from *within* Africa. Each
African tradition is placed in one of two genetic tiers from the settled back-migration geography — a
deep, largely un-admixed reservoir in West, Central, and Southern Africa (the out-of-Africa substrate,
with minimal Eurasian backflow) versus an admixed corridor across North Africa, the Horn, and the Sahel
(heavy with Bronze-Age Eurasian ancestry). A motif that reaches the deep reservoir predates the
back-flow; one whose African presence sits *only* in the admixed corridor is a back-migration candidate.
Of 836 motifs shared between Africa and West Eurasia, the split is **361 back-migration (43%)** against
435 deep-out-of-Africa (52%), with 40 ambiguous. And the contrast is sharp: the mean corridor-fraction
of a back-migration motif's African footprint is 0.60, against 0.17 for the interior-anchored ones, a
factor of about 3.5. The apparent African substratum is, in substantial part, Eurasian material that
flowed back along the corridor, not a relic of the first human dispersal. This does not erase the deep substrate that
Chapter 6 established — the both-hemisphere spine survived every control — but it forbids the lazy
inference from "touches Africa" to "oldest," and it names a mechanism, admixture direction, that a
finer genetic analysis could turn into a real third axis.

> **Figure 7.1.** The joint Poisson factorization: in one fit it de-confounds sampling (η² of catalogue
> richness 0.34, against 0.67 for k-means and ~0.80 for co-clustering) and recovers geography (block
> ARI 0.37 vs 0.08), its twelve components being the twelve macro-areas. **Figure 7.2.** The landscape
> gate: held-out R² for great-circle distance (0.158) against resistance distance (≤0.110) across the
> three sea regimes — the upgrade fails out of sample. **Figure 7.3.** Historical empires: traditions in
> different macro-areas that shared an empire share ×2.6 more motifs (distance-matched +0.029), against
> a negligible global effect (ΔR² +0.011). **Figure 7.4.** The back-migration check: 43% of 836
> Africa–Eurasia motifs sit only in the admixed corridor (corridor-fraction 0.60 vs 0.17, ×3.5).

---

The connectivity chapter thus closes very little of the residual, and its value lies in that honesty.
Physical landscape connectivity failed the test set for it; historical empire closed only the thin
cross-area sliver it was ever positioned to close; and the back-migration check removed a false
shortcut rather than adding explanatory power. Two-thirds of motif sharing remains unaccounted for by
everything the corpus can currently bring to bear. That is not a defeat but a specification: the
residual is the shape of the missing data, and it names precisely what a finer genetic, trade-route,
and node-dated calibration would have to supply. Before turning to that frontier, though, the book
returns to a question left open since Chapter 5 — whether the thematic axis, re-derived from the
material rather than inherited from the catalogues, describes a tradition better than the classical one
does. That is the subject of Chapter 8.
