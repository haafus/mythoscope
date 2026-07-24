"""GraphsStage: desired() folds the corpus fp with prompts/LLM/limits (reusing the real
_graph_fingerprint); actual() reads each book's .fp. On-disk fixture, no LLM."""

import json

import settings as settings_mod
from graphs.build_graphs import _graph_fingerprint
from graphs.store import GRAPH_TYPES
from pipeline import plan
from pipeline.stages import GraphsStage

PROMPTS = {"beings": "b", "relations": "r", "locations": "l", "time": "t"}


class FakeCorpus:
    name, store = "corpus", None

    def __init__(self, fps):
        self._fps = fps

    def inputs(self):
        return []

    def doc_fingerprints(self):
        return dict(self._fps)

    desired = actual = lambda self: {}
    build = delete = lambda self, keys: None


def _fp(content_fp):
    return _graph_fingerprint(content_fp, PROMPTS, settings_mod.settings.graphs)


def _write_book(graphs_dir, did, fp):
    d = graphs_dir / did
    d.mkdir(parents=True)
    (d / ".fp").write_text(fp, encoding="utf-8")
    for name in GRAPH_TYPES:
        (d / f"{name}.json").write_text("{}", encoding="utf-8")


def _fixture(tmp_path, monkeypatch):
    monkeypatch.setattr(settings_mod.settings, "graphs_dir", tmp_path / "graphs")
    monkeypatch.setattr(settings_mod.settings, "config_dir", tmp_path / "config")
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "prompts.json").write_text(json.dumps(PROMPTS), encoding="utf-8")
    (tmp_path / "graphs").mkdir()


def test_clean_when_fp_matches(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    _write_book(tmp_path / "graphs", "docA", _fp("cfA"))
    assert plan(GraphsStage(FakeCorpus({"docA": "cfA"}))).clean


def test_missing_when_no_graph_dir(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    _write_book(tmp_path / "graphs", "docA", _fp("cfA"))
    p = plan(GraphsStage(FakeCorpus({"docA": "cfA", "docB": "cfB"})))
    assert p.missing == {"docB"}


def test_stale_when_content_changed(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    _write_book(tmp_path / "graphs", "docA", _fp("OLD"))
    assert plan(GraphsStage(FakeCorpus({"docA": "NEW"}))).stale == {"docA"}


def test_incomplete_book_is_missing(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    d = tmp_path / "graphs" / "docA"
    d.mkdir(parents=True)
    (d / ".fp").write_text(_fp("cfA"), encoding="utf-8")  # .fp but no graph JSONs
    assert plan(GraphsStage(FakeCorpus({"docA": "cfA"}))).missing == {"docA"}


def test_orphan_when_book_left_corpus(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    _write_book(tmp_path / "graphs", "docA", _fp("cfA"))
    _write_book(tmp_path / "graphs", "gone", _fp("x"))
    assert plan(GraphsStage(FakeCorpus({"docA": "cfA"}))).orphans == {"gone"}


def test_delete_removes_book_dir(tmp_path, monkeypatch):
    _fixture(tmp_path, monkeypatch)
    _write_book(tmp_path / "graphs", "docA", _fp("cfA"))
    GraphsStage(FakeCorpus({})).delete({"docA"})
    assert not (tmp_path / "graphs" / "docA").exists()
