"""Motif-database pipeline step.

Builds a browsable, cross-referenced motif database from traditional folklore
indexes and writes it to ``outputs/motifs/``:

- **Berezkin** — areal distribution catalogue (scraped from areasofmyths.com):
  motif codes, names, areal indices, internal see-also links, short definitions.
- **TMI** — Thompson Motif-Index (from the Trilogy dataset).
- **ATU** — Aarne-Thompson-Uther tale types, each carrying its ordered TMI
  motifs (from the Trilogy dataset).

A cross-walk links ATU tale types to their TMI motifs (and back), forming the
"traditional index" layer the server exposes under ``/api/motifs``.

The step is idempotent and resumable: raw sources are cached under
``outputs/motifs/raw/`` so re-runs are cheap, and ``--force`` rebuilds from
scratch.
"""

# Index identifiers used across the store, API and frontend.
INDEX_BEREZKIN = "berezkin"
INDEX_TMI = "tmi"
INDEX_ATU = "atu"

INDEX_LABELS = {
    INDEX_BEREZKIN: "Berezkin",
    INDEX_TMI: "Thompson (TMI)",
    INDEX_ATU: "ATU tale types",
}

INDEX_ORDER = [INDEX_BEREZKIN, INDEX_TMI, INDEX_ATU]
