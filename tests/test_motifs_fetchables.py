"""Each source stage composes its own fetchables from the modules it owns (self-contained
refresh): the URL rules live in the source modules, the stage just aggregates them. Verifies the
tail rule, the shared trilogy CSV split, ``.absent`` skipping, and per-source coverage."""

import json

import settings as settings_mod
from motifs.sources import ashliman, atu_wikidata, berezkin_bibliography, bibliography
from pipeline.stages.motifs import AtuSource, BerezkinSource, TmiSource

CONFIG = {
    "berezkin": {"enabled": True, "base_url": "http://areasofmyths.com", "index_page": "index-left.html"},
    "trilogy": {"enabled": True, "base_url": "https://tr.example/data",
                "files": {"tmi": "tmi.csv", "atu_df": "atu_df.csv", "atu_seq": "atu_seq.csv",
                          "atu_combos": "atu_combos.csv"}},
    "mellmann": {"enabled": True, "base_url": "https://mel.example", "files": {"tmi": "tmi.csv"}},
}


def _tree(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "motifs_dir", tmp_path / "motifs")
    monkeypatch.setattr(settings_mod.settings, "config_dir", tmp_path / "config")
    (tmp_path / "config").mkdir(parents=True)
    (tmp_path / "config" / "motifs.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    raw = tmp_path / "motifs" / "raw"
    for rel in ["berezkin/index-left.html", "berezkin/k103.html", "berezkin/biblio.html",
                "trilogy/tmi.csv", "trilogy/atu_df.csv", "trilogy/atu_seq.csv", "trilogy/atu_combos.csv",
                "mellmann/tmi.csv", "folkmasa_bibliography.html",
                "ashliman/type0300.html", "ashliman/type9999.html.absent", "wikidata/atu.json"]:
        p = raw / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    # mapsofmyths: no motifs_full pinned → only the two listing pages are enumerated (nodes/markers
    # are discovered from pinned state, absent here) — keeps this unit test off the parse path.
    return raw


def _urls(fetchables):
    return {f.title: f.url for f in fetchables}


def test_berezkin_owns_areal_pages_plus_mapsofmyths_and_bibliography(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    monkeypatch.setenv("MAPSOFMYTHS_AUTH", "user:pass")    # mapsofmyths folds in only under credentials
    urls = _urls(BerezkinSource().fetchables())
    assert urls["berezkin/index-left.html"] == "http://areasofmyths.com/index-left.html"
    assert urls["berezkin/k103.html"] == "http://areasofmyths.com/k103.html"
    assert urls["berezkin/biblio.html"] == f"{berezkin_bibliography.BASE}/biblio.html"
    assert "mapsofmyths/motifs_full.html" in urls          # enrichment folded into berezkin


def test_tmi_owns_trilogy_tmi_mellmann_folkmasa(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    urls = _urls(TmiSource().fetchables())
    assert urls["trilogy/tmi.csv"] == "https://tr.example/data/tmi.csv"
    assert urls["mellmann/tmi.csv"] == "https://mel.example/tmi.csv"
    assert urls["folkmasa_bibliography.html"] == bibliography.SOURCE_URL
    assert not any("atu_" in t for t in urls)              # ATU CSVs belong to the atu source


def test_atu_owns_atu_csvs_wikidata_ashliman(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    urls = _urls(AtuSource().fetchables())
    assert urls["trilogy/atu_df.csv"] == "https://tr.example/data/atu_df.csv"
    assert urls["wikidata/atu.json"] == atu_wikidata.query_url()
    assert urls["ashliman/type0300.html"] == f"{ashliman.BASE}/type0300.html"
    assert "trilogy/tmi.csv" not in urls                   # TMI CSV belongs to the tmi source
    assert not any(t.endswith(".absent") for t in urls)    # known-404 markers skipped


def test_every_pinned_file_is_covered_once_across_sources(tmp_path, monkeypatch):
    raw = _tree(tmp_path, monkeypatch)
    pinned = {p for p in raw.rglob("*") if p.is_file() and not p.name.endswith(".absent")}
    enumerated = [f.cache_file for s in (BerezkinSource(), TmiSource(), AtuSource()) for f in s.fetchables()]
    # every pinned raw file is claimed by exactly one source (mapsofmyths listing pages are
    # unconditional, so drop them — they have no pinned file in this synthetic tree)
    enumerated_pinned = [c for c in enumerated if c in pinned]
    assert set(enumerated_pinned) == pinned
    assert len(enumerated_pinned) == len(pinned)           # no double-claim


# --- #3 validators + #4 mapsofmyths credential gate ------------------------------------------

def test_content_validators():
    from motifs.sources.fetch import valid_csv, valid_html, valid_json

    assert valid_html(b"<html><body>x</body></html>")
    assert not valid_html(b"") and not valid_html(b"not found: plain error, no markup")

    assert valid_csv(b"a,b,c\n1,2,3\n")
    assert not valid_csv(b"<!DOCTYPE html><html>error</html>")   # CSV url returned HTML
    assert not valid_csv(b"a,b,c\n") and not valid_csv(b"")      # header only / empty

    assert valid_json(b'{"markers": []}')
    assert not valid_json(b"<html>oops</html>")


def test_fetchables_carry_typed_validators(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    from motifs.sources.fetch import valid_csv, valid_html
    tmi = {f.title: f.validate for f in TmiSource().fetchables()}
    assert tmi["trilogy/tmi.csv"] is valid_csv and tmi["mellmann/tmi.csv"] is valid_csv
    assert tmi["folkmasa_bibliography.html"] is valid_html
    berezkin = {f.title: f.validate for f in BerezkinSource().fetchables()}
    assert berezkin["berezkin/k103.html"] is valid_html


def test_mapsofmyths_skipped_without_credentials(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    monkeypatch.delenv("MAPSOFMYTHS_AUTH", raising=False)
    # its enrichment is credential-gated → no fetchables enter berezkin's refresh (no false degradeds)
    assert not any(f.title.startswith("mapsofmyths/") for f in BerezkinSource().fetchables())


def test_mapsofmyths_locator_scheme(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    from motifs.sources import mapsofmyths as mm
    url, cache = mm._locator("/motifs_full", "motifs_full.html")
    assert url == f"{mm.BASE}/motifs_full"
    assert cache == tmp_path / "motifs" / "raw" / "mapsofmyths" / "motifs_full.html"
    assert mm._locator("http://x/node/5", "node_5.html")[0] == "http://x/node/5"   # absolute href as-is
    assert mm._locator("/node/5", "node_5.html")[0] == f"{mm.BASE}/node/5"          # relative → BASE


def test_mapsofmyths_nodes_and_markers_via_locator(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    monkeypatch.setenv("MAPSOFMYTHS_AUTH", "u:p")
    from motifs.sources import mapsofmyths as mm
    root = tmp_path / "motifs" / "raw" / "mapsofmyths"
    root.mkdir(parents=True)
    (root / "motifs_full.html").write_text("x")                    # presence triggers node discovery
    monkeypatch.setattr(mm, "parse_motifs_full", lambda h: {"A1": {"href": "/node/5"}})
    (root / "markers").mkdir()
    (root / "markers" / "markers_5.json").write_text("[]")
    fs = {f.title: f for f in mm.fetchables()}
    # node URL + cache come from the shared _locator (same the build fetch uses)
    assert fs["mapsofmyths/node_5.html"].url == f"{mm.BASE}/node/5"
    assert fs["mapsofmyths/node_5.html"].cache_file == root / "node_5.html"
    assert fs["mapsofmyths/markers/markers_5.json"].fetch is not None   # POST override survives


def test_mapsofmyths_enumerated_with_credentials(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    monkeypatch.setenv("MAPSOFMYTHS_AUTH", "user:pass")
    from motifs.sources import mapsofmyths
    from motifs.sources.fetch import valid_html
    fs = mapsofmyths.fetchables()                          # listing pages always enumerated under auth
    titles = {f.title for f in fs}
    assert "mapsofmyths/motifs_full.html" in titles and "mapsofmyths/traditions_full.html" in titles
    assert all(f.auth == ("user", "pass") for f in fs)
    assert next(f for f in fs if f.title.endswith("motifs_full.html")).validate is valid_html
