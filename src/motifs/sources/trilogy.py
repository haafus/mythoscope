"""Trilogy dataset (j-hagedorn/trilogy): TMI + ATU as tidy CSVs.

We pull four files: ``tmi`` (Thompson motifs with parsed hierarchy), ``atu_df``
(tale types), ``atu_seq`` (the ordered TMI motifs that make up each tale type —
the bridge that powers the ATU<->TMI cross-walk) and ``atu_combos`` (tale types
commonly told together).
"""

from __future__ import annotations

import csv
import io
import logging
import re
from pathlib import Path

from settings import settings

from .fetch import fetch_to_cache

logger = logging.getLogger(__name__)

# TMI ``notes`` cells (long bibliographies) blow past the default 128 KB cell cap.
csv.field_size_limit(16 * 1024 * 1024)

_NA = {"", "NA", "N/A", "na"}


def _clean(value: str | None) -> str:
    value = (value or "").strip()
    return "" if value in _NA else value


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
        motifs.append({
            "id": code,
            "chapter": _clean(row.get("chapter_id")) or code[:1],
            "chapter_name": _clean(row.get("chapter_name")),
            "name": _clean(row.get("motif_name")),
            "notes": _clean(row.get("notes")),
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


def _parse_atu(df_rows: list[dict], seq: dict[str, list[str]], combos: dict[str, list[str]]) -> list[dict]:
    types = []
    for row in df_rows:
        atu_id = _clean(row.get("atu_id"))
        if not atu_id:
            continue
        types.append({
            "id": atu_id,
            "chapter": _clean(row.get("chapter")),
            "division": _clean(row.get("division")),
            "name": _clean(row.get("tale_name")),
            "summary": _clean(row.get("tale_type")),
            "motifs": seq.get(atu_id, []),
            "combos": combos.get(atu_id, []),
        })
    return types


def build(config: dict, *, force: bool = False) -> dict:
    """Download and parse the Trilogy CSVs into TMI + ATU store dicts and the seq map."""
    tmi_rows = _read_csv(config, "tmi", force=force)
    tmi = _parse_tmi(tmi_rows)
    # Hierarchical order so the list shows broader motifs before their narrower
    # children (A1 before A1.4) instead of raw CSV order.
    tmi.sort(key=lambda m: tmi_sort_key(m["id"]))
    logger.info("Trilogy: parsed %d TMI motifs", len(tmi))

    seq = _parse_atu_seq(_read_csv(config, "atu_seq", force=force))
    combos = _parse_atu_combos(_read_csv(config, "atu_combos", force=force))
    atu = _parse_atu(_read_csv(config, "atu_df", force=force), seq, combos)
    logger.info("Trilogy: parsed %d ATU tale types (%d with motif sequences)", len(atu), len(seq))

    attribution = config.get("attribution", "")
    homepage = config.get("homepage", "")
    return {
        "tmi": {
            "label": "Thompson (TMI)",
            "long_label": "Thompson Motif-Index of Folk-Literature",
            "attribution": attribution,
            "homepage": homepage,
            "chapters": _tmi_chapters(tmi),
            "motifs": tmi,
        },
        "atu": {
            "label": "ATU tale types",
            "long_label": "Aarne-Thompson-Uther tale-type index",
            "attribution": attribution,
            "homepage": homepage,
            "types": atu,
        },
        "atu_seq": seq,
    }
