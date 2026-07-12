# 54 · Dated catalogue

One **per-motif age table** combining every signal the project produces (analysis #8) — a synthesis deliverable,
not a new method.

Per motif: **M17 disjunction depth**, **phylo-signal** (M18/M30), **barrier floor** (mockup 49), **textual floor**
(mockup 50), **language-family age** (M30) → a **consensus best year-floor** and a count of **independent**
corroborating absolute methods.

**Coverage.** any signal **3338 / 3488**; an **absolute year-floor 1992**; corroborated by **≥ 2 independent
methods 447**. Consensus floors: ≥10 ka 1284 (the trans-Beringian blanket), 4–10 ka ~500, <2.5 ka ~190. The page
is a searchable, sortable catalogue (filter by name/id; sort by best floor, corroboration, M17, φ-signal) with a
provenance chip per motif for each contributing method.

**Honest limit.** Floors are **lower bounds**, not ages; the median is dominated by the weak trans-Beringian
"≥15 ka" blanket. The value is the **447 corroborated** motifs and a single browsable table where the five methods
cross-read.

`build_data.py` recomputes all five signals and emits the coverage, floor histogram and the top-400 corroborated
rows; writes `data.js` (~2 min).
