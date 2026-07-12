# 58 · Higher-order structure (synergy triples + the topology of trait-space)

The third Tier-A text-free experiment from
[`synthesis-and-directions.md`](../../docs/proposals/synthesis-and-directions.md). The pairwise view
(mockups 53 / 56) is blind to two things: irreducible **three-way packages** and the **global shape** of
the motif cloud. This mockup goes after both — and reports two honest negatives that sharpen the project's
central result.

## Method

- **Synergy** via **interaction information** `II(X;Y;Z) = ΣH(pairs) − ΣH(singles) − H(triple)` (sign
  convention: > 0 = synergy, the triple carries dependency beyond *all* its pairs; < 0 = redundancy).
  Evaluated over the 4000 best-supported triples drawn from the φ ≥ 0.30 co-occurrence graph among the
  top-300 motifs.
- **Topology** via **persistent homology** (`ripser`, Jaccard distance matrix): each motif is a point in
  948-dim tradition-incidence space; H0 tracks connected components and H1 tracks loops across every scale.

## What it shows (two negatives, one confirmation)

- **No synergy anywhere.** The maximum interaction information across 4000 triples is **negative** (≈ −0.02).
  Every motif triple is fully explained by its pairs — there is no irreducible three-way package. The
  pairwise couplings of mockup 56 already capture the dependency structure; the most *redundant* triples are
  simply variant-families (a motif, its subtype, its sub-subtype: one fact recorded thrice, II ≈ −0.33).
- **One connected blob, no loops.** H0 collapses to a **single** persistent component (everything merges);
  H1 shows **zero** features above the 0.08 noise floor (top persistence ≈ 0.06, all points sit on the
  birth = death diagonal). Trait-space is a single connected **cline**, not a set of discrete lumps and not
  a ring of mutually-avoiding regimes.

The value is precisely that the exotic machinery finds nothing exotic: the **geography-is-clinal** result of
the whole project (result 1), reconfirmed from an information-theoretic and a topological angle that could
in principle have shown synergy or loops and did not.

## Honest limits

Restricted to the **top-300 motifs** for tractability (ripser on the full 3488 is prohibitive); a rarer,
finer package could hide below the frequency cut. Interaction information at this support is noisy — the
claim is "no *strong* synergy," not "provably zero." Binary incidence discards frequency-within-tradition.

`build_data.py` computes interaction information over the capped triple set, runs `ripser` (maxdim = 1) on
the Jaccard distance matrix, and writes `data.js`. Deterministic.
