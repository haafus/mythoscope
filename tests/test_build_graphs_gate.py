"""A book whose inputs/params are unchanged and whose graphs are present is skipped —
the .fp gate spares the CPU regeneration (the LLM extraction is already cache-gated)."""

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


def test_graph_gate_skips_when_unchanged(tmp_path, monkeypatch):
    calls = []
    graph_dir = _wire(monkeypatch, tmp_path, [_FakeFile("a", "fp1")], calls)

    bg.build_graphs()
    assert sorted(calls) == ["ages", "beings", "realms"]   # first build generates all three
    assert (graph_dir / ".fp").exists()                    # and stamps the fp

    calls.clear()
    bg.build_graphs()
    assert calls == []                                     # unchanged → skipped


def test_graph_gate_rebuilds_on_changed_input(tmp_path, monkeypatch):
    calls = []
    _wire(monkeypatch, tmp_path, [_FakeFile("a", "fp1")], calls)
    bg.build_graphs()

    calls.clear()
    # same document_id (same dir), new content fingerprint → regenerate
    monkeypatch.setattr(bg, "iter_files", lambda _dir: [_FakeFile("a", "fp2")])
    bg.build_graphs()
    assert sorted(calls) == ["ages", "beings", "realms"]

    calls.clear()
    bg.build_graphs()                                      # fp2 now stamped → skip again
    assert calls == []
