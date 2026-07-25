"""The motifs stages — the folklore-index mini-pipeline atomised onto the driver:

    source:berezkin ┐
    source:tmi      ┼─► crosswalk ─► parallels ─┐
    source:atu      ┘        │                  ├─► meta
           └─────────────────┴─► semantic ──────┘

Each stage wraps one ``_build_*`` helper (in ``motifs.build_motifs``) and gates on its own fp
sidecar (``outputs/motifs/.fp.<stage>``): sources on their per-source raw fp (isolated, so one
source's raw change never rebuilds another), the derived stages on a fold of their inputs' fps.
Build stays offline — the source builds fold enrichment from the pinned raw cache and never
re-fetch (that is ``refresh``). These stages, sequenced by the driver, ARE the motifs build now:
the monolithic ``build_motifs`` orchestrator and the coarse ``MotifsStage`` are both retired.
"""

from __future__ import annotations

from json_utils import load_json_optional
from motifs import store
from motifs.build_motifs import (
    _build_atu,
    _build_berezkin,
    _build_crosswalk,
    _build_meta,
    _build_parallels,
    _build_semantic,
    _build_tmi,
    _load_config,
    _log_summary,
)
from motifs.fingerprint import combine_fingerprints, semantic_fingerprint, source_fingerprint
from motifs.refresh import Fetchable, RefreshResult, refresh_fetchables
from motifs.sources import (
    ashliman,
    atu_wikidata,
    berezkin,
    berezkin_bibliography,
    bibliography,
    mapsofmyths,
    trilogy,
)

from ..stage import Stage


def _fp_path(name: str):
    return store.motifs_dir() / f".fp.{name}"


def _drop(*paths) -> None:
    """Level-1 clean: remove a stage's artifact(s) + fp sidecar so a driver `clean --apply` on an
    orphaned motifs stage (e.g. a source disabled in config) actually reaps it, not a silent no-op."""
    for p in paths:
        p.unlink(missing_ok=True)


class SourceStage(Stage):
    """Base for the three source index stages (``berezkin`` / ``tmi`` / ``atu``): parse this source's
    raw + fold its enrichment, write ``<source>.json`` + the enrichment sidecar. Offline build
    (``force=False`` reuses the pinned cache, never re-fetches); disabled in config → no desired key.

    Each concrete source is **self-contained**: it names its own build fn, config flag, and — for
    ``refresh`` — its own ``fetchables()`` composed from the source modules it owns. Drop a source
    (delete its subclass + modules) and its whole fetch/build/refresh goes with it; nothing central
    lists it. Shared machinery (the fp gate here, the ``refresh_fetchables`` engine) is the base."""

    store = None
    source: str
    _flag: str  # config key whose ``enabled`` gates this source (tmi/atu share ``trilogy``)

    @property
    def name(self) -> str:
        return f"motifs:source:{self.source}"

    def inputs(self) -> list[Stage]:
        return []

    def _build_source(self, config: dict) -> None:
        raise NotImplementedError

    def fetchables(self) -> list[Fetchable]:
        """The upstream resources this source owns — what ``refresh`` re-checks. Composed here from
        the source's own modules, so it lives and dies with the source."""
        raise NotImplementedError

    def _enabled(self) -> bool:
        return _load_config().get(self._flag, {}).get("enabled", True)

    def desired(self) -> dict[str, str]:
        return {self.source: source_fingerprint(self.source)} if self._enabled() else {}

    def actual(self) -> dict[str, str]:
        fp = _fp_path(f"source.{self.source}")
        if store.index_path(self.source).exists() and fp.exists():
            return {self.source: fp.read_text(encoding="utf-8").strip()}
        return {}

    def build(self, keys: set[str]) -> None:
        self._build_source(_load_config())
        _fp_path(f"source.{self.source}").write_text(source_fingerprint(self.source), encoding="utf-8")

    def refresh(self, *, apply: bool = False) -> RefreshResult:
        """Re-check this source's upstream against its pinned raw (§9): diff / keep-pinned / adopt."""
        return refresh_fetchables(self.fetchables(), apply=apply)

    def delete(self, keys: set[str]) -> None:
        _drop(store.index_path(self.source), _fp_path(f"source.{self.source}"),
              store.enrichment_path(self.source), store.discovered_path(self.source))


class BerezkinSource(SourceStage):
    source, _flag = "berezkin", "berezkin"

    def _build_source(self, config: dict) -> None:
        _build_berezkin(config, force=False)

    def fetchables(self) -> list[Fetchable]:
        cfg = _load_config()
        return [*berezkin.fetchables(cfg.get("berezkin", {})),
                *mapsofmyths.fetchables(), *berezkin_bibliography.fetchables()]


class TmiSource(SourceStage):
    source, _flag = "tmi", "trilogy"

    def _build_source(self, config: dict) -> None:
        _build_tmi(config, force=False)

    def fetchables(self) -> list[Fetchable]:
        return [*trilogy.fetchables(_load_config(), "tmi"), *bibliography.fetchables()]


class AtuSource(SourceStage):
    source, _flag = "atu", "trilogy"

    def _build_source(self, config: dict) -> None:
        _build_atu(config, force=False)

    def fetchables(self) -> list[Fetchable]:
        return [*trilogy.fetchables(_load_config(), "atu"),
                *atu_wikidata.fetchables(), *ashliman.fetchables()]


class CrosswalkStage(Stage):
    """Cross-walk over the three source indexes (reloaded + re-derived via ``motifs.derive``).
    fp = fold of the three sources' fps, so it goes stale whenever any source does."""

    store = None
    name = "motifs:crosswalk"

    def __init__(self, sources: list[SourceStage]):
        self._sources = sources

    def inputs(self) -> list[Stage]:
        return list(self._sources)

    def _fp(self) -> str:
        parts = [s.desired().get(s.source, "") for s in self._sources]
        return combine_fingerprints("crosswalk", *parts)

    def desired(self) -> dict[str, str]:
        return {"crosswalk": self._fp()}

    def actual(self) -> dict[str, str]:
        fp = _fp_path("crosswalk")
        if store.crosswalk_path().exists() and fp.exists():
            return {"crosswalk": fp.read_text(encoding="utf-8").strip()}
        return {}

    def build(self, keys: set[str]) -> None:
        _build_crosswalk()
        _fp_path("crosswalk").write_text(self._fp(), encoding="utf-8")

    def delete(self, keys: set[str]) -> None:
        _drop(store.crosswalk_path(), _fp_path("crosswalk"))


class ParallelsStage(Stage):
    """Heuristic textual parallels — reloads the cross-walk from disk and passes it to the
    lexical matcher. fp folds the cross-walk fp (which already folds the sources)."""

    store = None
    name = "motifs:parallels"

    def __init__(self, crosswalk: CrosswalkStage):
        self._crosswalk = crosswalk

    def inputs(self) -> list[Stage]:
        return [self._crosswalk]

    def _fp(self) -> str:
        return combine_fingerprints("parallels", self._crosswalk.desired().get("crosswalk", ""))

    def desired(self) -> dict[str, str]:
        return {"parallels": self._fp()}

    def actual(self) -> dict[str, str]:
        fp = _fp_path("parallels")
        if store.parallels_path().exists() and fp.exists():
            return {"parallels": fp.read_text(encoding="utf-8").strip()}
        return {}

    def build(self, keys: set[str]) -> None:
        _build_parallels(load_json_optional(store.crosswalk_path()) or {})
        # sklearn absent / no TMI+ATU → _build_parallels writes no parallels.json; don't stamp the
        # fp over a missing artifact (actual() would stay {} → the stage would never reconcile).
        if store.parallels_path().exists():
            _fp_path("parallels").write_text(self._fp(), encoding="utf-8")

    def delete(self, keys: set[str]) -> None:
        _drop(store.parallels_path(), _fp_path("parallels"))


class SemanticStage(Stage):
    """Copy-in of the committed, precomputed BGE-M3 semantic parallels. fp = hash of the
    committed file, so a new committed file rebuilds; absent file → no desired key."""

    store = None
    name = "motifs:semantic"

    def inputs(self) -> list[Stage]:
        return []

    def desired(self) -> dict[str, str]:
        fp = semantic_fingerprint()
        return {"semantic": fp} if fp else {}

    def actual(self) -> dict[str, str]:
        fp = _fp_path("semantic")
        if store.semantic_parallels_path().exists() and fp.exists():
            return {"semantic": fp.read_text(encoding="utf-8").strip()}
        return {}

    def build(self, keys: set[str]) -> None:
        _build_semantic()
        fp = semantic_fingerprint()
        if fp:
            _fp_path("semantic").write_text(fp, encoding="utf-8")

    def delete(self, keys: set[str]) -> None:
        _drop(store.semantic_parallels_path(), _fp_path("semantic"))


class MetaStage(Stage):
    """Final aggregator: assembles ``meta.json`` (counts, enrichment, tallies, degradation guard)
    entirely from what the upstream stages wrote to disk. fp folds every upstream fp, so meta
    rebuilds whenever anything upstream changes."""

    store = None
    name = "motifs:meta"

    def __init__(self, upstream: list[Stage]):
        self._upstream = upstream

    def inputs(self) -> list[Stage]:
        return list(self._upstream)

    def _fp(self) -> str:
        parts: list[str] = []
        for s in self._upstream:
            parts.extend(sorted(s.desired().values()))  # sorted: a stage's key set is unordered
        return combine_fingerprints("meta", *parts)

    def desired(self) -> dict[str, str]:
        return {"meta": self._fp()}

    def actual(self) -> dict[str, str]:
        fp = _fp_path("meta")
        if store.meta_path().exists() and fp.exists():
            return {"meta": fp.read_text(encoding="utf-8").strip()}
        return {}

    def build(self, keys: set[str]) -> None:
        counts, links, par_counts = _build_meta(_load_config())
        _log_summary(counts, links, par_counts)   # final cross-index rollup (was the monolith's tail)
        _fp_path("meta").write_text(self._fp(), encoding="utf-8")

    def delete(self, keys: set[str]) -> None:
        _drop(store.meta_path(), _fp_path("meta"))


def motifs_stages() -> list[Stage]:
    """The atomised motifs sub-pipeline, in declaration (topological tie-break) order."""
    sources = [BerezkinSource(), TmiSource(), AtuSource()]
    crosswalk = CrosswalkStage(sources)
    parallels = ParallelsStage(crosswalk)
    semantic = SemanticStage()
    meta = MetaStage([*sources, crosswalk, parallels, semantic])
    return [*sources, crosswalk, parallels, semantic, meta]
