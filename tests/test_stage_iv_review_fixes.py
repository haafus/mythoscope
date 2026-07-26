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


_DISABLED = {"berezkin": {"enabled": False}, "trilogy": {"enabled": False}}


def test_build_meta_survives_missing_crosswalk(tmp_path, monkeypatch):
    from motifs.build_motifs import _build_meta

    _motifs_dir(tmp_path, monkeypatch)
    # no crosswalk.json on disk → links == {} inside _build_meta; the read must degrade to zeros,
    # not KeyError (regression: scoped `build motifs:meta` without a built crosswalk stage).
    _build_meta(_DISABLED)
    cw = store.load_meta()["crosswalk"]
    assert cw["atu_to_tmi"] == 0 and cw["linked_tmi_count"] == 0


def test_build_meta_clears_readside_cache(tmp_path, monkeypatch):
    from motifs.build_motifs import _build_meta

    _motifs_dir(tmp_path, monkeypatch)
    store._cache["stale"] = {"old": 1}          # a pre-build memoized read
    _build_meta(_DISABLED)
    assert store._cache == {}                   # terminal stage drops the memoize (in-process build+read)


def test_disabled_source_clears_discovered_sidecar(tmp_path, monkeypatch):
    from motifs.build_motifs import _build_atu, _build_berezkin

    _motifs_dir(tmp_path, monkeypatch)
    for root in ("berezkin", "mapsofmyths", "ashliman"):   # stale sets left by a prior enabled build
        save_json(store.discovered_path(root), ["X"])
    _build_berezkin({"berezkin": {"enabled": False}}, force=False)
    _build_atu({"trilogy": {"enabled": False}}, force=False)
    # a disabled source must clear the sidecars it owns → _discovery_check reads 'not checked',
    # never a stale set frozen at disable time (which would raise a perpetual false discovery-shrank).
    assert not store.discovered_path("berezkin").exists()
    assert not store.discovered_path("mapsofmyths").exists()
    assert not store.discovered_path("ashliman").exists()


def test_mapsofmyths_empty_traditions_degrades_without_clobbering(tmp_path, monkeypatch):
    from motifs.sources import mapsofmyths as mm

    monkeypatch.setattr(settings_mod.settings, "motifs_dir", tmp_path / "motifs")
    (tmp_path / "motifs").mkdir(parents=True)
    monkeypatch.setattr(mm, "fetch_text", lambda *a, **k: "dummy")
    monkeypatch.setattr(mm, "parse_motifs_full",
                        lambda html: {"M1": {"name_eng": "n", "definition_eng": "d", "href": ""}})
    monkeypatch.setattr(mm, "parse_traditions_full", lambda html: {})   # empty parse (upstream shape drift)
    prior = mm.data_dir() / mm.TRADITIONS_FILE
    prior.write_text('{"traditions": {"keep": 1}}', encoding="utf-8")    # a good prior pinned file

    counts = mm.build_enrichment(auth=("u", "p"))                        # creds pass the guard; traditions empty
    # an empty parse must NOT overwrite the prior traditions file, and must mark the build degraded
    # (else _degradation_check treats a half-built source as trusted and advances the high-water)
    assert counts["skipped"] == "traditions-degraded"
    assert prior.read_text(encoding="utf-8") == '{"traditions": {"keep": 1}}'


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
