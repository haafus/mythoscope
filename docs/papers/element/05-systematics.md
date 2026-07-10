# 5 · Systematics and the tradition

*Computational Comparative Mythology: A Natural History of the Motif — Chapter 5 of 10. Draft.*

---

Before a single distribution can be dated, two prior questions have to be answered. Does the corpus
carry real structure at all — genuine "for these peoples, these motifs" regularities — or is any
apparent pattern just the shadow of who was catalogued most thoroughly? And once real structure is
granted, what is the right way to *describe* a tradition: which of its features carry the signal, which
are redundant, and how much of the whole they manage to account for? This is the systematics stage of
Chapter 3's arc, and it must come before the phylogeny of Chapter 6, because a claim about how a
distribution arose is empty until the distribution has been shown to be real and the descriptive
vocabulary has been audited. This chapter does both, and it delivers the first substantive result of
the book along the way: the catalogue's structure is genuine, but the facets we use to describe a
tradition are entangled and, together, incomplete.

## 5.1 The catalogue carries real, de-confoundable structure

The natural first move on a motif × tradition matrix is to co-cluster it — to find blocks of
traditions that share a characteristic set of motifs. Doing so recovers exactly the region-coherent
groups a comparativist would hope to see: an Amazonian block, a Northwest-Coast block, a Siberian
block, a Turkic block, and a European tale-type block, each paired with the motifs that distinguish it,
and each recovered consistently across the three catalogues, with Berezkin giving the crispest areal
groups (Figure 5.1). Taken at face value, this looks like immediate vindication: the myths cluster by
region, just as they should.

But this is precisely where Chapter 3's discipline earns its place, because the naïve clustering is
badly confounded. When traditions are grouped by raw motif counts, the blocks separate the
densely-catalogued traditions from the thinly-catalogued ones almost as much as they separate regions:
the share of block membership explained by attestation-intensity alone reaches η² = 0.80. In other
words, four-fifths of what the raw clustering "discovers" could be the fingerprint of the collecting
enterprise rather than of the myths. A result that survives *this* is worth having; a result that does
not is a description of the archive. The corpus survives. Replacing the naïve clustering with a
**degree-corrected block model** — one that builds each tradition's catalogue richness into the model
as a nuisance parameter and factors it out — **halves** the confound, from η² = 0.80 to 0.48, while
keeping the interpretable regional blocks intact; a principled model-selection criterion settles on
nine blocks (Figure 5.2). The structure is real: it does not dissolve when the sampling is corrected,
it merely sheds the part of itself that was an artefact. This single before-and-after — 0.80 down to
0.48, blocks preserved — is the template for the whole book. Every later finding is asked to clear the
same bar, and the ones that do not are reported as failures rather than buried.

## 5.2 What a tradition is: four facets, audited

Granting that traditions cluster into real kinds, how should a single tradition be described? Chapter 3
proposed four facets — macro-area, language or religious family, subsistence economy, and thematic
profile — and insisted that whether these are the *right* descriptors is not to be assumed but audited.
The audit is unflattering to the tidy version of the model, and that is its value.

The facets are **not orthogonal.** Area and family, in particular, are strongly entangled: their
association reaches a Cramér's V of 0.73, because both are tracking one and the same underlying
history — the peopling of a region by a lineage of speakers. Knowing a tradition's macro-area tells
you a great deal about its language family and vice versa, so the two are not independent handles on a
tradition but two views of a single fact. This falsifies the comfortable assumption, stated openly in
Chapter 3 precisely so it could be attacked, that the descriptors would carve a tradition along
independent axes.

Worse for the model, the facets are **partly redundant** in what they explain. Partitioning the
variation in pairwise motif-set similarity among the four facets — dropping each in turn and asking how
much unique explanatory power it holds — shows that language family and subsistence add almost nothing
once the others are present: each carries a unique contribution of about ΔR² ≈ 0.01. The work is done
by the thematic profile (unique ΔR² ≈ 0.13) and, secondarily, by the macro-area (≈ 0.08). A tradition,
for the purpose of predicting which motifs it shares with another, is well described by *where it is*
and *how its tales are built*, and barely improved by adding *what it speaks* or *how it feeds itself*
once those two are known (Figure 5.3).

And the descriptors are, together, **incomplete.** Even using all four, the facet set recovers only
about a third of the structure in motif similarity — roughly 36%, a figure that agrees across two
independent ways of estimating it. This is not a small shortfall to be polished away; it is the
central negative fact that organises the rest of the book. Two-thirds of why traditions share the
motifs they do is *not* captured by area, family, subsistence, and theme combined. That unexplained
remainder — the **convergence residual** — is what Chapter 7 interrogates with connectivity models, and
what Chapter 10 hands to future genetic and historical calibration. The systematics stage, done
honestly, does not close the description of a tradition; it measures exactly how far from closed it is.

## 5.3 The theme axis is data-confirmed, and only partly geographic

One of the four facets deserves separate scrutiny, because it is the one the traditional catalogues
lean on most heavily and the one Chapter 3 flagged as never having been checked: the thematic axis, the
grouping of motifs by subject. Does it correspond to anything in the material, or is it a scholar's
imposition?

It corresponds to something. Berezkin's high-level division between cosmological/etiological material
(his Category A — cosmogony, the origin of death, the origin of humans) and novelistic/trickster
material (Category B — adventures, tricks, tale-types) **re-emerges from the data without using his
labels.** Seriating the co-occurrence of themes across traditions — which themes tend to appear
together in the same corpus — recovers the A/B split as a block structure on its own. The traditional
top-level cut is not arbitrary; the material clusters along it.

The themes are also strongly **geographic**, but only partly so. Particular themes concentrate sharply
in particular regions: the Sun-and-Moon theme is over-represented in Aboriginal Australia by a factor
of about 3.4, while the Adventures theme runs about 1.2 times expected across the Eurasian belt and
only 0.3 times expected in Australia (Figure 5.5). A tradition's genre balance is thus a real signal
with a real geographic patterning. But this is also the one headline in the book that **weakens under
the sampling correction rather than surviving it unchanged**: macro-area explains about 38% of the
variance in traditions' theme profiles on the raw counts, and that figure falls to roughly 26% once
attestation-intensity is weighted out. Geography's grip on genre balance is real but was partly
overstated by the fact that some regions were catalogued far more thoroughly than others. Reporting the
drop — 38% down to 26% — rather than the flattering raw figure is exactly the discipline Chapter 3
committed to, and it matters here because the theme axis returns as a central character in Chapter 8.

## 5.4 The subsistence gradient, and what Galton's problem does to it

The fourth facet, subsistence, is the only one with no in-corpus source: it has to be joined from
outside, from the Ethnographic Atlas via the D-PLACE database, by matching each tradition to its
nearest documented society. Wiring it in makes it possible to test a prediction the comparative
literature has often asserted but rarely checked: that **foragers are cosmology-heavy and intensive
agriculturalists are tale-heavy** — that the balance between Category A and Category B shifts with how a
people makes its living.

The gradient is there, and it runs in the predicted direction. Measuring each tradition's Category-A
(cosmological) share of motifs and grouping by subsistence, the extractive economies sit high —
foragers at 54.7%, horticulturalists at 57.6% — and the intensive or mobile ones sit low — agrarian
states at 39.5%, pastoralists at 36.2% (Figure 5.4). A roughly twenty-point spread separates the
cosmology-heaviest from the cosmology-lightest economies, in the direction the model predicted.

But a gradient across subsistence types is exactly the kind of finding Galton's problem can
manufacture out of nothing, because subsistence is spatially clustered: foragers are not scattered at
random over the globe, they are concentrated in particular regions with particular myth-histories, so a
"subsistence effect" could be an area effect or a shared-ancestry effect wearing a subsistence mask.
Chapter 3's answer is restricted permutation — shuffling the subsistence labels only *within* strata,
so that a stratum's structure is held fixed and the association has to survive being tested against the
right null. The gradient survives being controlled for macro-area (p = 0.003) and survives being
controlled for language family (p = 0.006) when each is handled on its own. It **attenuates to marginal
(p = 0.065) only when area and family are both controlled at once** — which is the honest result:
subsistence carries a genuine, partly independent contribution, but one that is substantially
entangled with the region-and-lineage history it rides on. The finding is neither the clean
confirmation an incautious reading would claim nor a debunking; it is a real effect with its
confounding stated to the decimal. That is what a de-confounded gradient looks like, and it is the
model the rest of the book follows: report the effect, report the control that nearly erases it, and
let the reader see the difference.

> **Figure 5.1.** Co-clustering the motif × tradition matrix: region-coherent tradition blocks
> (Amazonian, Northwest-Coast, Siberian, Turkic, European) paired with their characteristic motifs.
> **Figure 5.2.** Model selection and de-confounding: the block model settles on nine blocks (by BIC),
> and the degree-correction cuts the coverage confound from η² = 0.795 to 0.481 while keeping the
> regional blocks.
> **Figure 5.3.** The facet audit: drop-one unique ΔR² for each descriptor — theme profile (~0.13) and
> macro-area (~0.08) carry the signal; language family and subsistence add ~0.01 each once the others
> are known.
> **Figure 5.4.** The subsistence gradient in Category-A share (foragers 54.7%, horticulturalists 57.6%,
> agrarian states 39.5%, pastoralists 36.2%), with the restricted-permutation p-values that control area
> (0.003), family (0.006), and both at once (0.065).
> **Figure 5.5.** Theme × macro-area lift: the heatmap of over- and under-representation (Sun & Moon in
> Australia ×3.4; Adventures ×1.2 in the Eurasian belt, ×0.3 in Australia).

---

The systematics stage thus leaves the programme with a firm foundation and a precisely measured hole.
The corpus carries real regional structure that survives sampling correction; a tradition is best
described by where it is and how its tales are built, with language and subsistence largely redundant
once those are known; the thematic axis is data-confirmed but less geographic than the raw numbers
suggest; and the subsistence gradient is real but heavily entangled with area and descent. Above all,
the four facets together explain only about a third of motif similarity. With the description of a
tradition audited and its incompleteness quantified, the book can now turn from *describing*
distributions to *dating* them — to the question of how old each distribution is, and how much of that
antiquity can honestly be recovered.
