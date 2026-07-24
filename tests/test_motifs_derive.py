"""motifs.derive re-projects the structures crosswalk/parallels need from the stored indexes —
the single source of truth for splitting those into their own stages."""

from motifs.derive import derived_from_indexes, load_indexes

BEREZKIN = {"motifs": [{"id": "B1"}, {"id": "B2"}]}
TMI = {
    "motifs": [{"id": "A0", "atu_inline": ["Type 1"]}, {"id": "A1"}],
    "aliases": {"oldA": "A0"},
}
ATU = {
    "types": [
        {"id": "T1", "defining_motifs": ["A0"], "summary": "s", "concordances": {"AaTh": ["100"]}},
        {"id": "T2"},
    ],
    "aliases": {"oldT": "T1"},
    "atu_seq": {"T1": ["A0", "A1"]},
}


def test_reprojects_every_structure():
    d = derived_from_indexes(BEREZKIN, TMI, ATU)
    assert d["berezkin_motifs"] == BEREZKIN["motifs"]
    assert d["tmi_motifs"] == TMI["motifs"]
    assert d["atu_types"] == ATU["types"]
    assert d["tmi_ids"] == {"A0", "A1"}
    assert d["tmi_notes"] == {"A0": ["Type 1"]}
    assert d["tmi_aliases"] == {"oldA": "A0"}
    assert d["atu_ids"] == {"T1", "T2"}
    assert d["atu_defining"] == {"T1": ["A0"]}
    assert d["atu_summaries"] == {"T1": "s"}
    assert d["atu_aliases"] == {"oldT": "T1"}
    assert d["aath_to_atu"] == {"100": ["T1"]}
    assert d["atu_seq"] == {"T1": ["A0", "A1"]}


def test_atu_seq_empty_when_index_predates_it():
    d = derived_from_indexes(BEREZKIN, TMI, {"types": ATU["types"]})  # no atu_seq key
    assert d["atu_seq"] == {}


def test_load_indexes_dispatches_by_name():
    idx = {"berezkin": BEREZKIN, "tmi": TMI, "atu": ATU}
    d = load_indexes(loader=idx.__getitem__)
    assert d["atu_ids"] == {"T1", "T2"} and d["atu_seq"] == {"T1": ["A0", "A1"]}
