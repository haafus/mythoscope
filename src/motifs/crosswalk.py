"""Cross-index links between the motif indexes.

Two links are built:

- **ATU<->TMI** — every ATU tale type carries an ordered list of the TMI motifs
  that compose it (from Trilogy's ``atu_seq``); we store that mapping and its
  inverse so the UI can jump from a Thompson motif to the tale types that use it.
- **Berezkin<->ATU** — many Berezkin catalogue titles cite an ATU tale type
  ("... ATU 328A*"); those references give a direct Berezkin->ATU mapping.

Berezkin<->TMI is intentionally absent: the catalogue does not embed systematic
Thompson codes, so that mapping would need Berezkin's published concordance and
is left as future work. Berezkin's internal see-also links live on the records.
"""

from __future__ import annotations


def build(
    atu_seq: dict[str, list[str]],
    tmi_ids: set[str],
    berezkin_motifs: list[dict] | None = None,
    atu_ids: set[str] | None = None,
) -> dict:
    """Return the cross-walk maps from the ATU sequences and Berezkin refs."""
    atu_to_tmi = {atu_id: motifs for atu_id, motifs in atu_seq.items() if motifs}

    tmi_to_atu: dict[str, list[str]] = {}
    for atu_id, motifs in atu_to_tmi.items():
        for motif in motifs:
            tmi_to_atu.setdefault(motif, [])
            if atu_id not in tmi_to_atu[motif]:
                tmi_to_atu[motif].append(atu_id)

    # Berezkin -> ATU from the "ATU NNN" references embedded in titles, plus the
    # inverse. A ref resolves if it (or its non-starred form) is a known ATU id.
    atu_ids = atu_ids or set()
    berezkin_to_atu: dict[str, list[str]] = {}
    atu_to_berezkin: dict[str, list[str]] = {}
    for motif in berezkin_motifs or []:
        refs = motif.get("atu_refs") or []
        if not refs:
            continue
        berezkin_to_atu[motif["id"]] = refs
        for ref in refs:
            resolved = ref if ref in atu_ids else ref.rstrip("*")
            atu_to_berezkin.setdefault(resolved, [])
            if motif["id"] not in atu_to_berezkin[resolved]:
                atu_to_berezkin[resolved].append(motif["id"])

    known = sorted(code for code in tmi_to_atu if code in tmi_ids)

    return {
        "atu_to_tmi": atu_to_tmi,
        "tmi_to_atu": {k: sorted(v) for k, v in tmi_to_atu.items()},
        "berezkin_to_atu": berezkin_to_atu,
        "atu_to_berezkin": {k: sorted(v) for k, v in atu_to_berezkin.items()},
        "linked_tmi_count": len(known),
    }
