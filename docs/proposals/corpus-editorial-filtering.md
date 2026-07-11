# Proposal: excluding modern editorial prose from the embedding corpus

The downloaded source texts (mostly Project Gutenberg) carry **modern editorial prose** — translators'
prefaces, introductions, scholarly notes, appendices, glossaries, indexes, afterwords — mixed in with
the actual **tradition text** (the myth / epic / scripture). This editorial register contaminates the
embeddings and clusters (it reads as 19th–20th-century academic writing, not ancient narrative) and
skews per-tradition profiles. This note surveys approaches to keeping **only the tradition text** in the
corpus that feeds `corpus → embeddings`.

## Current state

- `config/corpus.json` is a **small, curated list** (~28–100 entries): `{title, tradition, url,
  description}` per text.
- The build already runs `clean_gutenberg_in_builder(text, url, title)` (`src/corpus/builder.py`),
  which strips the **Gutenberg licence boilerplate** (`*** START/END OF PROJECT GUTENBERG ***`) — but
  **not** the editorial front/back matter, which sits inside the "content".

The decisive fact: **N is small and curated**, so we can afford precision-oriented methods that would
not scale to thousands of texts.

## Two orthogonal choices

- **Where** to cut: the **clean stage** (before chunking, trim boundaries), the **chunk stage** (drop
  editorial chunks), or **post-embedding** (filter vectors).
- **How** to detect: markers/rules, curated per-text boundaries, TOC/structure, stylometric cues, a
  classifier/LLM, or embedding-space outliers.

Cross-cutting tensions: **precision vs recall** (dropping too much loses content), **effort vs scale**,
and **determinism/auditability** (a reproducible research pipeline strongly prefers deterministic,
auditable filtering).

## Approaches

### 1. Do nothing (baseline)
Keep everything; hope editorial prose averages out.
- **+** zero effort; no risk of dropping real content.
- **−** introductions can be long; contaminate clusters and per-tradition profiles with a modern
  academic register; the explicit goal is to remove it.

### 2. Curated per-text boundaries (markers in `config/corpus.json`) — trim at clean stage
Record, once per text, where the tradition body **begins and ends**, preferably as **heading-string /
regex markers** (`content_start`, `content_end`) rather than raw character offsets. Trim in the clean
step.
- **+** highest precision — you *know* what is included; deterministic and auditable; feasible at
  N≈28–100 in a single pass; committed as data; robust to per-edition formatting variety.
- **−** one-time manual labour; markers chosen by eye; edge cases (is an epic's proem part of the text?)
  need human judgement; does not scale to thousands; a re-download could shift a marker (mitigated by
  pinned/cached URLs and by using **heading markers**, which survive minor edits, over char offsets).

### 3. Generic marker / TOC heuristics — automatic trim
Rules: drop everything before the first "content" heading and after the last, by a denylist of editorial
section titles (`INTRODUCTION`, `PREFACE`, `TRANSLATOR'S NOTE`, `CONTENTS`, `NOTES`, `APPENDIX`,
`INDEX`, `GLOSSARY`, `CONCLUSION`…); for HTML editions use the heading structure.
- **+** cheap, deterministic, no per-text annotation; scales.
- **−** brittle — every edition formats differently; multilingual (markers differ per language);
  "Introduction" is sometimes part of the text itself; cannot catch **interleaved** notes/footnotes;
  false positives/negatives.

### 4. Stylometric / cue-based chunk filter — drop editorial chunks
At the chunk stage, drop chunks with modern-editorial signatures: footnote/citation markers (`[1]`,
`cf.`, `op. cit.`, `ibid.`), modern dates (1800–2000), meta-language ("the reader", "this
edition/translation", "I have rendered"), pagination artifacts.
- **+** cheap, interpretable, deterministic; catches **interleaved** editorial matter that boundary
  methods (2/3) miss; a good **complement**, not a replacement; adaptable per language via cue lists.
- **−** heuristic thresholds; false positives (a cue word can appear inside a translated myth); needs
  per-language cue lists; imperfect recall.

### 5. Classifier / LLM section classification
A model (zero-shot LLM or a light classifier) labels each chunk/section as **primary source (tradition
text)** vs **editorial (modern prose)**.
- **+** scales; handles variety and multiple languages; catches interleaved editorial matter; an LLM
  "understands" the difference between ancient narrative and a scholarly preface.
- **−** cost (LLM per chunk); **non-deterministic** (poor fit for a reproducible pipeline); needs
  validation; confuses edge cases (a modern retelling vs a translation; a scholarly summary embedded in
  the myth); adds a stage + a model dependency. **Best used one-off to *propose* boundaries for human
  review** (to accelerate approach 2), not as a standing filter.

### 6. Embedding-space outlier filtering (post-hoc)
Embed everything, then drop editorial chunks as outliers / a distinct cluster (modern academic prose
separates from ancient narrative), or by proximity to an "editorial" centroid (embeddings of a few known
prefaces).
- **+** no upfront segmentation; language-agnostic; catches editorial matter wherever it sits; reuses the
  embeddings being computed anyway.
- **−** post-hoc (GPU spent on noise first); fuzzy cluster boundary; risk of dropping genuine content in a
  modern style (recent translations); needs a threshold; harder to audit ("why was this dropped?").

## Summary

| Approach | Precision | Recall | Effort | Deterministic | Scales | Catches interleaved |
|---|---|---|---|---|---|---|
| 1 Do nothing | — | — | none | ✓ | ✓ | — |
| 2 Curated boundaries | **highest** | high | medium (one-off) | ✓ | ✗ | partial |
| 3 Auto markers / TOC | medium | medium | low | ✓ | ✓ | ✗ |
| 4 Stylometric chunk filter | medium | med–high | low | ✓ | ✓ | **yes** |
| 5 LLM / classifier | high | high | medium | ✗ | ✓ | yes |
| 6 Embedding outliers | medium | medium | low | ✗ | ✓ | yes |

## Empirical validation on the corpus

The two deterministic methods (3 auto markers and 4 stylometric cues) were run over the actual 28-text
corpus (`config/corpus.json` texts, cleaned with `clean_gutenberg_in_builder`). Method A = the editorial
heading denylist (`INTRODUCTION|PREFACE|CONTENTS|NOTES|APPENDIX|INDEX|GLOSSARY|…`); Method B = editorial
cue density (`[12]` footnote refs, `cf./ibid./op. cit.`, modern years `1600–1999`, meta-language "this
translation"/"the reader") measured per decile, expecting a **U-shape** (outer deciles ≫ middle) when
editorial matter sits at the front/back.

| Measure | Result |
|---|---|
| Front-matter heading detected | **25 / 28** |
| Back-matter heading detected | **15 / 28** |
| Body fully clean (zero cues in middle deciles) | **10 / 28** |
| U-shaped cue profile (outer/middle > 1) | **14 / 18** measurable |
| Outer/middle cue-density ratio | median **4.20**, mean **13.62** |

**Where it works.** Clean translations with separated apparatus are handled almost perfectly: 10 texts
have a completely cue-free body, with editorial matter strictly at the edges — *Odyssey* ×39, *Ramayan*
×80, *Kalevala* ×44, *West African Folk-Tales* ×27, *Te Tohunga* ×18. The heading anchor and the cue
profile agree: cut the edges, keep the body. Plain scripture with no apparatus (King James, Dhammapada,
Tao Teh King, Bhagavad Gita, Upanishads, Analects) is equally safe — nothing to strip, and the methods
strip nothing.

**Where it fails.**

- **Annotated critical editions** are the main failure mode: scholarly notes are interleaved line-by-line,
  so the U-shape collapses. *Poetic Edda* — 89 headings, ratio **0.78** (the denylist over-fires because
  "NOTES" is a per-poem heading, so heading position cannot define a single front/back boundary);
  *Beowulf* — ratio **0.86**, cues in every decile (`[6,12,11,10,13,10,14,12,9,13]`); *Nibelungenlied*
  **0.62**; *Koran* **1.40** (barely U-shaped). These are exactly the texts a boundary cut cannot handle.
- **Mid-document editorial headings**: *Mahabharata* (9 headings) and *Ramayan* carry structural book/parva
  titles resembling editorial sections, which naive "cut before first / after last heading" logic would
  mistake for boundaries.

**What this validates.** The layered conclusion below is confirmed by the numbers, and confirmed in the
specific way it claims: Method A is a reliable **front-matter anchor** (25/28) but weaker on back matter
(15/28) and must be guarded by an "is the heading near an edge?" check (or it over-fires on the Edda).
Method B is not itself a cutter but an excellent **validator/flagger**: it confirms a clean body (10/28
perfect) and, more usefully, flags the ~4 annotated editions where positional cutting is unsafe and
per-text or LLM handling is required. Neither method alone covers the corpus; ~2/3 clean automatically,
and the annotated remainder needs the curated/LLM layer — as the hybrid prescribes.

## Conclusion — a layered hybrid

For this project (small curated corpus, reproducibility matters, an existing per-text clean hook, but a
scaling ambition) the answer is not one method but a **layered hybrid**:

1. **Primary — curated per-text boundaries (approach 2), as heading markers** in `config/corpus.json`,
   applied in the clean stage. At N≈28–100 this gives maximum precision and full auditability for a
   bounded one-off effort. This is the anchor.
2. **Secondary — a stylometric cue filter (approach 4)** for the **interleaved** notes/footnotes that
   boundaries miss. Cheap, deterministic, complementary.
3. **LLM (approach 5) — one-off, not standing:** use it to **propose** boundaries for human review,
   removing most of the manual labour of step 1 while keeping human control and determinism.
4. **Embedding outliers (approach 6) — as QA/audit**, not the primary filter: run after embedding to
   check whether editorial prose leaked through, feeding back into steps 1–2.

Avoid as the **basis**: pure generic-marker automation (3) — too brittle across mixed editions — and
LLM/outlier methods as the standing filter (non-determinism in a reproducible pipeline).

In short: **per-text heading-marker boundaries as the anchor (with an LLM assist for annotation), plus a
stylometric filter for interleaved editorial matter, with embedding-outlier detection as a QA check.**
Maximum precision at controlled effort, deterministic, and it grows into scale through layers 4–5.

## Suggested first implementation step

Extend the `config/corpus.json` entry schema with optional `content_start` / `content_end` (heading
strings or regexes) and extend `clean_gutenberg_in_builder` (or a new clean step) to trim to those
markers when present; add a small, per-language cue denylist applied at the chunk stage. Both are
deterministic and committed as data.
