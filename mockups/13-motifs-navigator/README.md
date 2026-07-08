# Unified motif navigator — interactive mock

An **isolated, click-through mock** of the design in
[`docs/motifs-browser-ui.md`](../../docs/motifs/proposals/motifs-browser-ui.md). It is not wired
into the app and calls no API — open `index.html` directly in a browser
(`file://…`). The data is a small **real slice of the TMI index** (≈83 motifs from
chapter A, embedded in the file).

## What it demonstrates

**One navigator surface + composable lenses** (the toolbar acts on one result region):

- **Search** — narrows id / name / definition. In **List** it filters + ranks; in
  **Tree** it highlights matches, auto-expands their ancestors, and shows a
  *"N matches — show as list →"* nudge (it never force-switches the view).
- **View** — `⊟ Tree` (drill-down with subtree-relevance: a category stays
  visible if any descendant matches) vs `☰ List` (flat, sorted).
- **Filter** — Full / With definitions / Substantive / With ATU types, with live
  counts; category badges swap to the active tier.
- **Sort** — code / notes size / cultures (enabled only in List view).
- **Chapter** — scopes the surface.

Row affordances mirror the app: `✓` tick = has a definition, a left rule = a
substantive motif, the badge count follows the active tier.

**Browse ↔ Read focus toggle** (same split, rebalanced):

- *Browse* — navigator wide, reader shows a compact preview.
- *Read* — click **Open to read →** (or double-click a row / press `Enter`). The
  navigator collapses to a thin **rail** of id codes and the reader expands to a
  full card. Step records with `↑`/`↓`; leave with **Back to list** / `Esc`.

## Decisions baked in (the accepted defaults)

Search covers id+name+definition; the tree auto-expands ancestors of matches; sort
lives in List view; the rail shows id codes only. See the doc's open-questions
section for the rationale.

## Not included

Real API, the overview dashboards, the other two indexes (Berezkin/ATU tabs are
inert), and deep-link start state. Those belong to the phased rollout in the doc,
not this look-and-feel mock.
