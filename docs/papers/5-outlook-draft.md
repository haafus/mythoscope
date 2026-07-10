# Open Problems and Outlook

*Computational Comparative Mythology — Monograph **Part V** (the closing chapter, not one of the four
standalone papers). It ends the book on the frontier: what the programme has *not* yet done, and what
finishing it would resolve. Draws together threads from Papers II–IV — see [README](README.md).*

---

The four papers close on a coherent picture: over a cross-indexed global motif corpus, areal diffusion
dominates, a datable fairy-tale descent minority tracks language, a small trans-hemispheric substrate
survives every control, and a tradition is best described by its macro-area and by the narrative form
of its corpus. But the picture is honest about its edges, and those edges are the research programme.
This chapter names four of them.

## 1. Finishing motif induction from text

The main pipeline (`corpus → embeddings → projections → graphs → motifs`) is *built* to induce motifs
from raw multilingual text and anchor them to the curated vocabulary, and its component steps are
individually validated: section detection across the source texts, a recall@k/MRR grid for composing a
motif embedding, and the retrieval layer against the confirmed crosswalk. What remains is the field's
hard, unsolved core — validating *induced* motifs **at scale** against the curated gold.

The path is not a single model but a loop: (i) generate candidates from chunk clusters; (ii) **align**
each candidate to the TMI/ATU/Berezkin vocabulary via the crosswalk, so induction is anchored, not
open-vocabulary; (iii) route uncertain candidates to **human culture-bearers** (the MIME lesson) rather
than trusting the model; (iv) score against a held-out gold with **strong classical baselines** always
present — the consistent finding is that TF-IDF/SVM rival neural/LLM systems on small folktale corpora,
so beating them is the bar. The realistic near-term deliverable is not "automatic motif discovery" but
a **high-recall candidate generator with human confirmation**, which is exactly what would let the
distributional analysis of Papers II–IV extend beyond the curated catalogues to the raw corpus.

## 2. Closing the convergence residual

The facet audit is blunt: macro-area, family, subsistence and theme together recover only ~36% of
motif similarity, and the joint factorization leaves a large **cross-continental convergence residual**
— motifs shared across oceans that neither geography nor language nor genre explains. Three pending
external joins each address one face of it.

- **Fine SNP genetics — a true third axis.** At continental resolution the genetic tree we could build
  is derived from area, so it cannot separate descent from geography where language and area already
  agree (the alt-tree test made this explicit). A fine population-genetic graph is the one dataset that
  could distinguish deep shared ancestry from mere co-location — the mechanistic upgrade the
  back-migration result also calls for.
- **Trade routes (OWTRAD).** Historical empires added real but narrow cross-area signal; documented
  trade corridors are the complementary connectivity layer, targeting exactly the long-range sharing
  that isolation-by-distance under-predicts.
- **Node-level Bayesian dating (BEAST).** Current calendar ages are family-resolution ceilings. A dated
  tree with relaxed-random-walk phylogeography would give node-consistent origin locations *and* ages
  with uncertainty, sharpening the breadth/disjunction proxy into calibrated dates and re-running the
  depth analysis on ages rather than proxies.

The residual is not a defect to be tuned away; it is a **map of the joins still to make**, and each
join has a falsifiable gate waiting for it.

## 3. The two-facet taxonomy in production

The data-driven re-derivation showed the theme axis is two orthogonal things — *etiological function*
(what the myth explains) and *narrative form* (how the tale is built) — and that the narrative facet is
a strictly better tradition descriptor while the etiological one better carries geography. The next
step is to write **both** into the pipeline as per-motif fields (`narrative_cluster` / `narrative_sub`
beside the 13 hand themes), so downstream analyses can pick the right axis per question. Two cautions
carry forward: the narrative facet must never be used as an axis *independent of content* (it is
circular by construction), and its cluster boundaries depend on the embedding model and reduction
seed, so it ships with its provenance, not as ground truth.

## 4. Release and reproducibility

The programme's assets — the ingestion-and-crosswalk pipeline, the assembled indices, the analysis
prototypes, and the derived facets (`narrative_taxonomy.json`) — are built to be released as a tagged
bundle off committed public-domain sources. The constraint is licensing, not code: the curated indices
carry their sources' terms (Berezkin via its query engine; several aggregators forbid mining), so a
release must ship the *pipeline and derived analyses* with clear provenance and access notes for each
external asset, documented in `docs/research/` and `docs/motifs/`.

## 5. The larger arc

A finished programme would look like this: a corpus large and multilingual enough that induced,
human-confirmed motifs extend the curated indices rather than merely retrieving over them; a facet set
enriched with genetics, corridors and node-level dates until the convergence residual is small and what
remains is genuine independent innovation; and a two-facet taxonomy that lets every question be asked on
the right axis. The value of stating the residual so plainly is that it converts an open-ended
comparative project into a **finite, testable agenda** — each remaining question named, each with a
dataset that would answer it and a gate that would falsify the easy answer. That agenda, not any single
result, is what makes this a science of myth rather than a catalogue of resemblances.
