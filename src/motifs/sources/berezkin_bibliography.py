"""Berezkin catalogue bibliography + citation → region/ethnos linkage (areasofmyths.com).

Two artefacts, from the same static site the Berezkin catalogue is scraped from:

  * ``biblio.html`` — the full bibliography, grouped by author: an author-class
    paragraph heads a run of year-leading work paragraphs. Parsed into
    ``{'<surname> <year>': {author, year, title}}``.
  * every motif detail page (already cached) — its areal distribution, written as
    ``Region. Ethnos [summary]: Author Year: pages`` blocks. Each ``NormalMai``
    paragraph is one region; citations are author-year shorthands into the
    bibliography above.

``refresh()`` re-reads the cached detail pages (no new fetches except biblio.html),
splits each region block, extracts the author-year citations, resolves them against
the bibliography (year + surname-in-author, with same-surname collisions flagged
``ambiguous``), and attributes each to its macro-area (from the canonical area
legend). It writes a machine-readable ``berezkin_bibliography.json`` (per-motif
region→citation tree + source→regions aggregates) — gitignored, best-effort
enrichment that always works from the hardcoded area legend (no credentials).

Parsing is separated from fetching so it can be unit-tested on static fixtures.
"""

from __future__ import annotations

import json
import logging
import re
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from settings import settings

from . import berezkin
from .fetch import fetch_text

logger = logging.getLogger(__name__)

BASE = "http://areasofmyths.com"
OUT_FILE = "berezkin_bibliography.json"
_ATTRIB = ("Ю.Е. Березкин, Е.Н. Дувакин. Тематическая классификация и распределение "
           "фольклорно-мифологических мотивов по ареалам. Аналитический каталог.")

# Paragraph classes that head an author (the rest are year-leading works).
_AUTHOR_CLASSES = {"NormalMai", "MsoNormal", "NormalMai0"}

# A year key: 4 digits + an optional single disambiguating letter (1958a).
_YEAR = r"\d{4}[a-zа-яё]?"
_YEAR_HEAD = re.compile(rf"^({_YEAR})")

# A citation in a description: a surname token (hyphen/apostrophe kept, so
# "Pechuël-Loesche" stays whole) + optional "et al."/"и др." + a year.
_REF_RE = re.compile(rf"([\w'\-]+)(?:\s+(?:et al\.?|и др\.?))?[\s,]+({_YEAR})")
# Lower-case tokens that are legitimate name particles, not noise.
_PARTICLE_PREFIXES = ("el-", "al-", "ag-", "ал-", "d'", "l'", "t'")


def cleanup(s: str) -> str:
    """Normalize quotes/apostrophes and connectives so surnames match across pages."""
    s = s.replace(", &", " &").replace(", and", " &").replace(", и", " и")
    for ch in "˝‟″“”«»":
        s = s.replace(ch, '"')
    for ch in "`´′‘’":
        s = s.replace(ch, "'")
    return " ".join(s.split())


# ---------------------------------------------------------------------------
# Bibliography
# ---------------------------------------------------------------------------

def parse_bibliography(html: str) -> dict[str, dict]:
    """``{'<surname> <year>': {author, year, title, homonyms?}}`` from biblio.html.

    Author-class paragraphs (or a non-year continuation of one) set the current
    author; a year-leading paragraph — or an ``в``/``s.``/``MS`` one — is a work.
    Same surname+year for different authors is kept once with the collisions in
    ``homonyms`` (the bare "surname year" citation can't distinguish them).
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    out: dict[str, dict] = {}
    author = ""
    for p in soup.find_all("p"):
        text = cleanup(p.get_text(" ", strip=True))
        if not text:
            continue
        words = text.split()
        first = words[0]
        m = _YEAR_HEAD.match(first)
        if m:
            year, title = m.group(1), " ".join(words[1:])
        elif first in ("в", "s.", "MS"):  # в печати / s. a. / manuscript
            year = {"в": "в печати", "s.": "s. a.", "MS": "MS"}[first]
            title = " ".join(words[1:])
        else:
            # Not a work: a fresh author heading (by class) or a wrapped-name
            # continuation of the previous heading.
            if (set(p.get("class") or []) & _AUTHOR_CLASSES) or not author:
                author = text
            else:
                author = f"{author} {text}"
            continue

        surname = re.split(r"[,\s]", author, maxsplit=1)[0].strip()
        if not surname:
            continue
        key = f"{surname} {year}"
        if key not in out:
            out[key] = {"author": author, "year": year, "title": title}
        elif out[key]["author"] != author and author not in out[key].get("homonyms", []):
            # A different work under the same surname+year (e.g. a multi-author
            # "Dorsey … Kroeber" vs a same-year "Dorsey" solo): keep it as its own
            # entry under a "#n" key so its authors stay searchable, and flag the
            # collision on the primary.
            out[key].setdefault("homonyms", []).append(author)
            n = 2
            while f"{key} #{n}" in out:
                n += 1
            out[f"{key} #{n}"] = {"author": author, "year": year, "title": title}
    return out


# ---------------------------------------------------------------------------
# Citations in descriptions
# ---------------------------------------------------------------------------

def parse_refs(text: str) -> list[tuple[int, str, str]]:
    """``[(position, surname, year)]`` citations in a description fragment.

    Filters the open regex's false positives: lone/lower-case tokens (unless a
    known name particle) and the literal ``ATU``.
    """
    out: list[tuple[int, str, str]] = []
    for m in _REF_RE.finditer(text):
        author, year = m.group(1), m.group(2)
        if len(author) < 2 or author == "ATU":
            continue
        if author[0].islower() and not author.startswith(_PARTICLE_PREFIXES):
            continue
        out.append((m.start(), author, year))
    return out


def _fold(s: str) -> str:
    """Diacritic-insensitive key: drop combining marks and unify ё/ë → е, so
    "Galvão"/"Fernández"/"Лёбите" match their plain-letter bibliography forms."""
    s = s.replace("ё", "е").replace("Ё", "Е").replace("ë", "е").replace("Ë", "Е")
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


# Cyrillic disambiguating-suffix letters -> Latin, so a citation's "2011b" matches
# the bibliography's Cyrillic "2011б" (and vice versa).
_SUFFIX_TR = {"а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ж": "j",
              "з": "z", "и": "i", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
              "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h"}


def _year_norm(year: str) -> str:
    """4-digit year + a script-normalised suffix letter (Cyrillic → Latin)."""
    m = re.match(r"(\d{4})([a-zа-яё]?)", year.lower())
    if not m:
        return year.lower()
    return m.group(1) + _SUFFIX_TR.get(m.group(2), m.group(2))


def _resolve(surname: str, year: str, index: dict[str, list[tuple[str, str, str]]]) -> dict:
    """Resolve a citation to a bibliography key. ``index`` maps a 4-digit year to
    ``[(key, folded_author, normalised_year)]``. Matching is diacritic-insensitive;
    the year suffix is script-normalised, and when it still misses we fall back to
    any work of the same 4-digit year. ``status`` is resolved / ambiguous /
    unresolved."""
    pat = re.compile(rf"(?<!-)\b{re.escape(_fold(surname))}\b(?!-)", re.IGNORECASE)
    cands = index.get(year[:4], ())
    yn = _year_norm(year)
    exact = [k for k, fa, ny in cands if ny == yn and pat.search(fa)]
    hits = list(dict.fromkeys(exact or [k for k, fa, ny in cands if pat.search(fa)]))
    if len(hits) == 1:
        return {"key": hits[0], "status": "resolved"}
    if len(hits) > 1:
        return {"key": f"{surname} {year}", "status": "ambiguous"}
    return {"key": f"{surname} {year}", "status": "unresolved"}


# ---------------------------------------------------------------------------
# Detail-page attestations: region -> ethnos -> citations
# ---------------------------------------------------------------------------

_CF_PREFIX = re.compile(r"^[(\[]?\s*(ср|см|cf)\.?\s*", re.IGNORECASE)
_DASH = re.compile(r"[-–—]")
_WS = re.compile(r"\s+")


def _norm_region(s: str) -> str:
    """Region name key: lower-cased, dashes → spaces, whitespace collapsed — so
    'Южная Сибирь - Монголия' matches the legend's 'Южная Сибирь – Монголия', and a
    two-part name reads the same regardless of the dash form or spacing."""
    return _WS.sub(" ", _DASH.sub(" ", s.lower())).strip()


def region_index(legend: dict[str, str]) -> dict[str, tuple[str, str]]:
    """``{normalised name: (code, display)}`` from the area legend, also indexing
    the reversed form of two-part names ('Микронезия – Полинезия' ↔ the legend's
    'Полинезия – Микронезия')."""
    idx: dict[str, tuple[str, str]] = {}
    for code, name in legend.items():
        if not name:
            continue
        idx.setdefault(_norm_region(name), (code, name))
        parts = re.split(r"\s*[-–—]\s*", name)
        if len(parts) == 2:
            idx.setdefault(_norm_region(f"{parts[1]} {parts[0]}"), (code, name))
    return idx


def _region_of(block: str, index: dict[str, tuple[str, str]]) -> tuple[str, str, str]:
    """``(area_code, area_name, rest)`` — the region header (up to the first '. ',
    which no area name contains) matched against the normalised legend index."""
    head = _CF_PREFIX.sub("", block).lstrip("([ ")
    i = head.find(". ")
    candidate, rest = (head[:i], head[i:]) if i != -1 else (head, "")
    hit = index.get(_norm_region(candidate))
    return (hit[0], hit[1], rest) if hit else ("", "", head)


def parse_attestations(html: str, area_index: dict[str, tuple[str, str]]) -> list[dict]:
    """Parse a motif detail page into region blocks with their citations.

    Each ``NormalMai`` paragraph is one region:
    ``[{area_code, region, cf, cites: [{pos, surname, year}]}]``.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "lxml")
    regions: list[dict] = []
    for p in soup.find_all("p", class_="NormalMai"):
        block = cleanup(p.get_text(" ", strip=True))
        if not block:
            continue
        cf = bool(_CF_PREFIX.match(block)) or block.lstrip().startswith("(")
        code, name, rest = _region_of(block, area_index)
        cites = [{"pos": pos, "surname": surname, "year": year}
                 for pos, surname, year in parse_refs(rest)]
        if cites:
            regions.append({"area_code": code, "region": name, "cf": cf, "cites": cites})
    return regions


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def out_path() -> Path:
    return Path(settings.motifs_dir) / OUT_FILE


def refresh(motifs: list[dict], *, force: bool = False) -> dict:
    """Fetch + parse the Berezkin bibliography, link it to regions/ethnos.

    Reads the already-cached motif detail pages (only ``biblio.html`` is fetched).
    Writes ``outputs/motifs/berezkin_bibliography.json`` and returns a count dict;
    returns ``{"skipped": ...}`` if the bibliography page can't be fetched.
    """
    cache = Path(settings.motifs_dir) / "raw" / "berezkin"
    try:
        biblio_html = fetch_text(f"{BASE}/biblio.html", cache / "biblio.html",
                                 encoding="windows-1251", force=force)
    except Exception as exc:  # bibliography is optional enrichment
        logger.warning("Berezkin bibliography: could not fetch biblio.html (%s) — skipping", exc)
        return {"skipped": "no-bibliography"}

    biblio = parse_bibliography(biblio_html)
    # Resolution index: 4-digit year -> [(key, folded author, normalised year)].
    by_year: dict[str, list[tuple[str, str, str]]] = defaultdict(list)
    for key, e in biblio.items():
        by_year[e["year"][:4]].append((key, _fold(e["author"]), _year_norm(e["year"])))

    # Region names (hardcoded legend, normalised for dash/case/order-insensitive
    # matching). Citations are linked to macro-areas only — the far more expensive
    # ethnos linkage (matching every block against ~1000 tradition names) was
    # dropped, as nothing displays it.
    area_index = region_index(berezkin.canonical_area_legend())

    def parse_one(m: dict) -> tuple[str, list[dict]]:
        page = m.get("page")
        # Read only already-cached detail pages (no fetching here): a limited or
        # partial scrape then links exactly what it scraped, never hits the network.
        if not page or not (cache / page).exists():
            return m["id"], []
        try:
            html = (cache / page).read_text("windows-1251", errors="replace")
        except Exception as exc:
            logger.debug("Berezkin bibliography: detail read failed for %s: %s", page, exc)
            return m["id"], []
        return m["id"], parse_attestations(html, area_index)

    workers = max(1, settings.motifs.max_workers)
    logger.info("Berezkin bibliography: parsing %d cached detail pages for citations...", len(motifs))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        parsed = list(pool.map(parse_one, motifs))

    # Resolve + aggregate.
    per_motif: dict[str, list[dict]] = {}
    src_regions: dict[str, set] = defaultdict(set)
    src_uses: Counter = Counter()
    area_agg: dict[str, set] = defaultdict(set)
    n_cite = n_res = n_amb = 0

    for mid, regions in parsed:
        tree = []
        for reg in regions:
            citations = []
            for c in reg["cites"]:
                n_cite += 1
                r = _resolve(c["surname"], c["year"], by_year)
                if r["status"] == "resolved":
                    n_res += 1
                elif r["status"] == "ambiguous":
                    n_amb += 1
                citations.append({"key": r["key"], "status": r["status"]})
                # Aggregates (skip comparative "cf" blocks — not direct attestations).
                if not reg["cf"]:
                    src_uses[r["key"]] += 1
                    if reg["area_code"]:
                        src_regions[r["key"]].add(reg["area_code"])
                        area_agg[reg["area_code"]].add(r["key"])
            tree.append({"area_code": reg["area_code"], "region": reg["region"],
                         "cf": reg["cf"], "citations": citations})
        if tree:
            per_motif[mid] = tree
        # A motif whose detail page carries no citations is common and expected —
        # the total is reported as `motifs_without_citations` in the summary, so we
        # don't warn per page.

    sources = {k: {"author": biblio.get(k, {}).get("author", ""),
                   "year": biblio.get(k, {}).get("year", ""),
                   "regions": sorted(src_regions.get(k, ())),
                   "uses": src_uses[k]}
               for k in src_uses}

    payload = {
        "source": "areasofmyths.com", "attribution": _ATTRIB,
        "bibliography": biblio,
        "by_motif": per_motif,
        "sources": sources,
        "area_index": {a: sorted(ks) for a, ks in area_agg.items()},
    }
    out_path().write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")

    return {
        "works": len(biblio),
        "citations": n_cite,
        "resolved": n_res,
        "ambiguous": n_amb,
        "motifs_with_citations": len(per_motif),
        "motifs_without_citations": len(motifs) - len(per_motif),
    }
