"""Per-source offline fingerprints — the atomised motifs staleness keys: stable when a source's
own raw+config are unchanged, isolated so one source's change never moves another's."""

import settings as settings_mod
from motifs.fingerprint import source_fingerprint


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
