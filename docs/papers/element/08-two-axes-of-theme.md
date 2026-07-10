# 8 · Two axes of theme

*Computational Comparative Mythology: A Natural History of the Motif — Chapter 8 of 10. Draft.*

---

Chapter 5 left one question deliberately open. The thematic axis — the grouping of motifs by subject
that the classical catalogues rely on — was shown to be data-confirmed at its highest level: the split
between cosmological and novelistic material re-emerges from co-occurrence without using the labels.
But Chapter 3 had flagged a deeper worry, that the *particular* themes might cut across the natural
grain of the corpus rather than following it, and that worry was never settled. This chapter settles
it, by doing what Chapter 4's restraint made possible: re-deriving the theme axis from the material
itself and comparing it, head to head, with the scholar's scheme. The result is not that one axis is
right and the other wrong. It is that there are **two** good axes, orthogonal to each other, and each is
better at a different job.

## 8.1 Re-deriving theme from meaning

The classical themes order motifs by what they are *about*. The alternative is to let the motifs'
meanings group themselves. Embedding every motif by its name and definition (the validated retrieval
layer of Chapter 4), reducing the embeddings, and clustering them in two levels yields a data-driven
taxonomy of 16 clusters subdivided into 61 sub-themes, each hand-named after inspection (Figure 8.1).
By every internal measure this is a better description of the material in content space than the
thirteen hand themes. It is far more coherent — the silhouette score, a measure of how well each motif
sits inside its assigned group, rises from −0.03 for the hand themes (essentially no coherence) to
+0.28 for the data clusters. It is more balanced — the effective number of groups rises from 7.4 to
12.1, and there is no single 1,243-motif catch-all swallowing a fifth of the corpus. And it is
complete: the 141 motifs the hand scheme leaves un-grouped all receive a theme.

Its agreement with the hand scheme is only moderate — an adjusted Rand index of 0.12 — and the
disagreement is informative rather than noisy. Where the two agree, they agree on the celestial,
cosmogonic, and formulaic block, which the data recovers cleanly. Where they diverge, the data isolates
tight micro-complexes the hand scheme buries: the Formulae group comes out 100% pure, the African
death-messenger complex emerges as its own thing, and the trickster's zoological *casting* — which
animals play which roles — separates from trickster *plots*. The data sees structure the etiological
ordering was not built to see.

## 8.2 Orthogonality: what a myth explains versus how a tale is built

The most consequential divergence is what happens to the two giant genre catch-alls. Berezkin's
Adventures (1,243 motifs) and Tricks (620 motifs) **dissolve** under the data-driven clustering into
narrative complexes — the magic wife, the ogre outwitted and escaped, the animal fable, the
revenge plot — and those complexes cut straight across the Adventures/Tricks line. A motif's membership
in the data scheme has little to do with its membership in the hand scheme, because the two are indexing
**orthogonal** things. The classical axis sorts motifs by *etiological function* — what the myth
explains, the inheritance of the Aarne–Thompson chapter logic. The data axis sorts them by *narrative
form* — how the tale is built, something much closer to the tale-type tradition and to Propp's
functions. Neither is the "correct" taxonomy of motifs, because they are not competing answers to one
question; they are projections onto two different questions. A flood myth and a trickster tale differ
in what they explain and in how they are constructed, and these two differences do not have to line up.

## 8.3 Head to head as a descriptor of a tradition

Orthogonality alone would be a curiosity. What makes it matter is that the two axes perform
differently when put to work, and the difference is legible when each is used as a facet to describe a
tradition and predict which motifs it shares with another.

The head-to-head runs on the same 910-tradition working set as the facet audit of Chapter 5, and it
begins by reproducing the hand theme's published unique contribution exactly — ΔR² = 0.125 — so that the
comparison is on equal footing. On that footing the data-driven axis wins decisively:

| tradition facet | unique ΔR² | residual (1 − full R²) |
|---|---|---|
| 13 hand themes | 0.125 | 0.636 |
| 16 narrative clusters | 0.191 | 0.570 |
| 61 narrative sub-themes | 0.321 | 0.440 |

The narrative facet shrinks the 64% residual of Chapter 5 to 57% at the coarse resolution and 44% at the
fine one (Figure 8.2). More striking still is what happens when both facets are placed in the same
model: the hand theme's unique contribution collapses to **0.003** — nearly redundant — while the
narrative facet keeps **0.069** on top of the hand theme. The subsumption runs one way only. Almost
everything the classical themes explain about a tradition, the narrative axis already explains, and then
some; almost nothing the narrative axis explains is left for the classical themes to add. As a tradition profile it is also more
geography-orthogonal — macro-area explains 31% of its variance against 38% for the hand profile — and
it recovers the same cross-continental worldview clusters a comparativist would want to see, a shared
celestial profile linking the Cherokee, ancient Italy, southeastern Australia, and the Netsilik across
oceans (Figure 8.3).

And yet the classical axis is not thereby retired, because it is better at the one job the narrative
axis is worse at: **reading geography**. As an areal marker at the coarse level, the hand scheme's
theme × area association (Cramér's V of 0.125) beats the narrative scheme's (0.102); the narrative
clusters are so good at capturing form that they *dilute* the areal signal the etiological categories
carry, and the narrative axis only catches up at the fine 61-sub-theme resolution. The etiological
themes encode geography precisely *because* they were built around what regional cosmologies explain.
So the two axes divide the labour: narrative form is the better descriptor of a tradition and the
better predictor of what it shares; etiological function is the better instrument for reading where a
tradition sits. The practical conclusion is a **two-facet representation**, keeping both, rather than
replacing one with the other.

## 8.4 The depth the catch-alls hid

The re-derivation pays a final dividend that ties this chapter back to Chapter 6. The original
motivation for re-deriving themes was that Berezkin's giant catch-alls average over motifs of very
different antiquity, so a theme-by-depth analysis on the hand scheme is blunt. Running the depth
measures of Chapter 6 on the narrative taxonomy instead exposes the gradient the flat categories
averaged away (Figure 8.4). The narrative clusters range in cross-continental span from 1.00 for
Formulae — shallow, formal, recent — to 2.10 for the death-messenger complex — deep and disjunct.
The deep clusters are overwhelmingly etiological, drawing only 0–32% of their motifs from the old
Adventures/Tricks catch-alls; the shallow clusters are märchen, drawing 82–90% from them. Depth and
narrative kind line up, once the catch-alls are broken open.

The payoff case is the swallowing-monster and vulnerable-body complex — the motif family in which a
being is swallowed and the world or the body is made from what is inside. It sits *deep*, at a span of
1.80, and yet 53% of it is built from motifs Berezkin had filed under Adventures, Tricks, and Flora. The
flat genre category had averaged this genuinely deep cosmological stratum together with shallow tales,
and only re-deriving the axis from meaning pulls it back out. The decomposition makes the point in
aggregate as well as in this one case: the old flat Adventures category, with a single mega-set span of
1.59, now fans across narrative clusters spanning 1.43 to 1.96, and the old Tricks, flat at 1.40, fans
across 1.26 to 1.67 — a spread of antiquity the single number had collapsed. This is the clearest
demonstration in the book of why the theme axis had to be checked rather than assumed: a scholar's
ordering, however reasonable, can hide exactly the stratum a depth analysis is looking for.

> **Figure 8.1.** The UMAP re-derivation: motifs embedded, reduced, and clustered into 16 clusters ×
> 61 sub-themes, coloured by the hand themes for comparison — coherence rises from silhouette −0.03 to
> +0.28, ARI with the hand scheme only 0.12. **Figure 8.2.** The facet showdown: the narrative axis's
> unique ΔR² (0.191 at 16 clusters, 0.321 at 61 sub-themes) against the hand theme's 0.125, and the
> collapse of the hand theme's unique contribution to 0.003 when both are in the model. **Figure 8.3.**
> The cross-continental worldview clusters the narrative profile recovers — a celestial profile linking
> the Cherokee, ancient Italy, southeastern Australia, and the Netsilik. **Figure 8.4.** Depth on the
> narrative taxonomy: cross-continental span from 1.00 (Formulae) to 2.10 (death-messenger), with the
> deep swallowing-monster complex (span 1.80) shown to be 53% built from old Adventures/Tricks motifs.

---

The theme chapter thus resolves the question Chapter 5 deferred, and it does so in the book's
characteristic shape — not a replacement but a measured division of labour. There are two good axes of
theme, orthogonal because they answer different questions; the data-derived narrative axis is the
better descriptor of a tradition and nearly subsumes the classical one, while the classical etiological
axis remains the better reader of geography; and breaking the catch-alls open recovers a depth gradient
the flat scheme had averaged into invisibility. With the descriptive apparatus now complete — a tradition
described, its facets audited, its distributions dated as far as they can be, its residual measured, and
its theme axis doubled — the book can slow down and watch the whole machine work on three individual
motifs, before drawing the threads together at the frontier.
