"""build_graphs executes exactly the `rebuild` work-list handed to it — it generates the three
graphs and stamps the .fp for each requested book, and touches nothing outside the list. The
freshness/skip DECISION (unchanged -> skip, changed -> rebuild) now lives only in the driver and
is covered by test_graphs_stage.py (plan().clean / .missing / .stale) + test_pipeline_driver.py."""

from graphs import build_graphs as bg


class _FakeFile:
    def __init__(self, doc_id, fp):
        self.document_id = doc_id
        self.text_id = doc_id
        self._fp = fp

    def read_text(self):
        return "once upon a time"

    def content_fingerprint(self):
        return self._fp


def _wire(monkeypatch, tmp_path, files, calls):
    graph_dir = tmp_path / "gd"
    monkeypatch.setattr(bg, "iter_files", lambda _dir: list(files))
    monkeypatch.setattr(bg, "graph_dir", lambda _doc: graph_dir)
    monkeypatch.setattr(bg, "chunk_text", lambda *a, **k: ["chunk1"])
    monkeypatch.setattr(bg, "chunk_hash", lambda c: c)
    monkeypatch.setattr(bg, "clear_cache", lambda *a, **k: None)
    monkeypatch.setattr(bg, "load_cache", lambda *a, **k: {"chunk1": {"beings": [], "relations": [], "locations": [], "times": []}})

    def gen(name):
        def _g(*a, **k):
            graph_dir.mkdir(parents=True, exist_ok=True)
            (graph_dir / f"{name}.json").write_text("{}", encoding="utf-8")
            calls.append(name)
        return _g

    monkeypatch.setattr(bg, "generate_beings_graph", gen("beings"))
    monkeypatch.setattr(bg, "generate_realms_graph", gen("realms"))
    monkeypatch.setattr(bg, "generate_ages_graph", gen("ages"))
    return graph_dir


def test_build_generates_all_graphs_and_stamps_fp(tmp_path, monkeypatch):
    calls = []
    graph_dir = _wire(monkeypatch, tmp_path, [_FakeFile("a", "fp1")], calls)

    bg.build_graphs(rebuild={"a"})
    assert sorted(calls) == ["ages", "beings", "realms"]   # the requested book generates all three
    assert (graph_dir / ".fp").exists()                    # and stamps the fp


def test_build_touches_only_the_work_list(tmp_path, monkeypatch):
    # The builder executes exactly `rebuild` — an empty work-list builds nothing (and, given a
    # subset, only that subset), leaving freshness/skip decisions entirely to the driver.
    calls = []
    _wire(monkeypatch, tmp_path, [_FakeFile("a", "fp1"), _FakeFile("b", "fp2")], calls)

    bg.build_graphs(rebuild=set())
    assert calls == []                                     # nothing requested → nothing built

    bg.build_graphs(rebuild={"b"})
    assert sorted(calls) == ["ages", "beings", "realms"]   # only book "b" built
