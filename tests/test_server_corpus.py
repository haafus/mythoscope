import csv
import json

import server.services.corpus as corpus_mod
from server.services.corpus import (
    get_catalog_documents,
    get_traditions_info,
    read_document,
    resolve_document_path,
)


def _make_corpus(tmp_path, docs=None):
    """Create a minimal corpus directory structure for testing."""
    if docs is None:
        docs = [("European", "Greek", "Iliad", "Sing, O goddess, the anger of Achilles")]

    for major, tradition, title, text in docs:
        doc_dir = tmp_path / major / tradition / title
        doc_dir.mkdir(parents=True, exist_ok=True)
        (doc_dir / f"{title}.txt").write_text(text)


class TestResolveDocumentPath:
    def test_existing_file(self, tmp_path, monkeypatch):
        _make_corpus(tmp_path)
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})

        file_path, title = resolve_document_path("Iliad", "European", "Greek")
        assert file_path is not None
        assert file_path.exists()
        assert title == "Iliad"

    def test_missing_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})

        file_path, title = resolve_document_path("Missing", "No", "Where")
        assert file_path is not None
        assert not file_path.exists()
        assert title == "Missing"

    def test_path_traversal_sanitized(self, tmp_path, monkeypatch):
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})

        file_path, title = resolve_document_path("../../etc/passwd", "a", "b")
        assert file_path is not None
        assert tmp_path.resolve() in file_path.resolve().parents
        assert "/" not in title

    def test_sanitizes_special_chars(self, tmp_path, monkeypatch):
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})

        _, title = resolve_document_path('bad<>file:name', "a", "b")
        assert "<" not in title
        assert ">" not in title
        assert ":" not in title


class TestReadDocument:
    def test_reads_text(self, tmp_path, monkeypatch):
        _make_corpus(tmp_path)
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})

        text, title = read_document("Iliad", "European", "Greek")
        assert "Achilles" in text
        assert title == "Iliad"

    def test_missing_raises_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})

        import pytest

        with pytest.raises(FileNotFoundError):
            read_document("Nonexistent", "A", "B")

    def test_traversal_sanitized_raises_not_found(self, tmp_path, monkeypatch):
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})

        import pytest

        with pytest.raises(FileNotFoundError):
            read_document("../../etc/passwd", "a", "b")


class TestDocumentIndex:
    def test_chunked_fallback_finds_file_by_normalized_name(self, tmp_path, monkeypatch):
        _make_corpus(tmp_path, [("Euro_pean", "Greek_Myth", "The_Iliad", "wrath of Achilles")])
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"chunked": tmp_path})
        monkeypatch.setattr(corpus_mod, "_doc_index_cache", {})

        file_path, _ = resolve_document_path("The Iliad", "Euro pean", "Greek Myth", source="chunked")
        assert file_path is not None
        assert file_path.exists()
        assert file_path.name == "The_Iliad.txt"

    def test_lookup_is_case_insensitive(self, tmp_path, monkeypatch):
        _make_corpus(tmp_path, [("European", "Greek", "Iliad", "text")])
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"chunked": tmp_path})
        monkeypatch.setattr(corpus_mod, "_doc_index_cache", {})

        file_path, _ = resolve_document_path("ILIAD", "european", "GREEK", source="chunked")
        assert file_path is not None
        assert file_path.exists()

    def test_symlink_escape_excluded_from_index(self, tmp_path, monkeypatch):
        outside = tmp_path / "outside"
        outside.mkdir()
        secret = outside / "secret.txt"
        secret.write_text("secret data")

        root = tmp_path / "corpus"
        link_dir = root / "Major" / "Trad" / "Doc"
        link_dir.mkdir(parents=True)
        (link_dir / "Doc.txt").symlink_to(secret)

        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"chunked": root})
        monkeypatch.setattr(corpus_mod, "_doc_index_cache", {})

        assert corpus_mod._document_index("chunked") == {}

    def test_index_is_cached_within_ttl(self, tmp_path, monkeypatch):
        _make_corpus(tmp_path, [("A", "B", "First", "text")])
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"chunked": tmp_path})
        monkeypatch.setattr(corpus_mod, "_doc_index_cache", {})

        first = corpus_mod._document_index("chunked")
        assert len(first) == 1

        _make_corpus(tmp_path, [("A", "B", "Second", "text")])
        second = corpus_mod._document_index("chunked")
        assert len(second) == 1


class TestGetCatalogDocuments:
    def test_from_metadata_json(self, tmp_path, monkeypatch):
        metadata = [
            {"id": "Iliad", "major_tradition": "European", "tradition": "Greek", "language": "en"},
        ]
        (tmp_path / "corpus_metadata.json").write_text(json.dumps(metadata))
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})
        monkeypatch.setattr(corpus_mod, "_catalog_cache", {})

        docs = get_catalog_documents("corpus")
        assert len(docs) == 1
        assert docs[0]["id"] == "Iliad"
        assert docs[0]["language"] == "en"
        assert docs[0]["source"] == "corpus"

    def test_from_catalog_csv(self, tmp_path, monkeypatch):
        csv_path = tmp_path / "corpus_catalog.csv"
        with csv_path.open("w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["id", "major_tradition", "tradition", "word_count"])
            writer.writeheader()
            writer.writerow({"id": "Odyssey", "major_tradition": "European", "tradition": "Greek", "word_count": "5000"})

        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})
        monkeypatch.setattr(corpus_mod, "_catalog_cache", {})

        docs = get_catalog_documents("corpus")
        assert len(docs) == 1
        assert docs[0]["id"] == "Odyssey"
        assert docs[0]["word_count"] == 5000

    def test_empty_corpus(self, tmp_path, monkeypatch):
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})
        monkeypatch.setattr(corpus_mod, "_catalog_cache", {})

        docs = get_catalog_documents("corpus")
        assert docs == []

    def test_cache_hit(self, tmp_path, monkeypatch):
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})
        monkeypatch.setattr(corpus_mod, "_catalog_cache", {})

        get_catalog_documents("corpus")
        (tmp_path / "corpus_metadata.json").write_text(json.dumps([{"id": "new"}]))
        docs = get_catalog_documents("corpus")
        assert docs == []

    def test_sorted_by_tradition(self, tmp_path, monkeypatch):
        metadata = [
            {"id": "B", "major_tradition": "Z", "tradition": "Z"},
            {"id": "A", "major_tradition": "A", "tradition": "A"},
        ]
        (tmp_path / "corpus_metadata.json").write_text(json.dumps(metadata))
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})
        monkeypatch.setattr(corpus_mod, "_catalog_cache", {})

        docs = get_catalog_documents("corpus")
        assert docs[0]["major_tradition"] == "A"
        assert docs[1]["major_tradition"] == "Z"


class TestGetTraditionsInfo:
    def test_from_specific_source(self, tmp_path, monkeypatch):
        info = {"Greek": {"color": "#ff0000", "description": "Ancient Greek"}}
        (tmp_path / "traditions_info.json").write_text(json.dumps(info))
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})

        result = get_traditions_info("corpus")
        assert result["Greek"]["color"] == "#ff0000"

    def test_fallback_without_source(self, tmp_path, monkeypatch):
        from server.config import ProjectPaths

        info = {"Norse": {"color": "#0000ff"}}
        (tmp_path / "traditions_info.json").write_text(json.dumps(info))
        nonexistent = tmp_path / "nonexistent"
        fake_paths = ProjectPaths(
            project_root=tmp_path,
            ui_root=tmp_path,
            web_root=tmp_path,
            assets_dir=tmp_path,
            analysis_dir=tmp_path,
            template_dir=tmp_path,
            corpus_dir=nonexistent,
            corpus_chunked_dir=tmp_path,
        )
        monkeypatch.setattr(corpus_mod, "paths", fake_paths)
        monkeypatch.setattr(
            corpus_mod,
            "CATALOG_SOURCES",
            {"corpus": nonexistent, "chunked": tmp_path},
        )

        result = get_traditions_info()
        assert "Norse" in result

    def test_missing_returns_empty(self, tmp_path, monkeypatch):
        monkeypatch.setattr(corpus_mod, "CATALOG_SOURCES", {"corpus": tmp_path})

        result = get_traditions_info("corpus")
        assert result == {}
