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

Berezkin's internal see-also links live on the records themselves.
"""

from __future__ import annotations

import re

# A TMI motif token as it appears in an ATU summary — mirrors the read-side
# ``_SUMMARY_MOTIF`` used to linkify those codes, so the derived inverse map lists
# exactly the motifs the summary renders as links.
_SUMMARY_MOTIF = re.compile(r"\b[A-Z]\d[A-Za-z0-9]*(?:\.\d+)*")


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

    # Berezkin -> ATU from the "ATU NNN" references embedded in titles, plus the
    # inverse. A ref resolves to a known id, an old number via `aliases`, or its
    # non-starred form.
    aliases = aliases or {}
    berezkin_to_atu: dict[str, list[str]] = {}
    atu_to_berezkin: dict[str, list[str]] = {}
    for motif in berezkin_motifs or []:
        refs = motif.get("atu_refs") or []
        if not refs:
            continue
        berezkin_to_atu[motif["id"]] = refs
        for ref in refs:
            resolved = (ref if ref in atu_ids
                        else aliases.get(ref) or aliases.get(ref.rstrip("*")) or ref.rstrip("*"))
            atu_to_berezkin.setdefault(resolved, [])
            if motif["id"] not in atu_to_berezkin[resolved]:
                atu_to_berezkin[resolved].append(motif["id"])

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
        "linked_tmi_count": len(known),
    }
