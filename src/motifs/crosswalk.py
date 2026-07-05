"""Cross-index links between the motif indexes.

Two links are built:

- **ATU<->TMI** — every ATU tale type carries an ordered list of the TMI motifs
  that compose it (from Trilogy's ``atu_seq``); we store that mapping and its
  inverse so the UI can jump from a Thompson motif to the tale types that use it.
  Separately, the **defining** motif(s) Uther names at the label (``defining_motifs``)
  give a distinct "this motif defines type X" link — kept apart from the
  constituent one, since the two relationships barely overlap. Two further
  *inline* relations are stored in both directions so an edge shows on both pages:
  a TMI note that cites "Type N" (``atu_inline``, AaTh-resolved) and a TMI motif
  code named in an ATU type's summary prose.
- **Berezkin<->ATU** — many Berezkin catalogue titles cite an ATU tale type
  ("... ATU 328A*"); those references give a direct Berezkin->ATU mapping. A cited
  number that is a pre-2004 (renumbered/merged) type is resolved through the ATU
  ``aliases`` map to the current type.
- **Berezkin<->TMI** — the curated Thompson id each Berezkin motif carries
  (``tmi_refs``, from mapsofmyths); the one *direct* Berezkin<->TMI bridge (the
  rest go through ATU). Present only when the mapsofmyths enrichment ran.

Beyond these direct concordances, a small **inferred** layer completes triangles
transitively — but only through a *low fan-out* pivot (a point-like motif, never a
tale type, which would fan out to all its constituent motifs). Each inferred edge
records the bridge it came through and is kept apart from the direct links.

Berezkin's internal see-also links live on the records themselves.
"""

from __future__ import annotations

import re

# A TMI motif token as it appears in an ATU summary — mirrors the read-side
# ``_SUMMARY_MOTIF`` used to linkify those codes, so the derived inverse map lists
# exactly the motifs the summary renders as links.
_SUMMARY_MOTIF = re.compile(r"\b[A-Z]\d[A-Za-z0-9]*(?:\.\d+)*")

# Transitive closure: a triangle is completed only through a *low fan-out* pivot
# (a vertex whose edge into the target index reaches at most this many nodes). A
# tale-type node fans out to all its constituent motifs, so closing through it
# would flood the graph; a point-like motif does not. ``2`` keeps ~1:1 bridges.
INFER_FANOUT_CAP = 2


def _clean_tmi(ref: str) -> str:
    """Normalise a mapsofmyths Thompson id (``*A2211.1``, ``A1313.3.1.``)."""
    return ref.lstrip("*").rstrip(".").strip()


def _invert(forward: dict[str, list[str]]) -> dict[str, list[str]]:
    inv: dict[str, list[str]] = {}
    for key, vals in forward.items():
        for v in vals:
            inv.setdefault(v, [])
            if key not in inv[v]:
                inv[v].append(key)
    return inv


def build(
    atu_seq: dict[str, list[str]],
    tmi_ids: set[str],
    berezkin_motifs: list[dict] | None = None,
    atu_ids: set[str] | None = None,
    atu_defining: dict[str, list[str]] | None = None,
    aliases: dict[str, str] | None = None,
    tmi_notes: dict[str, list[str]] | None = None,
    aath_to_atu: dict[str, list[str]] | None = None,
    atu_summaries: dict[str, str] | None = None,
) -> dict:
    """Return the cross-walk maps from the ATU sequences and Berezkin refs."""
    atu_ids = atu_ids or set()
    atu_to_tmi = {atu_id: motifs for atu_id, motifs in atu_seq.items() if motifs}
    tmi_to_atu = _invert(atu_to_tmi)

    # ATU <-> TMI via the *defining* motif(s), kept separate from the constituent
    # link above; only codes that exist in the TMI index are linked.
    atu_to_tmi_defining = {
        a: kept for a, codes in (atu_defining or {}).items()
        if (kept := [c for c in codes if c in tmi_ids])
    }
    tmi_to_atu_defining = _invert(atu_to_tmi_defining)

    # ATU <-> TMI via the two *inline* free-text relations, each kept separate and
    # stored in both directions so the edge shows on both indexes' pages:
    #  * a TMI note that cites "Type N" (``atu_inline``) -> the ATU type(s) it names
    #    (AaTh numbers, so resolved straight through or via the AaTh->ATU concordance;
    #    orphan numbers with no ATU 2004 type produce no edge);
    #  * a TMI motif code named in an ATU type's summary prose.
    tmi_to_atu_note: dict[str, list[str]] = {}
    for tmi_id, refs in (tmi_notes or {}).items():
        landed: list[str] = []
        for ref in refs:
            targets = [ref] if ref in atu_ids else (aath_to_atu or {}).get(ref, [])
            for a in targets:
                if a not in landed:
                    landed.append(a)
        if landed:
            tmi_to_atu_note[tmi_id] = landed
    atu_to_tmi_note = _invert(tmi_to_atu_note)

    atu_to_tmi_summary: dict[str, list[str]] = {}
    for atu_id, summary in (atu_summaries or {}).items():
        codes: list[str] = []
        for tok in _SUMMARY_MOTIF.findall(summary):
            code = tok if tok in tmi_ids else tok.rstrip("f")  # "J21ff" -> base "J21"
            if code in tmi_ids and code not in codes:
                codes.append(code)
        if codes:
            atu_to_tmi_summary[atu_id] = codes
    tmi_to_atu_summary = _invert(atu_to_tmi_summary)

    # Berezkin <-> ATU from the "ATU NNN" references embedded in titles. Each cited
    # ref is resolved to a current id (a known id, an old number via `aliases`, or
    # its non-starred form) and BOTH directions are built from that same resolved
    # edge, so the two maps are exact inverses. The verbatim citation stays on the
    # motif record (`atu_refs`).
    aliases = aliases or {}

    def _resolve_atu(ref: str) -> str:
        return (ref if ref in atu_ids
                else aliases.get(ref) or aliases.get(ref.rstrip("*")) or ref.rstrip("*"))

    berezkin_to_atu: dict[str, list[str]] = {}
    atu_to_berezkin: dict[str, list[str]] = {}
    for motif in berezkin_motifs or []:
        resolved_refs: list[str] = []
        for ref in motif.get("atu_refs") or []:
            r = _resolve_atu(ref)
            if r not in resolved_refs:
                resolved_refs.append(r)
        if not resolved_refs:
            continue
        berezkin_to_atu[motif["id"]] = resolved_refs
        for r in resolved_refs:
            atu_to_berezkin.setdefault(r, [])
            if motif["id"] not in atu_to_berezkin[r]:
                atu_to_berezkin[r].append(motif["id"])

    # Berezkin -> TMI, direct: the curated Thompson ids on each motif (mapsofmyths
    # `tmi_refs`), plus the inverse — kept only when the id exists in our TMI index.
    berezkin_to_tmi: dict[str, list[str]] = {}
    tmi_to_berezkin: dict[str, list[str]] = {}
    for motif in berezkin_motifs or []:
        refs = [r for r in (_clean_tmi(x) for x in (motif.get("tmi_refs") or [])) if r in tmi_ids]
        if not refs:
            continue
        berezkin_to_tmi[motif["id"]] = refs
        for ref in refs:
            tmi_to_berezkin.setdefault(ref, [])
            if motif["id"] not in tmi_to_berezkin[ref]:
                tmi_to_berezkin[ref].append(motif["id"])

    # --- Transitive closure (inferred links) -------------------------------
    # Complete triangles only through a low-fan-out pivot (see INFER_FANOUT_CAP):
    #   A: ATU<->TMI via a Berezkin motif that concords to both;
    #   D: Berezkin<->ATU via a TMI motif that defines/constitutes few types;
    #   C: Berezkin<->TMI via an ATU type's (near-1:1) defining motif.
    # Each inferred edge keeps its bridge (provenance) and is stored both ways,
    # kept apart from the direct concordances above.
    bz_atu_resolved: dict[str, set[str]] = {}
    for a, bs in atu_to_berezkin.items():
        for b in bs:
            bz_atu_resolved.setdefault(b, set()).add(a)
    direct_atu_tmi = {(a, m) for src in (atu_to_tmi, atu_to_tmi_defining,
                                         atu_to_tmi_note, atu_to_tmi_summary)
                      for a, ms in src.items() for m in ms}
    direct_bz_tmi = {(b, m) for b, ms in berezkin_to_tmi.items() for m in ms}
    direct_bz_atu = {(b, a) for b, aset in bz_atu_resolved.items() for a in aset}

    inferred: dict[str, dict[str, list]] = {"berezkin": {}, "tmi": {}, "atu": {}}
    _seen: set[tuple] = set()

    def _infer(ia: str, a: str, ib: str, b: str, via_i: str, via: str) -> None:
        key = tuple(sorted(((ia, a), (ib, b))))
        if key in _seen:
            return
        _seen.add(key)
        inferred[ia].setdefault(a, []).append({"index": ib, "id": b, "via_index": via_i, "via_id": via})
        inferred[ib].setdefault(b, []).append({"index": ia, "id": a, "via_index": via_i, "via_id": via})

    cap = INFER_FANOUT_CAP
    # A: ATU <-> TMI, bridged by a Berezkin motif narrow on both sides
    for b, tmis in berezkin_to_tmi.items():
        atus = bz_atu_resolved.get(b, ())
        if len(tmis) > cap or len(atus) > cap:
            continue
        for m in tmis:
            for a in atus:
                if (a, m) not in direct_atu_tmi:
                    _infer("atu", a, "tmi", m, "berezkin", b)
    # D: Berezkin <-> ATU, bridged by a TMI motif that belongs to few types
    for b, tmis in berezkin_to_tmi.items():
        for m in tmis:
            types = tmi_to_atu.get(m, ())
            if not types or len(types) > cap:
                continue
            for a in types:
                if (b, a) not in direct_bz_atu:
                    _infer("berezkin", b, "atu", a, "tmi", m)
    # C: Berezkin <-> TMI, bridged by an ATU type's defining motif(s)
    for b, atus in bz_atu_resolved.items():
        for a in atus:
            defs = atu_to_tmi_defining.get(a, ())
            if not defs or len(defs) > cap:
                continue
            for m in defs:
                if (b, m) not in direct_bz_tmi:
                    _infer("berezkin", b, "tmi", m, "atu", a)
    for byid in inferred.values():
        for lst in byid.values():
            lst.sort(key=lambda e: (e["index"], e["id"]))

    known = sorted(code for code in tmi_to_atu if code in tmi_ids)

    return {
        "atu_to_tmi": atu_to_tmi,
        "tmi_to_atu": {k: sorted(v) for k, v in tmi_to_atu.items()},
        "atu_to_tmi_defining": atu_to_tmi_defining,
        "tmi_to_atu_defining": {k: sorted(v) for k, v in tmi_to_atu_defining.items()},
        "tmi_to_atu_note": {k: sorted(v) for k, v in tmi_to_atu_note.items()},
        "atu_to_tmi_note": {k: sorted(v) for k, v in atu_to_tmi_note.items()},
        "atu_to_tmi_summary": {k: sorted(v) for k, v in atu_to_tmi_summary.items()},
        "tmi_to_atu_summary": {k: sorted(v) for k, v in tmi_to_atu_summary.items()},
        "berezkin_to_atu": berezkin_to_atu,
        "atu_to_berezkin": {k: sorted(v) for k, v in atu_to_berezkin.items()},
        "berezkin_to_tmi": berezkin_to_tmi,
        "tmi_to_berezkin": {k: sorted(v) for k, v in tmi_to_berezkin.items()},
        "inferred": inferred,
        "inferred_count": len(_seen),
        "linked_tmi_count": len(known),
    }
