# Unified proposal: one tradition entity — taxonomy, presentation, and code

Synthesises five point-in-time reviews and the converged taxonomy into a single architecture. It replaces
five overlapping, string-driven ad-hoc systems with **one canonical, id-keyed, faceted `Tradition` entity**
whose geographic axis (`area`) is the single region vocabulary, and from which colour and grouping are
**derived deterministically** rather than authored or randomised.

> **Canon.** The `region` axis is canonically specified in [`regions.md`](../regions.md) —
> the definitive **14-region** classification (names, descriptions, subdivisions, strata, per-region traditions,
> palette). It is the corpus-first successor to the retired `major_tradition` and to Berezkin's 12-area `area`
> scaffold this proposal still calls `area` below; **where this document and `regions.md` diverge, `regions.md`
> is authoritative.**
>
> **Single-axis decision (2026-07):** the multi-facet Tradition model below (`family`, `subsistence`,
> `theme_profile`) is **not adopted** — a tradition has one classification axis, `region`, and no facet layer.
> `family`/`subsistence` are dropped; the facet material here is retained only as the exploration that led to
> that decision.

Sources folded in:
[`../reviews/archive/tradition-review.md`](../../reviews/archive/tradition-review.md) ·
[`../reviews/archive/major-tradition-review.md`](../../reviews/archive/major-tradition-review.md) ·
[`../reviews/archive/color-system-review.md`](../../reviews/archive/color-system-review.md) ·
[`tradition-taxonomy-final.md`](tradition-taxonomy-final.md) ·
[`macro-area-facets.md`](macro-area-facets.md) ·
[`../known-issues.md`](../../known-issues.md) §competing macro-area schemes.

---

## 1. The five reviews, one root cause

| Review | The pain it found |
|---|---|
| **tradition** | A free **string** is the identity, the join key, the group label and the colour seed all at once. Two config files join by exact string equality with **no validation** → a typo silently degrades colour, coordinates, major, and map presence. |
| **major_tradition** | Derived + **denormalised** onto every row/chunk, **thrown away** in served `traditions.json` (asymmetry), transported-but-unused on similarity, and the tree itself is an **eclectic mix of axes** (language + religion + geography + ethnos). |
| **colour** | **Non-deterministic** `random.randint` reshuffles every build; no contrast control; unrelated to any structure; 5–6 "no colour" defaults (partly unified). |
| **taxonomy (converged)** | The real answer is a **multi-facet entity model**, audited and validated — but **not wired into the pipeline**. |
| **macro-areas** | **Six** non-aligned "region" vocabularies; the same motif page names regions two ways on one screen. |

**Root cause (one sentence):** there is no single canonical `Tradition` entity with a stable id and
principled facets — a name-string is overloaded as identity + join + label + colour seed, and "region" is
re-invented six times. Everything below follows from fixing exactly that.

---

## 2. Taxonomy layer — the target model

A **canonical `Tradition`** identified by a stable `id` (slug), with a display `name` and a set of
**facets**; region is **one** vocabulary, `area`.

```
Tradition {
  id            # stable slug — the join key everywhere ("norse", "greek")
  name          # display only ("Norse")
  area          # 12 macro-areas — THE single region axis (scheme #6, from areal_path)
  family        # ~11 language/religion families (the descent backbone)
  subsistence   # 4 economy types (targeted covariate)
  coordinates   # for the map
  # theme_profile is DERIVED (from motif attestations), not stored authored
}
Motif { theme (A/B → 13), stratum (7, derived from distribution) }   # depth is a MOTIF property
```

Facet roles are **not co-equal** (adequacy audit, mockup 32): `area` + `theme_profile` are load-bearing,
`family` is the descent backbone (dating/ASR, not a motif predictor), `subsistence` is a covariate and the
drop-candidate. **12 areas / 11 families** is the optimal granularity. The facets recover ~36 % of motif
similarity; the residual gets a future **connectivity** axis. (Full detail:
[`tradition-taxonomy-final.md`](tradition-taxonomy-final.md).)

**The six region schemes collapse onto `area`:**

| Old scheme | Fate |
|---|---|
| #1 Berezkin broad (11), #3 Berezkin hierarchy (16) | fold into `area` via one curated `code → area` bridge (both are the same 59-area system) |
| #4 `major_tradition` tree (12, eclectic) | **retired** — `area` does the geography, `family` does the cultural grouping |
| #5 `REGION_COLORS` palette | **re-keyed** to the 12 `area` names (becomes a derived colour ramp, §3) |
| #6 proposed `area` facet | **becomes the one vocabulary** |
| #2 TMI culture regions (12) | stays source-native (Thompson has no areal codes) but ships an `area` cross-map for cross-referencing |

---

## 3. Presentation / UI layer

**Colour lives only at the region level** (single-colour decision, 2026-07): a tradition has no colour of its
own — it takes its **region's** colour. *(This supersedes the earlier per-tradition "gradient within the
macro-area" — `L/S = f(index of tradition within its area)` — struck below; there is no within-region
per-tradition shade.)* Consequences:

- kin traditions share a **family tone** (Greek/Roman/Norse read as one Indo-European hue band);
- an `area` is recognisable by hue in **every** view — corpus map, motif region bars, embeddings scatter;
- **one legend** of 12 areas everywhere — the "chart says X, Traditions section says Y" clash disappears
  because both draw from the same `area` and the same ramp;
- no build reshuffles it (deterministic), and contrast is controlled (spread within a known band).

**One "unassigned" presentation** — a single grey token (extend the already-landed `CATEGORY_NONE`) and one
`—/Unassigned` label, instead of `""` / `unknown` / `Unknown` / `Other` scattered by view.

---

## 4. Architecture / code / pipeline layer

> **Superseded by [`region-implementation.md`](../region-implementation.md).** §4 and §6 below still assume the
> retired facet model (`area`/`family`/`subsistence`, area-gradient colour, facet selector). The live,
> decision-reconciled code plan — region only, colour from the region palette — is in `region-implementation.md`;
> read that for implementation. §4/§6 here are kept as the reasoning that led to it.

**4.1 One source of truth, id-keyed.** `config/traditions.json` becomes a registry keyed by `id`; each entry
carries `name` + facets (`area`, `family`, `subsistence`, `coordinates`, `language`, `areal_id`). Books in
`config/corpus.json` reference `tradition_id`, not a display string.

**4.2 Kill the silent join — validate at build.** If a book's `tradition_id` is absent from the registry,
the build **fails loudly** (today `traditions_info.get()` returns `{}` and everything degrades to defaults in
silence). Names become display-only; all joins are by `id`.

**4.3 Derive, don't author or randomise.**
- `area = area(areal_path)` — a pure function (productionise mockup 21's recipe as `src/…/region_facets.py`),
  run over both the corpus and the 1046-tradition Berezkin catalogue.
- `colour = f(area, index_within_area)` — deterministic, replaces `random.randint`; drops colour storage and
  both transport tracks (the front end can compute it).
- `major_tradition` is **retired** (its geography → `area`, its grouping → `family`), removing the derived
  field, its denormalisation, and its served-store asymmetry.

**4.4 Served model, normalised.** Served `traditions.json` carries the full facet set **once per tradition**
(`id → {name, area, family, subsistence, colour, coordinates}`). Catalog documents carry only `tradition_id`
(+ optionally a denormalised `name` for convenience); the front end joins facets from the single traditions
map. Drop the transported-but-unused `major_tradition` from `SearchResult`.

**4.5 Chroma metadata.** Store the stable `tradition_id` on each chunk (not the mutable display name, and not
a denormalised facet bundle); facets are looked up from the registry at query time.

**4.6 One default constant.** Extend the `CATEGORY_NONE` unification to the *value* layer: a single
`UNASSIGNED` id/label across `schemas.py`, `iterator.py`, and the front end.

---

## 5. Traceability — which review pain each change closes

| Change | tradition | major | colour | taxonomy | macro-areas |
|---|:--:|:--:|:--:|:--:|:--:|
| `id` identity + build validation | ✓ (fragile join, no identity) | | | | |
| Retire `major_tradition` → `area`/`family` | | ✓ (derived/denorm/asymmetry) | | ✓ | ✓ |
| Facet registry (`area/family/subsistence`) | | ✓ (eclectic tree) | | ✓ (wire in) | ✓ (#6) |
| Deterministic area-gradient colour | | | ✓ (random/contrast) | | ✓ (#5 re-key) |
| Collapse six schemes onto `area` | | | | | ✓ |
| Single `UNASSIGNED` default | ✓ | ✓ | ✓ | | |

---

## 6. Migration order (each phase shippable on its own)

1. **Identity + validation.** Add `id` to the registry and `tradition_id` to books; build-time validation;
   name → display-only. *(Closes the biggest risk — the silent string join — with no behaviour change.)*
2. **Facet registry + `region_facets.py`.** Populate `area/family/subsistence` deterministically; wire `area`
   into geography grouping alongside the existing tree.
3. **Area-gradient colour.** Replace random colour with `f(area, index)`; re-key `REGION_COLORS` to the 12
   areas; one legend.
4. **Retire `major_tradition`.** Switch UI grouping to the `area`/`family` facet selector; delete the derived
   field, its denormalisation, and the dead `SearchResult.major_tradition`.
5. **Collapse region schemes.** The `code → area` bridge folds #1/#3; TMI (#2) ships its `area` cross-map.
6. **One `UNASSIGNED` default** across schemas, iterator, front end.

Phase 1 is the highest value-to-risk; 3 is the most visible; 4–5 are the cleanup that makes "region"
unambiguous.

---

## 7. What deliberately stays separate / open

- **TMI (#2)** is intrinsically its own scheme (Thompson culture labels, no areal codes) — it maps to `area`
  for cross-reference but never fully merges.
- **The connectivity axis** and node-level dating remain future work (the ~64 % residual); this proposal
  fixes the classification and its plumbing, not the science of the residual.
- **Two theme axes** (etiological + narrative) productionisation is its own milestone (Element ch. 10); this
  proposal only reserves the UI toggle and the `theme_profile` derivation slot for it.

---

*Status: proposal. Nothing here is implemented; it consolidates the five reviews and the converged taxonomy
into one target architecture and a phased path. The facet model is validated in mockups 15/16/21/23/32/42/43;
the plumbing changes are new.*
