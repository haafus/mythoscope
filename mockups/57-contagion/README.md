# 57 · Contagion (simple vs complex spreading as a generative model)

The second Tier-A text-free experiment from
[`synthesis-and-directions.md`](../../docs/proposals/archive/synthesis-and-directions.md). Borrowed from the
**epidemiology of representations**: two competing spreading rules leave different geographic signatures,
so the observed footprints can be scored against both as a *model comparison*.

## Method

Build a **small-world tradition network** — k-NN geography (k = 6, haversine `BallTree`) plus ~2% random
long-range weak ties — then simulate a motif spreading under two rules:

- **Simple contagion (SI):** a tradition adopts if *any* neighbour has it (one exposure). Crosses weak ties
  → can jump → spatially disjunct footprints are reachable.
- **Complex contagion (threshold θ = 0.4):** adopts only if a *fraction* of neighbours have it
  (reinforcement). Stalls at weak ties, stays in dense cores → compact, contiguous footprints.

The summary statistic is **geographic fragmentation** (DBSCAN clusters, haversine) at a given footprint
size. Simulate a fragmentation-vs-size band for each rule (40 runs per size), then assign every real motif
the better-fitting mechanism; motifs too disjunct for *either* local band are labelled
**long-range / descent**. The assignment is cross-checked against motif complexity (mockup 51's
definition-content-word proxy).

## What it shows

- **Three regimes:** most motifs fit **simple** contagion, a substantial minority fit **complex**, and a
  tail is too disjunct for any local rule (**long-range / descent**).
- **The complexity axis is mechanistically confirmed.** Mean definition-complexity orders exactly as
  predicted: **complex-contagion motifs > simple > long-range/descent**. Complex, arbitrary motifs need
  reinforcement to spread (so they stay compact); the simplest, most-disjunct ones are unreachable locally
  and travel by descent or long jumps. This is an *independent* mechanistic vote for the complexity
  gradient mockup 51 read off content words.

The chart overlays the two simulated bands (fragmentation vs footprint size) with the real motifs as dots
coloured by assigned mechanism.

## Honest limits

**No time axis** — this is model comparison on the static snapshot, not a reconstruction of history. The
network is a **geographic proxy**: the long-range ties are random, not real contact routes (mockup 35 has
the historical corridors). "long-range/descent" conflates two mechanisms the snapshot cannot separate
(result 3). Read the assignment as *which spreading rule is consistent with the footprint*, not proof a
motif spread that way.

`build_data.py` builds the network (`networkx`), runs both simulations across footprint sizes, scores every
motif, and writes `data.js`. Deterministic (fixed seed).
