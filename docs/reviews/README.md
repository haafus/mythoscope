# Reviews

Point-in-time audits of the codebase — each records findings against a specific
commit and does **not** itself change code.

- [`2026-07-repo-review.md`](2026-07-repo-review.md) — full repository review across four zones (data pipeline, motifs, server + frontend, tests/infra): refactorings, ranked bug clusters (P0–P2) and proposed features

## Archived

Spent — findings folded into the tradition-`region` architecture; kept for the trail under [`archive/`](archive/).

- [`color-system-review.md`](archive/color-system-review.md) — deep dive on the category-colour system: where colours are generated, stored, passed and used across back end and front end, with every duplicate and inconsistency. *Folded into `../proposals/tradition-architecture-unified.md` → `region-implementation.md`.*
- [`major-tradition-review.md`](archive/major-tradition-review.md) — same end-to-end lens on the `major_tradition` (macro-area) field: how it is derived from the tradition tree at build time, where it is stored/denormalised, how it reaches the front end, and every default-value/duplication inconsistency. *Folded in — `major_tradition` → renamed/re-partitioned to `region`.*
- [`tradition-review.md`](archive/tradition-review.md) — same end-to-end lens on the primary `tradition` field: unlike colour/major it is an authored source field and the cross-cutting join key, so the emphasis shifts to its lack of a canonical identity and the fragile string-match join between `config/corpus.json` and `config/traditions.json`. *Folded in — the string-join fix is §2 of the region plan.*
