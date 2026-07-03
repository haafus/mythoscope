# Cross-index geographic layer — mockup

A design mockup for laying **one shared region taxonomy** over all three motif
indexes (ATU attestations · TMI cultures · Berezkin areal traditions), so they
can be read and compared geographically.

Open `index.html` in a browser. Three views:

1. **Regional footprint** — a compact "geographic fingerprint" for one entity
   (ATU 510A), drawn from all three indexes via the existing id cross-walk.
2. **Aggregate** — share of each index's attestations by region, same region
   order for all, plus a fourth **All three** row (equal-weight mean of the
   three shares — a raw count-sum would just echo TMI's 46k motifs). The shapes
   expose the catalogues themselves: ATU is Euro-centric (71% European),
   Berezkin is globally even, TMI sits between (its South-Asian mass is
   Thompson-Balys India); pooled, Europe leads at only 49%.
3. **Regional lens** — pick a region → material from all three indexes at once.
   Index order throughout is Thompson → Berezkin → ATU. The region name opens a
   **region page** (`region-siberia.html`); each index header / "+N" chip opens
   that index's **filtered list** (`list-{tmi,berezkin,atu}-siberia.html`) with
   compose-filters over the cross-walk. Entity chips open the detail pages.

**Data:** the ATU/TMI/Berezkin aggregate profiles and ATU 510A footprint are
real (computed from the built `outputs/motifs/*.json`). The region grouping is a
first-pass illustrative map, to be curated; TMI/ATU per-entity rows are
illustrative until the `tradition → region` dictionary is built.

**Framing:** attestations are *where a tale/motif is recorded*, not where it
originates — every label in the UI says so.

Concept and analysis: see [`docs/motifs/atu-reference.md`](../../docs/motifs/atu-reference.md)
(§7 apparatus) and the data-sources overview.
