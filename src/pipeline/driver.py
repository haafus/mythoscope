"""The one generic driver: every operation is a diff of ``desired()`` vs ``actual()``.

``status`` (report the diff), ``build`` (make ``missing``/``stale`` real), and ``clean``
(reap ``orphans``) are one traversal over the same two maps — not four bespoke paths. The
engine is **stateless**: the registry is ``build_pipeline()``'s output, the state is each
stage's ``actual()`` on disk. See ``docs/proposals/pipeline-and-incrementality.md`` §2.6–2.7.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field, replace

from .stage import Stage

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class StagePlan:
    """The per-stage diff: what the driver would build vs reap."""

    stage: Stage
    missing: set[str] = field(default_factory=set)  # should exist, doesn't → build
    stale: set[str] = field(default_factory=set)    # exists, fp diverged  → rebuild
    orphans: set[str] = field(default_factory=set)   # exists, shouldn't    → clean (level 1)
    built: set[str] = field(default_factory=set)     # keys actually built this run (post-build actual ∩ todo)
    desired_count: int = 0                            # |desired()| — total elements the stage should hold (the check total)
    planned_count: int = 0                            # keys this run set out to build (todo: missing+stale, or all on --force, capped by --sample) — the denominator for "built N/planned"

    @property
    def to_build(self) -> set[str]:
        return self.missing | self.stale

    @property
    def clean(self) -> bool:
        return not (self.missing or self.stale or self.orphans)


def topo_order(stages: list[Stage]) -> list[Stage]:
    """Order stages so each follows all of its ``inputs()`` — a stable topological sort.

    Ties (independent / same-depth stages) break by **declaration order** in ``stages``, so
    the walk reproduces the registry's intended sequence. Raises on an input outside the
    pipeline or a dependency cycle (both before any real work)."""
    order = {id(s): i for i, s in enumerate(stages)}
    known = {id(s) for s in stages}
    for s in stages:
        for inp in s.inputs():
            if id(inp) not in known:
                raise ValueError(
                    f"stage {s.name!r} depends on {getattr(inp, 'name', inp)!r}, "
                    "which is not in the pipeline"
                )

    placed: list[Stage] = []
    placed_ids: set[int] = set()
    remaining = list(stages)
    while remaining:
        ready = [s for s in remaining if all(id(inp) in placed_ids for inp in s.inputs())]
        if not ready:
            cycle = ", ".join(s.name for s in remaining)
            raise ValueError(f"dependency cycle among stages: {cycle}")
        nxt = min(ready, key=lambda s: order[id(s)])  # stable: earliest-declared ready stage
        placed.append(nxt)
        placed_ids.add(id(nxt))
        remaining.remove(nxt)
    return placed


def plan(stage: Stage) -> StagePlan:
    """Diff one stage's ``desired()`` against its ``actual()``."""
    d, a = stage.desired(), stage.actual()
    dk, ak = set(d), set(a)
    stale = {k for k in dk & ak if d[k] != a[k]}
    return StagePlan(stage=stage, missing=dk - ak, stale=stale, orphans=ak - dk, desired_count=len(dk))


def status(stages: list[Stage]) -> list[StagePlan]:
    """The full diff, in topological order — the shared basis for status/build/clean."""
    return [plan(s) for s in topo_order(stages)]


def build(stages: list[Stage], *, force: bool = False, targets: set[str] | None = None,
          sample: int | None = None) -> list[StagePlan]:
    """Build ``missing``/``stale`` per stage in topological order (``force`` → rebuild every
    ``desired()`` key, ignoring the fingerprint gate). Returns the plan acted on per stage.

    ``targets`` (a set of stage names) restricts building to exactly those stages — the scope
    is literal: an upstream dependency present only for wiring/ordering is **not** rebuilt, even
    if stale (a scoped ``build X`` does X and nothing else; a full ``build`` cascades). ``None``
    builds every stage.

    ``sample`` caps every stage's per-run build to at most N keys. Throughput only: ``desired()``
    is untouched, so skipped keys stay ``missing`` (not orphan) and a later full ``build``
    completes them. Single-key stages (projections/motifs) are unaffected (``[:N≥1]`` is a no-op).

    ``build`` is offline: a stage acquires missing inputs from its own pinned cache, never the
    network — re-fetching is the separate ``refresh`` path."""
    acted: list[StagePlan] = []
    for stage in topo_order(stages):
        if targets is not None and stage.name not in targets:
            continue  # in the list only to wire/order the targets — not itself requested
        # Header BEFORE plan() — the check itself (desired()/actual(): reading Chroma, loading a
        # model, walking the corpus) can be the slow part, so this attributes that pause to a stage.
        logger.info("=== %s ===", stage.name)
        p = plan(stage)
        todo = set(stage.desired()) if force else p.to_build
        if sample is not None:
            todo = set(sorted(todo)[:sample])
        logger.info("  check: %d total, %d missing, %d stale%s -> %d to build",
                    p.desired_count, len(p.missing), len(p.stale),
                    " (force)" if force else "", len(todo))
        built: set[str] = set()
        if todo:
            stage.build(todo)
            built = todo & set(stage.actual())   # what is *actually* built now — a per-key failure
            logger.info("  build: %d/%d built", len(built), len(todo))
        else:
            logger.info("  build: up to date")
        acted.append(replace(p, built=built, planned_count=len(todo)))  # (no fp sidecar) drops out, so N/planned is honest
    return acted


@dataclass(frozen=True)
class CleanReport:
    """What ``clean`` reaped (or would reap, on a dry run)."""

    level1: dict[str, set[str]] = field(default_factory=dict)   # stage.name → orphan keys
    level2: dict[str, set[str]] = field(default_factory=dict)   # stage.name → orphan store ids

    @property
    def empty(self) -> bool:
        return not any(self.level1.values()) and not any(self.level2.values())


def clean(stages: list[Stage], *, apply: bool = False, targets: set[str] | None = None) -> CleanReport:
    """Reap orphans at two levels:

    * **level 1** — orphan *keys* inside a surviving stage (a removed document): ``a − d``.
    * **level 2** — a whole *stage* removed from the pipeline leaves its shared-store artifact
      unowned; it never enters the per-key diff, so we ask each store which ids it holds and
      subtract the ids still claimed by a live stage.

    ``targets`` (stage names) restricts *what is reaped* to those stages (and the stores they
    own); every stage still contributes to each store's claimed-id set, so a scoped clean never
    mistakes a non-target stage's live artifact for an orphan. ``None`` reaps across all stages.

    **Level-2 is family-granular.** An orphan (a dropped model's collection) has no live stage, so
    it can be attributed to its store's *family* (``embeddings``) but not to a single member. A
    scoped clean therefore reaps a store's orphans only when the scope covers the store's **whole
    family** (all its live stages) — ``clean embeddings`` or an unscoped ``clean`` — and leaves them
    untouched under a single-member scope (``clean embeddings:modelA`` no longer sweeps a dropped
    ``modelC``). A live artifact is never reaped (all stages contribute claims); a dropped model is
    still cleaned via the family scope or a full ``clean``.
    """
    ordered = topo_order(stages)

    def wanted(stage: Stage) -> bool:
        return targets is None or stage.name in targets

    level1: dict[str, set[str]] = {}
    for stage in ordered:
        if not wanted(stage):
            continue
        orphans = plan(stage).orphans
        if orphans:
            level1[stage.name] = orphans
            if apply:
                stage.delete(orphans)

    # Group ALL stages by their shared store (for a correct claimed set + the store's full family),
    # but reap only the stores a target stage owns, and only at family granularity (see docstring).
    stores: dict[int, tuple[object, set[str], set[str]]] = {}   # sid → (store, claimed ids, stage names)
    target_stores: set[int] = set()
    for stage in ordered:
        if stage.store is not None:
            sid = id(stage.store)
            store, claimed, names = stores.setdefault(sid, (stage.store, set(), set()))
            claimed.add(stage.id)
            names.add(stage.name)
            if wanted(stage):
                target_stores.add(sid)
    level2: dict[str, set[str]] = {}
    for sid, (store, claimed, names) in stores.items():
        if sid not in target_stores:
            continue
        if targets is not None and not names <= targets:
            continue   # single-member scope → don't touch sibling orphans (family granularity only)
        orphan_ids = store.ids() - claimed
        if orphan_ids:
            level2[getattr(store, "label", type(store).__name__)] = orphan_ids
            if apply:
                for oid in orphan_ids:
                    store.delete(oid)

    return CleanReport(level1=level1, level2=level2)
