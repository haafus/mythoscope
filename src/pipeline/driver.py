"""The one generic driver: every operation is a diff of ``desired()`` vs ``actual()``.

``status`` (report the diff), ``build`` (make ``missing``/``stale`` real), and ``clean``
(reap ``orphans``) are one traversal over the same two maps — not four bespoke paths. The
engine is **stateless**: the registry is ``build_pipeline()``'s output, the state is each
stage's ``actual()`` on disk. See ``docs/proposals/pipeline-and-incrementality.md`` §2.6–2.7.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .stage import Stage


@dataclass(frozen=True)
class StagePlan:
    """The per-stage diff: what the driver would build vs reap."""

    stage: Stage
    missing: set[str] = field(default_factory=set)  # should exist, doesn't → build
    stale: set[str] = field(default_factory=set)    # exists, fp diverged  → rebuild
    orphans: set[str] = field(default_factory=set)   # exists, shouldn't    → clean (level 1)

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
    return StagePlan(stage=stage, missing=dk - ak, stale=stale, orphans=ak - dk)


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

    ``sample`` (a doc-count smoke throttle) caps the per-run build of the ``sampleable`` stage
    (the corpus root) to at most N keys — a quick end-to-end run over N documents. It limits
    *throughput*, not the spec: ``desired()`` is untouched, so the unbuilt keys stay ``missing``
    (not orphan) and a later full ``build`` simply completes them — no re-fetch, no churn. Plans
    are computed per stage after its upstream builds, so the fan-out stages downstream of the
    capped corpus see only N documents and follow automatically; ``sample`` is applied to the
    root alone.

    ``build`` is offline: a stage acquires missing inputs from its own pinned cache, never the
    network — re-fetching is the separate ``refresh`` path."""
    acted: list[StagePlan] = []
    for stage in topo_order(stages):
        if targets is not None and stage.name not in targets:
            continue  # in the list only to wire/order the targets — not itself requested
        p = plan(stage)
        todo = set(stage.desired()) if force else p.to_build
        if sample is not None and stage.sampleable:
            todo = set(sorted(todo)[:sample])  # cap the root; downstream follows via its fps
        if todo:
            stage.build(todo)
        acted.append(p)
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

    # Group ALL stages by their shared store (for a correct claimed set), but reap only the
    # stores that a target stage owns.
    stores: dict[int, tuple[object, set[str]]] = {}
    target_stores: set[int] = set()
    for stage in ordered:
        if stage.store is not None:
            sid = id(stage.store)
            store, claimed = stores.setdefault(sid, (stage.store, set()))
            claimed.add(stage.id)
            if wanted(stage):
                target_stores.add(sid)
    level2: dict[str, set[str]] = {}
    for sid, (store, claimed) in stores.items():
        if sid not in target_stores:
            continue
        orphan_ids = store.ids() - claimed
        if orphan_ids:
            level2[type(store).__name__] = orphan_ids
            if apply:
                for oid in orphan_ids:
                    store.delete(oid)

    return CleanReport(level1=level1, level2=level2)
