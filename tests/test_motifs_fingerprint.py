"""Motifs coarse input fingerprint + the MotifsStage gate over it: stable when raw+config are
unchanged, stale when either changes, missing until built."""

import settings as settings_mod
from motifs.fingerprint import motifs_fingerprint, source_fingerprint
from motifs.store import META_FILE
from pipeline import plan
from pipeline.stages import MotifsStage


def _tree(tmp_path, monkeypatch, *, raw=b"page", cfg=b"{}"):
    monkeypatch.setattr(settings_mod.settings, "motifs_dir", tmp_path / "motifs")
    monkeypatch.setattr(settings_mod.settings, "config_dir", tmp_path / "config")
    (tmp_path / "config").mkdir(parents=True)
    (tmp_path / "config" / "motifs.json").write_bytes(cfg)
    (tmp_path / "motifs" / "raw").mkdir(parents=True)
    (tmp_path / "motifs" / "raw" / "a.html").write_bytes(raw)


def test_fingerprint_stable_and_input_sensitive(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    fp = motifs_fingerprint()
    assert fp == motifs_fingerprint()                                  # stable
    (tmp_path / "motifs" / "raw" / "a.html").write_bytes(b"page EDIT")  # raw changed
    assert motifs_fingerprint() != fp
    (tmp_path / "config" / "motifs.json").write_bytes(b'{"x":1}')       # config changed
    assert motifs_fingerprint() != fp


def _mark_built(tmp_path, fp):
    (tmp_path / "motifs" / META_FILE).write_text("{}", encoding="utf-8")
    (tmp_path / "motifs" / ".fp").write_text(fp, encoding="utf-8")


def test_clean_when_fp_matches(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    _mark_built(tmp_path, motifs_fingerprint())
    assert plan(MotifsStage()).clean


def test_missing_until_built(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    assert plan(MotifsStage()).missing == {"motifs"}


def test_stale_when_inputs_change(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    _mark_built(tmp_path, motifs_fingerprint())
    (tmp_path / "motifs" / "raw" / "a.html").write_bytes(b"refetched")  # a refresh changed raw
    assert plan(MotifsStage()).stale == {"motifs"}


# --- per-source fingerprints (atomisation task 4) -------------------------------------------

def _source_tree(tmp_path, monkeypatch, cfg=b"{}"):
    monkeypatch.setattr(settings_mod.settings, "motifs_dir", tmp_path / "motifs")
    monkeypatch.setattr(settings_mod.settings, "config_dir", tmp_path / "config")
    (tmp_path / "config").mkdir(parents=True)
    (tmp_path / "config" / "motifs.json").write_bytes(cfg)
    raw = tmp_path / "motifs" / "raw"
    files = {
        "berezkin/b.html": b"bz", "mapsofmyths/m.html": b"mm",           # berezkin
        "trilogy/tmi.csv": b"tmi", "mellmann/x.csv": b"mel",             # tmi
        "folkmasa_bibliography.html": b"folk",                           # tmi
        "trilogy/atu_seq.csv": b"atu", "wikidata/w.json": b"wd", "ashliman/a.html": b"ash",  # atu
    }
    for rel, data in files.items():
        p = raw / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return raw


def test_source_fp_stable(tmp_path, monkeypatch):
    _source_tree(tmp_path, monkeypatch)
    for s in ("berezkin", "tmi", "atu"):
        assert source_fingerprint(s) == source_fingerprint(s)


def test_source_fp_isolated_from_other_sources(tmp_path, monkeypatch):
    # The whole point of partitioning: a change under ATU's raw moves ATU's fp, not the others'.
    raw = _source_tree(tmp_path, monkeypatch)
    bz, tmi, atu = (source_fingerprint(s) for s in ("berezkin", "tmi", "atu"))
    (raw / "trilogy" / "atu_seq.csv").write_bytes(b"atu EDIT")
    assert source_fingerprint("atu") != atu
    assert source_fingerprint("berezkin") == bz
    assert source_fingerprint("tmi") == tmi


def test_source_fp_sensitive_to_own_raw(tmp_path, monkeypatch):
    raw = _source_tree(tmp_path, monkeypatch)
    bz = source_fingerprint("berezkin")
    (raw / "mapsofmyths" / "m.html").write_bytes(b"mm EDIT")  # berezkin's enrichment raw
    assert source_fingerprint("berezkin") != bz


def test_source_fp_config_sensitive(tmp_path, monkeypatch):
    _source_tree(tmp_path, monkeypatch)
    before = source_fingerprint("tmi")
    (tmp_path / "config" / "motifs.json").write_bytes(b'{"x":1}')
    assert source_fingerprint("tmi") != before
