"""Deep links into Ashliman's Folktexts for ATU tale types with example tales.

Most types have a page at ``sites.pitt.edu/~dash/type{NNNN}[letter].html`` whose table
of contents maps each variant's title to an in-page anchor; a curated handful of
famous types live on a themed page instead (``_PAGE_OVERRIDES`` — each verified
by the page's own text declaring that type). This best-effort enrichment fetches
those pages (cached under ``raw/ashliman/``) and sets each stored tale's ``url``
to the anchored deep link, falling back to the page itself, then to no link.

The TOC parsing / title matching is separated from fetching so it can be unit
tested on a static fixture.
"""

from __future__ import annotations

import collections
import concurrent.futures
import html
import logging
import re
from pathlib import Path

from settings import settings

from .fetch import fetch_text

logger = logging.getLogger(__name__)

# Ashliman's Folktexts moved from www.pitt.edu/~dash to sites.pitt.edu/~dash (the
# old host now 301-redirects there); point at the canonical home directly.
BASE = "https://sites.pitt.edu/~dash"

# Types whose ``type{NNNN}.html`` page does not exist but whose tales sit on a
# themed page. Curated by crawling the site: each page's own text declares this
# type (e.g. friday.html says "type 779J"). Keyed by the ATU id as stored
# (asterisk kept), value is the page filename.
# Only pages that actually *list variants* (a table of contents of several
# tales) belong here — a single-text or two-edition-comparison page yields no
# anchors and misrepresents a "variant", so it is excluded (see 440/779J*).
_PAGE_OVERRIDES = {
    "325": "magicbook.html",        # The Magician and his Pupil ("Magic Books")
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


def canon(atu_id: str) -> str | None:
    """Normalise an ATU id for cross-source matching: strip leading zeros of the
    numeric prefix and upper-case, **keeping** any letters and ``*`` — both are
    significant (``1585`` and ``1585*`` are distinct types, so never strip the
    star here). Returns ``None`` only for empty input; a non-numeric id is
    returned upper-cased unchanged (never dropped).

    Caveat: Ashliman page URLs cannot carry a ``*``, so when matching a *site*
    number against catalogue ids, compare the star-stripped forms of both —
    ``canon`` alone will not equate site ``779J`` with catalogue ``779J*``.
    """
    s = (atu_id or "").strip().upper()
    m = re.match(r"^0*(\d+)(.*)$", s)
    return f"{int(m.group(1))}{m.group(2)}" if m else (s or None)


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


# Noise in a page's table of contents that is not a tale variant: navigation /
# meta links, footnote markers, and links out to other type pages. (Filtering
# tuned on the full crawl; note 'version' is NOT a stop-word — it appears in real
# titles like "… version 1".)
_NAV = re.compile(r"\b(links?|related|additional\s+\w+\s+tales?|sites?|contents?|"
                  r"return|index|home|printer|e-?mail|copyright|revised|back to|top of)\b", re.I)
_FOOTNOTE = re.compile(r"^\{?\s*footnote", re.I)
_XTYPE = re.compile(r"^\s*tales?\s+of\s+types?\b|\btype\s+\d", re.I)


def _display_title(title_html: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", title_html or ""))).strip()


def _is_noise(title: str) -> bool:
    return bool(_NAV.search(title) or _FOOTNOTE.match(title) or _XTYPE.search(title))


def parse_variants(page_html: str, base_url: str) -> list[dict]:
    """``[{title, url}]`` — a page's table-of-contents tale entries as display
    title + anchored deep link, with nav/footnote/cross-type noise removed and
    anchors de-duplicated."""
    out, seen = [], set()
    for anchor, title_html, _country in _TOC.findall(page_html):
        title = _display_title(title_html)
        if not title or anchor.lower() == "contents" or anchor in seen or _is_noise(title):
            continue
        seen.add(anchor)
        out.append({"title": title, "url": f"{base_url}#{anchor}"})
    return out


def refresh(atu_types: list[dict], *, force: bool = False) -> dict:
    """Source each type's example tales straight from Ashliman's site — no aft
    dataset. Crawl the site (``discover_site_types``); for every site ATU type
    that maps to a catalogue type (itself, or a parent/family via
    ``attach_target``) parse its page's table of contents into ``{title, url}``
    variants (noise filtered) and set them as that type's ``tales`` (deduped by
    title). Genuine-orphan site types are dropped. Best-effort: on total site
    failure nothing is set and the step is skipped."""
    known = {t["id"] for t in atu_types}
    by_id = {t["id"]: t for t in atu_types}
    by_base = {}                                   # starless canon -> catalogue id
    for t in atu_types:
        by_base.setdefault(canon(t["id"]).rstrip("*"), t["id"])
        t.pop("tales", None)                       # start from a clean slate

    site = discover_site_types(force=force)   # curated numbered pages + contents walk
    if not site["all"]:
        logger.warning("Ashliman: site discovery found nothing — unreachable?; skipping")
        return {"skipped": "unreachable"}

    # site type (canon) -> the catalogue type its variants attach to, and the
    # page to read them from (its own page, direct or via attach_target's child).
    page_targets: dict[str, set[str]] = collections.defaultdict(set)
    orphans = 0
    for cid in site["all"]:
        base = cid.rstrip("*")
        target = by_base.get(base)                 # a catalogue type as-is
        source = target
        if target is None:                         # off-catalogue: attach to a relative
            target = attach_target(base, known)
            source = base
            if target is None:
                orphans += 1
                continue
        page = _type_page(source)
        if page:
            page_targets[target].add(page)

    pages_read = 0
    n_types = n_variants = 0
    for tid, pages in page_targets.items():
        variants, seen = [], set()
        for page in sorted(pages):
            page_html = _fetch_page(page, force)
            if page_html is None:
                continue
            pages_read += 1
            for v in parse_variants(page_html, f"{BASE}/{page}"):
                key = v["title"].lower()
                if key not in seen:
                    seen.add(key)
                    variants.append(v)
        if variants:
            by_id[tid]["tales"] = variants
            n_types += 1
            n_variants += len(variants)

    logger.info("Ashliman: %d types carry %d tale variants (from %d pages; %d orphan site types dropped)",
                n_types, n_variants, pages_read, orphans)
    return {"types_with_tales": n_types, "variants": n_variants,
            "pages": pages_read, "orphans_dropped": orphans}


# ---------------------------------------------------------------------------
# Site-coverage discovery: which ATU types does Ashliman actually carry?
# ---------------------------------------------------------------------------
_INDEX_PAGES = ("folktexts.html", "folktexts2.html")
_HREF = re.compile(r'href="([a-z0-9_]+\.html)"', re.I)
_TYPE_DECL = re.compile(r"\btypes?\s+(\d{1,4}[A-Za-z]?)", re.I)

# Numbered `type{NNNN}.html` pages found to exist by a one-time full probe of
# every catalogue code (canon ids). Used in place of re-probing on each build;
# regenerate by calling ``discover_site_types(known_ids, probe=True)`` and pasting
# its ``numbered`` set here.
_TYPE_PAGES = frozenset({
    "1", "2", "15", "47A", "50", "57", "63", "66A", "68A", "91", "92", "101", "103", "105",
    "112", "122E", "122F", "123B", "124", "130", "150", "154", "155", "156", "160", "173",
    "175", "178A", "207C", "214A", "225", "231", "237", "243A", "244", "247", "275", "278",
    "278A", "280A", "295", "298", "303", "306", "310", "311", "312", "326", "327", "332", "333",
    "335", "361", "365", "366", "402", "410", "425C", "451", "480", "500", "501", "502", "503",
    "505", "510A", "510B", "545B", "555", "562", "563", "565", "570", "571B", "592", "613",
    "650A", "670", "675", "700", "703", "704", "706", "709", "720", "726", "737", "750A", "753",
    "756", "763", "777", "779", "780", "782", "800", "845", "850", "882", "888", "898", "900",
    "901", "910B", "910F", "920E", "926", "955", "980", "980D", "981", "982", "990", "1030",
    "1157", "1161", "1174", "1175", "1176", "1191", "1215", "1287", "1288A", "1317", "1319",
    "1335A", "1342", "1351", "1353", "1362", "1375", "1377", "1381", "1381D", "1383", "1415",
    "1422", "1423", "1430", "1451", "1540", "1548", "1558", "1562A", "1586", "1592", "1592B",
    "1620", "1626", "1641", "1641C", "1645", "1645B", "1655", "1675", "1676", "1678", "1696",
    "1730", "1741", "1791", "1889B", "1889F", "1965", "1967", "2015", "2022", "2025", "2030",
    "2031C", "2032", "2035", "2043", "2250",
})


def _fetch_page(page: str, force: bool) -> str | None:
    """Fetch a page, cached under ``raw/ashliman/`` — a cached copy is reused without
    a network call unless ``force`` (as elsewhere in the pipeline). Returns ``None``
    when the page is absent or unreachable; only a definitive 404 drops the cache, so
    a transient network error during a ``--force`` rebuild can't wipe a good copy."""
    cache = Path(settings.motifs_dir) / "raw" / "ashliman" / page
    try:
        return fetch_text(f"{BASE}/{page}", cache, force=force)
    except Exception as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status == 404:
            cache.unlink(missing_ok=True)
        return None


def _atu_range(cid: str) -> bool:
    m = re.match(r"\d+", cid or "")
    return bool(m) and int(m.group()) < 3000   # >=3000 = Christiansen migratory legends


def _probe_filename(cid: str) -> str | None:
    m = re.match(r"^(\d+)([A-Za-z]*)", cid or "")
    return f"type{int(m.group(1)):04d}{m.group(2)}.html" if m else None


def discover_site_types(known_ids=None, *, force: bool = False, workers: int = 12,
                        probe: bool = False) -> dict:
    """The ATU types Ashliman's Folktexts covers, found two complementary ways:

    * **contents walk** — the index pages (folktexts.html / folktexts2.html) give
      the type-numbered page links, and every *themed* page they link declares the
      ATU type(s) it covers; this finds types even when absent from the catalogue.
    * **numbered pages** — the curated ``_TYPE_PAGES`` set (numbered pages a
      one-time full probe found), so no per-build probing. Pass ``probe=True`` with
      ``known_ids`` to re-run the brute-force probe instead (to regenerate the set).

    Only the ATU range (<3000; higher numbers are Christiansen migratory legends)
    is kept. Returns canon-id sets ``{contents, numbered, all}``.
    """
    slugs: set[str] = set()
    for idx in _INDEX_PAGES:
        slugs.update(_HREF.findall(_fetch_page(idx, force) or ""))
    contents: set[str] = set()
    for s in slugs:                             # type-numbered page filenames
        m = re.match(r"^type(\d+)([a-z]?)\.html$", s)
        if m:
            contents.add(canon(f"{m.group(1)}{m.group(2)}"))
    themed = [s for s in slugs
              if not re.match(r"^type\d", s) and not s.startswith("folktexts")]

    def _declared(slug: str) -> set[str]:
        return {canon(x) for x in _TYPE_DECL.findall(_fetch_page(slug, force) or "")}

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        for nums in ex.map(_declared, themed):
            contents |= {c for c in nums if c}
    contents = {c for c in contents if _atu_range(c)}

    if probe:                                   # brute-force (only to regenerate _TYPE_PAGES)
        probe_ids = sorted({c for i in (known_ids or ()) if (c := canon(i)) and _atu_range(c)})

        def _exists(cid: str) -> str | None:
            page = _probe_filename(cid)
            return cid if page and _fetch_page(page, force) is not None else None

        numbered = set()
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
            for hit in ex.map(_exists, probe_ids):
                if hit:
                    numbered.add(hit)
    else:
        numbered = {c for c in _TYPE_PAGES if _atu_range(c)}

    both = contents | numbered
    logger.info("Ashliman site coverage: %d types (contents-walk %d, numbered pages %d%s)",
                len(both), len(contents), len(numbered), ", brute-force probed" if probe else " curated")
    return {"contents": contents, "numbered": numbered, "all": both}
