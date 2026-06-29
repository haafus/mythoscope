"""Read-side service for the motif database.

Serves the browsable Motifs catalog: index summaries, paginated/filtered motif
lists, and per-motif detail with resolved cross-walk links. All data is read
from ``outputs/motifs/`` (built by ``mytho motifs``) and cached per process.
"""

from __future__ import annotations

from motifs import INDEX_LABELS, INDEX_ORDER, store

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
# The Trilogy `parent` field is empty for ~3% of dotted ids; fall back to
# trimming the id (A52.0.1 -> A52.0 -> A52) until an existing ancestor is found.
_SUBTREE_CAP = 300


def _tmi_effective_parent(motif_id: str, parent: str, by_id: dict) -> str:
    if parent:
        return parent
    trimmed = motif_id
    while "." in trimmed:
        trimmed = trimmed.rsplit(".", 1)[0]
        if trimmed in by_id:
            return trimmed
    return ""


def _tmi_children() -> dict[str, list[str]]:
    """parent id -> child ids, in stored (hierarchical) order."""
    def build() -> dict[str, list[str]]:
        by_id = _by_id("tmi")
        children: dict[str, list[str]] = {}
        for mid, rec in by_id.items():
            parent = _tmi_effective_parent(mid, rec.get("parent", ""), by_id)
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
        parent = _tmi_effective_parent(cur["id"], cur.get("parent", ""), by_id)
        if not parent or parent in seen or parent not in by_id:
            break
        seen.add(parent)
        chain.append(parent)
        cur = by_id[parent]
    return [_link("tmi", mid) for mid in reversed(chain)]


def _tmi_subtree(root_id: str) -> dict:
    """Nested narrower motifs under root, capped at _SUBTREE_CAP total nodes."""
    children = _tmi_children()
    by_id = _by_id("tmi")
    state = {"count": 0, "truncated": False}

    def walk(motif_id: str) -> list[dict]:
        nodes = []
        for child_id in children.get(motif_id, []):
            if state["count"] >= _SUBTREE_CAP:
                state["truncated"] = True
                break
            state["count"] += 1
            rec = by_id.get(child_id, {})
            nodes.append({
                "id": child_id,
                "name": rec.get("name", ""),
                "children": walk(child_id),
            })
        return nodes

    return {"nodes": walk(root_id), "truncated": state["truncated"]}


def _link(index: str, motif_id: str) -> dict:
    """A cross-walk link: id + resolved name + whether the target exists here."""
    rec = _by_id(index).get(motif_id)
    return {
        "index": index,
        "id": motif_id,
        "name": rec.get("name", "") if rec else "",
        "exists": rec is not None,
    }


def _chapter_label(data: dict, chapter: str) -> str:
    title = (data.get("chapters") or {}).get(chapter, "")
    return f"{chapter} — {title}" if title else chapter


def list_indexes() -> list[dict]:
    """Summaries for every built index: label, count, and chapters with counts."""
    out = []
    for index in INDEX_ORDER:
        data = store.load_index(index)
        if not data:
            continue
        records = data.get(_RECORDS_KEY.get(index, "motifs"), [])
        chapter_counts: dict[str, int] = {}
        for r in records:
            chapter_counts[r.get("chapter", "")] = chapter_counts.get(r.get("chapter", ""), 0) + 1
        chapters = [
            {"id": ch, "label": _chapter_label(data, ch), "count": chapter_counts[ch]}
            for ch in sorted(chapter_counts)
            if ch
        ]
        out.append({
            "index": index,
            "label": data.get("label") or INDEX_LABELS.get(index, index),
            "long_label": data.get("long_label", ""),
            "attribution": data.get("attribution", ""),
            "homepage": data.get("homepage", ""),
            "count": len(records),
            "chapters": chapters,
        })
    return out


def _list_item(index: str, rec: dict) -> dict:
    """A compact record for the scrolling list (index-specific badge included)."""
    item = {"index": index, "id": rec["id"], "name": rec.get("name", ""), "chapter": rec.get("chapter", "")}
    if index == "berezkin":
        item["badge"] = f"{len(rec.get('areas', []))} areas"
    elif index == "atu":
        item["badge"] = f"{len(rec.get('motifs', []))} motifs"
    elif index == "tmi":
        item["badge"] = f"L{rec.get('level', 0)}"
    return item


def list_motifs(index: str, *, chapter: str = "", q: str = "", limit: int = 200, offset: int = 0) -> dict:
    """Filtered, paginated motif list for one index."""
    records = _records(index)
    query = q.strip().lower()
    if chapter:
        records = [r for r in records if r.get("chapter", "") == chapter]
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
        # Areal indices decoded to macro-area names (legend voted from detail-page
        # headers); name is "" for the few indices not covered by the legend.
        legend = data.get("areas") or {}
        detail["areas"] = [{"id": a, "name": legend.get(str(a), "")} for a in rec.get("areas", [])]
        detail["links"]["see_also"] = [_link("berezkin", c) for c in rec.get("see_also", [])]
        detail["links"]["atu"] = [_link("atu", a) for a in rec.get("atu_refs", [])]

    elif index == "tmi":
        detail["chapter_name"] = rec.get("chapter_name", "")
        detail["notes"] = rec.get("notes", "")
        detail["level"] = rec.get("level", 0)
        detail["breadcrumbs"] = _tmi_ancestors(rec)  # broadest first
        detail["subtree"] = _tmi_subtree(rec["id"])
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
