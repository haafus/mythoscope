"""Read-side service for the motif database.

Serves the browsable Motifs catalog: index summaries, paginated/filtered motif
lists, and per-motif detail with resolved cross-walk links. All data is read
from ``outputs/motifs/`` (built by ``mytho motifs``) and cached per process.
"""

from __future__ import annotations

import json
import re
from importlib.resources import files as _pkg_files

from motifs import INDEX_LABELS, INDEX_ORDER, store
from motifs.sources.culture_dict import canonical

# A standalone Roman numeral token (Latin letters) — kept upper-case when
# sentence-casing all-caps titles.
_ROMAN_RE = re.compile(r"\b[IVXLCDM]+\b", re.IGNORECASE)

# Which list key each index stores its records under.
_RECORDS_KEY = {"berezkin": "motifs", "tmi": "motifs", "atu": "types"}


def is_built() -> bool:
    return store.is_built()


def _records(index: str) -> list[dict]:
    data = store.load_index(index)
    if not data:
        return []
    return data.get(_RECORDS_KEY.get(index, "motifs"), [])


def _by_id(index: str) -> dict[str, dict]:
    """Cached id -> record map for an index (for cross-link name resolution)."""
    return store.cached(f"byid:{index}", lambda: {r["id"]: r for r in _records(index)})


# --- TMI hierarchy (breadcrumbs + subtree) ------------------------------------
# Parents/levels are corrected at build time (see trilogy._finalize_tmi), so the
# read side just walks the stored `parent`.
_CHILDREN_CAP = 500


def _tmi_children() -> dict[str, list[str]]:
    """parent id -> child ids, in stored (hierarchical) order."""
    def build() -> dict[str, list[str]]:
        children: dict[str, list[str]] = {}
        for mid, rec in _by_id("tmi").items():
            parent = rec.get("parent", "")
            if parent:
                children.setdefault(parent, []).append(mid)
        return children
    return store.cached("tmi:children", build)


def _tmi_ancestors(rec: dict) -> list[dict]:
    """Cross-walk links for every ancestor, broadest first."""
    by_id = _by_id("tmi")
    chain: list[str] = []
    seen = {rec["id"]}
    cur = rec
    while True:
        parent = cur.get("parent", "")
        if not parent or parent in seen or parent not in by_id:
            break
        seen.add(parent)
        chain.append(parent)
        cur = by_id[parent]
    return [_link("tmi", mid) for mid in reversed(chain)]


def _tmi_descendant_counts() -> dict[str, int]:
    """id -> total number of descendants (recursively, down to the leaves)."""
    def build() -> dict[str, int]:
        children = _tmi_children()
        counts: dict[str, int] = {}

        def count(mid: str, stack: frozenset) -> int:
            if mid in counts:
                return counts[mid]
            total = 0
            for child in children.get(mid, []):
                total += 1 + (count(child, stack | {mid}) if child not in stack else 0)
            counts[mid] = total
            return total

        for mid in children:
            count(mid, frozenset())
        return counts

    return store.cached("tmi:descendants", build)


_TIERS = ("all", "def", "sub", "atu")


def _tmi_descendant_tier_counts() -> dict[str, dict[str, int]]:
    """id -> {tier: number of descendants matching that tier}, recursively.

    ``all`` is the plain descendant total; ``def``/``sub``/``atu`` count only the
    descendants that have a definition / are substantive / are ATU-linked. Lets a
    node's descendant badge follow the active filter.
    """
    def build() -> dict[str, dict[str, int]]:
        children = _tmi_children()
        by_id = _by_id("tmi")
        memo: dict[str, dict[str, int]] = {}

        def own(mid: str) -> dict[str, int]:
            r = by_id.get(mid) or {}
            return {"all": 1, "def": int(bool(r.get("definition"))),
                    "sub": int(_substantive(r)), "atu": int(_has_atu(r))}

        def walk(mid: str, stack: frozenset) -> dict[str, int]:
            if mid in memo:
                return memo[mid]
            acc = {t: 0 for t in _TIERS}
            for child in children.get(mid, []):
                if child in stack:
                    continue
                co, cd = own(child), walk(child, stack | {mid})
                for t in _TIERS:
                    acc[t] += co[t] + cd[t]
            memo[mid] = acc
            return acc

        for mid in children:
            walk(mid, frozenset())
        return memo

    return store.cached("tmi:descendant_tiers", build)


def _descendant_counts(motif_id: str) -> dict[str, int]:
    return _tmi_descendant_tier_counts().get(motif_id, {t: 0 for t in _TIERS})


def _tmi_direct_children(motif_id: str) -> tuple[list[dict], bool]:
    """Immediate child links (one level down), capped at _CHILDREN_CAP."""
    kids = _tmi_children().get(motif_id, [])
    shown = [_link("tmi", c) for c in kids[:_CHILDREN_CAP]]
    return shown, len(kids) > _CHILDREN_CAP


def _notes_size(notes: str) -> str:
    """Byte size of a notes string as a compact badge label: '' / '42b' / '1.2k'."""
    n = len((notes or "").encode("utf-8"))
    if not n:
        return ""
    return f"{n}b" if n < 100 else f"{n / 1024:.1f}k"


# A TMI node is "substantive" (a real motif, not an empty grouping header or a
# thin variation) when it carries enough notes or is attested across several
# cultures. Tuned so the substantive core is ~12% of the catalogue.
_SUBSTANTIVE_MIN_NOTES = 150


def _substantive(rec: dict) -> bool:
    return (len(rec.get("notes", "").encode("utf-8")) >= _SUBSTANTIVE_MIN_NOTES
            or len(rec.get("cultures") or {}) >= 3)


def _has_atu(rec: dict) -> bool:
    """Linked to an ATU tale type — by inline `Type` ref or the seq cross-walk."""
    return bool(rec.get("atu_inline")) or rec["id"] in store.load_crosswalk().get("tmi_to_atu", {})


def _link(index: str, motif_id: str) -> dict:
    """A cross-walk link: id + resolved name + whether the target exists here."""
    rec = _by_id(index).get(motif_id)
    counts = _descendant_counts(motif_id) if index == "tmi" else {t: 0 for t in _TIERS}
    n = counts["all"]
    return {
        "index": index,
        "id": motif_id,
        "name": rec.get("name", "") if rec else "",
        "exists": rec is not None,
        "level": rec.get("level", 0) if rec else 0,  # for the TMI lineage tree badges
        "leaf": index == "tmi" and n == 0,
        "descendant_count": n,
        "descendant_counts": counts,  # per-tier, for the filter-aware badge
        "notes_size": _notes_size(rec.get("notes", "")) if rec and index == "tmi" else "",
        "has_definition": bool(rec.get("definition")) if rec and index == "tmi" else False,
        "substantive": _substantive(rec) if rec and index == "tmi" else True,
        "has_atu": _has_atu(rec) if rec and index == "tmi" else False,
        **(_subtree_flags(motif_id) if rec and index == "tmi" else {}),
    }


def _chapter_label(data: dict, chapter: str) -> str:
    title = (data.get("chapters") or {}).get(chapter, "")
    if title.isupper():  # all-caps source titles (Berezkin) -> sentence case
        title = title[0] + title[1:].lower()
        title = _ROMAN_RE.sub(lambda m: m.group().upper(), title)  # keep Roman numerals
    return f"{chapter} — {title}" if title else chapter


def list_indexes() -> list[dict]:
    """Summaries for every built index: label, count, and chapters with counts."""
    out = []
    for index in INDEX_ORDER:
        data = store.load_index(index)
        if not data:
            continue
        records = data.get(_RECORDS_KEY.get(index, "motifs"), [])
        is_tmi = index == "tmi"
        # Per chapter: [count, substantive, definitions, atu] — the tiers also let
        # the catalog-root chapter rows honour the motif filter.
        chstats: dict[str, list[int]] = {}
        for r in records:
            st = chstats.setdefault(r.get("chapter", ""), [0, 0, 0, 0])
            st[0] += 1
            if is_tmi:
                st[1] += _substantive(r)
                st[2] += bool(r.get("definition"))
                st[3] += _has_atu(r)
        chapters = []
        for ch in sorted(chstats):
            if not ch:
                continue
            st = chstats[ch]
            entry = {"id": ch, "label": _chapter_label(data, ch), "count": st[0]}
            if is_tmi:
                entry["substantive"], entry["definitions"], entry["atu"] = st[1], st[2], st[3]
            chapters.append(entry)
        summary = {
            "index": index,
            # Tab label is presentation: take the canonical short name so it can
            # change without rebuilding the stored data.
            "label": INDEX_LABELS.get(index) or data.get("label") or index,
            "long_label": data.get("long_label", ""),
            "attribution": data.get("attribution", ""),
            "homepage": data.get("homepage", ""),
            "count": len(records),
            "chapters": chapters,
        }
        if is_tmi:  # index-wide tier counts for the motif-filter dropdown
            summary["substantive_count"] = sum(st[1] for st in chstats.values())
            summary["definition_count"] = sum(st[2] for st in chstats.values())
            summary["atu_count"] = sum(st[3] for st in chstats.values())
        out.append(summary)
    return out


def culture_legend(index: str) -> dict:
    """The culture dictionary for an index (only TMI has one), or {}."""
    return (store.load_index(index) or {}).get("culture_legend", {})


# --- index overview statistics ------------------------------------------------

# Notes-size histogram buckets (bytes): [lo, hi, label].
_NOTES_BUCKETS = [
    (1, 50, "1–49"), (50, 100, "50–99"), (100, 200, "100–199"),
    (200, 400, "200–399"), (400, 800, "400–799"), (800, 10 ** 9, "800+"),
]


def _breadth_label(n: int) -> str:
    return ("0", "1", "2", "3–5", "6–10", "11+")[
        0 if n == 0 else 1 if n == 1 else 2 if n == 2 else 3 if n <= 5 else 4 if n <= 10 else 5]


def _citation_key(text: str) -> str:
    """The bibliography key a citation resolves to, or '' (for the source tally)."""
    m = _CITE_HEAD.match(text)
    if not m:
        return ""
    index = _bibliography_index()
    parts = m.group(1).split()
    for i in range(len(parts), 0, -1):
        key = " ".join(parts[:i])
        if key in index:
            return key
    return ""


def _top_sources(records: list[dict], limit: int = 15) -> list[dict]:
    """Most-cited bibliography sources by number of motifs citing them."""
    import collections

    bib = _bibliography_index()
    motifs_per_source: collections.Counter = collections.Counter()
    for r in records:
        keys = set()
        for ref in r.get("references", []):
            keys.add(_citation_key(ref))
        for cites in (r.get("cultures") or {}).values():
            for c in cites:
                keys.add(_citation_key(c))
        for k in keys:
            if k and k not in ("Type", "Types"):  # the ATU marker isn't a source
                motifs_per_source[k] += 1

    out = []
    for key, n in motifs_per_source.most_common(limit):
        cands = bib.get(key) or []
        out.append({
            "label": key, "count": n,
            "title": cands[0]["title"] if cands else key,
            "url": next((c["url"] for c in cands if c["url"]), ""),
        })
    return out


_STATS_BUILDERS = {}  # filled below once the builders are defined


def stats(index: str) -> dict:
    """Aggregate statistics for an index overview dashboard."""
    if index in _STATS_BUILDERS:
        return store.cached(f"{index}:stats", _STATS_BUILDERS[index])
    return {"index": index, "totals": {"count": len(_records(index))}}


def _areal_breadth_label(n: int) -> str:
    return ("0", "1–2", "3–5", "6–10", "11–20", "21+")[
        0 if n == 0 else 1 if n <= 2 else 2 if n <= 5 else 3 if n <= 10 else 4 if n <= 20 else 5]


def _clean_tmi_ref(ref: str) -> str:
    """Normalise a mapsofmyths Thompson id (``*A2211.1``, ``A1313.3.1.``) to our tmi id."""
    return ref.lstrip("*").rstrip(".").strip()


def _berezkin_tradition_distribution(areal_ids: list[str], catalogue: dict) -> dict:
    """Summarise a motif's attesting traditions (mapsofmyths) by macro-region.

    Returns the total tradition count and a per-top-region breakdown, each with the
    named traditions — the fine, tradition-level distribution behind the maps.
    """
    import collections

    regions: dict[str, dict] = collections.OrderedDict()
    for aid in areal_ids:
        trad = catalogue.get(aid)
        if not trad:
            continue
        path = trad.get("areal_path") or []
        region = path[0][1] if path else "—"
        bucket = regions.setdefault(region, {"region": region, "count": 0, "traditions": []})
        bucket["count"] += 1
        bucket["traditions"].append(trad.get("name", aid))
    ordered = sorted(regions.values(), key=lambda r: r["count"], reverse=True)
    return {"total": len(areal_ids), "regions": ordered}


def _berezkin_region(code: int) -> str:
    """Group a Berezkin area code (10–74) into a broad region (see docs §6)."""
    if 10 <= code <= 14:
        return "Africa"
    if code in (15, 16, 27, 28, 31):
        return "Europe"
    if code in (17, 29, 30):
        return "Near East"
    if code in (32, 33):
        return "Central Asia"
    if 18 <= code <= 20:
        return "Oceania"
    if 21 <= code <= 26:
        return "Asia"
    if 34 <= code <= 39:
        return "Siberia"
    if code in (40, 41):
        return "Arctic"
    if 42 <= code <= 51:
        return "North America"
    if 52 <= code <= 54:
        return "Mesoamerica & Caribbean"
    if 55 <= code <= 74:
        return "South America"
    return ""


def _motif_count_label(n: int) -> str:
    return ("0", "1", "2–3", "4–6", "7–10", "11+")[
        0 if n == 0 else 1 if n == 1 else 2 if n <= 3 else 3 if n <= 6 else 4 if n <= 10 else 5]


def _build_berezkin_stats() -> dict:
    import collections

    records = _records("berezkin")
    data = store.load_index("berezkin") or {}
    legend = data.get("areas") or {}
    chapters = collections.Counter()
    areas = collections.Counter()
    breadth = collections.Counter()
    regions = collections.Counter()
    n_def = n_atu = n_see = 0
    for r in records:
        chapters[r.get("chapter", "")] += 1
        n_def += bool(r.get("definition"))
        n_atu += bool(r.get("atu_refs"))
        n_see += bool(r.get("see_also"))
        ars = r.get("areas") or []
        breadth[_areal_breadth_label(len(ars))] += 1
        regs = set()
        for a in ars:
            areas[a] += 1
            if (reg := _berezkin_region(a)):
                regs.add(reg)
        for reg in regs:
            regions[reg] += 1
    # Each areal code decodes to a distinct macro-area in the published key, so
    # we label the top codes directly (no de-duplication of names needed).
    top_codes = sorted(areas.items(), key=lambda kv: kv[1], reverse=True)[:20]
    widest = sorted(records, key=lambda r: len(r.get("areas", [])), reverse=True)[:15]
    return {
        "index": "berezkin",
        "title": "Berezkin & Duvakin areal motif catalogue — overview",
        "cards": [
            {"value": len(records), "label": "motifs"},
            {"value": len([c for c in chapters if c]), "label": "chapters"},
            {"value": n_def, "label": "with definition"},
            {"value": n_atu, "label": "ATU-linked"},
            {"value": len(legend), "label": "decoded areas"},
        ],
        "panels": [
            {"id": "bzChapters", "title": "Motifs per chapter"},
            {"id": "bzBreadth", "title": "Areal breadth (areas per motif)"},
            {"id": "bzRegions", "title": "Motifs by region"},
            {"id": "bzAreas", "title": "Top areas (most attested)"},
            {"id": "bzWidest", "title": "Most widespread motifs (areas attested)"},
        ],
        "chapters": [{"id": ch, "count": c} for ch, c in sorted(chapters.items()) if ch],
        "regions": [{"region": reg, "count": c} for reg, c in regions.most_common()],
        "top_areas": [{"label": legend.get(str(code), f"#{code}"), "count": c} for code, c in top_codes],
        "widest": [{"label": f"{r['id']} {r.get('name', '')}", "count": len(r.get("areas", []))}
                   for r in widest],
        "breadth": [{"bucket": b, "count": breadth[b]} for b in ("0", "1–2", "3–5", "6–10", "11–20", "21+")],
    }


def _build_atu_stats() -> dict:
    import collections

    types = _records("atu")
    data = store.load_index("atu") or {}
    chapters = collections.Counter()
    divisions = collections.Counter()
    motif_hist = collections.Counter()
    n_sum = n_mot = n_combo = 0
    for t in types:
        chapters[t.get("chapter", "")] += 1
        if t.get("division"):
            divisions[t["division"]] += 1
        n_sum += bool(t.get("summary"))
        n_mot += bool(t.get("motifs"))
        n_combo += bool(t.get("combos"))
        motif_hist[_motif_count_label(len(t.get("motifs", [])))] += 1
    top_rich = sorted(types, key=lambda t: len(t.get("motifs", [])), reverse=True)[:15]
    return {
        "index": "atu",
        "title": (data.get("long_label") or "ATU tale types") + " — overview",
        "cards": [
            {"value": len(types), "label": "tale types"},
            {"value": len([c for c in chapters if c]), "label": "chapters"},
            {"value": n_mot, "label": "with TMI motifs"},
            {"value": n_combo, "label": "with combos"},
            {"value": round(100 * n_sum / len(types)) if types else 0, "label": "have summary", "suffix": "%"},
        ],
        "panels": [
            {"id": "atChapters", "title": "Types per chapter"},
            {"id": "atDivisions", "title": "Top divisions"},
            {"id": "atMotifHist", "title": "TMI motifs per type"},
            {"id": "atRich", "title": "Most motif-rich types"},
        ],
        "chapters": [{"label": ch, "count": c} for ch, c in chapters.most_common() if ch],
        "divisions": [{"label": dv, "count": c} for dv, c in divisions.most_common(15)],
        "motif_hist": [{"bucket": b, "count": motif_hist[b]} for b in ("0", "1", "2–3", "4–6", "7–10", "11+")],
        "top_rich": [{"label": f"{t['id']} {t.get('name', '')}", "count": len(t.get("motifs", []))}
                     for t in top_rich],
    }


def _build_tmi_stats() -> dict:
    import collections

    records = _records("tmi")
    data = store.load_index("tmi") or {}
    region_of = {canon: (e.get("region") or "") for canon, e in (data.get("culture_legend") or {}).items()}
    have_kids = {r["parent"] for r in records if r.get("parent")}

    levels = collections.Counter()
    notes_hist = collections.Counter()
    breadth = collections.Counter()
    chapters: dict[str, list[int]] = {}
    regions = collections.Counter()
    cultures = collections.Counter()
    indeg = collections.Counter()
    comp = collections.Counter()
    n_def = n_notes = n_atu = n_sub = 0

    for r in records:
        nb = len(r.get("notes", "").encode("utf-8"))
        sub = _substantive(r)
        levels[r.get("level", 0)] += 1
        n_notes += bool(r.get("notes", "").strip())
        n_def += bool(r.get("definition"))
        n_atu += _has_atu(r)
        n_sub += sub
        comp["substantive" if sub else "scaffold" if r["id"] in have_kids else "variation"] += 1
        for lo, hi, label in _NOTES_BUCKETS:
            if lo <= nb < hi:
                notes_hist[label] += 1
                break
        cults = r.get("cultures") or {}
        breadth[_breadth_label(len(cults))] += 1
        seen_regions = set()
        for raw in cults:
            canon = canonical(raw)[0]
            cultures[canon] += 1
            if region_of.get(canon):
                seen_regions.add(region_of[canon])
        for reg in seen_regions:
            regions[reg] += 1
        if (ch := r.get("chapter", "")):
            row = chapters.setdefault(ch, [0, 0])
            row[0] += 1
            row[1] += sub
        sa = r.get("see_also") or {}
        for t in sa.get("ref", []) + sa.get("cf", []):
            indeg[t] += 1

    by = _by_id("tmi")
    top_notes = sorted(records, key=lambda r: len(r.get("notes", "").encode("utf-8")), reverse=True)[:15]
    hubs = [(mid, c) for mid, c in indeg.most_common(50) if mid in by][:15]
    chapter_labels = data.get("chapters") or {}

    return {
        "index": "tmi",
        "title": "Thompson Motif-Index of Folk-Literature — overview",
        "totals": {
            "count": len(records), "chapters": len(chapters), "with_notes": n_notes,
            "definitions": n_def, "substantive": n_sub, "atu": n_atu,
        },
        "cards": [
            {"value": len(records), "label": "motifs"},
            {"value": len(chapters), "label": "chapters"},
            {"value": n_sub, "label": "substantive"},
            {"value": n_def, "label": "with definition"},
            {"value": n_atu, "label": "ATU-linked"},
            {"value": round(100 * n_notes / len(records)) if records else 0, "label": "have notes", "suffix": "%"},
        ],
        "panels": [
            {"id": "ovComposition", "title": "Composition"},
            {"id": "ovLevels", "title": "Nodes per hierarchy level"},
            {"id": "ovNotes", "title": "Notes size (bytes)"},
            {"id": "ovChapters", "title": "Motifs per chapter (all vs substantive)"},
            {"id": "ovRegions", "title": "Motifs by region"},
            {"id": "ovCultures", "title": "Top cultures"},
            {"id": "ovTopNotes", "title": "Most-documented motifs"},
            {"id": "ovHubs", "title": "Most-referenced motifs (cf./†)"},
            {"id": "ovBreadth", "title": "Cultural breadth (cultures per motif)"},
            {"id": "ovSources", "title": "Top sources (motifs citing)"},
        ],
        "composition": [{"label": k, "count": comp[k]} for k in ("substantive", "scaffold", "variation")],
        "levels": [{"level": f"L{lv}", "count": levels[lv]} for lv in sorted(levels)],
        "notes_histogram": [{"bucket": label, "count": notes_hist[label]} for _, _, label in _NOTES_BUCKETS],
        "breadth_histogram": [{"bucket": b, "count": breadth[b]}
                              for b in ("0", "1", "2", "3–5", "6–10", "11+")],
        "chapters": [{"id": ch, "label": chapter_labels.get(ch, ch), "count": c, "substantive": s}
                     for ch, (c, s) in sorted(chapters.items())],
        "regions": [{"region": reg, "count": n} for reg, n in regions.most_common()],
        "top_cultures": [{"label": lbl, "count": n} for lbl, n in cultures.most_common(30)],
        "top_notes": [{"id": r["id"], "name": r.get("name", ""),
                       "bytes": len(r.get("notes", "").encode("utf-8"))} for r in top_notes],
        "see_also_hubs": [{"id": mid, "name": by[mid].get("name", ""), "indeg": c} for mid, c in hubs],
        "top_sources": _top_sources(records),
    }


_STATS_BUILDERS.update({
    "tmi": _build_tmi_stats, "berezkin": _build_berezkin_stats, "atu": _build_atu_stats,
})


def _bibliography_index() -> dict[str, list[dict]]:
    """Citation key -> [{title, url}] from the packaged TMI bibliography key.

    A key (author surname or abbreviation) can map to several works; the list
    preserves them so a multi-work author is disambiguated by the short title.
    """
    def build() -> dict[str, list[dict]]:
        try:
            raw = _pkg_files("motifs").joinpath("data/tmi_bibliography.json").read_text("utf-8")
        except (FileNotFoundError, ModuleNotFoundError, OSError):
            return {}
        index: dict[str, list[dict]] = {}
        for e in json.loads(raw).get("entries", []):
            url = e["urls"][0]["url"] if e.get("urls") else ""
            rec = {"title": e.get("citation", ""), "url": url}
            for key in e.get("keys", []):
                index.setdefault(key, []).append(rec)
        return index
    return store.cached("tmi:bib", build)


# The leading author/abbreviation of a citation (skipping Thompson's '*' marks).
_CITE_HEAD = re.compile(r"^[*☉\s]*([A-Z][A-Za-z.'\-]+(?:[ -][A-Z][A-Za-z.'\-]+){0,2})")


def _resolve_citation(text: str) -> dict:
    """A citation string + a book link/title when its head matches a known work."""
    out = {"text": text}
    m = _CITE_HEAD.match(text)
    if not m:
        return out
    index = _bibliography_index()
    parts = m.group(1).split()
    for i in range(len(parts), 0, -1):
        cands = index.get(" ".join(parts[:i]))
        if not cands:
            continue
        tail = parts[i:]  # short-title tokens after the matched key
        titled = [c for c in cands if c["url"] and any(t.lower() in c["title"].lower() for t in tail)]
        linked = [c for c in cands if c["url"]]
        rec = (titled or linked or cands)[0]  # prefer title-matched, then any linked
        if rec["url"]:
            out["url"], out["title"] = rec["url"], rec["title"]
        break
    return out


def _list_item(index: str, rec: dict) -> dict:
    """A compact record for the scrolling list (index-specific badge included)."""
    item = {"index": index, "id": rec["id"], "name": rec.get("name", ""), "chapter": rec.get("chapter", "")}
    if index == "berezkin":
        item["badge"] = f"{len(rec.get('areas', []))} areas"
    elif index == "atu":
        item["badge"] = f"{len(rec.get('motifs', []))} motifs"
    elif index == "tmi":
        counts = _descendant_counts(rec["id"])
        n = counts["all"]
        size = _notes_size(rec.get("notes", ""))
        item["badge"] = (f"{size} · " if size else "") + (f"{n} · " if n else "") + f"L{rec.get('level', 0)}"
        item["level"] = rec.get("level", 0)  # for the indented tree in the sidebar
        item["descendant_count"] = n
        item["descendant_counts"] = counts  # per-tier, for the filter-aware tree badge
        item["notes_size"] = size  # for the tree-row badge in the chapter browse view
        item["has_definition"] = bool(rec.get("definition"))
        item["substantive"] = _substantive(rec)
        item["has_atu"] = _has_atu(rec)
        item.update(_subtree_flags(rec["id"]))  # for the drill-down tree filter
        item["leaf"] = n == 0
        item["duplicate"] = bool(rec.get("duplicate"))
    return item


_TIER_PREDICATE = {
    "def": lambda r: bool(r.get("definition")),
    "sub": _substantive,
    "atu": _has_atu,
}


def _tier_relevant(tier: str) -> set[str]:
    """TMI ids whose subtree (self or any descendant) holds a tier-matching motif.

    Lets the tree filter keep a category visible when its content sits deeper,
    so only one child level is shown but deeper matches still count.
    """
    def build() -> set[str]:
        pred = _TIER_PREDICATE[tier]
        by = _by_id("tmi")
        relevant: set[str] = set()
        for r in _records("tmi"):
            if pred(r):
                cur = r["id"]
                while cur and cur in by and cur not in relevant:  # mark self + ancestors
                    relevant.add(cur)
                    cur = by[cur].get("parent", "")
        return relevant
    return store.cached(f"tmi:relevant:{tier}", build)


def _subtree_flags(motif_id: str) -> dict:
    """Per-tier `<tier>_subtree` flags used by the tree filter (drill-down)."""
    return {f"{t}_subtree": motif_id in _tier_relevant(t) for t in ("def", "sub", "atu")}


def list_motifs(index: str, *, chapter: str = "", q: str = "", level: int | None = None,
                tier: str = "", limit: int = 200, offset: int = 0) -> dict:
    """Filtered, paginated motif list for one index."""
    records = _records(index)
    query = q.strip().lower()
    if chapter:
        records = [r for r in records if r.get("chapter", "") == chapter]
    if level is not None:
        records = [r for r in records if r.get("level", 0) == level]
    if index == "tmi" and tier in _TIER_PREDICATE:  # substantive / definitions / ATU
        records = [r for r in records if _TIER_PREDICATE[tier](r)]
    if query:
        records = [
            r for r in records
            if query in r.get("id", "").lower() or query in r.get("name", "").lower()
        ]
    total = len(records)
    page = records[offset: offset + limit]
    return {"index": index, "total": total, "items": [_list_item(index, r) for r in page]}


def get_motif(index: str, motif_id: str) -> dict | None:
    """Full detail for one motif with resolved cross-walk links, or None."""
    rec = _by_id(index).get(motif_id)
    if rec is None:
        return None

    cw = store.load_crosswalk()
    data = store.load_index(index) or {}
    detail: dict = {
        "index": index,
        "id": rec["id"],
        "name": rec.get("name", ""),
        "chapter": rec.get("chapter", ""),
        "chapter_label": _chapter_label(data, rec.get("chapter", "")),
        "links": {},
    }

    if index == "berezkin":
        detail["definition"] = rec.get("definition", "")
        # Name/definition are English-preferred (mapsofmyths); the Russian originals
        # ride along as sub-titles on the motif page.
        detail["name_rus"] = rec.get("name_rus", "")
        detail["definition_rus"] = rec.get("definition_rus", "")
        # Link back to the source catalog page the motif was scraped from.
        page, home = rec.get("page", ""), data.get("homepage", "")
        if page and home:
            detail["source_url"] = f"{home.rstrip('/')}/{page}"
        # Areal indices decoded to macro-area names (legend voted from detail-page
        # headers); name is "" for the few indices not covered by the legend.
        legend = data.get("areas") or {}
        detail["areas"] = [{"id": a, "name": legend.get(str(a), "")} for a in rec.get("areas", [])]
        detail["links"]["see_also"] = [_link("berezkin", c) for c in rec.get("see_also", [])]
        detail["links"]["atu"] = [_link("atu", a) for a in rec.get("atu_refs", [])]
        # mapsofmyths enrichment: thematic taxonomy, direct Thompson (TMI) links, and
        # the tradition-level distribution grouped by macro-region.
        detail["motif_type"] = rec.get("motif_type", "")
        detail["motif_group"] = rec.get("motif_group", "")
        detail["links"]["tmi"] = [_link("tmi", _clean_tmi_ref(t)) for t in rec.get("tmi_refs", [])]
        detail["traditions"] = _berezkin_tradition_distribution(rec.get("traditions", []), data.get("traditions") or {})

    elif index == "tmi":
        detail["chapter_name"] = rec.get("chapter_name", "")
        detail["notes"] = rec.get("notes", "")
        detail["notes_size"] = _notes_size(rec.get("notes", ""))  # for the tree badge
        detail["definition"] = rec.get("definition", "")
        detail["has_definition"] = bool(rec.get("definition"))
        detail["substantive"] = _substantive(rec)
        detail["has_atu"] = _has_atu(rec)
        # Cultures with their region, and each citation linked to its source book.
        raw_cultures = rec.get("cultures") or {}
        legend = culture_legend("tmi")
        detail["cultures"] = [
            {"label": label, "region": (legend.get(canonical(label)[0]) or {}).get("region", ""),
             "citations": [_resolve_citation(c) for c in cites]}
            for label, cites in raw_cultures.items()
        ]
        # General references = bibliography segments not headed by a culture label.
        general = [r for r in rec.get("references", [])
                   if not any(r.startswith(label + ":") for label in raw_cultures)]
        detail["references"] = [_resolve_citation(r) for r in general]
        detail["level"] = rec.get("level", 0)
        detail["code"] = rec.get("code", rec["id"])
        detail["duplicate"] = bool(rec.get("duplicate"))
        detail["breadcrumbs"] = _tmi_ancestors(rec)  # broadest first
        detail["children"], detail["children_truncated"] = _tmi_direct_children(rec["id"])
        detail["descendant_counts"] = _descendant_counts(rec["id"])
        detail["descendant_count"] = detail["descendant_counts"]["all"]
        # Cross-references parsed from the note text: '†' to other motifs (split
        # into direct refs and softer 'Cf.' compares) and inline 'Type' to ATU.
        see_also = rec.get("see_also") or {}
        detail["links"]["see_also"] = [_link("tmi", m) for m in see_also.get("ref", [])]
        detail["links"]["see_also_cf"] = [_link("tmi", m) for m in see_also.get("cf", [])]
        detail["links"]["atu_inline"] = [_link("atu", a) for a in rec.get("atu_inline", [])]
        atu_ids = cw.get("tmi_to_atu", {}).get(rec["id"], [])
        detail["links"]["atu"] = [_link("atu", a) for a in atu_ids]

    elif index == "atu":
        detail["division"] = rec.get("division", "")
        detail["summary"] = rec.get("summary", "")
        detail["links"]["tmi"] = [_link("tmi", m) for m in rec.get("motifs", [])]
        detail["links"]["combos"] = [_link("atu", c) for c in rec.get("combos", [])]
        bz = cw.get("atu_to_berezkin", {}).get(rec["id"], [])
        detail["links"]["berezkin"] = [_link("berezkin", b) for b in bz]

    return detail
