"""Deep links into Ashliman's Folktexts for ATU tale types with example tales.

Most types have a page at ``pitt.edu/~dash/type{NNNN}[letter].html`` whose table
of contents maps each variant's title to an in-page anchor; a curated handful of
famous types live on a themed page instead (``_PAGE_OVERRIDES`` — each verified
by the page's own text declaring that type). This best-effort enrichment fetches
those pages (cached under ``raw/ashliman/``) and sets each stored tale's ``url``
to the anchored deep link, falling back to the page itself, then to no link.

The TOC parsing / title matching is separated from fetching so it can be unit
tested on a static fixture.
"""

from __future__ import annotations

import html
import logging
import re
from pathlib import Path

from settings import settings

from .fetch import fetch_text

logger = logging.getLogger(__name__)

BASE = "https://www.pitt.edu/~dash"

# Types whose ``type{NNNN}.html`` page does not exist but whose tales sit on a
# themed page. Curated by crawling the site: each page's own text declares this
# type (e.g. friday.html says "type 779J"). Keyed by the ATU id as stored
# (asterisk kept), value is the page filename.
_PAGE_OVERRIDES = {
    "325": "magicbook.html",        # The Magician and his Pupil ("Magic Books")
    "440": "frogking.html",         # The Frog King or Iron Henry
    "779J*": "friday.html",         # Breaking the Sabbath ("Friday")
    "954": "alibaba.html",          # The Forty Thieves ("Ali Baba")
    "958E*": "hand.html",           # Deep Sleep Brought on by a Robber
    "1408": "tradingplaces.html",   # The Man who Does his Wife's Work
}


def _type_page(atu_id: str) -> str | None:
    """The Ashliman page filename for a type: a curated override, else the
    ``type{4-digit}{letter}.html`` form derived from the id (asterisk dropped —
    starred sub-types have no page of their own)."""
    if atu_id in _PAGE_OVERRIDES:
        return _PAGE_OVERRIDES[atu_id]
    m = re.match(r"^(\d+)([A-Za-z]*)\*?$", atu_id)
    if not m:
        return None
    return f"type{int(m.group(1)):04d}{m.group(2)}.html"


# A table-of-contents entry: <a href="#anchor">Title</a> optionally (Country).
_TOC = re.compile(r'<a\s+href="#([^"]+)"\s*>(.*?)</a>\s*(?:\(([^)]*)\))?', re.I | re.S)
_SUFFIX = re.compile(r"\s*\(([^)]*)\)\s*$")   # a trailing "(Grimm)" disambiguator


def _norm(text: str) -> str:
    """Fold a title to a match key: strip tags/entities, lowercase, drop a
    leading 'the', collapse to single-spaced alphanumerics."""
    s = html.unescape(re.sub(r"<[^>]+>", "", text)).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return re.sub(r"^the\s+", "", s)


def parse_toc(page_html: str) -> list[tuple[str, str, str]]:
    """``[(norm_title, country_lower, anchor)]`` from the page's contents list."""
    out: list[tuple[str, str, str]] = []
    for anchor, title, country in _TOC.findall(page_html):
        nt = _norm(title)
        if nt and anchor.lower() != "contents":
            out.append((nt, (country or "").lower(), anchor))
    return out


def resolve_anchor(title: str, toc: list[tuple[str, str, str]]) -> str | None:
    """The anchor for a tale, matched by title against the TOC. Same-titled
    variants (rare) are told apart by the title's own parenthetical against the
    TOC's country column. ``None`` when no title matches."""
    base = _SUFFIX.sub("", title)
    suffix_m = _SUFFIX.search(title)
    cands = [t for t in toc if t[0] == _norm(base)]
    if not cands:
        cands = [t for t in toc if t[0] == _norm(title)]
    if not cands:
        return None
    if len(cands) == 1:
        return cands[0][2]
    for word in _norm(suffix_m.group(1) if suffix_m else "").split():
        for _nt, country, anchor in cands:
            if word and word in country:
                return anchor
    return cands[0][2]


_BASE = re.compile(r"^(\d+)")


def _base(atu_id: str) -> str | None:
    """The bare base number of an ATU id: ``333A`` / ``333A*`` -> ``333``."""
    m = _BASE.match(atu_id or "")
    return m.group(1) if m else None


def attach_target(atu_id: str, known_ids: set[str]) -> str | None:
    """The existing type an *off-index* Ashliman type attaches to.

    Ashliman lists ATU types the trilogy catalogue omits. Such a type is linked
    to a relative already in the index — its **parent** (the bare base number)
    when present, else the **lowest sibling** sharing the same base number.
    Returns ``None`` for a genuine orphan: no indexed type shares its base.
    The link is hierarchical (parent/family), not equivalence.
    """
    b = _base(atu_id)
    if not b:
        return None
    if b in known_ids:                       # a subtype whose parent is indexed
        return b
    family = [i for i in known_ids if _base(i) == b]
    return min(family) if family else None    # lowest sibling, else orphan


def refresh(atu_types: list[dict], *, force: bool = False) -> dict:
    """Attach ``url`` to each example tale in place. Best-effort: a missing page
    (starred/absent types) leaves its tales unlinked; if every fetch fails the
    site is unreachable and the step is skipped."""
    pages_ok = pages_missing = anchored = page_level = tried = 0
    for t in atu_types:
        tales = t.get("tales")
        if not tales:
            continue
        page = _type_page(t["id"])
        if not page:
            continue
        tried += 1
        cache = Path(settings.motifs_dir) / "raw" / "ashliman" / page
        try:
            page_html = fetch_text(f"{BASE}/{page}", cache, force=force)
        except Exception:  # 404 for starred/absent types is expected, not fatal
            cache.unlink(missing_ok=True)
            pages_missing += 1
            continue
        pages_ok += 1
        toc = parse_toc(page_html)
        base_url = f"{BASE}/{page}"
        for tale in tales:
            anchor = resolve_anchor(tale["title"], toc)
            tale["url"] = f"{base_url}#{anchor}" if anchor else base_url
            anchored += bool(anchor)
            page_level += not anchor
    if tried and pages_ok == 0:
        logger.warning("Ashliman: %d type pages tried, none fetched — site unreachable?; skipping", tried)
        return {"skipped": "unreachable"}
    logger.info("Ashliman: %d pages (%d missing), %d tales anchored, %d page-level links",
                pages_ok, pages_missing, anchored, page_level)
    return {"pages": pages_ok, "pages_missing": pages_missing,
            "tales_anchored": anchored, "tales_page_level": page_level}
