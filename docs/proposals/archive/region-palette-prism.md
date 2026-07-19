# Archived — the CARTO Prism region palette (superseded)

> **Status: archived (2026-07).** This was §8 of [`../regions.md`](../regions.md) — the original
> CARTOColors-Prism-based region palette, with per-region `base` + `light`/`dark` ramp ends. The canon now
> uses the **intuitive (associative)** palette and keeps **`base` only** (no `light`/`dark`). This file is
> kept for provenance: the spectral-arc reasoning and the hand-tuned swaps that produced the Prism values,
> in case they are ever wanted again. It is **not** the live palette.

## Colour palette (Prism — archived)

Built on **CARTOColors Prism** — a cartographer-designed qualitative palette (https://carto.com/carto-colors/).
Prism's 11 coloured hues map onto the arc in spectral order (its 12th, a neutral grey, is dropped); the
3 remaining slots are filled by colours interpolated *in Prism's style* into its two widest hue gaps
(teal↔blue and blue↔purple), leaving the 11 originals untouched. The result is a continuous spectral
ribbon along the out-of-Africa arc — hue carries the sequence, and the map's borders + labels carry the
neighbour distinction (per-pair contrast is deliberately not maximised).

Each region has a **base** (its map colour) plus **light**/**dark** ramp ends.

**Two swaps break the strict arc for legibility.** The arc's tail (purples→magentas) piled four
similar hues into the New World, where they read as one blur. So two American regions trade colours
with Old-World neighbours whose own clusters were also too tight: **Native North America ↔ Caucasus &
Iran** (green ⇄ dark-purple) and **Lowland South America ↔ Mainland Southeast Asia** (teal ⇄ magenta).
The Americas now carry purple (Circumpolar) · green (N. America) · orchid (Meso & Andes) · teal
(Lowland S. Am.); the swap also loosens the Caucasus/Inner-Asia greens and the South/SE/East-Asia teals.
Because the two hemispheres never share map space, the borrowed hues collide with nothing.

**A third rotation lifts the East-Asian / Pacific cluster,** which had piled blue (East Asia),
dark-blue (Austronesia) and indigo (Papua) into one quadrant. A 3-cycle across East Asia, Austronesia
and West Asia: **East Asia takes orange** (from Near East & North Africa) so it pops among the
surrounding greens/blues/purples; East Asia's medium blue then passes on to **Inner Asia**, and **Near
East & North Africa takes Austronesia's dark-blue**, distinct against its red/yellow/purple
Mediterranean neighbours. This trades away the warm Mediterranean orange, but the East-Asian legibility
is worth it. A final trade — **Austronesia ↔ Inner Asia** (blue ⇄ green) — gives Austronesia the Prism
green, clear across the Sahul seam, and Inner Asia carries the blue among the greens and purples of the
steppe.

**Papua & Aboriginal Australia leaves the arc for a warm ochre** (`#A9773F`). At the blue→purple tail it
was near-indistinguishable from the Near East's dark-blue, and the two are hard to tell apart even far
apart on the map. Moved into the warm gap between the reds/oranges and the greens, it now separates
cleanly from every neighbour (Austronesian green around it, the dark-blue Near East) — and ochre is apt
for the Aboriginal "red centre". This is the one region placed purely for contrast rather than arc
position.

| # | region | base | light | dark | source |
|---|---|---|---|---|---|
| 1 | Sub-Saharan Africa | `#CC503E` | `#D79389` | `#953223` | Prism red |
| 2 | Near East & North Africa | `#2A4895` | `#5473C2` | `#162857` | insert blue↔purple (↔ Austronesia via E. Asia) |
| 3 | Europe | `#EDAD08` | `#EDC55F` | `#9B7208` | Prism gold |
| 4 | Caucasus & Iran | `#6F4070` | `#9F67A0` | `#3C223D` | Prism dark-purple (↔ N. America) |
| 5 | Inner Asia | `#1D6996` | `#3F97CB` | `#0E3A54` | Prism blue (↔ Austronesia) |
| 6 | South Asia | `#38A6A5` | `#70C5C4` | `#216B6A` | Prism teal |
| 7 | Mainland Southeast Asia | `#94346E` | `#BD6299` | `#591D41` | Prism magenta (↔ Lowland S. Am.) |
| 8 | East Asia | `#E17C05` | `#EDA550` | `#8D5007` | Prism orange (↔ Near East) |
| 9 | Austronesia | `#0F8554` | `#26C583` | `#075534` | Prism green (↔ Inner Asia) |
| 10 | Papua & Aboriginal Australia | `#A9773F` | `#C9A578` | `#6E4C24` | warm ochre (off the arc — see note) |
| 11 | Circumpolar North | `#5F4690` | `#8C78B5` | `#3A2A5A` | Prism purple |
| 12 | Native North America | `#73AF48` | `#A2C688` | `#4D772E` | Prism yellow-green (↔ Caucasus) |
| 13 | Mesoamerica & the Andes | `#994E95` | `#B984B7` | `#643162` | Prism orchid |
| 14 | Lowland South America | `#2A8A9F` | `#59B3C7` | `#175361` | insert teal↔blue (↔ Mainland SE Asia) |
