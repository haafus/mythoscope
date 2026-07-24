"""Motifs coarse input fingerprint + the MotifsStage gate over it: stable when raw+config are
unchanged, stale when either changes, missing until built."""

import settings as settings_mod
from motifs.fingerprint import motifs_fingerprint
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
