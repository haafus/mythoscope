"""`mytho refresh documents` — re-check pinned corpus raw against upstream.

The fetch/build boundary (pipeline §5, fetch-and-refresh §2): ``build`` acquires missing
raw and never re-fetches; ``refresh`` is the separate, human-gated, networked re-check. It
downloads each web source fresh, diffs it against the pinned copy, and by default **keeps
the pinned bytes** — a genuine change is adopted (``os.replace``) only on ``--apply``, after
which the fingerprint cascade re-derives that document. Local ``file:`` sources are re-read
on every build (a free hash check), so refresh leaves them to the build.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from fetch_cache import commit_bytes
from settings import settings

from .downloader import load_download_list
from .locator import corpus_raw_path
from .sources import WEB_SCHEMES, source_scheme

logger = logging.getLogger(__name__)


@dataclass
class RefreshResult:
    unchanged: int = 0
    skipped_local: int = 0
    changed: list[str] = field(default_factory=list)              # upstream drift, kept pinned
    new: list[str] = field(default_factory=list)                  # no pinned raw yet (first acquire)
    adopted: list[str] = field(default_factory=list)              # committed this run (--apply)
    unreachable: list[tuple[str, str]] = field(default_factory=list)  # (title, reason): transport/404
    degraded: list[tuple[str, str]] = field(default_factory=list)     # (title, reason): 200 but unhealthy


def _reason(exc: Exception) -> str:
    status = getattr(getattr(exc, "response", None), "status_code", None)
    if status == 404:
        return "gone-404"
    if status:
        return f"http-{status}"
    return "fetch-error"


def _invalidate_output(url: str, corpus_dir: Path) -> None:
    """Delete the derived ``.txt`` for ``url`` so a plain ``mytho build`` re-derives it from
    the newly-adopted raw. Web reuse keys on output-presence (not raw-vs-output), so without
    this an adopted change would not propagate until ``build --force`` (which re-embeds all)."""
    catalog = corpus_dir / "corpus.json"
    try:
        rows = json.loads(catalog.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    for row in rows:
        if row.get("url") == url and row.get("path"):
            (corpus_dir / row["path"]).unlink(missing_ok=True)
            return


def refresh_corpus(*, apply: bool = False, max_texts: int | None = None) -> RefreshResult:
    """Re-fetch the web corpus sources and reconcile against the pinned raw archive.

    Never overwrites blindly: a transport failure or 404 keeps the pinned copy and is
    reported; an unchanged source is a no-op; a changed source is adopted only with
    ``apply``. Returns a :class:`RefreshResult` for the caller to render.
    """
    from .downloader import download_file  # lazy: requests lives in the corpus extra

    result = RefreshResult()
    corpus_dir = Path(settings.corpus_dir)
    raw_dir = corpus_dir / "raw"
    items = load_download_list()
    if max_texts is not None:
        items = items[:max_texts]

    for item in items:
        url = item.get("url", "")
        title = item.get("title") or url
        if source_scheme(url) not in WEB_SCHEMES:
            result.skipped_local += 1
            continue

        raw = corpus_raw_path(raw_dir, url)
        try:
            fresh = download_file(url)
        except Exception as exc:  # transport / 404 — keep pinned, report (situations F/G)
            reason = _reason(exc)
            result.unreachable.append((title, reason))
            logger.warning("refresh: %s unreachable (%s) — keeping pinned raw", title, reason)
            continue

        # Validate before commit (situation H): a 200 with an empty/whitespace body is a
        # degraded reply (soft error, anti-bot stub, truncation) — never adopt it over the
        # pinned last-good copy. Richer per-source validators are Part 3 (fetch-and-refresh §8).
        if not fresh.strip():
            result.degraded.append((title, "empty-body"))
            logger.warning("refresh: %s returned an empty/degraded body — keeping pinned raw", title)
            continue

        pinned = raw.read_bytes() if (raw.exists() and raw.stat().st_size > 0) else None
        if pinned is None:                       # A: never acquired — first fetch
            result.new.append(title)
            if apply:
                commit_bytes(raw, fresh)
                _invalidate_output(url, corpus_dir)
                result.adopted.append(title)
        elif fresh == pinned:                    # D: identical — no-op
            result.unchanged += 1
        else:                                    # E: changed — adopt only on --apply
            result.changed.append(title)
            if apply:
                commit_bytes(raw, fresh)
                _invalidate_output(url, corpus_dir)   # so a plain `build` re-derives this doc
                result.adopted.append(title)
            else:
                logger.info("refresh: %s changed upstream — rerun with --apply to adopt", title)

    return result
