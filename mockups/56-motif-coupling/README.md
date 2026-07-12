# 56 · Motif coupling (inverse-Ising / pairwise MaxEnt)

The first of the "Tier-A" text-free experiments from
[`synthesis-and-directions.md`](../../docs/proposals/synthesis-and-directions.md). The minimal model
reproducing the observed pairwise motif co-occurrences is the Ising / Boltzmann model
`P(s) ∝ exp( Σ hᵢsᵢ + Σ Jᵢⱼsᵢsⱼ )`. Its couplings **Jᵢⱼ are the *direct* links** — what remains after
every transitive path through other motifs is removed.

## Method

Fit by **pseudo-likelihood**: an L1-logistic regression of each motif (top 500 by frequency) on all the
others, **with the tradition's log-richness as a covariate** so the cataloguing-effort confound (a
densely-recorded tradition has more of everything) does not masquerade as coupling. Symmetrise, then read:

- **positive J** = direct attraction — motifs that co-occur beyond what their other correlations explain;
- **negative J** = direct **repulsion** — mutually-exclusive motifs (the co-occurrence matrix's marginals
  cannot show this);
- **high correlation but J ≈ 0** = an **indirect** pair, correlated only through a shared hub.

## What it shows

- **Only 9% of strongly-correlated pairs (|φ| ≥ 0.30) survive as direct couplings — 91% are indirect.**
  Most apparent motif associations (and most of mockup 53's implications) are transitive: motifs co-occur
  because they share the same over-catalogued regional/thematic traditions, not because of any direct link.
- **Direct attraction recovers real motif complexes:** *Stupid imitation ↔ The bungling host*,
  *Big Dipper is seven men ↔ seven persons*, *The couple of close relations ↔ Brother and sister beget
  mankind*, *A late son kills monsters ↔ Youngest brother kills monsters*.
- **Direct repulsion recovers competing variant-slots (the genuinely new result):** a tradition tells one
  filler of a narrative slot *or* the other — *Pleiades are boys ↔ Pleiades are girls* (J = −1.04),
  *Man in the Moon ↔ The Moon rabbit* (−1.02), *Female producer of valuables ↔ Male producer* (−0.85),
  *Revenge for the male relatives ↔ Revenge for the mother*. These "allomotifs" are invisible to
  co-occurrence (their raw φ is near zero or even positive) but fall straight out of the direct coupling.

The network view plots the strongest |J| edges (green attract / red repel), nodes coloured by theme group.

## Honest limits

The couplings still carry the **residual effort/areal confound** (result 2): the log-richness covariate
removes the coarse "densely-recorded" effect, but two motifs confined to differently-sampled regions can
still show a spurious negative J. Read the couplings as **structure, not causation**. C (L1 strength) is
fixed at 0.15 — a stability-selection sweep would firm up the edge set.

`build_data.py` fits 500 L1-logistic regressions (liblinear), symmetrises, computes the raw φ matrix for the
direct/indirect split, and lays out the strongest-|J| graph with networkx spring layout; writes `data.js`.
