# 36 · Admixture-graph back-migration (roadmap M36)

Tests **alt-hypothesis #6 ("Africa is a sink")** and the standing **back-migration critique of
axiom A8**: for a motif shared between **Africa and West Eurasia**, is it a **deep out-of-Africa**
inheritance or a **recent back-into-Africa** flow? A tree cannot tell — both give Africa+Eurasia
co-occurrence. The admixture graph adds the documented **Eurasian → Africa** edges, and direction
comes from the motif's **within-Africa** footprint.

## The directional idea

Classify each African tradition into a genetic tier (settled back-migration geography — Hellenthal
2014, Pagani, Pickrell — encoded as a coarse regional map; no raw SNP needed at this resolution):

- **deep / un-admixed reservoir** — West / Central / Southern Africa, San (Bantu, West Africa,
  Southwest Africa): the out-of-Africa substrate, minimal Eurasian back-flow;
- **admixed corridor** — North Africa, the Horn, the Sahel (Bronze-Age Eurasian ancestry heavy):
  the documented back-migration edge.

A motif that reaches the deep reservoir predates the back-flow (**deep OoA**); one whose African
presence sits **only in the admixed corridor** is a **back-migration** candidate.

## What it shows

- **836 Africa↔West-Eurasia motifs.** Direction: **back-migration 361 (43 %)**, deep-OoA 435
  (52 %), ambiguous 40 (5 %).
- **The sharp contrast.** Mean corridor-fraction of the African footprint is **0.60 for
  Africa↔Eurasia motifs vs 0.17 for Africa-only motifs (×3.5)** — Africa–Eurasia sharing is
  strongly concentrated on the **northern, Eurasian-admixed edge** of Africa, exactly what
  back-migration predicts.
- **Both directions are real.** Deep-OoA motifs reach San / West Africa (trickster-hare M29G,
  origin-of-death H36A — old African substrate); back-migration candidates sit corridor-only
  (incest / hero tales K120A, K35A — recent).

## Verdict — the A8 critique is confirmed

**~43 % of Africa–Eurasia shared motifs are recent northern-corridor flow, not deep out-of-Africa**
→ a substantial part of the "African substratum" is really **back-flow**, which **weakens "African
substratum = oldest"** (axiom A8).

**Honest confound.** The admixed corridor is *also* the part of Africa **geographically nearest the
Near East**, so from distribution alone **genetic back-migration cannot be separated from cultural
diffusion along the same corridor** — but both are *recent, not deep*, which is the point for A8.
A fine SNP admixture graph (HGDP/SGDP) would pin the mechanism. For the capstone (**M38**):
flag high-corridor-fraction Africa–Eurasia motifs as **back-migration candidates**, not deep
substrate.

## Run

```bash
python mockups/36-admixture-backmigration/build_data.py   # writes data.js (~3 s)
python -m http.server -d mockups 8890
# → http://127.0.0.1:8890/36-admixture-backmigration/
```

`data.js` is git-ignored; `land.js` committed. Reads `outputs/motifs/` + `tradition-coords.json`.
Builds on M33's genetics; the admixture tiers are a coarse published-genetics classification.
