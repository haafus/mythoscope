import json

from server.services.corpus import (
    document_ids_for_tradition,
    get_document_text,
    get_documents,
    get_traditions_tree,
    tradition_of_document,
)
from settings import settings


def _config_tree(tmp_path, monkeypatch):
    config = tmp_path / "config"
    config.mkdir(exist_ok=True)
    tree = {
        "Europe": {"color": "#4F7A4E", "traditions": {"Greek": {}, "Norse": {}}},
        "East Asia": {"color": "#C0392B", "traditions": {"Chinese": {}}},
    }
    (config / "traditions.json").write_text(json.dumps(tree))
    monkeypatch.setattr(settings, "config_dir", config)
    return tree


def _catalog(tmp_path, monkeypatch, rows):
    monkeypatch.setattr(settings, "corpus_dir", tmp_path)
    (tmp_path / "corpus.json").write_text(json.dumps(rows))


class TestGetTraditionsTree:
    def test_serves_config_tree(self, tmp_path, monkeypatch):
        _config_tree(tmp_path, monkeypatch)
        tree = get_traditions_tree()
        assert set(tree) == {"Europe", "East Asia"}
        assert tree["Europe"]["color"] == "#4F7A4E"

    def test_missing_config_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "config_dir", tmp_path / "nope")
        assert get_traditions_tree() == {}


class TestGetDocuments:
    def test_trims_to_reference_fields(self, tmp_path, monkeypatch):
        _config_tree(tmp_path, monkeypatch)
        _catalog(tmp_path, monkeypatch, [
            {"document_id": "d1", "title": "Iliad", "tradition": "Greek",
             "major_tradition": "European", "color": "#ff0000", "url": "http://x/i"},
        ])
        docs = get_documents()
        assert len(docs) == 1
        assert docs[0]["document_id"] == "d1"
        assert docs[0]["tradition"] == "Greek"
        assert "major_tradition" not in docs[0]   # dropped
        assert "color" not in docs[0]              # resolved on the front, not stored

    def test_sorted_by_region_then_tradition_then_title(self, tmp_path, monkeypatch):
        _config_tree(tmp_path, monkeypatch)
        _catalog(tmp_path, monkeypatch, [
            {"document_id": "c", "title": "Journey", "tradition": "Chinese"},   # East Asia
            {"document_id": "b", "title": "Edda", "tradition": "Norse"},        # Europe
            {"document_id": "a", "title": "Iliad", "tradition": "Greek"},       # Europe
        ])
        titles = [d["title"] for d in get_documents()]
        # Europe (Greek, Norse) before East Asia; sort is by region name: "East Asia" < "Europe".
        assert titles == ["Journey", "Iliad", "Edda"]

    def test_missing_corpus_json_returns_empty(self, tmp_path, monkeypatch):
        _config_tree(tmp_path, monkeypatch)
        monkeypatch.setattr(settings, "corpus_dir", tmp_path)
        assert get_documents() == []


class TestGetDocumentText:
    def test_reads_by_document_id(self, tmp_path, monkeypatch):
        _catalog(tmp_path, monkeypatch, [{"document_id": "d1", "path": "Europe/Greek/Iliad.txt"}])
        (tmp_path / "Europe" / "Greek").mkdir(parents=True)
        (tmp_path / "Europe" / "Greek" / "Iliad.txt").write_text("Sing, O goddess")
        assert get_document_text("d1") == "Sing, O goddess"

    def test_unknown_id_returns_none(self, tmp_path, monkeypatch):
        _catalog(tmp_path, monkeypatch, [{"document_id": "d1", "path": "x.txt"}])
        assert get_document_text("nope") is None

    def test_traversal_path_blocked(self, tmp_path, monkeypatch):
        # A row whose path escapes corpus_dir must not be served.
        _catalog(tmp_path, monkeypatch, [{"document_id": "d1", "path": "../secret.txt"}])
        (tmp_path.parent / "secret.txt").write_text("leak")
        assert get_document_text("d1") is None


class TestTraditionResolution:
    def test_document_ids_for_tradition(self, tmp_path, monkeypatch):
        _catalog(tmp_path, monkeypatch, [
            {"document_id": "a", "tradition": "Greek"},
            {"document_id": "b", "tradition": "Greek"},
            {"document_id": "c", "tradition": "Norse"},
        ])
        assert document_ids_for_tradition("Greek") == {"a", "b"}

    def test_tradition_of_document(self, tmp_path, monkeypatch):
        _catalog(tmp_path, monkeypatch, [{"document_id": "a", "tradition": "Greek"}])
        assert tradition_of_document("a") == "Greek"
        assert tradition_of_document("zzz") is None
