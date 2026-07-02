"""Trilogy dataset (j-hagedorn/trilogy): TMI + ATU as tidy CSVs.

We pull four files: ``tmi`` (Thompson motifs with parsed hierarchy), ``atu_df``
(tale types), ``atu_seq`` (the ordered TMI motifs that make up each tale type —
the bridge that powers the ATU<->TMI cross-walk) and ``atu_combos`` (tale types
commonly told together).
"""

from __future__ import annotations

import collections
import csv
import io
import logging
import re
from pathlib import Path

from settings import settings

from .culture_dict import build_legend
from .fetch import fetch_to_cache
from .tmi_notes import parse_notes

logger = logging.getLogger(__name__)

# TMI ``notes`` cells (long bibliographies) blow past the default 128 KB cell cap.
csv.field_size_limit(16 * 1024 * 1024)

_NA = {"", "NA", "N/A", "na"}

# An unclosed `notes` cell in the source CSV (motif A736.1.1) runs on and swallows
# the serialized text of ~4,200 later rows, each starting with `<code>. †<code>.`.
# That dagger form never occurs in a genuine note, so we cut at the first one.
_NOTES_BLEED_RE = re.compile(r"([A-Z]\d[\dA-Za-z.]*)\.\s*†\1\.")


def _clean(value: str | None) -> str:
    value = (value or "").strip()
    return "" if value in _NA else value


def _strip_notes_bleed(notes: str) -> str:
    m = _NOTES_BLEED_RE.search(notes)
    return notes[: m.start()].strip() if m else notes


def _read_csv(config: dict, key: str, *, force: bool) -> list[dict]:
    base = config["base_url"].rstrip("/")
    filename = config["files"][key]
    cache = Path(settings.motifs_dir) / "raw" / "trilogy" / filename
    raw = fetch_to_cache(f"{base}/{filename}", cache, force=force)
    text = raw.decode("utf-8", errors="replace")
    return list(csv.DictReader(io.StringIO(text)))


_NAT_RE = re.compile(r"\d+|\D+")


def tmi_sort_key(motif_id: str) -> list:
    """Hierarchical key so a parent precedes its descendants and numbers sort
    numerically: A1 < A1.4 < A10 < A100, C12.5 < C12.5.8."""
    return [(1, int(t)) if t.isdigit() else (0, t) for t in _NAT_RE.findall(motif_id)]


def _is_zero_family(motif_id: str) -> bool:
    """True if the id has a ``.0`` grouping segment (e.g. A52.0, A52.0.1)."""
    return "0" in motif_id.split(".")[1:]


def _id_trim_parent(code: str, idset: set[str]) -> str:
    """Recover an ancestor by trimming dotted segments (A52.0.1 -> A52.0 -> A52)."""
    trimmed = code
    while "." in trimmed:
        trimmed = trimmed.rsplit(".", 1)[0]
        if trimmed in idset:
            return trimmed
    return ""


def _finalize_tmi(motifs: list[dict]) -> list[dict]:
    """Repair the known Trilogy TMI defects, annotate, and hierarchically sort.

    - Duplicate codes (one code reused for distinct motifs): the first keeps the
      bare code, the rest get a lowercase letter sub-index (Z64 -> Z64, Z64b) so
      they are distinguishable; all are flagged ``duplicate``. ``code`` keeps the
      original. Cross-walk/parent references to the bare code resolve to the first.
    - ``parent`` is corrected to the effective parent (stored, else id-trimmed).
    - ``level`` keeps the dataset's place-value value for ordinary motifs; only
      the broken '.0' interpolations get a depth computed from corrected parents.
    All defects are logged.
    """
    counts = collections.Counter(m["id"] for m in motifs)
    used = set(counts)
    dup_codes = {code for code, n in counts.items() if n > 1}

    occ: dict[str, int] = {}
    for m in motifs:
        m["code"] = m["id"]
        if m["id"] in dup_codes:
            m["duplicate"] = True
            occ[m["id"]] = occ.get(m["id"], 0) + 1
            if occ[m["id"]] > 1:  # first keeps the bare code
                letter = occ[m["id"]] - 1
                while True:
                    cand = f"{m['code']}{chr(ord('a') + letter)}"
                    if cand not in used:
                        break
                    letter += 1
                used.add(cand)
                m["id"] = cand

    idset = {m["id"] for m in motifs}

    # Correct parents. The most specific existing dotted ancestor wins (so
    # A52.0.1 -> A52); dot-less codes (A111, whose place-value parent A110
    # isn't an id-prefix) fall back to the stored source parent. A dotted id with
    # no source parent is a real defect (the dataset dropped its level path);
    # a dot-less one with no parent is just a root (A0, A100, …) — not a defect.
    recovered = unresolved = 0
    for m in motifs:
        stored = m.get("parent", "")
        eff = _id_trim_parent(m["code"], idset) or (stored if stored in idset else "")
        if not stored and "." in m["code"]:
            recovered += eff != ""
            unresolved += eff == ""
        m["parent"] = eff

    # Level: keep the source value for ordinary motifs (the dataset's place-value
    # level is authoritative). Only the broken '.0' interpolations get a depth
    # computed from the corrected parents.
    by_id = {m["id"]: m for m in motifs}
    src_level = {m["id"]: m.get("level", 0) for m in motifs}
    memo: dict[str, int] = {}

    def resolve_level(mid: str, stack: frozenset) -> int:
        if mid in memo:
            return memo[mid]
        m = by_id[mid]
        if not _is_zero_family(m["id"]):
            memo[mid] = src_level.get(mid, 0)
        else:
            parent = m["parent"]
            memo[mid] = resolve_level(parent, stack | {mid}) + 1 \
                if (parent and parent in by_id and parent not in stack) else 0
        return memo[mid]

    for m in motifs:
        m["level"] = resolve_level(m["id"], frozenset())
        m.pop("source_level", None)

    if dup_codes:
        logger.warning("TMI defect: %d duplicate codes given letter sub-indices: %s",
                       len(dup_codes), ", ".join(sorted(dup_codes)))
    if recovered or unresolved:
        logger.warning("TMI defect: %d dotted ids had no source parent — reattached %d via id-trim, %d unresolved",
                       recovered + unresolved, recovered, unresolved)

    motifs.sort(key=lambda m: tmi_sort_key(m["id"]))
    return motifs


def _tmi_chapters(motifs: list[dict]) -> dict[str, str]:
    """Letter chapter -> name (e.g. ``A`` -> ``Myths``), in first-seen order."""
    chapters: dict[str, str] = {}
    for m in motifs:
        chapter = m["chapter"]
        if chapter and chapter not in chapters and m["chapter_name"]:
            chapters[chapter] = m["chapter_name"]
    return chapters


def _parse_tmi(rows: list[dict]) -> list[dict]:
    motifs = []
    for row in rows:
        code = _clean(row.get("id"))
        if not code:
            continue
        try:
            level = int(_clean(row.get("level")) or 0)
        except ValueError:
            level = 0
        parent = _clean(row.get(f"level_{level - 1}")) if level > 0 else ""
        notes = _strip_notes_bleed(_clean(row.get("notes")))
        motifs.append({
            "id": code,
            "chapter": _clean(row.get("chapter_id")) or code[:1],
            "chapter_name": _clean(row.get("chapter_name")),
            "name": _clean(row.get("motif_name")),
            "notes": notes,
            **parse_notes(notes),  # definition, cultures, references, see_also, atu_inline
            "level": level,
            "parent": parent if parent and parent != code else "",
        })
    return motifs


def _parse_atu_seq(rows: list[dict]) -> dict[str, list[str]]:
    """Group ``atu_seq`` rows into ``{atu_id: [ordered unique TMI motif codes]}``."""
    ordered: dict[str, list[tuple[float, str]]] = {}
    for row in rows:
        atu_id = _clean(row.get("atu_id"))
        motif = _clean(row.get("motif"))
        if not atu_id or not motif:
            continue
        try:
            order = float(_clean(row.get("motif_order")) or 0)
        except ValueError:
            order = 0.0
        ordered.setdefault(atu_id, []).append((order, motif))

    result: dict[str, list[str]] = {}
    for atu_id, pairs in ordered.items():
        pairs.sort(key=lambda p: p[0])
        seen: set[str] = set()
        motifs: list[str] = []
        for _, motif in pairs:
            if motif not in seen:
                seen.add(motif)
                motifs.append(motif)
        result[atu_id] = motifs
    return result


def _parse_atu_combos(rows: list[dict]) -> dict[str, list[str]]:
    combos: dict[str, set[str]] = {}
    for row in rows:
        atu_id = _clean(row.get("atu_id"))
        combo = _clean(row.get("combos") or row.get("combo"))
        if atu_id and combo:
            combos.setdefault(atu_id, set()).add(combo)
    return {k: sorted(v) for k, v in combos.items()}


# An ATU id is a number, optional letter suffix(es), optional "*" (313, 313A, 1861*).
_ATU_NUM = re.compile(r"^(\d+)")
# A division label carries its number range: "Supernatural Adversaries 300-399".
_ATU_RANGE = re.compile(r"^(.*?)\s*(\d+)\s*-\s*(\d+)\s*$")


def _atu_num(atu_id: str) -> int | None:
    m = _ATU_NUM.match(atu_id)
    return int(m.group(1)) if m else None


def _atu_sort_key(atu_id: str) -> tuple:
    """(number, suffix) so 313 < 313A < 313A* < 1861."""
    m = _ATU_NUM.match(atu_id)
    return (int(m.group(1)) if m else 1 << 30, atu_id[m.end():] if m else atu_id)


def _split_division(s: str) -> tuple[str, int | None, int | None]:
    """'Supernatural Adversaries 300-399' -> ('Supernatural Adversaries', 300, 399)."""
    m = _ATU_RANGE.match(s or "")
    return (m.group(1).strip(), int(m.group(2)), int(m.group(3))) if m else ((s or "").strip(), None, None)


def _parse_atu(df_rows: list[dict], seq: dict[str, list[str]], combos: dict[str, list[str]]) -> list[dict]:
    types = []
    for row in df_rows:
        atu_id = _clean(row.get("atu_id"))
        if not atu_id:
            continue
        name, start, end = _split_division(_clean(row.get("division")))
        types.append({
            "id": atu_id,
            "num": _atu_num(atu_id),
            "chapter": _clean(row.get("chapter")),
            "division": name,
            "division_range": [start, end] if start is not None else None,
            "name": _clean(row.get("tale_name")),
            "summary": _clean(row.get("tale_type")),
            "motifs": seq.get(atu_id, []),
            "combos": combos.get(atu_id, []),
        })

    # Fill an unlabelled division from the number range that contains the type.
    ranges = {(t["division"], *t["division_range"]) for t in types if t["division_range"]}
    for t in types:
        if t["division"] or t["num"] is None:
            continue
        for nm, s, e in ranges:
            if s <= t["num"] <= e:
                t["division"], t["division_range"] = nm, [s, e]
                break

    # Subtype families: a subtype (313A) hangs off its base number type (313), when
    # that base type exists; the base lists its subtypes (natural-sorted).
    by_id = {t["id"]: t for t in types}
    for t in types:
        base = str(t["num"]) if t["num"] is not None else ""
        t["parent"] = base if base and base != t["id"] and base in by_id else None
        t["subtypes"] = []
    for t in types:
        if t["parent"]:
            by_id[t["parent"]]["subtypes"].append(t["id"])
    for t in types:
        t["subtypes"].sort(key=_atu_sort_key)
    # The atu_df rows aren't globally ordered by number; sort so the sidebar list
    # reads 1 → 2399 (and ascending within a division).
    types.sort(key=lambda t: _atu_sort_key(t["id"]))
    return types


def _atu_divisions(types: list[dict]) -> list[dict]:
    """Division hierarchy, ascending by number range: [{chapter, name, start, end, count}]."""
    counts: collections.Counter = collections.Counter()
    for t in types:
        if t["division_range"]:
            counts[(t["chapter"], t["division"], *t["division_range"])] += 1
    rows = [{"chapter": ch, "name": nm, "start": s, "end": e, "count": c}
            for (ch, nm, s, e), c in counts.items()]
    rows.sort(key=lambda r: r["start"])  # ascending by number range (1 → 2399)
    return rows


def build_tmi(config: dict, *, force: bool = False) -> dict:
    """Download and parse only the Trilogy TMI CSV into the TMI store dict.

    Uses just ``tmi.csv`` — disjoint from the ATU files — so it can be a step of
    its own (the caller logs the step header before invoking it, keeping any TMI
    parse warnings under that header).
    """
    tmi = _finalize_tmi(_parse_tmi(_read_csv(config, "tmi", force=force)))
    return {
        "label": "Thompson",
        "long_label": "Thompson Motif-Index of Folk-Literature",
        "attribution": config.get("attribution", ""),
        "homepage": config.get("homepage", ""),
        "chapters": _tmi_chapters(tmi),
        "culture_legend": build_legend(tmi),
        "motifs": tmi,
    }


def build_atu(config: dict, *, force: bool = False) -> tuple[dict, dict]:
    """Download and parse the Trilogy ATU CSVs into ``(atu store dict, atu_seq)``.

    Uses ``atu_seq``/``atu_combos``/``atu_df`` — disjoint from the TMI file.
    ``atu_seq`` (tale type -> ordered TMI motif codes) feeds the ATU<->TMI walk.
    """
    seq = _parse_atu_seq(_read_csv(config, "atu_seq", force=force))
    combos = _parse_atu_combos(_read_csv(config, "atu_combos", force=force))
    atu = _parse_atu(_read_csv(config, "atu_df", force=force), seq, combos)
    return {
        "label": "ATU tale types",
        "long_label": "Aarne-Thompson-Uther tale-type index",
        "attribution": config.get("attribution", ""),
        "homepage": config.get("homepage", ""),
        "divisions": _atu_divisions(atu),
        "types": atu,
    }, seq


def build(config: dict, *, force: bool = False) -> dict:
    """Download and parse the Trilogy CSVs into TMI + ATU store dicts and the seq map."""
    tmi = build_tmi(config, force=force)
    atu, seq = build_atu(config, force=force)
    return {"tmi": tmi, "atu": atu, "atu_seq": seq}
