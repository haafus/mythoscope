# Reviews

Point-in-time audits of the codebase — each records findings against a specific
commit and does **not** itself change code.

- [`2026-07-repo-review.md`](2026-07-repo-review.md) — full repository review across four zones (data pipeline, motifs, server + frontend, tests/infra): refactorings, ranked bug clusters (P0–P2) and proposed features
- [`color-system-review.md`](color-system-review.md) — deep dive on the category-colour system: where colours are generated, stored, passed and used across back end and front end, with every duplicate and inconsistency
- [`major-tradition-review.md`](major-tradition-review.md) — same end-to-end lens on the `major_tradition` (macro-area) field: how it is derived from the tradition tree at build time, where it is stored/denormalised, how it reaches the front end, and every default-value/duplication inconsistency
