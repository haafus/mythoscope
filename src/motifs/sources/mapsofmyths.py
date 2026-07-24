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
import os
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


_NODE_RE = re.compile(r"/node/(\d+)")


def parse_traditions_full(html: str) -> dict[str, dict]:
    """areal_id -> {name, name_rus, areal_path:[[id,name]], language:[...], node}.

    ``node`` is the Drupal node id, used to fetch the tradition's map coordinates
    from the ``/gmap-markers-tradition`` endpoint (see ``refresh``).
    """
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
        node_link = r.find("a", href=_NODE_RE)
        node = _NODE_RE.search(node_link["href"]).group(1) if node_link else ""
        out[aid] = {"name": name, "name_rus": _field(r, "body"),
                    "areal_path": path, "language": language, "node": node}
    return out


def parse_tradition_markers(payload: str) -> list | None:
    """``[lat, lon]`` for a tradition from a ``/gmap-markers-tradition`` JSON reply.

    The endpoint returns a list of ``{lat, lng, ...}`` markers (a tradition may span
    several points); we take their centroid. Returns ``None`` if the reply is empty
    or unparseable, so a missing/odd tradition can't poison the catalogue.
    """
    try:
        markers = json.loads(payload)
    except (ValueError, TypeError):
        return None
    lats, lons = [], []
    for m in markers or []:
        try:
            # some rows use a comma as the decimal separator (e.g. "61,5")
            lat = float(str(m["lat"]).replace(",", "."))
            lon = float(str(m["lng"]).replace(",", "."))
        except (KeyError, ValueError, TypeError):
            continue
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            lats.append(lat)
            lons.append(lon)
    if not lats:
        return None
    return [round(sum(lats) / len(lats), 4), round(sum(lons) / len(lons), 4)]


# --- pipeline step ---------------------------------------------------------

def _auth() -> tuple[str, str] | None:
    # A single ``user:pass`` env var (loaded from .env by dotenv, like the API
    # keys) — split on the first colon, curl-style.
    raw = os.environ.get("MAPSOFMYTHS_AUTH", "")
    user, sep, password = raw.partition(":")
    return (user, password) if sep and user and password else None


def data_dir() -> Path:
    """Where the parsed enrichment files live (next to the index JSONs)."""
    return Path(settings.motifs_dir)


def _write(name: str, payload: dict) -> None:
    (data_dir() / name).write_text(json.dumps(payload, ensure_ascii=False, indent=0), encoding="utf-8")


def _post_markers(node: str, cache_dir: Path, auth: tuple[str, str], *, force: bool = False) -> str:
    """POST the ``/gmap-markers-tradition`` endpoint for one node, cached like a
    fetch (a non-empty cached reply short-circuits unless ``force``)."""
    cache_file = cache_dir / f"markers_{node}.json"
    if not force and cache_file.exists() and cache_file.stat().st_size > 0:
        return cache_file.read_text(encoding="utf-8")
    import requests  # lazy: the HTTP dep lives in the corpus extra

    resp = requests.post(f"{BASE}/gmap-markers-tradition", data={"tradition": node},
                         auth=auth, timeout=60)
    resp.raise_for_status()
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(resp.text, encoding="utf-8")
    return resp.text


def refresh(*, force: bool = False, auth: tuple[str, str] | None = None) -> dict:
    """Fetch + parse mapsofmyths into ``outputs/motifs/``. Returns a count dict.

    No-op (returns ``{"skipped": ...}``) when credentials are absent — the Berezkin
    catalogue is then built without the enrichment. ``auth`` overrides settings.
    """
    auth = auth or _auth()
    if not auth:
        logger.warning("mapsofmyths: no credentials (MAPSOFMYTHS_AUTH=user:pass in .env) — "
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
    logger.info("mapsofmyths: parsing %d motif node pages...", len(targets))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for mid, rec in pool.map(one, targets):
            if rec:
                nodes[mid] = rec
    _write(NODES_FILE, {
        "source": "mapsofmyths.com", "license": _LICENSE, "attribution": _ATTRIB, "motifs": nodes})

    traditions = parse_traditions_full(get("/traditions_full", "traditions_full.html"))

    # Real per-tradition coordinates: each catalogue row carries a Drupal node id
    # whose map markers give the tradition's actual location(s). Fetch them (cached,
    # concurrent) and attach the marker centroid as ``coordinates`` = [lat, lon].
    marker_cache = cache / "markers"

    def coord(item):
        aid, rec = item
        node = rec.get("node")
        if not node:
            return aid, None
        try:
            return aid, parse_tradition_markers(_post_markers(node, marker_cache, auth, force=force))
        except Exception as exc:  # a missing/odd marker reply must not abort the build
            logger.debug("mapsofmyths: marker fetch failed for node %s: %s", node, exc)
            return aid, None

    with_coords = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for aid, coords in pool.map(coord, traditions.items()):
            if coords:
                traditions[aid]["coordinates"] = coords
                with_coords += 1

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
        "traditions_with_coords": with_coords,
    }
    logger.info("mapsofmyths: refreshed — motifs:%d type/group:%d tmi:%d atu:%d "
                "traditions-sets:%d; tradition catalogue:%d",
                counts["motifs"], counts["with_type"], counts["with_tmi"],
                counts["with_atu"], counts["with_traditions"], counts["traditions"])
    logger.info("mapsofmyths: tradition coordinates resolved — coords:%d/%d",
                with_coords, counts["traditions"])
    return counts
