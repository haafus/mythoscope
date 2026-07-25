"""Regression tests for the Stage IV code-review fixes: motifs stages reap on clean, parallels
never stamps an fp over a missing artifact, and export rejects an unknown scope."""


import pytest

import settings as settings_mod
from json_utils import save_json
from motifs import store


def _motifs_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "motifs_dir", tmp_path / "motifs")
    store.clear_cache()
    (tmp_path / "motifs").mkdir(parents=True)


def test_source_stage_delete_reaps_all_its_sidecars(tmp_path, monkeypatch):
    from pipeline.stages.motifs import TmiSource

    _motifs_dir(tmp_path, monkeypatch)
    # a built-then-orphaned source leaves index + fp + enrichment + discovered on disk
    save_json(store.index_path("tmi"), {"motifs": []})
    (store.motifs_dir() / ".fp.source.tmi").write_text("x", encoding="utf-8")
    save_json(store.enrichment_path("tmi"), {})
    save_json(store.discovered_path("tmi"), [])
    paths = [store.index_path("tmi"), store.motifs_dir() / ".fp.source.tmi",
             store.enrichment_path("tmi"), store.discovered_path("tmi")]
    assert all(p.exists() for p in paths)

    TmiSource().delete({"tmi"})                       # was a silent no-op before the fix
    assert not any(p.exists() for p in paths)


def test_parallels_stage_skips_fp_when_no_artifact(tmp_path, monkeypatch):
    from pipeline.stages import motifs as m

    _motifs_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(m, "_build_parallels", lambda links: {})   # sklearn absent → writes no json
    m.ParallelsStage(m.CrosswalkStage([])).build({"parallels"})
    # no parallels.json ⇒ no .fp.parallels (else actual() stays {} forever → never reconciles)
    assert not (store.motifs_dir() / ".fp.parallels").exists()
    assert not store.parallels_path().exists()


def test_export_rejects_unknown_scope():
    from export_bundle import _components

    with pytest.raises(ValueError, match="not an exportable component"):
        _components(("grpahs",))                       # typo → clean error, not a silent empty bundle
    assert _components(("graphs",))                     # a real family still resolves
    assert len(_components()) == 6                      # no scope → all components


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
