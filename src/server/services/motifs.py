"""Read-side service for the motif database.

Serves the browsable Motifs catalog: index summaries, paginated/filtered motif
lists, and per-motif detail with resolved cross-walk links. All data is read
from ``outputs/motifs/`` (built by ``mytho motifs``) and cached per process.
"""

from __future__ import annotations

import html
import json
import re

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


def _tmi_dup_code_index() -> dict[str, list[str]]:
    """Cached ``source code -> [ids]`` for the TMI motifs Thompson's index gives a
    duplicate number (so a suffixed id can point at its sibling(s))."""
    def build() -> dict[str, list[str]]:
        m: dict[str, list[str]] = {}
        for r in _records("tmi"):
            if r.get("duplicate"):
                m.setdefault(r.get("code", r["id"]), []).append(r["id"])
        return m
    return store.cached("dupcode:tmi", build)


def _tmi_dup_siblings(rec: dict) -> list[dict]:
    """Links to the other TMI motifs that share this one's duplicated code."""
    if not rec.get("duplicate"):
        return []
    code = rec.get("code", rec["id"])
    return [_link("tmi", i) for i in _tmi_dup_code_index().get(code, []) if i != rec["id"]]


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


def _mark_missing(link: dict, reason: str) -> dict:
    """Tag a link that failed to resolve with why, for a clearer tooltip."""
    if not link["exists"]:
        link["missing_reason"] = reason
    return link


def _aath_to_atu() -> dict[str, list[str]]:
    """Aarne-Thompson (AaTh) tale-type number -> ATU 2004 id(s), inverted from the
    Wikidata concordance carried on each ATU type. Uther renumbered many AaTh types
    (and split some across several ATU types), so this is one-to-many in places."""
    def build() -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for t in _records("atu"):
            for code in (t.get("concordances") or {}).get("AaTh", []):
                out.setdefault(code, [])
                if t["id"] not in out[code]:
                    out[code].append(t["id"])
        return {k: sorted(v) for k, v in out.items()}
    return store.cached("aath_to_atu", build)


_ATU_NUM_RE = re.compile(r"^(\d+)")


def _atu_num_key(atu_id: str) -> tuple:
    """(number, suffix) so 301 < 301A < 301D* < 1542 sort numerically."""
    m = _ATU_NUM_RE.match(atu_id)
    return (int(m.group(1)) if m else 1 << 30, atu_id[m.end():] if m else atu_id)


def _merge_atu_relations(appears: list[str], referenced: list[dict]) -> list[dict]:
    """Merge the two motif↔ATU relations into one deduplicated list, each link
    tagged ``rel``: ``appears`` (⇐ constituent, from atu_seq), ``cited`` (⇒ named
    in the note) or ``both`` (⇔). Ordered: ⇔ first (corroborated by two
    independent sources), then ascending by tale-type number."""
    chips: dict[str, dict] = {}
    for aid in appears:  # ⇐ constituent
        if aid not in chips:
            link = _link("atu", aid)
            link["rel"] = "appears"
            chips[aid] = link
    for rl in referenced:  # ⇒ cited (resolved real ATU, or orphan AaTh)
        key = rl["id"]
        if rl.get("exists") and key in chips:
            chips[key]["rel"] = "both"
            if rl.get("aath") and not chips[key].get("aath"):
                chips[key]["aath"] = rl["aath"]
        elif key not in chips:
            link = dict(rl)
            link["rel"] = "cited"
            chips[key] = link
    return sorted(chips.values(),
                  key=lambda c: (0 if c["rel"] == "both" else 1, _atu_num_key(c["id"])))


def _merge_tmi_related(cf: list[str], ref: list[str]) -> list[dict]:
    """One '†' cross-reference list: 'Cf.' compares (the majority, unmarked)
    followed by the bare '†X' redirects not already among them, each flagged
    ``see_also`` so the frontend can tag that minority."""
    out = [_link("tmi", m) for m in cf]
    seen = {m for m in cf}
    for m in ref:
        if m in seen:
            continue
        seen.add(m)
        link = _link("tmi", m)
        link["see_also"] = True
        out.append(link)
    return out


def _resolve_atu_inline(refs: list[str]) -> list[dict]:
    """Resolve the inline 'Type N' refs a TMI note cites. The note predates ATU
    2004, so these are AaTh numbers: link straight through if the number still
    exists in ATU, else remap via the AaTh->ATU concordance (tagging the original
    number), else keep it as a missing link flagged as an orphaned AaTh number."""
    atu_index = _by_id("atu")
    conc = _aath_to_atu()
    out: list[dict] = []
    seen: set[tuple] = set()
    for a in refs:
        if a in atu_index:
            out.append(_link("atu", a))
        elif a in conc:
            for atu_id in conc[a]:
                if (atu_id, a) in seen:
                    continue
                seen.add((atu_id, a))
                link = _link("atu", atu_id)
                link["aath"] = a  # the AaTh number the note actually cited
                out.append(link)
        else:
            link = _link("atu", a)
            link["missing_reason"] = "aath"  # AaTh number, no ATU 2004 equivalent
            out.append(link)
    return out


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
        if data.get("divisions"):  # chapter → division → sub_division browse (ATU; TMI via Mellmann)
            summary["divisions"] = data.get("divisions", [])
            summary["subdivisions"] = data.get("subdivisions", [])
            if data.get("subdivisions3"):  # TMI carries a third heading level (division3)
                summary["subdivisions3"] = data.get("subdivisions3", [])
            if data.get("sections"):       # …and the finest section (tens) level
                summary["sections"] = data.get("sections", [])
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


# Leading author/abbreviation of one ';'-separated ATU citation ("Krohn 1889, 46"
# -> "Krohn"; "BP II, 116" -> "BP II"), before the first comma/digit.
_ATU_SRC_HEAD = re.compile(r"^(?:cf\.?\s+)?([^,\d]+)", re.I)


def _atu_top_sources(types: list[dict], limit: int = 15) -> list[dict]:
    """Most-cited apparatus works in Uther's key-literature (`references`), by number
    of tale types citing each. Heuristic: the leading author/abbreviation of every
    ';'-separated citation, minus a trailing volume numeral or `ff.`"""
    import collections

    counts: collections.Counter = collections.Counter()
    for t in types:
        seen = set()
        for seg in (t.get("references") or "").split(";"):
            m = _ATU_SRC_HEAD.match(seg.strip())
            if not m:
                continue
            key = re.sub(r"\s+(?:ff\.?|[IVXLC]+\.?)$", "", m.group(1).strip()).strip()
            if len(key) >= 2:
                seen.add(key)
        for k in seen:
            counts[k] += 1
    return [{"label": k, "count": n} for k, n in counts.most_common(limit)]


def _berezkin_top_sources(limit: int = 15) -> list[dict]:
    """Most-cited works in the Berezkin bibliography (areasofmyths), by citation
    count (`uses`). Empty when the bibliography file is absent."""
    srcs = (_berezkin_bibliography() or {}).get("sources") or {}
    top = sorted(srcs.items(), key=lambda kv: kv[1].get("uses", 0), reverse=True)[:limit]
    return [{"label": key, "count": s.get("uses", 0)} for key, s in top]


_STATS_BUILDERS = {}  # filled below once the builders are defined

# Short scholarly header shown at the top of each index overview: one-paragraph
# description, authorship, the academic citation for the source work, and the
# concrete data sources used here (with links). Kept server-side so the three
# overviews stay consistent.
# Overview charts split into two colour-coded sections: what the index says about
# the folklore (distributions, cultural/geographic spread, correlations) vs. the
# shape and completeness of the dataset itself. Panels within each carry an
# explicit `section`; the frontend groups and tints by it.
_OVERVIEW_SECTIONS = [
    {"key": "content", "title": "Distribution & content"},
    {"key": "diagnostics", "title": "Dataset diagnostics"},
]

_INTRO = {
    "tmi": {
        "blurb": "The Thompson Motif-Index breaks world folk narrative into ~46,000 numbered "
                 "<em>motifs</em> — the smallest reusable story elements (an act, a character, an "
                 "object) — in a place-value hierarchy under 23 lettered chapters. It is the "
                 "reference grid the other two indexes point back to.",
        "author": "Stith Thompson (1885–1976)",
        "citation": "Thompson, Stith. <em>Motif-Index of Folk-Literature</em>. 6 vols. "
                    "Bloomington: Indiana University Press, 1955–58.",
        "sources": [
            {"label": "Trilogy dataset (j-hagedorn/trilogy, CC-BY-SA)", "url": "https://github.com/j-hagedorn/trilogy"},
            {"label": "Mellmann TMI_as_CSV — classification headings, edition history & recovered motifs (CC-BY-4.0)", "url": "https://github.com/KatjaMellmann/TMI_as_CSV"},
            {"label": "folkmasa.org — citation-abbreviation decoding", "url": "https://folkmasa.org/motiv/motif.htm"},
        ],
    },
    "atu": {
        "blurb": "The Aarne-Thompson-Uther index catalogues ~2,250 <em>tale types</em> — recurrent "
                 "international plots such as 510A Cinderella — each with a summary, its constituent "
                 "TMI motifs, a key-literature apparatus, and attestations across the traditions that "
                 "have recorded it. Hans-Jörg Uther's 2004 revision of the older Aarne-Thompson system.",
        "author": "Hans-Jörg Uther, after Antti Aarne & Stith Thompson",
        "citation": "Uther, Hans-Jörg. <em>The Types of International Folktales</em>. 3 vols. "
                    "FF Communications 284–286. Helsinki: Academia Scientiarum Fennica, 2004.",
        "sources": [
            {"label": "Trilogy dataset (j-hagedorn/trilogy, CC-BY-SA)", "url": "https://github.com/j-hagedorn/trilogy"},
            {"label": "Wikidata — concordances, multilingual names, Wikisource full texts", "url": "https://www.wikidata.org"},
            {"label": "Ashliman's Folktexts (AFT) — example tales", "url": "https://sites.pitt.edu/~dash/folktexts.html"},
        ],
    },
    "berezkin": {
        "blurb": "The Berezkin & Duvakin catalogue classifies world mythological and folklore motifs "
                 "by their <em>areal distribution</em> — which of the world's traditions carry each "
                 "motif — rather than by narrative type. That design makes it the most geographically "
                 "even of the three indexes, reaching deep into Siberia and the Americas.",
        "author": "Ю. Е. Березкин & Е. Н. Дувакин (Yuri Berezkin & Evgeny Duvakin)",
        "citation": "Березкин, Ю. Е., Дувакин, Е. Н. <em>Тематическая классификация и распределение "
                    "фольклорно-мифологических мотивов по ареалам</em> (The Analytical Catalogue of "
                    "World Mythology and Folklore).",
        "sources": [
            {"label": "areasofmyths.com — the catalogue & bibliography (CC BY-NC-SA 4.0)", "url": "http://areasofmyths.com"},
            {"label": "mapsofmyths.com — English names, thematic groups & concordances (CC BY-NC-SA 4.0)", "url": "https://mapsofmyths.com/motifs"},
        ],
    },
}


def stats(index: str) -> dict:
    """Aggregate statistics for an index overview dashboard."""
    if index in _STATS_BUILDERS:
        return store.cached(f"{index}:stats", _STATS_BUILDERS[index])
    return {"index": index, "totals": {"count": len(_records(index))}}


def _areal_breadth_label(n: int) -> str:
    return ("0", "1–2", "3–5", "6–10", "11–20", "21+")[
        0 if n == 0 else 1 if n <= 2 else 2 if n <= 5 else 3 if n <= 10 else 4 if n <= 20 else 5]


def _breadth_label(n: int) -> str:
    return ("0", "1", "2", "3–5", "6–10", "11+")[
        0 if n == 0 else 1 if n == 1 else 2 if n == 2 else 3 if n <= 5 else 4 if n <= 10 else 5]


_AREA_SPAN_BUCKETS = ("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
                      "13–15", "16–20", "21–30", "31–45", "46+")


def _area_span_label(n: int) -> str:
    if n <= 12:
        return _AREA_SPAN_BUCKETS[n]
    return _AREA_SPAN_BUCKETS[13 if n <= 15 else 14 if n <= 20 else 15 if n <= 30 else 16 if n <= 45 else 17]


_TRAD_SPAN_BUCKETS = ("1–2", "3–5", "6–10", "11–20", "21–35", "36–50",
                      "51–75", "76–100", "101–150", "151–250", "250+")


def _trad_span_label(n: int) -> str:
    return _TRAD_SPAN_BUCKETS[
        0 if n <= 2 else 1 if n <= 5 else 2 if n <= 10 else 3 if n <= 20 else 4 if n <= 35
        else 5 if n <= 50 else 6 if n <= 75 else 7 if n <= 100 else 8 if n <= 150
        else 9 if n <= 250 else 10]


def _deflen_label(n: int) -> str:
    return ("0", "1–60", "61–120", "121–240", "241–480", "480+")[
        0 if n == 0 else 1 if n <= 60 else 2 if n <= 120 else 3 if n <= 240 else 4 if n <= 480 else 5]


# A dotted sub-segment the source rendered as a Roman/stick "I" is the digit 1.
_TMI_ROMAN_RE = re.compile(r"(?<=\.)(I+)(?=\.|$|\+)")


def _clean_tmi_ref(ref: str) -> str:
    """Normalise a mapsofmyths Thompson id (``*A2211.1``, ``A1313.3.1.``) to our tmi id.
    A dotted sub-segment written with a Roman/stick "I" is the digit 1, so its link
    resolves (``A700.I`` → ``A700.1``, ``A724.I.I.`` → ``A724.1.1.``)."""
    ref = _TMI_ROMAN_RE.sub(lambda m: "1" * len(m.group(1)), ref)
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
    groups = collections.Counter()
    indeg = collections.Counter()      # how often each motif is a see-also target
    trad_breadth = collections.Counter()
    trad_counts = collections.Counter()  # motifs attested in each tradition (people)
    deflen = collections.Counter()
    trad_ids: set = set()              # distinct attesting traditions (peoples), like ATU peoples
    n_def = n_atu = n_english = n_tmi = n_areas = n_see = n_trad = 0
    for r in records:
        chapters[r.get("chapter", "")] += 1
        n_def += bool(r.get("definition"))
        n_atu += bool(r.get("atu_refs"))
        n_english += bool(r.get("name_rus"))  # English name preferred (mapsofmyths)
        n_tmi += bool(r.get("tmi_refs"))       # direct Thompson crosswalk (mapsofmyths)
        n_see += bool(r.get("see_also"))
        deflen[_deflen_label(len(r.get("definition") or ""))] += 1
        if r.get("motif_group"):
            groups[r["motif_group"]] += 1
        for t in r.get("see_also") or []:
            indeg[t] += 1
        trads = r.get("traditions") or []
        if trads:
            n_trad += 1
            trad_ids.update(trads)
            trad_breadth[_trad_span_label(len(trads))] += 1
            for t in trads:
                trad_counts[t] += 1
        ars = r.get("areas") or []
        n_areas += bool(ars)
        breadth[_area_span_label(len(ars))] += 1
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
    # Tradition (people) leaderboards, parallel to the areal ones above.
    tname = {tid: (t.get("name") or t.get("name_eng") or tid)
             for tid, t in (data.get("traditions") or {}).items()}
    top_trads = trad_counts.most_common(20)
    trad_widest = sorted(records, key=lambda r: len(r.get("traditions") or []), reverse=True)[:15]
    by = _by_id("berezkin")
    hubs = [(mid, c) for mid, c in indeg.most_common(50) if mid in by][:15]

    # The mapsofmyths enrichment (English text, thematic groups, TMI links) is
    # credential-gated, so the cards/panels that surface it appear only when the
    # data is actually present — the overview stays valid without credentials.
    # Carrier count, parallel to ATU "peoples" / TMI "cultures": Berezkin's fine unit
    # is the attesting **tradition** (a people, e.g. Ainu/Aymara — enrichment-gated);
    # without it, fall back to the coarser areal-code count.
    carrier = ({"value": len(trad_ids), "label": "traditions"} if trad_ids
               else {"value": len(areas), "label": "areas"})
    cards = [
        {"value": len(records), "label": "motifs"},
        {"value": len([c for c in chapters if c]), "label": "chapters"},
        carrier,
        {"value": n_atu, "label": "ATU-linked"},
    ]
    if n_tmi:
        cards.append({"value": n_tmi, "label": "TMI-linked"})
    if n_english:
        cards.append({"value": round(100 * n_english / len(records)) if records else 0,
                      "label": "English name", "suffix": "%"})

    # Distribution & content — region and chapter first, then the areal trio, the
    # tradition (people) trio, and the see-also hub leaderboard.
    panels = [
        {"id": "bzRegions", "title": "Motifs by region", "section": "content"},
        {"id": "bzChapters", "title": "Motifs by chapter", "section": "content"},
    ]
    if groups:
        panels.append({"id": "bzGroups", "title": "Motifs by thematic group", "section": "content"})
    panels += [
        {"id": "bzAreas", "title": "Areas with the most motifs", "section": "content"},
        {"id": "bzBreadth", "title": "Areas per motif", "section": "content"},
        {"id": "bzWidest", "title": "Most widespread motifs (areas attesting)", "section": "content"},
    ]
    if n_trad:
        panels += [
            {"id": "bzTradTop", "title": "Traditions with the most motifs", "section": "content"},
            {"id": "bzTradBreadth", "title": "Traditions per motif", "section": "content"},
            {"id": "bzTradWidest", "title": "Most widespread motifs (traditions attesting)", "section": "content"},
        ]
    if hubs:
        panels.append({"id": "bzHubs", "title": "Most cross-referenced motifs (see-also)", "section": "content"})
    # Dataset diagnostics.
    top_sources = _berezkin_top_sources()
    panels += [
        {"id": "bzCoverage", "title": "Field coverage", "section": "diagnostics"},
        {"id": "bzDefLen", "title": "Motifs by definition length", "section": "diagnostics"},
    ]
    if top_sources:
        panels.append({"id": "bzSources", "title": "Most-cited sources", "section": "diagnostics"})
    coverage = [{"label": "definition", "count": n_def}]
    if n_english:
        coverage.append({"label": "English name", "count": n_english})
    coverage.append({"label": "areal indices", "count": n_areas})
    coverage.append({"label": "ATU-linked", "count": n_atu})
    if n_tmi:
        coverage.append({"label": "TMI-linked", "count": n_tmi})
    coverage.append({"label": "see-also", "count": n_see})

    stats = {
        "index": "berezkin",
        "intro": _INTRO["berezkin"],
        "title": "Berezkin & Duvakin Areal Motif Catalogue",
        "cards": cards,
        "sections": _OVERVIEW_SECTIONS,
        "panels": panels,
        "chapters": [{"id": ch, "chapter": ch, "label": _chapter_label(data, ch), "count": c}
                     for ch, c in sorted(chapters.items()) if ch],
        "regions": [{"region": reg, "count": c} for reg, c in regions.most_common()],
        "top_areas": [{"label": legend.get(str(code), f"#{code}"), "count": c} for code, c in top_codes],
        "widest": [{"id": r["id"], "label": f"{r['id']} {r.get('name', '')}", "count": len(r.get("areas", []))}
                   for r in widest],
        "hubs": [{"id": mid, "label": f"{mid} {by[mid].get('name', '')}", "count": c} for mid, c in hubs],
        "breadth": [{"bucket": b, "count": breadth[b]} for b in _AREA_SPAN_BUCKETS],
        "coverage": coverage,
        "deflen": [{"bucket": b, "count": deflen[b]} for b in ("0", "1–60", "61–120", "121–240", "241–480", "480+")],
        "top_sources": top_sources,
    }
    if n_trad:
        stats["trad_breadth"] = [{"bucket": b, "count": trad_breadth[b]} for b in _TRAD_SPAN_BUCKETS]
        stats["top_traditions"] = [{"label": tname.get(tid, tid), "count": c} for tid, c in top_trads]
        stats["trad_widest"] = [{"id": r["id"], "label": f"{r['id']} {r.get('name', '')}",
                                 "count": len(r.get("traditions") or [])} for r in trad_widest]
    if groups:
        # Group labels are long ("03 Cosmogony, the earth and the sky, ..."); keep
        # the leading number + first segment for a readable axis label.
        stats["groups"] = [{"label": g.split(",")[0].strip(), "count": c}
                           for g, c in groups.most_common()]
    return stats


def _build_atu_stats() -> dict:
    import collections

    types = _records("atu")
    data = store.load_index("atu") or {}
    legend = data.get("culture_legend") or {}
    chapters = collections.Counter()
    divisions = collections.Counter()
    motif_hist = collections.Counter()
    reg_breadth = collections.Counter()   # how many macro-regions a type spans
    region_types = collections.Counter()  # types present per region (each type once/region)
    n_sum = n_mot = n_combo = n_att = n_refs = 0
    for t in types:
        chapters[t.get("chapter", "")] += 1
        if t.get("division"):
            divisions[t["division"]] += 1
        n_sum += bool(t.get("summary"))
        n_mot += bool(t.get("motifs"))
        n_combo += bool(t.get("combos"))
        n_refs += bool(t.get("references"))
        motif_hist[_motif_count_label(len(t.get("motifs", [])))] += 1
        grouped = t.get("attestations_grouped") or {}
        named = [r for r in grouped.get("regions", []) if r["region"] != "—"]
        if grouped.get("total"):
            n_att += 1
            reg_breadth[_areal_breadth_label(len(named))] += 1
            for r in named:
                region_types[r["region"]] += 1
    def _people_count(t: dict) -> int:
        ag = t.get("attestations_grouped") or {}
        seen = {e["people"] for r in ag.get("regions", []) for e in r.get("entries", []) if e.get("people")}
        return len(seen)

    top_rich = sorted(types, key=lambda t: len(t.get("motifs", [])), reverse=True)[:15]
    top_families = sorted((t for t in types if t.get("subtypes")),
                          key=lambda t: len(t["subtypes"]), reverse=True)[:15]
    top_combos = sorted(types, key=lambda t: len(t.get("combos", [])), reverse=True)[:15]
    top_widest = sorted(types, key=_people_count, reverse=True)[:15]
    # Peoples: types attesting each canonical people (culture_legend counts).
    top_peoples = sorted(legend.items(), key=lambda kv: kv[1]["count"], reverse=True)[:18]
    return {
        "index": "atu",
        "intro": _INTRO["atu"],
        "title": "Aarne-Thompson-Uther Tale-Type Index",
        "cards": [
            {"value": len(types), "label": "tale types"},
            {"value": len([c for c in chapters if c]), "label": "chapters"},
            {"value": len(legend), "label": "peoples"},
            {"value": n_att, "label": "attested"},
            {"value": n_mot, "label": "TMI-linked"},
            {"value": round(100 * n_refs / len(types)) if types else 0, "label": "with references", "suffix": "%"},
        ],
        "sections": _OVERVIEW_SECTIONS,
        "panels": [
            # Distribution & content — region & chapter first
            {"id": "atRegions", "title": "Tale types by region", "section": "content"},
            {"id": "atChapters", "title": "Tale types by chapter", "section": "content"},
            {"id": "atDivisions", "title": "Largest divisions", "section": "content"},
            {"id": "atPeoples", "title": "Peoples with the most tale types", "section": "content"},
            {"id": "atRich", "title": "Most motif-rich tale types", "section": "content"},
            {"id": "atWidest", "title": "Most widespread tale types (peoples attesting)", "section": "content"},
            {"id": "atCombos", "title": "Most-combined tale types", "section": "content"},
            {"id": "atFamilies", "title": "Largest subtype families", "section": "content"},
            # Dataset diagnostics
            {"id": "atMotifHist", "title": "Constituent motifs per tale type", "section": "diagnostics"},
            {"id": "atRegBreadth", "title": "Regions per tale type", "section": "diagnostics"},
            {"id": "atSources", "title": "Most-cited sources", "section": "diagnostics"},
        ],
        "chapters": [{"chapter": ch, "label": ch, "count": c} for ch, c in chapters.most_common() if ch],
        "divisions": [{"division": dv, "label": dv, "count": c} for dv, c in divisions.most_common(15)],
        "motif_hist": [{"bucket": b, "count": motif_hist[b]} for b in ("0", "1", "2–3", "4–6", "7–10", "11+")],
        "top_rich": [{"id": t["id"], "label": f"{t['id']} {t.get('name', '')}", "count": len(t.get("motifs", []))}
                     for t in top_rich],
        "families": [{"id": t["id"], "label": f"{t['id']} {t.get('name', '')}", "count": len(t["subtypes"])}
                     for t in top_families],
        "combos": [{"id": t["id"], "label": f"{t['id']} {t.get('name', '')}", "count": len(t.get("combos", []))}
                   for t in top_combos],
        "widest": [{"id": t["id"], "label": f"{t['id']} {t.get('name', '')}", "count": _people_count(t)}
                   for t in top_widest],
        "regions": [{"region": reg, "count": c} for reg, c in region_types.most_common()],
        "top_peoples": [{"label": canon, "count": e["count"]} for canon, e in top_peoples],
        "reg_breadth": [{"bucket": b, "count": reg_breadth[b]}
                        for b in ("0", "1–2", "3–5", "6–10", "11–20", "21+")],
        "top_sources": _atu_top_sources(types),
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
    widest = sorted(records, key=lambda r: len(r.get("cultures") or {}), reverse=True)[:15]
    hubs = [(mid, c) for mid, c in indeg.most_common(50) if mid in by][:15]
    chapter_labels = data.get("chapters") or {}

    return {
        "index": "tmi",
        "intro": _INTRO["tmi"],
        "title": "Thompson Motif-Index of Folk-Literature",
        "totals": {
            "count": len(records), "chapters": len(chapters), "with_notes": n_notes,
            "definitions": n_def, "substantive": n_sub, "atu": n_atu,
        },
        "cards": [
            {"value": len(records), "label": "motifs"},
            {"value": len(chapters), "label": "chapters"},
            {"value": len(cultures), "label": "cultures"},
            {"value": n_sub, "label": "substantive"},
            {"value": n_atu, "label": "ATU-linked"},
            {"value": round(100 * n_notes / len(records)) if records else 0, "label": "have notes", "suffix": "%"},
        ],
        "sections": _OVERVIEW_SECTIONS,
        "panels": [
            # Distribution & content — region & chapter first
            {"id": "ovRegions", "title": "Motifs by region", "section": "content"},
            {"id": "ovChapters", "title": "Motifs by chapter (all vs. substantive)", "section": "content"},
            {"id": "ovCultures", "title": "Cultures with the most motifs", "section": "content"},
            {"id": "ovBreadth", "title": "Cultures per motif", "section": "content"},
            {"id": "ovWidest", "title": "Most widespread motifs (cultures attesting)", "section": "content"},
            {"id": "ovHubs", "title": "Most cross-referenced motifs (cf./†)", "section": "content"},
            # Dataset diagnostics
            {"id": "ovComposition", "title": "Motifs by kind", "section": "diagnostics"},
            {"id": "ovLevels", "title": "Motifs by hierarchy level", "section": "diagnostics"},
            {"id": "ovNotes", "title": "Motifs by note length", "section": "diagnostics"},
            {"id": "ovTopNotes", "title": "Best-documented motifs", "section": "diagnostics"},
            {"id": "ovSources", "title": "Most-cited sources", "section": "diagnostics"},
        ],
        "composition": [{"label": k, "count": comp[k]} for k in ("substantive", "scaffold", "variation")],
        "levels": [{"level": f"L{lv}", "count": levels[lv]} for lv in sorted(levels)],
        "notes_histogram": [{"bucket": label, "count": notes_hist[label]} for _, _, label in _NOTES_BUCKETS],
        "widest": [{"id": r["id"], "label": f"{r['id']} {r.get('name', '')}", "count": len(r.get("cultures") or {})}
                   for r in widest],
        "breadth_histogram": [{"bucket": b, "count": breadth[b]}
                              for b in ("0", "1", "2", "3–5", "6–10", "11+")],
        "chapters": [{"id": ch, "chapter": ch, "label": chapter_labels.get(ch, ch), "count": c, "substantive": s}
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
    """Citation key -> [{title, url}] from the built TMI bibliography key.

    A key (author surname or abbreviation) can map to several works; the list
    preserves them so a multi-work author is disambiguated by the short title. The
    key is produced by the pipeline (motifs.sources.bibliography) into
    ``outputs/motifs/tmi_bibliography.json``; absent when built without network.
    """
    def build() -> dict[str, list[dict]]:
        path = store.motifs_dir() / "tmi_bibliography.json"
        try:
            raw = path.read_text("utf-8")
        except (FileNotFoundError, OSError):
            return {}
        index: dict[str, list[dict]] = {}
        for e in json.loads(raw).get("entries", []):
            url = e["urls"][0]["url"] if e.get("urls") else ""
            rec = {"title": e.get("citation", ""), "url": url}
            for key in e.get("keys", []):
                index.setdefault(key, []).append(rec)
        return index
    return store.cached("tmi:bib", build)


def _berezkin_bibliography() -> dict:
    """The whole ``berezkin_bibliography.json`` (bibliography + per-motif tree).

    Produced by ``motifs.sources.berezkin_bibliography``; absent when the
    catalogue was built without it. Cached per process.
    """
    def build() -> dict:
        path = store.motifs_dir() / "berezkin_bibliography.json"
        try:
            return json.loads(path.read_text("utf-8"))
        except (FileNotFoundError, OSError):
            return {}
    return store.cached("berezkin:bib", build)


def _berezkin_motif_bibliography(motif_id: str) -> dict:
    """Per-motif Berezkin sources grouped by macro-area, plus the citations not tied
    to any areal code (the "Other" bucket). Comparative ``(Ср. …)`` blocks are
    excluded. Empty when the file is absent."""
    data = _berezkin_bibliography()
    tree = (data.get("by_motif") or {}).get(motif_id)
    if not tree:
        return {}
    bib = data.get("bibliography") or {}

    def source(cite: dict) -> dict:
        e = bib.get(cite["key"], {})
        return {"key": cite["key"], "author": e.get("author", ""),
                "year": e.get("year", ""), "title": e.get("title", ""),
                "status": cite.get("status", "")}

    def region_citations(reg: dict) -> list:
        # Flat schema (citations per region); tolerate the older ethnos-grouped
        # schema so the display works before the bibliography is rebuilt.
        if reg.get("citations") is not None:
            return reg["citations"]
        return [c for e in reg.get("ethnos", []) for c in e.get("citations", [])]

    by_area: dict[str, dict] = {}
    unattached: list[dict] = []
    seen_un: set = set()
    for reg in tree:
        if reg.get("cf"):
            continue
        code = reg.get("area_code") or ""
        if not code:  # citations with no recognised macro-area → "Other" bucket
            for c in region_citations(reg):
                if c["key"] not in seen_un:
                    seen_un.add(c["key"])
                    unattached.append(source(c))
            continue
        slot = by_area.setdefault(code, {"area_code": code, "region": reg.get("region", ""),
                                         "sources": [], "_seen": set()})
        for c in region_citations(reg):
            if c["key"] not in slot["_seen"]:
                slot["_seen"].add(c["key"])
                slot["sources"].append(source(c))

    areas = []
    for a in by_area.values():
        a.pop("_seen", None)
        areas.append(a)
    areas.sort(key=lambda a: len(a["sources"]), reverse=True)
    return {"by_area": areas, "unattached": unattached}


# The leading author/abbreviation of a citation (skipping Thompson's '*' marks).
_CITE_HEAD = re.compile(r"^[*\s]*([A-Z][A-Za-z.'\-]+(?:[ -][A-Z][A-Za-z.'\-]+){0,2})")


def _resolve_citation(text: str) -> dict:
    """A citation string + a book link/title when its head matches a known work."""
    text = re.sub(r"^\s*\*+\s*", "", text)  # drop Thompson's leading */** source markers
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


def list_motifs(index: str, *, chapter: str = "", division: str = "", sub_division: str = "",
                sub_division3: str = "", section: str = "", q: str = "", level: int | None = None,
                tier: str = "", limit: int = 200, offset: int = 0) -> dict:
    """Filtered, paginated motif list for one index."""
    records = _records(index)
    query = q.strip().lower()
    if chapter:
        records = [r for r in records if r.get("chapter", "") == chapter]
    if division:  # ATU browse level (chapter → division → type)
        records = [r for r in records if r.get("division", "") == division]
    if sub_division:  # ATU finer level (division → sub_division → type)
        records = [r for r in records if r.get("sub_division", "") == sub_division]
    if sub_division3:  # TMI's third heading level (division3)
        records = [r for r in records if r.get("division3", "") == sub_division3]
    if section:  # TMI's finest heading level (the tens section)
        records = [r for r in records if r.get("section", "") == section]
    if level is not None:
        records = [r for r in records if r.get("level", 0) == level]
    if index == "tmi" and tier in _TIER_PREDICATE:  # substantive / definitions / ATU
        records = [r for r in records if _TIER_PREDICATE[tier](r)]
    if query:
        records = [
            r for r in records
            if query in r.get("id", "").lower() or query in r.get("name", "").lower()
            # ATU aliases: the pre-2004 name and old numbers also match (find 1891 by
            # searching "The Great Rabbit-Catch" or "1891A*").
            or query in (r.get("former_name") or "").lower()
            or any(query in fid.lower() for fid in r.get("former_ids", []))
        ]
    total = len(records)
    page = records[offset: offset + limit]
    return {"index": index, "total": total, "items": [_list_item(index, r) for r in page]}


def get_motif(index: str, motif_id: str) -> dict | None:
    """Full detail for one motif with resolved cross-walk links, or None.

    For ATU an id that is an old (pre-2004) number, and for TMI a pre-1st-edition
    (renumbered) code, resolves to the current record it was renumbered to / merged
    into, flagged with ``redirected_from``."""
    rec = _by_id(index).get(motif_id)
    data = store.load_index(index) or {}
    redirected_from = ""
    if rec is None and index in ("atu", "tmi"):
        target = (data.get("aliases") or {}).get(motif_id)
        if target:
            rec = _by_id(index).get(target)
            redirected_from = motif_id
    if rec is None:
        return None

    cw = store.load_crosswalk()
    detail: dict = {
        "index": index,
        "id": rec["id"],
        "redirected_from": redirected_from,
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
        # Cross-index links are outgoing references (this motif -> the target),
        # tagged rel="out" so the frontend shows a ⇒ direction marker. Resolved
        # ATU ids (old numbers mapped to the current type) come from the cross-walk,
        # so the chips link the live type rather than a dead cited number.
        atu_refs = cw.get("berezkin_to_atu", {}).get(rec["id"], rec.get("atu_refs", []))
        detail["links"]["atu"] = [{**_link("atu", a), "rel": "out"} for a in atu_refs]
        # mapsofmyths enrichment: thematic taxonomy, direct Thompson (TMI) links, and
        # the tradition-level distribution grouped by macro-region.
        detail["motif_type"] = rec.get("motif_type", "")
        detail["motif_group"] = rec.get("motif_group", "")
        detail["links"]["tmi"] = [{**_link("tmi", _clean_tmi_ref(t)), "rel": "out"} for t in rec.get("tmi_refs", [])]
        detail["traditions"] = _berezkin_tradition_distribution(rec.get("traditions", []), data.get("traditions") or {})
        # Source bibliography (areasofmyths.com) grouped by macro-area, + the
        # citations not tied to an areal code.
        detail["bibliography"] = _berezkin_motif_bibliography(rec["id"])

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
        detail["duplicate_siblings"] = _tmi_dup_siblings(rec)
        detail["breadcrumbs"] = _tmi_ancestors(rec)  # broadest first
        detail["children"], detail["children_truncated"] = _tmi_direct_children(rec["id"])
        detail["descendant_counts"] = _descendant_counts(rec["id"])
        detail["descendant_count"] = detail["descendant_counts"]["all"]
        # '†' cross-references parsed from the note text, in one list: Thompson's
        # 'Cf.' compares are the default; the rarer bare '†X' direct redirects
        # carry a ``see_also`` flag so the frontend can mark that minority.
        see_also = rec.get("see_also") or {}
        detail["links"]["related"] = _merge_tmi_related(
            see_also.get("cf", []), see_also.get("ref", []))
        # One merged section: tale types this motif is a constituent of (⇐, from
        # atu_seq) and those its note references (⇒, AaTh-resolved); ⇔ = both.
        atu_ids = cw.get("tmi_to_atu", {}).get(rec["id"], [])
        detail["links"]["atu_related"] = _merge_atu_relations(
            atu_ids, _resolve_atu_inline(rec.get("atu_inline", [])))
        # Tale types this motif *defines* (Uther's heading motif) — a distinct link
        # from the constituent one above.
        detail["links"]["atu_defines"] = [_link("atu", a) for a in cw.get("tmi_to_atu_defining", {}).get(rec["id"], [])]
        # Tale types whose summary prose names this motif — the inverse of the
        # inline TMI links the ATU summary renders, so the edge shows both ways.
        detail["links"]["atu_summary_refs"] = [_link("atu", a) for a in cw.get("tmi_to_atu_summary", {}).get(rec["id"], [])]
        # Direct Berezkin motifs that map here (mapsofmyths concordance).
        detail["links"]["berezkin"] = [_link("berezkin", b) for b in cw.get("tmi_to_berezkin", {}).get(rec["id"], [])]
        # Mellmann's printed classification headings (division1-3), for the
        # Classification line — as in the ATU index.
        detail["division"] = rec.get("division", "")
        detail["division_range"] = rec.get("division_range")
        detail["sub_division"] = rec.get("sub_division", "")
        detail["sub_division_range"] = rec.get("sub_division_range")
        detail["division3"] = rec.get("division3", "")
        detail["division3_range"] = rec.get("division3_range")
        detail["section"] = rec.get("section", "")
        detail["section_range"] = rec.get("section_range")
        # Earlier (1st-edition, 1932) Thompson codes this motif was renumbered from
        # (Mellmann's ``1st ed.`` column) — the mirror of ATU's old numbers.
        detail["former_ids"] = rec.get("former_ids") or []

    elif index == "atu":
        detail["division"] = rec.get("division", "")
        detail["division_range"] = rec.get("division_range")
        detail["sub_division"] = rec.get("sub_division", "")
        detail["sub_division_range"] = rec.get("sub_division_range")
        detail["names"] = rec.get("names") or {}                # multilingual names (Wikidata)
        detail["wikipedia"] = rec.get("wikipedia") or []        # [{lang, title, url}]
        detail["wikisource"] = rec.get("wikisource") or []      # full texts [{lang, title, url}]
        detail["concordances"] = rec.get("concordances") or {}  # {KHM|AaTh|Perry|…: [codes]}
        detail["former_name"] = rec.get("former_name", "")       # pre-2004 Uther name → subtitle
        detail["former_ids"] = rec.get("former_ids") or []       # old ATU numbers → this type
        detail["summary"] = rec.get("summary", "")
        detail["summary_html"] = _atu_summary_html(rec.get("summary", ""))
        detail["references"] = rec.get("references", "")      # Uther litvar (key literature)
        detail["attestations"] = rec.get("attestations", "")  # Uther provenance (by tradition)
        detail["attestations_grouped"] = rec.get("attestations_grouped") or {}  # by macro-region
        detail["remarks"] = rec.get("remarks", "")            # Uther remarks (historical notes)
        detail["tales"] = rec.get("tales", [])                # Ashliman AFT example tales (metadata)
        detail["links"]["parent"] = [_link("atu", rec["parent"])] if rec.get("parent") else []
        detail["links"]["subtypes"] = [_link("atu", s) for s in rec.get("subtypes", [])]
        detail["links"]["defining"] = [_mark_missing(_link("tmi", m), "tmi_gap") for m in rec.get("defining_motifs", [])]
        detail["links"]["tmi"] = [_mark_missing(_link("tmi", m), "tmi_gap") for m in rec.get("motifs", [])]
        # TMI motifs whose notes cite this tale type ("Type N") — the inverse of the
        # ⇒ "cited" relation shown on the motif page, so the edge shows both ways.
        detail["links"]["tmi_via_notes"] = [_link("tmi", m) for m in cw.get("atu_to_tmi_note", {}).get(rec["id"], [])]
        detail["links"]["combos"] = [_link("atu", c) for c in rec.get("combos", [])]
        bz = cw.get("atu_to_berezkin", {}).get(rec["id"], [])
        detail["links"]["berezkin"] = [_link("berezkin", b) for b in bz]

    # Heuristic textual parallels — look-alike motifs in the other indexes with no
    # recorded cross-walk link. A separate, clearly-labelled *suggestion* layer.
    detail["parallels"] = _parallels(index, rec["id"])
    # Semantic parallels — nearest look-alikes by BGE-M3 embeddings (share meaning,
    # not necessarily words); another suggestion layer, precomputed offline.
    detail["semantic_parallels"] = _semantic_parallels(index, rec["id"])
    # Curated conceptual parallels found by reasoning (same mytheme, different label).
    detail["reasoned_parallels"] = _reasoned_parallels(index, rec["id"])
    # Transitively inferred cross-links (triangle closure through a low-fan-out
    # pivot), each carrying the bridge it was derived through.
    detail["inferred"] = _inferred(index, rec["id"])

    return detail


def _inferred(index: str, motif_id: str) -> list[dict]:
    """Resolve the transitively-inferred cross-links for a motif, each tagged with
    the bridge motif it was derived through (provenance)."""
    entries = store.load_crosswalk().get("inferred", {}).get(index, {}).get(motif_id, [])
    out = []
    for e in entries:
        link = _link(e["index"], e["id"])
        via_rec = _by_id(e["via_index"]).get(e["via_id"])
        link["via"] = {"index": e["via_index"], "id": e["via_id"],
                       "name": via_rec.get("name", "") if via_rec else ""}
        out.append(link)
    return out


def _parallels(index: str, motif_id: str) -> list[dict]:
    """Resolve the suggested textual parallels for a motif into display links."""
    entries = store.load_parallels().get("adjacency", {}).get(index, {}).get(motif_id, [])
    out = []
    for e in entries:
        link = _link(e["index"], e["id"])
        link["title_sim"], link["doc_sim"], link["shared"] = e["title_sim"], e["doc_sim"], e["shared"]
        link["tier"] = e.get("tier", "A")
        out.append(link)
    return out


def _semantic_parallels(index: str, motif_id: str) -> list[dict]:
    """Resolve the BGE-M3 semantic look-alikes for a motif into display links."""
    entries = store.load_semantic_parallels().get("adjacency", {}).get(index, {}).get(motif_id, [])
    out = []
    for e in entries:
        link = _link(e["index"], e["id"])
        link["sim"] = e["sim"]
        link["also_lexical"] = e.get("also_lexical", False)
        out.append(link)
    return out


def _reasoned_parallels(index: str, motif_id: str) -> list[dict]:
    """The curated conceptual-parallel groups this motif belongs to, each with the
    *other* members resolved into links (see ``motifs.reasoned_parallels``)."""
    from motifs import reasoned_parallels as rp
    adj = store.cached("reasoned_parallels_adj", rp.adjacency)
    out = []
    for gi in adj.get(index, {}).get(motif_id, []):
        g = rp.GROUPS[gi]
        links = [_link(idx, mid) for idx, mid in g["members"] if not (idx == index and mid == motif_id)]
        out.append({"theme": g["theme"], "title": g["title"], "note": g["note"],
                    "confidence": g["confidence"], "links": links})
    return out


# A TMI motif token (letter + digits + dotted sub-numbers) and a "Type N[, M]"
# clause in an ATU summary — linked to the existing motif/type they name.
_SUMMARY_MOTIF = re.compile(r"\b[A-Z]\d[A-Za-z0-9]*(?:\.\d+)*")
_SUMMARY_TYPE = re.compile(
    r"\b(Types?\s+)(\d+[A-Za-z*]*(?:(?:\s*,\s*|\s+and\s+|\s*&\s*)\d+[A-Za-z*]*)*)")
# An inline "(k)" enumeration marker (Uther lists a tale's forms as "(1)… (2)…").
_SUMMARY_ENUM = re.compile(r"\((\d{1,2})\)")

# A bracketed motif reference like `[S31, L55]` or `[J758.1, cf. J341.1]`. Uther
# wraps motif codes in square brackets, but since we render them as links the
# brackets are redundant, so we unwrap groups whose content is only motif codes.
_BRACKET_GROUP = re.compile(r"\[([^\]]*)\]")
_MOTIF_ONLY = re.compile(r"[A-Z]\d[A-Za-z0-9]*(?:\.\d+)*(?:–[A-Z]?\d[A-Za-z0-9.]*)?f{0,2}")
# A motif *range* — `J1759'J1763`, `X1030'1036`. The separator is a mojibake en-dash
# printed as an apostrophe; we restore the dash so it reads as a range (the crosswalk
# credits every member the range spans — see crosswalk._SUMMARY_RANGE).
_RANGE_SEP = re.compile(r"([A-Z]\d[A-Za-z0-9.]*)'([A-Z]?\d[A-Za-z0-9.]*)")


def _is_motif_group(content: str) -> bool:
    parts = [p.strip() for p in content.split(",") if p.strip()]
    if not parts:
        return False
    return all(_MOTIF_ONLY.fullmatch(re.sub(r"^cf\.\s*", "", p).rstrip(".")) for p in parts)


def _inline_link(index: str, ref: str) -> str:
    return (f'<a class="motif-link" href="#/motifs?index={index}&id={ref}" '
            f'data-index="{index}" data-id="{ref}">{ref}</a>')


def _linkify_summary(text: str) -> str:
    """Escape one summary fragment, then linkify the TMI motif codes and ATU 'Type N'
    refs it names — only those that resolve to a real motif/type. Tokens are
    alphanumeric, so injecting them raw after escaping the surrounding prose is safe."""
    tmi, atu = _by_id("tmi"), _by_id("atu")
    esc = html.escape(text, quote=False)
    # Restore the mojibake apostrophe-as-en-dash between range endpoints so they read
    # as `J1759–J1763` (both endpoints still linkify; interior members are credited in
    # the crosswalk, not spelled out here).
    esc = _RANGE_SEP.sub("\\1–\\2", esc)
    # Drop the square brackets around motif-only groups (the chips carry the cue).
    esc = _BRACKET_GROUP.sub(lambda m: m.group(1) if _is_motif_group(m.group(1)) else m.group(0), esc)

    def _motif(m):
        tok = m.group(0)
        if tok in tmi:
            return _inline_link("tmi", tok)
        # "J1141ff" / "J21f" is the "and following" shorthand — link the base motif,
        # keep the trailing f/ff as plain text.
        base = tok.rstrip("f")
        if base != tok and base in tmi:
            return _inline_link("tmi", base) + tok[len(base):]
        return tok

    esc = _SUMMARY_MOTIF.sub(_motif, esc)
    esc = _SUMMARY_TYPE.sub(
        lambda m: m.group(1) + re.sub(
            r"\d+[A-Za-z*]*",
            lambda mm: _inline_link("atu", mm.group(0)) if mm.group(0) in atu else mm.group(0),
            m.group(2)),
        esc)
    return esc


def _atu_summary_html(text: str) -> str:
    """Render an ATU summary, turning inline ``(1)…(N)`` enumerations into ``<ol>``
    lists. A summary may hold several runs (each restarting at ``(1)``, as in type
    910A) with prose between and after them, and a run may be followed by trailing
    text (type 460A); every run becomes its own list and all surrounding prose stays
    in ``<p>`` blocks. Structure is parsed on the raw text (where brackets/parens are
    intact) and each piece is linkified independently — nothing is dropped."""
    if not text:
        return ""
    blocks = _summary_blocks(text)
    if blocks is None:
        return f'<p class="motif-text">{_linkify_summary(text)}</p>'
    parts = []
    for kind, payload in blocks:
        if kind == "p":
            parts.append(f'<p class="motif-text">{_linkify_summary(payload)}</p>')
        else:
            lis = "".join(f"<li>{_linkify_summary(it)}</li>" for it in payload)
            parts.append(f'<ol class="motif-text motif-summary-list">{lis}</ol>')
    return "".join(parts)


def _first_sentence_end(s: str) -> int | None:
    """Index just past the first sentence terminator at bracket/paren depth 0 (so
    ``s[:idx]`` keeps the punctuation), or ``None``. Decimal points inside numbers and
    terminators nested in ``(…)``/``[…]`` are skipped; a ``.`` counts only when it ends
    the string or is followed by whitespace and a capital / opening quote or bracket."""
    depth = 0
    for i, ch in enumerate(s):
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth = max(0, depth - 1)
        elif depth == 0 and ch in ".!?":
            if ch == "." and i > 0 and s[i - 1].isdigit() and i + 1 < len(s) and s[i + 1].isdigit():
                continue  # decimal point, not a sentence end
            j = i + 1
            while j < len(s) and s[j] == " ":
                j += 1
            if j >= len(s) or s[j].isupper() or s[j] in "([\"'":
                return i + 1
    return None


def _enum_runs(text: str) -> list[list[re.Match]]:
    """Group the ``(k)`` enumeration markers into runs, each a maximal strictly
    ascending ``1,2,3,…`` sequence. Markers that don't extend the current run (a stray
    ``(3)`` in prose) are ignored and stay as literal text. Runs of length one aren't
    lists and are discarded."""
    runs: list[list[re.Match]] = []
    cur: list[re.Match] = []
    expect = 0
    for m in _SUMMARY_ENUM.finditer(text):
        v = int(m.group(1))
        if v == 1:
            if len(cur) >= 2:
                runs.append(cur)
            cur, expect = [m], 2
        elif cur and v == expect:
            cur.append(m)
            expect += 1
    if len(cur) >= 2:
        runs.append(cur)
    return runs


def _comma_style(text: str, run: list[re.Match]) -> bool:
    """True when a run's items are comma-joined fragments of a single sentence (no
    sentence terminator between markers), as opposed to items that are whole
    sentences. Only comma-style runs have their last item split from trailing prose —
    a period-style item may legitimately span several sentences."""
    return all(_first_sentence_end(text[run[i].end():run[i + 1].start()]) is None
               for i in range(len(run) - 1))


def _summary_blocks(text: str) -> list[tuple[str, object]] | None:
    """Parse a raw ATU summary into an ordered list of blocks — ``("p", prose)`` and
    ``("ol", [items])`` — around its ``(1)…(N)`` enumeration runs. Returns ``None`` when
    there is no run to list. The ``(k)`` markers become the list numbering; every
    other character is preserved in exactly one block."""
    runs = _enum_runs(text)
    if not runs:
        return None
    blocks: list[tuple[str, object]] = []
    pre = text[:runs[0][0].start()].strip()
    if pre:
        blocks.append(("p", pre))
    for ri, run in enumerate(runs):
        next_start = runs[ri + 1][0].start() if ri + 1 < len(runs) else len(text)
        comma = len(run) >= 2 and _comma_style(text, run)
        items: list[str] = []
        tail = ""
        for mi, mk in enumerate(run):
            last = mi + 1 == len(run)
            chunk = text[mk.end():(next_start if last else run[mi + 1].start())]
            if last and comma:
                cut = _first_sentence_end(chunk)
                if cut is not None:
                    items.append(chunk[:cut].strip())
                    tail = chunk[cut:].strip()
                    continue
            items.append(chunk.strip())
        blocks.append(("ol", items))
        if tail:
            blocks.append(("p", tail))
    return blocks
