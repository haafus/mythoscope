"""The corpus stage's INPUT fingerprint — its own staleness key (pipeline §2.3).

Distinct from the per-row ``fingerprint`` (``blake2b`` of the *cleaned* text, D2) that the
catalog already stores and that embeddings/graphs fold downstream. That one is *output*-based
(known only after cleaning); this one is *input*-based, so a build can decide **offline**
whether a document's ``.txt`` is stale:

    source_fp = hash( raw_bytes  +  content_start/end  +  clean_version )

A change to any input — the pinned raw bytes (a re-delivered local source), the trim bounds in
config, or the cleaning code/params (``clean_version``) — flips ``source_fp`` and rebuilds just
that document; the new *output* fingerprint then cascades to embeddings/graphs.
"""

from __future__ import annotations

from settings import settings

from .utils import content_fingerprint

# Bump when the cleaning pipeline changes in a way that alters the .txt from the same raw
# (normalize_text / clean_gutenberg / trim / extraction logic). Forces a re-clean of all docs.
CLEAN_ALGO_VERSION = 1


def clean_version() -> str:
    """Fingerprint of the cleaning code version + the corpus settings that affect extraction."""
    c = settings.corpus
    parts = [
        f"clean_v={CLEAN_ALGO_VERSION}",
        f"html_comments={c.html_include_comments}",
        f"html_tables={c.html_include_tables}",
        f"pdf_tables={c.pdf_extract_tables}",
        f"pdf_layout={c.pdf_preserve_layout}",
    ]
    return content_fingerprint("|".join(parts).encode("utf-8"))


def source_fingerprint(raw: bytes, content_start: str | None, content_end: str | None) -> str:
    """The document's offline staleness key: raw content + trim bounds + cleaning version."""
    parts = [
        content_fingerprint(raw),
        content_start or "",
        content_end or "",
        clean_version(),
    ]
    return content_fingerprint("|".join(parts).encode("utf-8"))
