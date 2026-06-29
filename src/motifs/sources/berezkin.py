"""Berezkin & Duvakin areal motif catalogue (areasofmyths.com).

The whole motif inventory lives in one navigation page (``index-left.html``):
each ``<li>`` gives a motif code, name, optional internal see-also codes, and a
trailing list of areal indices. ``areas1.html`` maps those numeric indices to
ethnic/territorial group names. Per-motif detail pages add a short definition.

Parsing is split from fetching so it can be unit-tested on static fixtures.
"""

from __future__ import annotations

import logging
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from settings import settings

from .fetch import fetch_text

logger = logging.getLogger(__name__)

# A Berezkin motif code: latin letter(s), a digit, then any letters/digits — e.g.
# A1, A1A, A2a1, B12. Used to read the leading code of an entry.
_CODE = r"[A-Za-z]+[0-9][A-Za-z0-9]*"
_LEADING_CODE_RE = re.compile(rf"^({_CODE})\.\s*")
# A see-also reference to another Berezkin motif (uppercase-initial code). Some
# codes trail a stray ".I"/".I.I" artifact in the source — consumed but dropped.
_SEE_ALSO_RE = re.compile(r"\b([A-Z][A-Za-z]*[0-9][A-Za-z0-9]*)(?:\.I+)*")
# An ATU tale-type cross-reference embedded in a title, e.g. "ATU 328A*".
_ATU_REF_RE = re.compile(r"ATU\s+([0-9][0-9A-Za-z*]*)")
# A chapter header in the nav, e.g. "A. СОЛНЦЕ И ЛУНА".
_CHAPTER_RE = re.compile(r"^\s*([A-Z])\.\s+([А-ЯЁ][А-ЯЁ \-,]+?)\s*$")
# The trailing areal-index list: preceded by whitespace/comma, may open with "(".
_AREA_RE = re.compile(r"[\s,]+[.(]*\d[\d.()\s,\-]*$")
# Numbers / ranges that make up the areal-index list.
_AREA_NUM_RE = re.compile(r"\d+|-")
# Plausible upper bound for an areal index (the scheme has a few hundred areas).
_MAX_AREA = 350


def chapter_of(code: str) -> str:
    """Leading-letter chapter for a Berezkin code (``B12`` -> ``B``)."""
    m = re.match(r"[A-Za-z]+", code)
    return (m.group(0)[0].upper() if m else code[:1]).upper()


def _expand_areas(area_text: str) -> list[int]:
    """Expand a dotted area list (``.43.-.50.52.``) into sorted unique ints.

    A ``-`` between two numbers denotes an inclusive range; parentheses (motifs
    not yet in the digital DB) are ignored for expansion.
    """
    tokens = _AREA_NUM_RE.findall(area_text)
    nums: set[int] = set()
    i = 0
    while i < len(tokens):
        if tokens[i] == "-":
            i += 1
            continue
        start = int(tokens[i])
        if i + 2 < len(tokens) and tokens[i + 1] == "-" and tokens[i + 2] != "-":
            end = int(tokens[i + 2])
            if 0 <= end - start <= 300:
                nums.update(range(start, end + 1))
            else:  # defensive: implausible range, keep endpoints only
                nums.update((start, end))
            i += 3
        else:
            nums.add(start)
            i += 1
    # Berezkin's areal scheme has a few hundred areas; anything larger is a
    # parsing artifact (e.g. a digit that leaked out of a name), so drop it.
    return sorted(n for n in nums if 1 <= n <= _MAX_AREA)


def parse_motif_entry(text: str, page: str) -> dict | None:
    """Parse one nav ``<li>`` link into a motif record, or None if it has no code.

    Layout is ``CODE. Name. [SEE-ALSO codes] .area.area.`` — the areal list is
    introduced by a space-dot before the first number (``... .19.21.``), which
    lets us split it off without eating the digits of a see-also code (``A50.``).
    """
    text = " ".join(text.split())
    m = _LEADING_CODE_RE.match(text)
    if not m:
        return None
    code = m.group(1)
    rest = text[m.end():].strip()

    # ATU tale-type cross-references embedded in the title ("... ATU 328A*").
    atu_refs = _dedup(r.rstrip(".,") for r in _ATU_REF_RE.findall(rest))
    rest = _ATU_REF_RE.sub("", rest)

    # Trailing areal index list (whitespace/comma-introduced; may open with "(").
    areas: list[int] = []
    before = rest
    area_match = _AREA_RE.search(rest)
    if area_match:
        areas = _expand_areas(rest[area_match.start():])
        before = rest[: area_match.start()].strip()

    # What remains is the name plus see-also codes (cross-references to other
    # Berezkin motifs). Codes are latin; the name is Cyrillic, so pulling the code
    # tokens out leaves a clean name.
    see_also = _dedup(c for c in _SEE_ALSO_RE.findall(before) if c != code)
    name = _SEE_ALSO_RE.sub("", before)
    name = re.sub(r"\s+", " ", name).strip(" .,;").strip()

    return {
        "id": code,
        "chapter": chapter_of(code),
        "name": name,
        "areas": areas,
        "see_also": see_also,
        "atu_refs": atu_refs,
        "page": page,
    }


def _dedup(items) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def parse_index(html: str) -> tuple[list[dict], dict[str, str]]:
    """Parse the nav page into (motifs, chapter-titles-by-letter)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")

    chapters: dict[str, str] = {}
    for p in soup.find_all("p"):
        cm = _CHAPTER_RE.match(p.get_text(" ", strip=True))
        if cm:
            chapters[cm.group(1)] = cm.group(2).strip()

    motifs: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("li a[href]"):
        href = a.get("href", "")
        if not href.endswith(".html"):
            continue
        entry = parse_motif_entry(a.get_text(" ", strip=True), href)
        if entry and entry["id"] not in seen:
            seen.add(entry["id"])
            motifs.append(entry)
    return motifs, chapters


def parse_areas(html: str) -> dict[str, str]:
    """Parse ``areas1.html`` into ``{area_number: group_name}``.

    NOTE: areasofmyths numbers areal groups *per region* (each region restarts at
    1), whereas the motif entries reference a global areal index. The two schemes
    do not line up, so this legend is **not** used to name motif areas — doing so
    would mislabel them. Decoding the global index needs Berezkin's official area
    key; until then motif areas are shown as faithful numeric indices. The parser
    is kept for that future mapping.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    areas: dict[str, str] = {}
    entry_re = re.compile(r"^\s*(\d+)\.\s+(.+)$", re.DOTALL)
    for p in soup.find_all("p"):
        m = entry_re.match(p.get_text(" ", strip=True))
        if m:
            num, name = m.group(1), " ".join(m.group(2).split())
            # Keep the first, primary group name (drop long "incl. ..." tails).
            name = re.split(r";|\(вкл", name)[0].strip()
            if num not in areas and name:
                areas[num] = name
    return areas


def parse_definition(html: str) -> str:
    """Extract a motif's short definition (first ``NormalLis`` paragraph)."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    node = soup.find("p", class_="NormalLis")
    return " ".join(node.get_text(" ", strip=True).split()) if node else ""


# ---------------------------------------------------------------------------
# Fetch orchestration
# ---------------------------------------------------------------------------


def build(config: dict, *, force: bool = False) -> dict:
    """Scrape and parse the Berezkin catalogue into a store-ready dict."""
    base = config["base_url"].rstrip("/")
    encoding = config.get("encoding", "windows-1251")
    cache = Path(settings.motifs_dir) / "raw" / "berezkin"

    index_html = fetch_text(
        f"{base}/{config['index_page']}", cache / config["index_page"], encoding=encoding, force=force
    )
    motifs, chapters = parse_index(index_html)
    logger.info("Berezkin: parsed %d motifs across %d chapters", len(motifs), len({m["chapter"] for m in motifs}))

    if config.get("fetch_details", True) and settings.motifs.berezkin_details:
        _attach_definitions(motifs, base, cache, encoding, force)

    return {
        "label": config.get("label", "Berezkin"),
        "long_label": config.get("long_label", ""),
        "attribution": config.get("attribution", ""),
        "homepage": config.get("homepage", ""),
        "chapters": chapters,
        "motifs": motifs,
    }


def _attach_definitions(motifs: list[dict], base: str, cache: Path, encoding: str, force: bool) -> None:
    targets = motifs
    if settings.motifs.max_motifs is not None:
        targets = motifs[: settings.motifs.max_motifs]
    logger.info("Berezkin: fetching %d detail pages for definitions...", len(targets))

    def fetch_one(motif: dict) -> tuple[str, str]:
        page = motif["page"]
        try:
            html = fetch_text(f"{base}/{page}", cache / page, encoding=encoding, force=force)
            return motif["id"], parse_definition(html)
        except Exception as exc:  # a missing/odd page must not abort the whole build
            logger.debug("Berezkin: detail fetch failed for %s: %s", page, exc)
            return motif["id"], ""

    workers = max(1, settings.motifs.max_workers)
    definitions: dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for motif_id, definition in pool.map(fetch_one, targets):
            if definition:
                definitions[motif_id] = definition

    for motif in motifs:
        motif["definition"] = definitions.get(motif["id"], "")
    logger.info("Berezkin: attached %d definitions", len(definitions))
