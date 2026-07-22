"""Part 2 item 5 — graphs build/serve unify + the traversal guard."""

import json

import pytest

from graphs.store import GRAPH_TYPES, graph_dir


@pytest.fixture
def graphs_root(tmp_path, monkeypatch):
    from settings import settings

    root = tmp_path / "outputs" / "graphs"
    root.mkdir(parents=True)
    monkeypatch.setattr(settings, "graphs_dir", root)
    return root


class TestGraphDir:
    def test_normal_id_under_root(self, graphs_root):
        d = graph_dir("Iliad")
        assert d == (graphs_root / "Iliad").resolve()

    def test_matches_normalized_id(self, graphs_root):
        # A space-bearing title resolves to the same underscore id the build writes.
        assert graph_dir("The Iliad").name == "The_Iliad"

    def test_traversal_id_cannot_escape(self, graphs_root):
        # A '..' id is sanitised to a plain name inside the tree (never the parent).
        d = graph_dir("../../secret")
        assert d.is_relative_to(graphs_root.resolve())
        assert ".." not in d.name

    def test_empty_id_rejected(self, graphs_root):
        with pytest.raises(ValueError):
            graph_dir("   ")

    def test_graph_types(self):
        assert set(GRAPH_TYPES) == {"beings", "realms", "ages"}


class TestGetGraphDataGuard:
    def test_rejects_unknown_type(self, graphs_root):
        from server.services.graphs import get_graph_data

        assert get_graph_data("Iliad", "villains") is None

    def test_reads_valid_graph(self, graphs_root):
        from server.services.graphs import get_graph_data

        (graphs_root / "Iliad").mkdir()
        (graphs_root / "Iliad" / "beings.json").write_text(json.dumps({"nodes": [1]}))
        assert get_graph_data("Iliad", "beings") == {"nodes": [1]}

    def test_traversal_cannot_read_outside_root(self, tmp_path, graphs_root):
        from server.services.graphs import get_graph_data

        # A beings.json sitting OUTSIDE graphs_dir must be unreachable via a '..' id.
        outside = tmp_path / "outputs"
        (outside / "beings.json").write_text(json.dumps({"secret": True}))
        assert get_graph_data("../beings", "beings") is None
        assert get_graph_data("..", "beings") is None
