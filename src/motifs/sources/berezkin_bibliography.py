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
``ambiguous``), and attributes each to its region (from the canonical area legend)
and, where the ethnos name matches a mapsofmyths tradition (``name_rus``), to that
tradition. It writes a machine-readable ``berezkin_bibliography.json`` (per-motif
region→ethnos→citation tree + source→regions/traditions aggregates) — gitignored,
best-effort enrichment. Ethnos linkage is credential-gated (needs the mapsofmyths
tradition catalogue); region linkage always works from the hardcoded area legend.

Parsing is separated from fetching so it can be unit-tested on static fixtures.
"""

from __future__ import annotations

import json
import logging
import re
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

    soup = BeautifulSoup(html, "html.parser")
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

        surname = re.split(r"[,\s]", author, 1)[0].strip()
        if not surname:
            continue
        key = f"{surname} {year}"
        if key not in out:
            out[key] = {"author": author, "year": year, "title": title}
        elif out[key]["author"] != author:
            out[key].setdefault("homonyms", []).append(author)
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


def _resolve(surname: str, year: str, by_year: dict[str, list[tuple[str, str]]]) -> dict:
    """Resolve a citation to a bibliography key. ``status`` is resolved / ambiguous
    / unresolved; ``ambiguous`` = same surname+year for several authors."""
    hits = [key for key, full in by_year.get(year, ())
            if re.search(rf"(?<!-)\b{re.escape(surname)}\b(?!-)", full, re.IGNORECASE)]
    if len(hits) == 1:
        return {"key": hits[0], "status": "resolved"}
    if len(hits) > 1:
        return {"key": f"{surname} {year}", "status": "ambiguous"}
    return {"key": f"{surname} {year}", "status": "unresolved"}


# ---------------------------------------------------------------------------
# Detail-page attestations: region -> ethnos -> citations
# ---------------------------------------------------------------------------

_CF_PREFIX = re.compile(r"^[(\[]?\s*(ср|см|cf)\.?\s*", re.IGNORECASE)


def _region_of(block: str, area_names: list[tuple[str, str]]) -> tuple[str, str, str]:
    """``(area_code, area_name, rest)`` — the longest area name the block opens with."""
    head = _CF_PREFIX.sub("", block).lstrip("([ ")
    for name, code in area_names:  # pre-sorted longest-first
        if head.startswith(name):
            return code, name, head[len(name):]
    return "", "", head


def parse_attestations(html: str, area_names: list[tuple[str, str]],
                       trad_re: re.Pattern | None, trad_by_name: dict[str, str]) -> list[dict]:
    """Parse a motif detail page into region blocks with their citations.

    Each ``NormalMai`` paragraph is one region: ``[{area_code, region, cf, cites:
    [{pos, surname, year, ethnos, tradition_id}]}]``. Ethnos is the nearest
    preceding mapsofmyths tradition name (sticky within the block); ``None`` when
    the catalogue is absent (no credentials) or no name matched.
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    regions: list[dict] = []
    for p in soup.find_all("p", class_="NormalMai"):
        block = cleanup(p.get_text(" ", strip=True))
        if not block:
            continue
        cf = bool(_CF_PREFIX.match(block)) or block.lstrip().startswith("(")
        code, name, rest = _region_of(block, area_names)

        # Ethnos hits (positions of known tradition names), for nearest-preceding
        # attribution as we walk the citations left to right.
        ethnos_hits = ([(mm.start(), mm.group(0), trad_by_name[mm.group(0)])
                        for mm in trad_re.finditer(rest)] if trad_re else [])
        cites = []
        ethnos_i = 0
        cur_name = cur_tid = None
        for pos, surname, year in parse_refs(rest):
            while ethnos_i < len(ethnos_hits) and ethnos_hits[ethnos_i][0] < pos:
                _, cur_name, cur_tid = ethnos_hits[ethnos_i]
                ethnos_i += 1
            cites.append({"pos": pos, "surname": surname, "year": year,
                          "ethnos": cur_name, "tradition_id": cur_tid})
        if cites:
            regions.append({"area_code": code, "region": name, "cf": cf, "cites": cites})
    return regions


def _name_regex(names) -> re.Pattern | None:
    """One alternation matching any tradition name as a whole word (longest-first)."""
    ordered = sorted((n for n in names if len(n) >= 3), key=len, reverse=True)
    if not ordered:
        return None
    return re.compile(r"(?<!\w)(" + "|".join(re.escape(n) for n in ordered) + r")(?!\w)")


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
    by_year: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for key, e in biblio.items():
        by_year[e["year"]].append((key, e["author"]))

    # Region names (hardcoded legend, longest-first) and ethnos names (mapsofmyths,
    # credential-gated — absent => region-level only).
    area_names = sorted(((name, code) for code, name in berezkin.canonical_area_legend().items() if name),
                        key=lambda nc: len(nc[0]), reverse=True)
    trad_by_name: dict[str, str] = {}
    for tid, t in berezkin.load_traditions().items():
        nr = (t.get("name_rus") or "").strip()
        if nr:
            trad_by_name.setdefault(nr, tid)
    trad_re = _name_regex(trad_by_name)

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
        return m["id"], parse_attestations(html, area_names, trad_re, trad_by_name)

    workers = max(1, settings.motifs.max_workers)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        parsed = list(pool.map(parse_one, motifs))

    # Resolve + aggregate.
    per_motif: dict[str, list[dict]] = {}
    src_regions: dict[str, set] = defaultdict(set)
    src_trads: dict[str, set] = defaultdict(set)
    src_uses: Counter = Counter()
    area_index: dict[str, set] = defaultdict(set)
    trad_index: dict[str, set] = defaultdict(set)
    n_cite = n_res = n_amb = n_eth = 0

    for mid, regions in parsed:
        tree = []
        for reg in regions:
            groups: dict[tuple, dict] = {}
            order: list[tuple] = []
            for c in reg["cites"]:
                n_cite += 1
                r = _resolve(c["surname"], c["year"], by_year)
                if r["status"] == "resolved":
                    n_res += 1
                elif r["status"] == "ambiguous":
                    n_amb += 1
                if c["tradition_id"]:
                    n_eth += 1
                gk = (c["ethnos"], c["tradition_id"])
                if gk not in groups:
                    groups[gk] = {"name": c["ethnos"], "tradition_id": c["tradition_id"], "citations": []}
                    order.append(gk)
                groups[gk]["citations"].append({"key": r["key"], "status": r["status"]})
                # Aggregates (skip comparative "cf" blocks — not direct attestations).
                if not reg["cf"]:
                    src_uses[r["key"]] += 1
                    if reg["area_code"]:
                        src_regions[r["key"]].add(reg["area_code"])
                        area_index[reg["area_code"]].add(r["key"])
                    if c["tradition_id"]:
                        src_trads[r["key"]].add(c["tradition_id"])
                        trad_index[c["tradition_id"]].add(r["key"])
            tree.append({"area_code": reg["area_code"], "region": reg["region"],
                         "cf": reg["cf"], "ethnos": [groups[k] for k in order]})
        if tree:
            per_motif[mid] = tree

    sources = {k: {"author": biblio.get(k, {}).get("author", ""),
                   "year": biblio.get(k, {}).get("year", ""),
                   "regions": sorted(src_regions.get(k, ())),
                   "tradition_ids": sorted(src_trads.get(k, ())),
                   "uses": src_uses[k]}
               for k in src_uses}

    payload = {
        "source": "areasofmyths.com", "attribution": _ATTRIB,
        "bibliography": biblio,
        "by_motif": per_motif,
        "sources": sources,
        "area_index": {a: sorted(ks) for a, ks in area_index.items()},
        "tradition_index": {t: sorted(ks) for t, ks in trad_index.items()},
    }
    out_path().write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")

    return {
        "works": len(biblio),
        "citations": n_cite,
        "resolved": n_res,
        "ambiguous": n_amb,
        "ethnos_linked": n_eth,
        "traditions_available": len(trad_by_name),
        "motifs_with_citations": len(per_motif),
    }
