"""Staged per-source refresh for the motif sources — the fetch/refresh boundary (fetch-and-refresh
§2, §7, §9) applied to motifs, mirroring ``corpus.refresh``.

``build`` never re-fetches present raw; ``refresh`` is the deliberate, networked re-check. Each
source enumerates its **fetchables** (a resource = one URL ↔ one pinned cache file); this engine
downloads each fresh, diffs it against the pinned copy, classifies the outcome, and **keeps the
pinned bytes by default** — a genuine change is adopted (``os.replace`` via ``commit_bytes``) only
on ``apply``. The diff is over *raw bytes*, so no parsing happens here (that stays in the source
stages' build); refresh is purely the boundary operation on the raw input edge.

Ephemeral by design (§9): no durable needs-review record — re-running re-derives the same diff
from upstream-vs-pinned, so a pending ``changed`` simply reappears. The only durable flags are the
build-time silent-degradation ones in ``meta.json`` (``yield-drop``), untouched here.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from fetch_cache import commit_bytes, read_pinned

# §9 status vocabulary (column 2) and the action each maps to (column 3).
NOT_CHANGED, CHANGED, DEGRADED, GONE, NEW = "not changed", "changed", "degraded", "gone", "new"
_ACTION = {NOT_CHANGED: "keep cached", DEGRADED: "keep cached", GONE: "keep cached",
           NEW: "acquire on apply", CHANGED: "adopt on apply"}


@dataclass(frozen=True)
class Fetchable:
    """One refreshable resource: a URL and the pinned cache file it maps to. ``validate`` (optional)
    is the health check run on freshly downloaded bytes before they may be adopted (a degraded 200
    is kept-pinned, never adopted); ``auth`` carries per-source HTTP basic-auth when needed."""

    title: str
    url: str
    cache_file: Path
    auth: tuple[str, str] | None = None
    validate: Callable[[bytes], bool] | None = None


@dataclass
class Outcome:
    title: str
    status: str

    @property
    def action(self) -> str:
        return _ACTION[self.status]


@dataclass
class RefreshResult:
    """Per-resource outcomes plus what ``apply`` actually committed — the source stage renders this."""

    outcomes: list[Outcome] = field(default_factory=list)
    adopted: list[str] = field(default_factory=list)   # committed this run (new or changed, under apply)

    def tally(self) -> dict[str, int]:
        t: dict[str, int] = {}
        for o in self.outcomes:
            t[o.status] = t.get(o.status, 0) + 1
        return t

    @property
    def kept_pinned(self) -> int:
        """Resources whose upstream was bad/absent (degraded/gone) — a run is never 'all clear'
        while any source is unhealthy, so the caller surfaces this in the footer."""
        return sum(1 for o in self.outcomes if o.status in (DEGRADED, GONE))


def _status_for_failure(exc: Exception) -> str:
    """A transport failure with a pinned copy present: a 404 is a real disappearance (``gone``),
    anything else is a transient/unhealthy fetch (``degraded``). Both keep the pinned copy."""
    return GONE if getattr(getattr(exc, "response", None), "status_code", None) == 404 else DEGRADED


def refresh_fetchables(fetchables: list[Fetchable], *, apply: bool = False,
                       download: Callable[..., bytes] | None = None) -> RefreshResult:
    """Re-check each fetchable against upstream and reconcile with the pinned raw (never a blind
    overwrite). ``download`` is injectable for tests; it defaults to the shared HTTP downloader."""
    if download is None:
        from corpus.downloader import download_file as download  # lazy: requests in the corpus extra

    result = RefreshResult()
    for f in fetchables:
        pinned = read_pinned(f.cache_file)
        pinned_bytes = f.cache_file.read_bytes() if pinned is not None else None
        try:
            fresh = download(f.url, auth=f.auth)
        except Exception as exc:  # transport / 404 — keep pinned, report (§4 F/G)
            result.outcomes.append(Outcome(f.title, _status_for_failure(exc)))
            continue

        if not fresh.strip() or (f.validate is not None and not f.validate(fresh)):
            result.outcomes.append(Outcome(f.title, DEGRADED))   # §4 H: 200 but unhealthy → keep pinned
        elif pinned_bytes is None:                               # §4 A: never acquired
            result.outcomes.append(Outcome(f.title, NEW))
            if apply:
                commit_bytes(f.cache_file, fresh)
                result.adopted.append(f.title)
        elif fresh == pinned_bytes:                              # §4 D: identical
            result.outcomes.append(Outcome(f.title, NOT_CHANGED))
        else:                                                    # §4 E: changed — adopt only on apply
            result.outcomes.append(Outcome(f.title, CHANGED))
            if apply:
                commit_bytes(f.cache_file, fresh)
                result.adopted.append(f.title)
    return result
