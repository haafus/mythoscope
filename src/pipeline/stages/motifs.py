"""The motifs stages — the folklore-index mini-pipeline atomised onto the driver:

    source:berezkin ┐
    source:tmi      ┼─► crosswalk ─► parallels ─┐
    source:atu      ┘        │                  ├─► meta
           └─────────────────┴─► semantic ──────┘

Each stage wraps one ``build_motifs`` build function and gates on its own fp sidecar
(``outputs/motifs/.fp.<stage>``): sources on their per-source raw fp (isolated, so one
source's raw change never rebuilds another), the derived stages on a fold of their inputs'
fps. Build stays offline — the source builds fold enrichment from the pinned raw cache and
never re-fetch (that is ``refresh``). ``MotifsStage`` (the coarse monolith adapter) is kept
for now and retired once these subsume it.
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
    build_motifs,
)
from motifs.fingerprint import (
    combine_fingerprints,
    motifs_fingerprint,
    semantic_fingerprint,
    source_fingerprint,
)

from ..stage import Stage

_KEY = "motifs"


class MotifsStage(Stage):
    name = "motifs"
    store = None  # singleton — never orphaned within the pipeline

    def inputs(self) -> list[Stage]:
        return []  # its sources are external scrapes, not the corpus

    def desired(self) -> dict[str, str]:
        return {_KEY: motifs_fingerprint()}

    def actual(self) -> dict[str, str]:
        fp_path = store.motifs_dir() / ".fp"
        if store.is_built() and fp_path.exists():
            return {_KEY: fp_path.read_text(encoding="utf-8").strip()}
        return {}

    def build(self, keys: set[str]) -> None:
        build_motifs()

    def delete(self, keys: set[str]) -> None:
        pass  # singleton; never an orphan key


# --- atomised stages ---------------------------------------------------------------------

def _fp_path(name: str):
    return store.motifs_dir() / f".fp.{name}"


# source → (build fn, config flag gating it). TMI and ATU both live under the trilogy flag.
_SOURCES = {
    "berezkin": (_build_berezkin, "berezkin"),
    "tmi": (_build_tmi, "trilogy"),
    "atu": (_build_atu, "trilogy"),
}


class SourceStage(Stage):
    """One source index (``berezkin`` / ``tmi`` / ``atu``): parse its raw + fold its enrichment,
    write ``<source>.json`` + the enrichment sidecar. Offline — ``force=False`` reuses the pinned
    cache, never re-fetches. Disabled in config → no desired key (nothing to build)."""

    store = None

    def __init__(self, source: str):
        self.source = source
        self.name = f"motifs:source:{source}"
        self._build, self._flag = _SOURCES[source]

    def inputs(self) -> list[Stage]:
        return []

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
        self._build(_load_config(), force=False)
        _fp_path(f"source.{self.source}").write_text(source_fingerprint(self.source), encoding="utf-8")

    def delete(self, keys: set[str]) -> None:
        pass


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
        pass


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
        _fp_path("parallels").write_text(self._fp(), encoding="utf-8")

    def delete(self, keys: set[str]) -> None:
        pass


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
        pass


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
        _build_meta(_load_config())
        _fp_path("meta").write_text(self._fp(), encoding="utf-8")

    def delete(self, keys: set[str]) -> None:
        pass


def motifs_stages() -> list[Stage]:
    """The atomised motifs sub-pipeline, in declaration (topological tie-break) order."""
    sources = [SourceStage("berezkin"), SourceStage("tmi"), SourceStage("atu")]
    crosswalk = CrosswalkStage(sources)
    parallels = ParallelsStage(crosswalk)
    semantic = SemanticStage()
    meta = MetaStage([*sources, crosswalk, parallels, semantic])
    return [*sources, crosswalk, parallels, semantic, meta]
