# 60 · Worldview peel across catalogues

The **worldview half of [mockup 45](../45-stratigraphic-peeling/)**, ported to all three catalogues in each one's
**own authored taxonomy**, so the three are directly comparable in one frame. Answers "can mockup 45 be done for ATU
and TMI too?" — yes, but with an honest caveat (below).

## What it does

Each catalogue's **units** are recursively peeled (coverage-aware CLR, Ward routing — the same machinery as 45) by
their profile over that catalogue's **native categories**:

| Tab | Units | Native taxonomy (profile dims) |
|-----|-------|--------------------------------|
| **Berezkin** | 948 traditions | 13 etiological theme groups (`motif_group_num`) |
| **ATU** | 165 attested peoples | 7 tale-type chapters (Animal / Magic / Religious / Realistic / Ogre / Anecdotes / Formula) |
| **TMI** | 94 cited cultures | 23 letter-chapters (A Myths … Z Misc) |

A node's **name** = a depth **register** (Deep / Young, from the share of the catalogue's archaic/mythic categories) +
its **signature** category (the one most over-represented vs the parent block), with a dedup pass on the first
discriminating dimension. The per-node **depth index** is the mean cross-continent **breadth** of the categories the
block emphasises (broad = old — the same "breadth → age" proxy as 45). Every node also carries a **continent-composition
bar**.

## What it shows

- **Berezkin** reproduces 45's worldview result: a shallow **Old-World tale layer** (*Young Trick & contest /
  Adventures*, Eurasia+Africa, depth ~15) splits off from a **deep cosmological substrate** (*Deep Sun & Moon →
  Cosmogony*, Americas/Oceania-heavy, depth 60–77). The deep layer is genuinely **non-European**.
- **ATU** peels into a broad *Deep Animal-tales* block vs an over-catalogued **European wonder-tale core** (*Wonder
  tales*: German, Latvian, Finnish, Hungarian… — the shallowest, most Eurasia-only leaf).
- **TMI** splits a *Humor / Deception* young branch (Icelandic, Italian Novella, Spanish Exempla) from a *Deep Tabu /
  Myths* branch (A-Myths-heavy cultures: Icelandic, Siberian, Egyptian; India, Irish myth, Jewish, Chinese, Greek).

**The comparison is the payload:** in Berezkin the "deep" layer is a real non-European cosmological substrate; in ATU
and TMI the top structure is dominated by the **European cataloguing core**. Same peel, three catalogues, and you can
see which index carries a global signal and which mostly carries its own collection bias.

## Honest limits

ATU and TMI have **no per-tradition coordinates** and are heavily **Euro-/literary-biased**, so their "deep" register is
partly the over-catalogued European core, not antiquity — the continent bar on every node keeps that visible (this is
[direction 6, the effort confound](../../docs/proposals/synthesis-and-directions.md), made legible rather than hidden).
Continents for ATU come from attestation region labels, for TMI from a country/people gazetteer (~80% of cultures
placed; the rest shown as `?`). The depth index is a relative breadth proxy, not a calendar age.

`build_data.py` builds per-unit profiles over each catalogue's native categories, runs the generic `peel_catalogue`
(self-contained, no Berezkin globals), and writes `data.js`. Deterministic.
