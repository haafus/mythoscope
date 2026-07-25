"""Fetchable enumeration: each source maps its pinned raw tree back to upstream URLs by the
tail rule, splits the shared trilogy CSVs correctly, and skips ``.absent`` markers."""

import json

import settings as settings_mod
from motifs.fetchables import source_fetchables
from motifs.sources import ashliman, atu_wikidata, berezkin_bibliography, bibliography

CONFIG = {
    "berezkin": {"base_url": "http://areasofmyths.com", "index_page": "index-left.html"},
    "trilogy": {"base_url": "https://tr.example/data",
                "files": {"tmi": "tmi.csv", "atu_df": "atu_df.csv", "atu_seq": "atu_seq.csv",
                          "atu_combos": "atu_combos.csv"}},
    "mellmann": {"base_url": "https://mel.example"},
}


def _tree(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "motifs_dir", tmp_path / "motifs")
    monkeypatch.setattr(settings_mod.settings, "config_dir", tmp_path / "config")
    (tmp_path / "config").mkdir(parents=True)
    (tmp_path / "config" / "motifs.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    raw = tmp_path / "motifs" / "raw"
    files = [
        "berezkin/index-left.html", "berezkin/k103.html", "berezkin/biblio.html",   # base + enrichment
        "trilogy/tmi.csv", "trilogy/atu_df.csv", "trilogy/atu_seq.csv", "trilogy/atu_combos.csv",
        "mellmann/tmi.csv", "folkmasa_bibliography.html",
        "ashliman/type0300.html", "ashliman/type0301.html", "ashliman/type9999.html.absent",
        "wikidata/atu.json",
    ]
    for rel in files:
        p = raw / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(b"x")
    return raw


def _by_title(fetchables):
    return {f.title: f.url for f in fetchables}


def test_berezkin_base_and_bibliography(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    urls = _by_title(source_fetchables("berezkin"))
    assert urls["berezkin/index-left.html"] == "http://areasofmyths.com/index-left.html"
    assert urls["berezkin/k103.html"] == "http://areasofmyths.com/k103.html"
    # biblio.html is berezkin_bibliography's, not the areal scrape's tail
    assert urls["berezkin/biblio.html"] == f"{berezkin_bibliography.BASE}/biblio.html"


def test_tmi_splits_trilogy_and_adds_mellmann_folkmasa(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    urls = _by_title(source_fetchables("tmi"))
    assert urls["trilogy/tmi.csv"] == "https://tr.example/data/tmi.csv"
    assert urls["mellmann/tmi.csv"] == "https://mel.example/tmi.csv"
    assert urls["folkmasa_bibliography.html"] == bibliography.SOURCE_URL
    assert not any("atu_" in t for t in urls)                       # ATU CSVs belong to the atu source


def test_atu_takes_atu_csvs_ashliman_wikidata(tmp_path, monkeypatch):
    _tree(tmp_path, monkeypatch)
    urls = _by_title(source_fetchables("atu"))
    assert urls["trilogy/atu_df.csv"] == "https://tr.example/data/atu_df.csv"
    assert urls["ashliman/type0300.html"] == f"{ashliman.BASE}/type0300.html"
    assert urls["wikidata/atu.json"] == atu_wikidata.query_url()
    assert "trilogy/tmi.csv" not in urls                            # TMI CSV belongs to the tmi source
    assert not any(t.endswith(".absent") for t in urls)            # known-404 markers skipped


def test_every_pinned_file_is_covered_once(tmp_path, monkeypatch):
    raw = _tree(tmp_path, monkeypatch)
    pinned = {p for p in raw.rglob("*") if p.is_file() and not p.name.endswith(".absent")}
    enumerated = [f.cache_file for s in ("berezkin", "tmi", "atu") for f in source_fetchables(s)]
    assert set(enumerated) == pinned                               # covers everything
    assert len(enumerated) == len(pinned)                          # exactly once (no dupes)
