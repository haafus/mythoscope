"""English + node-level enrichment for the Berezkin catalogue from mapsofmyths.com.

mapsofmyths.com is the sister site of areasofmyths.com (same motif ids, CC BY-NC-SA
4.0). It carries, per motif, an English name and definition, a 2-level thematic
taxonomy (type/group), ATU & Thompson (TMI) ids, and the list of traditions
attesting the motif; and a catalogue of 1046 traditions with a named 4-level areal
hierarchy and language family.

``refresh()`` is a pipeline step: it fetches every page into the resumable raw
cache (``outputs/motifs/raw/mapsofmyths/``) and (re)writes three parsed data files
next to the index JSONs (``outputs/motifs/mapsofmyths_*.json``) that ``berezkin.py``
reads at build time. Neither the raw cache nor the parsed files are committed. It
is **credential-gated** (HTTP basic auth): without credentials it is a no-op and
the Berezkin catalogue is simply built without the enrichment.

Parsing is separated from fetching so it can be unit-tested on static fixtures.
"""

from __future__ import annotations

import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from settings import settings

from .fetch import fetch_text

logger = logging.getLogger(__name__)

BASE = "http://mapsofmyths.com"
# English text, node data and the tradition catalogue, keyed by upper-cased id.
EN_FILE, NODES_FILE, TRADITIONS_FILE = (
    "mapsofmyths_en.json", "mapsofmyths_nodes.json", "mapsofmyths_traditions.json")
_LICENSE = "CC BY-NC-SA 4.0"
_ATTRIB = ("Yu.E. Berezkin, E.N. Duvakin. The Electronic Analytic Catalogue of "
           "Folklore and Mythology Motifs")


# --- parsers (pure, testable) ----------------------------------------------

def _field(node, name: str) -> str:
    el = node.find("div", class_=f"field-name-{name}")
    item = el.find("div", class_="field-item") if el else None
    return " ".join(item.get_text(" ", strip=True).split()) if item else ""


def parse_motifs_full(html: str) -> dict[str, dict]:
    """id -> {name_eng, definition_eng, href} from the /motifs_full listing."""
    from bs4 import BeautifulSoup

    out: dict[str, dict] = {}
    for node in BeautifulSoup(html, "html.parser").find_all(
            "div", class_=lambda c: c and "node-motif" in c):
        h2, a = node.find("h2"), node.find("a", href=True)
        if not h2:
            continue
        out[h2.get_text(strip=True).upper()] = {
            "name_eng": _field(node, "field-name-eng"),
            "definition_eng": _field(node, "body"),
            "href": a["href"] if a else "",
        }
    return out


def parse_motif_node(html: str) -> dict:
    """Type/group, ATU & Thompson ids, and attesting-tradition areal ids."""
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    group = _field(soup, "field-motif-group")
    traditions: list[str] = []
    table = soup.find("table")
    if table:
        for row in table.find_all("tr"):
            cells = [" ".join(td.get_text(" ", strip=True).split()) for td in row.find_all("td")]
            if len(cells) >= 2 and re.match(r"^[\d.]+$", cells[0]):
                traditions.append(cells[0])
    return {
        "type": _field(soup, "field-motif-type"),
        "group_num": group.split()[0] if group else "",
        "group": group,
        "atu": _field(soup, "field-atu-id"),
        "tmi": _field(soup, "field-stith-thompson-id"),
        "traditions": traditions,
    }


def parse_traditions_full(html: str) -> dict[str, dict]:
    """areal_id -> {name, name_rus, areal_path:[[id,name]], language:[...]}."""
    from bs4 import BeautifulSoup

    out: dict[str, dict] = {}
    view = BeautifulSoup(html, "html.parser").find("div", class_="view-content")
    for r in view.find_all("div", class_=lambda c: c and "views-row" in c) if view else []:
        aid_el = r.find("div", class_="field-name-field-areal-id")
        aid = aid_el.find("div", class_="field-item").get_text(strip=True) if aid_el else ""
        if not aid:
            continue
        name = " ".join(r.find("h2").get_text(" ", strip=True).split()) if r.find("h2") else ""
        areal = r.find("div", class_="field-name-field-areal")
        levels = [" ".join(a.get_text(" ", strip=True).split())
                  for a in areal.select("ul.shs-hierarchy li a")] if areal else []
        parts = aid.split(".")
        path = [[".".join(parts[: i + 1]), lvl] for i, lvl in enumerate(levels)]
        lang = r.find("div", class_="field-name-field-language-hierarchy")
        language = [" ".join(a.get_text(" ", strip=True).split())
                    for a in lang.find_all("a")] if lang else []
        out[aid] = {"name": name, "name_rus": _field(r, "body"),
                    "areal_path": path, "language": language}
    return out


# --- pipeline step ---------------------------------------------------------

def _auth() -> tuple[str, str] | None:
    u, p = settings.motifs.mapsofmyths_user, settings.motifs.mapsofmyths_pass
    return (u, p) if u and p else None


def data_dir() -> Path:
    """Where the parsed enrichment files live (next to the index JSONs)."""
    return Path(settings.motifs_dir)


def _write(name: str, payload: dict) -> None:
    (data_dir() / name).write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")


def refresh(*, force: bool = False, auth: tuple[str, str] | None = None) -> dict:
    """Fetch + parse mapsofmyths into ``outputs/motifs/``. Returns a count dict.

    No-op (returns ``{"skipped": ...}``) when credentials are absent — the Berezkin
    catalogue is then built without the enrichment. ``auth`` overrides settings.
    """
    auth = auth or _auth()
    if not auth:
        logger.warning("mapsofmyths: no credentials (MYTHO_MOTIFS__MAPSOFMYTHS_USER/_PASS) — "
                       "skipping English/taxonomy/TMI/traditions enrichment")
        return {"skipped": "no-credentials"}

    cache = data_dir() / "raw" / "mapsofmyths"

    def get(path: str, cache_name: str) -> str:
        return fetch_text(f"{BASE}{path}", cache / cache_name, force=force, auth=auth)

    english = parse_motifs_full(get("/motifs_full", "motifs_full.html"))
    _write(EN_FILE, {
        "source": "mapsofmyths.com", "license": _LICENSE, "attribution": _ATTRIB,
        "motifs": {k: {"name_eng": v["name_eng"], "definition_eng": v["definition_eng"]}
                   for k, v in english.items()},
    })

    targets = [(mid, v["href"]) for mid, v in english.items() if v["href"]]
    workers = max(1, settings.motifs.max_workers)

    def one(mh):
        mid, href = mh
        try:
            node_id = href.rstrip("/").rsplit("/", 1)[-1]
            return mid, parse_motif_node(get(href, f"node_{node_id}.html"))
        except Exception as exc:  # a missing/odd node must not abort the whole build
            logger.debug("mapsofmyths: node fetch failed for %s: %s", href, exc)
            return mid, None

    nodes: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for mid, rec in pool.map(one, targets):
            if rec:
                nodes[mid] = rec
    _write(NODES_FILE, {
        "source": "mapsofmyths.com", "license": _LICENSE, "attribution": _ATTRIB, "motifs": nodes})

    traditions = parse_traditions_full(get("/traditions_full", "traditions_full.html"))
    _write(TRADITIONS_FILE, {
        "source": "mapsofmyths.com", "license": _LICENSE, "attribution": _ATTRIB,
        "traditions": traditions})

    counts = {
        "motifs": len(english),
        "with_type": sum(1 for r in nodes.values() if r.get("type")),
        "with_tmi": sum(1 for r in nodes.values() if r.get("tmi")),
        "with_atu": sum(1 for r in nodes.values() if r.get("atu")),
        "with_traditions": sum(1 for r in nodes.values() if r.get("traditions")),
        "traditions": len(traditions),
    }
    logger.info("mapsofmyths: refreshed — motifs:%d type/group:%d tmi:%d atu:%d "
                "traditions-sets:%d; tradition catalogue:%d",
                counts["motifs"], counts["with_type"], counts["with_tmi"],
                counts["with_atu"], counts["with_traditions"], counts["traditions"])
    return counts
