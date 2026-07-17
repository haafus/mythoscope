# 18 · Motif phylo-strata (Method B)

A prototype of **Method B** from
[`stratum-derivation.md`](../../docs/proposals/archive/stratum-derivation.md): estimate a
motif's history from a **language phylogeny**, not from geography. Method A (mockup 17)
scored motifs by areal spread and could not tell deep inheritance from areal diffusion
or reinvention. Method B can.

Each Berezkin tradition is placed on a language **classification tree** built from its
`language` chain (family → subfamily → …); every motif's presence/absence is mapped to
the tips, and **Fitch parsimony** reconstructs the minimum number of independent gains.
The headline metric is the **phylogenetic signal** — a D-like statistic comparing the
observed gains to gains under random tip placement:

- **high signal** → the motif sits in a clade — spread by **descent** (inheritance);
- **low signal** → it is scattered across the tree — spread **areally** (contact
  diffusion) or reinvented (homoplasy).

Crossed with geographic breadth (macro-areas) this gives four modes.

## What it shows (the payoff)

- **Only ~1% of motifs (32/3265) are both broad and clade-clustered** — genuine descent
  — and they turn out to be **European fairy-tale types** (Cinderella, "seven at one
  blow", people-turned-to-stone). This independently **recovers the published result**
  that märchen track language phylogeny within Eurasia (Tehrani; da Silva & Tehrani).
- **The broad motifs are overwhelmingly areal** (1057 broad-but-low-signal): cosmology
  (sun & moon A3, figure-on-lunar-disc), the trickster (M29B), and the **swan-maiden
  (K25, signal 0.16)** — widespread by *contact*, not descent. This reconciles their
  huge geographic breadth (Method A) with a near-random position on the language tree.
- **Clade-restricted motifs** (B4 fished-out earth, signal 0.62 — an Austronesian-clade
  motif) score high signal but narrow breadth.

## The conclusion for `stratum`

Methods A and B are **complementary, not competing**. Method B identifies the *mode* of
spread: it flags the few motifs that follow descent (and can be dated by clade depth),
while showing that most motif structure is **areal** — which is exactly why geography
(Method A) is the right primary signal for the bulk, with the deep-set / disjunction
cues for their age. Language is the "wrong tree" for most motifs, and Method B proves it.

## Interim vs full

The tree here is the coarse family→subfamily classification from our own `language`
field. Swapping in the **dated** Glottolog + Bouckaert/EDGE global phylogeny (open data)
upgrades the shallowest-inherited-clade depth into a true node **age**.

## Run

```bash
python mockups/18-motif-phylostrata/build_data.py   # writes data.js (~8 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/18-motif-phylostrata/
```

`data.js` is git-ignored.
