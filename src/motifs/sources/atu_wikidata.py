"""ATU tale-type enrichment from Wikidata.

Open SPARQL endpoint (`query.wikidata.org`), matched on the ATU-number property
(**P2540**). Per type we collect, aggregated over all its Wikidata items:

  * multilingual **names** — from its *tale-type* items (``P31 = wd:Q47451145``, so
    specific tale instances don't masquerade as names);
  * **Wikipedia** articles (en/ru/de/fr) — encyclopedic summaries of the type;
  * **Wikisource** links (any language) — full primary texts of tales of the type;
  * **concordances** to other catalogues — Grimm/KHM, Aarne-Thompson (AaTh), Perry
    (Aesop), Child ballads — from ``P528`` catalog codes (+ ``P972`` catalog) and the
    Perry-Index property ``P1852``.

Best-effort: a network failure just skips the enrichment (graceful degradation).
The raw response is cached under ``raw/wikidata/`` so re-runs are offline. Parsing
is separated from fetching so it can be unit-tested on a static fixture.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from urllib.parse import unquote, urlencode

from settings import settings

from .fetch import FetchRejected, fetch_text, read_pinned

logger = logging.getLogger(__name__)

WDQS = "https://query.wikidata.org/sparql"
OUT = Path("raw") / "wikidata" / "atu.json"
_LANGS = ("en", "de", "ru", "fr", "es", "it")     # alternate names, this preference order
_WIKIS = ("en", "ru", "de", "fr")                 # Wikipedia languages to link

# A catalogue (P972) -> short label under which we group its P528 codes.
_CATALOG = {
    "Grimms' fairy tales": "KHM",
    "Kinder- und Haus-Märchen Band 1": "KHM",
    "The Types of the Folktale": "AaTh",
    "Child Ballads": "Child",
    "Fabulae Aesopicae Collectae": "Aesop",
}
# AaTh first — the direct pre-2004 ancestor of ATU — then the story collections.
_CONCORDANCE_ORDER = ["AaTh", "KHM", "Perry", "Aesop", "Child"]

# wd:Q47451145 = "tale type"; only those items name the type itself.
_QUERY = """SELECT ?atu ?item ?isType (SAMPLE(?perry) AS ?perry)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?lang),"=",STR(?art)); separator="|") AS ?arts)
  (GROUP_CONCAT(DISTINCT CONCAT(STR(?slang),"=",STR(?src)); separator="|") AS ?srcs)
  (GROUP_CONCAT(DISTINCT CONCAT(?catL,"=",?code); separator="|") AS ?cats)
  %s WHERE {
  ?item wdt:P2540 ?atu .
  BIND(EXISTS { ?item wdt:P31 wd:Q47451145 } AS ?isType)
  OPTIONAL { ?item wdt:P1852 ?perry }
  OPTIONAL { ?art schema:about ?item ; schema:inLanguage ?lang ;
             schema:isPartOf [ wikibase:wikiGroup "wikipedia" ] . FILTER(?lang IN (%s)) }
  OPTIONAL { ?src schema:about ?item ; schema:inLanguage ?slang ;
             schema:isPartOf [ wikibase:wikiGroup "wikisource" ] }
  OPTIONAL { ?item p:P528 ?st . ?st ps:P528 ?code ; pq:P972 ?ci .
             ?ci rdfs:label ?catL FILTER(lang(?catL)="en") }
%s
} GROUP BY ?atu ?item ?isType""" % (  # noqa: UP031 — %-format keeps SPARQL braces unescaped
    " ".join(f"(SAMPLE(?l_{lang}) AS ?l_{lang})" for lang in _LANGS),
    ", ".join(f'"{w}"' for w in _WIKIS),
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


def _lang_key(w: dict) -> tuple:
    """Sort sitelinks by our language preference, then title."""
    return (_WIKIS.index(w["lang"]) if w["lang"] in _WIKIS else 9, w["title"])


def query_url() -> str:
    return f"{WDQS}?" + urlencode({"format": "json", "query": _QUERY})


def _add_concordance(entry: dict, catalog: str, code: str, atu: str) -> None:
    short = _CATALOG.get(catalog)
    if not short:
        return
    code = code.strip()
    if code.upper().startswith(short.upper() + " "):   # "KHM 59" -> "59"
        code = code[len(short) + 1:].strip()
    if not code or (short == "AaTh" and code == atu):  # AaTh == our number is redundant
        return
    codes = entry["concordances"].setdefault(short, [])
    if code not in codes:
        codes.append(code)


def parse_bindings(rows: list[dict], atu_ids: set[str]) -> dict[str, dict]:
    """SPARQL bindings -> ``{atu_id: {names, wikipedia, wikidata, concordances}}``.

    Aggregated across a number's items; names come only from tale-type items.
    Only ids in ``atu_ids`` are kept."""
    out: dict[str, dict] = {}
    for r in rows:
        atu = _norm_atu(r.get("atu", {}).get("value", ""))
        if atu not in atu_ids:
            continue
        e = out.setdefault(atu, {"names": {}, "wikipedia": [], "wikisource": [], "wikidata": None,
                                 "concordances": {}, "_seen": set()})
        is_type = r.get("isType", {}).get("value") == "true"
        if is_type:
            if e["wikidata"] is None:
                e["wikidata"] = r.get("item", {}).get("value", "").rsplit("/", 1)[-1]
            for lang in _LANGS:
                name = r.get(f"l_{lang}", {}).get("value")
                if name:
                    names = e["names"].setdefault(lang, [])
                    if name not in names:
                        names.append(name)
        for piece in filter(None, r.get("arts", {}).get("value", "").split("|")):
            lang, _, url = piece.partition("=")
            if url and url not in e["_seen"]:
                e["_seen"].add(url)
                e["wikipedia"].append({"lang": lang, "title": _wiki_title(url), "url": url})
        for piece in filter(None, r.get("srcs", {}).get("value", "").split("|")):
            lang, _, url = piece.partition("=")
            if url and url not in e["_seen"]:
                e["_seen"].add(url)
                e["wikisource"].append({"lang": lang, "title": _wiki_title(url), "url": url})
        for piece in filter(None, r.get("cats", {}).get("value", "").split("|")):
            label, _, code = piece.partition("=")
            _add_concordance(e, label, code, atu)
        perry = r.get("perry", {}).get("value")
        if perry and perry not in e["concordances"].setdefault("Perry", []):
            e["concordances"]["Perry"].append(perry)
    for e in out.values():
        e.pop("_seen", None)
        # Order Wikipedia/Wikisource links by our language preference, ordered concordances too.
        e["wikipedia"].sort(key=_lang_key)
        e["wikisource"].sort(key=_lang_key)
        e["concordances"] = {k: e["concordances"][k] for k in _CONCORDANCE_ORDER if e["concordances"].get(k)}
    return out


def refresh(atu_types: list[dict], *, force: bool = False) -> dict:
    """Fetch Wikidata and attach ``names`` / ``wikipedia`` / ``wikidata`` /
    ``concordances`` to each type, in place. ``{"skipped": ...}`` if the fetch failed."""
    cache = Path(settings.motifs_dir) / OUT
    ids = {t["id"] for t in atu_types}
    parsed: dict = {}   # the validator hands the parsed rows/mapping to the caller — parse once, reuse

    def _healthy(content: bytes) -> bool:
        """Validate-before-commit: a healthy full reply parses **and**, when substantial, carries some
        Wikipedia sitelinks. Rows-but-zero-sitelinks is a degraded WDQS reply (the heavy OPTIONALs timed
        out during an outage while cheap ``rdfs:label`` lookups still return); rejecting it here means it
        never overwrites the pinned copy. Any parse/structure error is unhealthy too — caught here, never
        raised out of the validator (else it would be mistaken for a transport failure)."""
        try:
            rows = json.loads(content)["results"]["bindings"]
            mapping = parse_bindings(rows, ids)
        except Exception:
            return False
        if len(rows) >= 50 and not any(m["wikipedia"] for m in mapping.values()):
            return False
        parsed.update(rows=rows, mapping=mapping)   # reused by the caller on the fresh path (no re-parse)
        return True

    try:
        raw = fetch_text(query_url(), cache, force=force, validate=_healthy)
    except FetchRejected:
        # Downloaded but unhealthy (unparseable or degraded) — the cache was NOT overwritten. Serve the last
        # good pinned copy if there is one; it is parsed (guarded) below.
        raw = read_pinned(cache)
        if raw is None:
            logger.warning("ATU Wikidata: reply unparseable or degraded and no pinned copy — skipping this "
                           "enrichment; re-run with --force once query.wikidata.org recovers")
            return {"skipped": "degraded-or-unparseable"}
        logger.warning("ATU Wikidata: reply unparseable or degraded — serving the pinned cached copy; re-run "
                       "with --force once query.wikidata.org recovers")
    except Exception as exc:
        # Transport/HTTP failure — raised before any write, so the pinned copy is intact; keep it. Name the
        # reason (429 = WDQS rate-limiting/outage) when the response carried one, else a generic fetch error.
        status = getattr(getattr(exc, "response", None), "status_code", None)
        reason = f"http-{status}" if status else "fetch-error"
        logger.warning("ATU Wikidata: SPARQL fetch failed [%s] (%s) — keeping the pinned cached copy; re-run "
                       "with --force once query.wikidata.org recovers", reason, exc)
        return {"skipped": reason}

    # The fresh fetch already parsed inside the validator. A cache-hit short-circuit (force=False, cache
    # present) or a served-pinned copy was NOT validated, so parse `raw` here — guarded, so a bad reply skips
    # the enrichment rather than aborting the whole build.
    if not parsed:
        try:
            rows = json.loads(raw)["results"]["bindings"]
            parsed.update(rows=rows, mapping=parse_bindings(rows, ids))
        except Exception as exc:
            logger.warning("ATU Wikidata: cached/pinned reply not parseable (%s) — skipping this enrichment; "
                           "re-run with --force once query.wikidata.org recovers", exc)
            return {"skipped": "cache-unparseable"}
    rows, mapping = parsed["rows"], parsed["mapping"]

    n_names = n_wiki = n_src = n_conc = 0
    for t in atu_types:
        m = mapping.get(t["id"])
        if not m:
            continue
        own = (t.get("name") or "").strip().lower()
        m["names"]["en"] = [n for n in m["names"].get("en", []) if n.strip().lower() != own]
        names = {lang: v for lang, v in m["names"].items() if v}
        if names:
            t["names"] = names
            n_names += 1
        if m["wikipedia"]:
            t["wikipedia"] = m["wikipedia"]
            n_wiki += 1
        if m["wikisource"]:
            t["wikisource"] = m["wikisource"]
            n_src += 1
        if m["concordances"]:
            t["concordances"] = m["concordances"]
            n_conc += 1
        if m["wikidata"]:
            t["wikidata"] = m["wikidata"]
    logger.info("ATU Wikidata: names %d, Wikipedia %d, Wikisource %d, concordances %d (of %d types)",
                n_names, n_wiki, n_src, n_conc, len(atu_types))
    return {"types_with_names": n_names, "types_with_wikipedia": n_wiki,
            "types_with_wikisource": n_src, "types_with_concordances": n_conc, "rows": len(rows)}
