"""Re-project the derived structures crosswalk/parallels need from the stored index JSONs.

The monolithic ``build_motifs`` passes ~10 in-memory projections of the three source indexes
straight into ``crosswalk.build`` / ``parallels.build``. To split those into their own stages,
the downstream stages must instead reload the indexes and re-derive the same structures — this
module is that single source of truth (used by both the monolith, once refactored, and the
future ``crosswalk``/``parallels`` stages). Every structure is a projection of data already in
the JSONs; the one field that must be *persisted* for this to work is ``atu_seq`` (see
``sources.trilogy.build_atu``), read here from ``atu_index["atu_seq"]``.
"""

from __future__ import annotations

from . import store


def derived_from_indexes(berezkin_data: dict, tmi_index: dict, atu_index: dict) -> dict:
    """The exact structures crosswalk/parallels consume, re-derived from the three indexes. A
    disabled/unbuilt source has no index JSON (``load_index`` → ``None``); it reads as empty
    structures, exactly as the monolith's in-memory path saw a disabled source (never a crash)."""
    berezkin_data, tmi_index, atu_index = berezkin_data or {}, tmi_index or {}, atu_index or {}
    tmi_motifs = tmi_index.get("motifs", [])
    atu_types = atu_index.get("types", [])

    aath_to_atu: dict[str, list[str]] = {}
    for t in atu_types:
        for code in (t.get("concordances") or {}).get("AaTh", []):
            aath_to_atu.setdefault(code, [])
            if t["id"] not in aath_to_atu[code]:
                aath_to_atu[code].append(t["id"])

    return {
        "berezkin_motifs": berezkin_data.get("motifs", []),
        "tmi_motifs": tmi_motifs,
        "atu_types": atu_types,
        "tmi_ids": {m["id"] for m in tmi_motifs},
        "tmi_aliases": tmi_index.get("aliases", {}),
        "tmi_notes": {m["id"]: m["atu_inline"] for m in tmi_motifs if m.get("atu_inline")},
        "atu_ids": {t["id"] for t in atu_types},
        "atu_defining": {t["id"]: t["defining_motifs"] for t in atu_types if t.get("defining_motifs")},
        "atu_aliases": atu_index.get("aliases", {}),
        "atu_summaries": {t["id"]: t["summary"] for t in atu_types if t.get("summary")},
        "aath_to_atu": aath_to_atu,
        # Persisted by build_atu into the index (a separate return in the monolith); {} on an
        # index built before atu_seq was persisted, until the next rebuild.
        "atu_seq": atu_index.get("atu_seq", {}),
    }


def load_indexes(loader=store.load_index) -> dict:
    """Load the three source indexes from disk and re-derive the downstream structures."""
    return derived_from_indexes(loader("berezkin"), loader("tmi"), loader("atu"))
