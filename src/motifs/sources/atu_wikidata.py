"""ATU tale-type enrichment from Wikidata — multilingual names + Wikipedia links.

Open SPARQL endpoint (`query.wikidata.org`), matched on the ATU-number property
(**P2540**). For each type we keep the multilingual names of its *tale-type* items
(``P31 = wd:Q47451145``, so specific tale instances don't masquerade as names) and
the Wikipedia articles of all its items. Best-effort: a network failure just skips
the enrichment and the ATU index stays as-is (graceful degradation). The raw
response is cached under ``raw/wikidata/`` so re-runs are offline.

Parsing is separated from fetching so it can be unit-tested on a static fixture.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.parse import unquote, urlencode

from settings import settings

from .fetch import fetch_text

logger = logging.getLogger(__name__)

WDQS = "https://query.wikidata.org/sparql"
OUT = Path("raw") / "wikidata" / "atu.json"
# Languages we surface as alternate names (in this preference order).
_LANGS = ("en", "de", "ru", "fr", "es", "it")
# wd:Q47451145 = "tale type"; only those items name the type itself.
_QUERY = """SELECT ?atu ?item ?isType ?art %s WHERE {
  ?item wdt:P2540 ?atu .
  BIND(EXISTS { ?item wdt:P31 wd:Q47451145 } AS ?isType)
  OPTIONAL { ?art schema:about ?item ; schema:isPartOf <https://en.wikipedia.org/> . }
%s
}""" % (
    " ".join(f"?l_{lang}" for lang in _LANGS),
    "\n".join(f'  OPTIONAL {{ ?item rdfs:label ?l_{lang} FILTER(lang(?l_{lang})="{lang}") }}'
              for lang in _LANGS),
)

# Cyrillic capitals sometimes typed for their Latin look-alikes in a Wikidata ATU
# number ("283В*" with a Cyrillic В); fold them so the number matches our id.
_HOMOGLYPHS = str.maketrans("АВСЕКМНОРТХ", "ABCEKMHOPTX")


def _norm_atu(value: str) -> str:
    return (value or "").strip().translate(_HOMOGLYPHS)


def _wiki_title(url: str) -> str:
    return unquote(url.rsplit("/", 1)[-1]).replace("_", " ")


def query_url() -> str:
    return f"{WDQS}?" + urlencode({"format": "json", "query": _QUERY})


def parse_bindings(rows: list[dict], atu_ids: set[str]) -> dict[str, dict]:
    """SPARQL bindings -> ``{atu_id: {names: {lang: [..]}, wikipedia: [{title,url}], wikidata}}``.

    Names come only from tale-type items; Wikipedia links from any item; both are
    de-duplicated in first-seen order. Only ids present in ``atu_ids`` are kept."""
    out: dict[str, dict] = {}
    for r in rows:
        atu = _norm_atu(r.get("atu", {}).get("value", ""))
        if atu not in atu_ids:
            continue
        entry = out.setdefault(atu, {"names": {}, "wikipedia": [], "wikidata": None, "_seen": set()})
        if r.get("isType", {}).get("value") == "true":
            if entry["wikidata"] is None:
                entry["wikidata"] = r.get("item", {}).get("value", "").rsplit("/", 1)[-1]
            for lang in _LANGS:
                name = r.get(f"l_{lang}", {}).get("value")
                if name:
                    names = entry["names"].setdefault(lang, [])
                    if name not in names:
                        names.append(name)
        art = r.get("art", {}).get("value")
        if art and art not in entry["_seen"]:
            entry["_seen"].add(art)
            entry["wikipedia"].append({"title": _wiki_title(art), "url": art})
    for entry in out.values():
        entry.pop("_seen", None)
    return out


def refresh(atu_types: list[dict], *, force: bool = False) -> dict:
    """Fetch Wikidata and attach ``names`` / ``wikipedia`` / ``wikidata`` to each type,
    in place. Returns a count dict, or ``{"skipped": ...}`` if the fetch failed."""
    cache = Path(settings.motifs_dir) / OUT
    try:
        raw = fetch_text(query_url(), cache, force=force)
        rows = json.loads(raw)["results"]["bindings"]
    except Exception as exc:  # open enrichment — never fatal to the build
        logger.warning("ATU Wikidata: could not fetch/parse SPARQL (%s) — skipping", exc)
        cache.unlink(missing_ok=True)  # don't cache a bad/partial response
        return {"skipped": "no-wikidata"}

    ids = {t["id"] for t in atu_types}
    mapping = parse_bindings(rows, ids)
    n_names = n_wiki = 0
    for t in atu_types:
        m = mapping.get(t["id"])
        if not m:
            continue
        # Drop an English name identical to our own type name (not an "alternate").
        own = (t.get("name") or "").strip().lower()
        m["names"]["en"] = [n for n in m["names"].get("en", []) if n.strip().lower() != own]
        names = {lang: v for lang, v in m["names"].items() if v}
        if names:
            t["names"] = names
            n_names += 1
        if m["wikipedia"]:
            t["wikipedia"] = m["wikipedia"]
            n_wiki += 1
        if m["wikidata"]:
            t["wikidata"] = m["wikidata"]
    logger.info("ATU Wikidata: %d/%d types enriched with multilingual names, %d with Wikipedia links",
                n_names, len(atu_types), n_wiki)
    return {"types_with_names": n_names, "types_with_wikipedia": n_wiki, "rows": len(rows)}
