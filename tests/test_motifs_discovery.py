"""The discovery-shrank guard (Stage I Phase 3 item 8): a parse-root that drops links it used to
list is flagged even though the build stays full off pinned copies; growth just extends the mark,
a skipped root is carried, and the union keeps every link ever seen so the flag self-clears."""

import json

import settings as settings_mod
from json_utils import save_json
from motifs import build_motifs as bm
from motifs import store


def _setup(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "motifs_dir", tmp_path)
    store.clear_cache()


def _union():
    return json.loads(store.discovery_union_path().read_text())


def test_first_run_seeds_union_no_flag(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    save_json(store.discovered_path("berezkin"), ["a", "b", "c"])
    assert bm._discovery_check({}, "T1") == []            # nothing prior → no shrink
    assert _union()["berezkin"] == ["a", "b", "c"]


def test_shrink_flags_and_keeps_dropped_in_union(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    save_json(store.discovery_union_path(), {"berezkin": ["a", "b", "c"]})
    save_json(store.discovered_path("berezkin"), ["a", "b"])     # 'c' vanished from the root
    flags = bm._discovery_check({}, "T2")
    assert [f["kind"] for f in flags] == ["discovery-shrank"]
    assert flags[0]["source"] == "berezkin" and "1 link" in flags[0]["detail"]
    assert _union()["berezkin"] == ["a", "b", "c"]       # dropped link stays in the union


def test_growth_extends_union_no_flag(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    save_json(store.discovery_union_path(), {"berezkin": ["a", "b"]})
    save_json(store.discovered_path("berezkin"), ["a", "b", "c", "d"])
    assert bm._discovery_check({}, "T3") == []            # only grew → no flag
    assert _union()["berezkin"] == ["a", "b", "c", "d"]


def test_skipped_root_carried_not_flagged(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    save_json(store.discovery_union_path(), {"mapsofmyths": ["x", "y"]})
    # no .discovered.mapsofmyths.json → source skipped this build (creds absent), not a shrink
    assert bm._discovery_check({}, "T4") == []
    assert _union()["mapsofmyths"] == ["x", "y"]          # union carried untouched


def test_first_seen_carried_then_auto_clears_on_recovery(tmp_path, monkeypatch):
    _setup(tmp_path, monkeypatch)
    save_json(store.discovery_union_path(), {"ashliman": ["a", "b", "c"]})
    save_json(store.discovered_path("ashliman"), ["a"])          # b, c dropped
    prior = {"flags": [{"kind": "discovery-shrank", "key": "ashliman", "first_seen": "T0"}]}
    flags = bm._discovery_check(prior, "T5")
    assert flags[0]["first_seen"] == "T0"                # a persisting flag keeps its first_seen
    save_json(store.discovered_path("ashliman"), ["a", "b", "c"])   # root re-lists them
    assert bm._discovery_check(prior, "T6") == []        # recovered → clears against the union
