import json
import sys
import types

for stub in ["pymupdf", "trafilatura", "bs4", "fake_useragent"]:
    sys.modules.setdefault(stub, types.ModuleType(stub))
bs4_mod = sys.modules["bs4"]
if not hasattr(bs4_mod, "BeautifulSoup"):
    bs4_mod.BeautifulSoup = type("BeautifulSoup", (), {})  # type: ignore[attr-defined]
fu_mod = sys.modules["fake_useragent"]
if not hasattr(fu_mod, "UserAgent"):

    class _FakeUA:
        def __init__(self, **_kw):
            pass

        random = "test-agent"

    fu_mod.UserAgent = _FakeUA  # type: ignore[attr-defined]

from datetime import datetime

from corpus import catalog
from corpus.builder import _add_to_catalog, _build_metadata, _item_tid, _update_traditions_info


class TestItemTid:
    def test_prefers_title(self):
        assert _item_tid({"title": "Iliad", "id": "123"}) == "Iliad"

    def test_falls_back_to_id(self):
        assert _item_tid({"id": "abc"}) == "abc"

    def test_falls_back_to_unknown(self):
        assert _item_tid({}) == "unknown_id"

    def test_empty_title_still_returned(self):
        assert _item_tid({"title": "", "id": "x"}) == ""


_BASE_ITEM = {
    "major_tradition": "Greek",
    "tradition": "Hellenic",
    "language": "en",
    "type": "translation",
    "url": "http://example.com/text",
}


class TestBuildMetadata:
    def test_date_downloaded_is_timezone_aware(self):
        stats = {"md5": "abc", "char_count": 10, "word_count": 2, "sentence_count": 1}
        item = {**_BASE_ITEM, "title": "Iliad"}
        meta = _build_metadata(item, path="/tmp/x.txt", color="#000", stats=stats)
        parsed = datetime.fromisoformat(meta["date_downloaded"])
        assert parsed.tzinfo is not None


class TestAddToCatalog:
    def setup_method(self):
        catalog.clear_catalog()

    def test_success_records_stats(self):
        stats = {"word_count": 500, "sentence_count": 40}
        _add_to_catalog(_BASE_ITEM, tid="Iliad", color="#FF0000", success=True, stats=stats)

        assert len(catalog.catalog_rows) == 1
        row = catalog.catalog_rows[0]
        assert row[0] == "Iliad"
        assert row[1] == "Greek"
        assert row[6] is True
        assert row[7] == 500
        assert row[8] == 40

    def test_error_records_zero_counts(self):
        item = {**_BASE_ITEM, "url": "http://example.com/fail"}
        _add_to_catalog(item, tid="Iliad", color="#FF0000", success=False, error="Timeout")

        row = catalog.catalog_rows[0]
        assert row[6] is False
        assert row[7] == 0
        assert row[8] == 0
        assert "Timeout" in row[10]

    def test_error_with_description_includes_both(self):
        item = {**_BASE_ITEM, "url": "http://example.com/fail2", "description": "The Odyssey"}
        _add_to_catalog(item, tid="Odyssey", color="#FF0000", success=False, error="404")

        row = catalog.catalog_rows[0]
        assert "The Odyssey" in row[10]
        assert "404" in row[10]

    def test_success_empty_description(self):
        item = {**_BASE_ITEM, "url": "http://example.com/nodesc"}
        stats = {"word_count": 10, "sentence_count": 1}
        _add_to_catalog(item, tid="X", color="#000", success=True, stats=stats)

        assert catalog.catalog_rows[0][10] == ""

    def test_missing_major_tradition_defaults(self):
        item = {"tradition": "T", "language": "en", "type": "original", "url": "http://example.com/no-major"}
        stats = {"word_count": 1, "sentence_count": 1}
        _add_to_catalog(item, tid="X", color="#000", success=True, stats=stats)

        assert catalog.catalog_rows[0][1] == "Unknown"


class TestUpdateTraditionsInfo:
    def _setup(self, tmp_path, monkeypatch, items):
        import corpus.builder as builder_mod

        dl_file = tmp_path / "download_list.json"
        dl_file.write_text(json.dumps(items))
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()

        monkeypatch.setattr(builder_mod, "DOWNLOAD_LIST_FILE", dl_file)
        monkeypatch.setattr(builder_mod, "CORPUS_DIR", corpus_dir)
        return corpus_dir

    def test_creates_new_file(self, tmp_path, monkeypatch):
        items = [
            {"title": "Iliad", "type": "translation", "tradition": "Greek"},
            {"title": "Odyssey", "type": "translation", "tradition": "Greek"},
            {"title": "Edda", "type": "original", "tradition": "Norse"},
        ]
        corpus_dir = self._setup(tmp_path, monkeypatch, items)

        _update_traditions_info({"translation", "original"}, force=False)

        data = json.loads((corpus_dir / "traditions_info.json").read_text())
        assert "Greek" in data
        assert "Norse" in data
        assert sorted(data["Greek"]["books"]) == ["Iliad", "Odyssey"]
        assert data["Norse"]["books"] == ["Edda"]
        assert data["Greek"]["description"] == ""
        assert data["Greek"]["color"].startswith("#")

    def test_preserves_existing_descriptions(self, tmp_path, monkeypatch):
        items = [
            {"title": "Iliad", "type": "translation", "tradition": "Greek"},
            {"title": "Odyssey", "type": "translation", "tradition": "Greek"},
        ]
        corpus_dir = self._setup(tmp_path, monkeypatch, items)

        existing = {
            "Greek": {
                "description": "Ancient Greek mythology",
                "region": "Mediterranean",
                "coordinates": [37.9, 23.7],
                "color": "#123456",
                "books": ["Iliad"],
            }
        }
        (corpus_dir / "traditions_info.json").write_text(json.dumps(existing))

        _update_traditions_info({"translation"}, force=False)

        data = json.loads((corpus_dir / "traditions_info.json").read_text())
        assert data["Greek"]["description"] == "Ancient Greek mythology"
        assert data["Greek"]["region"] == "Mediterranean"
        assert sorted(data["Greek"]["books"]) == ["Iliad", "Odyssey"]

    def test_force_creates_backup(self, tmp_path, monkeypatch):
        corpus_dir = self._setup(tmp_path, monkeypatch, [])

        existing = {"Greek": {"description": "old data", "color": "#000", "books": []}}
        (corpus_dir / "traditions_info.json").write_text(json.dumps(existing))

        _update_traditions_info(set(), force=True)

        backup = json.loads((corpus_dir / "traditions_info_backup.json").read_text())
        assert backup["Greek"]["description"] == "old data"

    def test_filters_by_type(self, tmp_path, monkeypatch):
        items = [
            {"title": "Iliad", "type": "translation", "tradition": "Greek"},
            {"title": "Edda", "type": "original", "tradition": "Norse"},
        ]
        corpus_dir = self._setup(tmp_path, monkeypatch, items)

        _update_traditions_info({"translation"}, force=False)

        data = json.loads((corpus_dir / "traditions_info.json").read_text())
        assert "Greek" in data
        assert "Norse" not in data

    def test_no_download_list(self, tmp_path, monkeypatch):
        import corpus.builder as builder_mod

        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        monkeypatch.setattr(builder_mod, "DOWNLOAD_LIST_FILE", tmp_path / "nonexistent.json")
        monkeypatch.setattr(builder_mod, "CORPUS_DIR", corpus_dir)

        _update_traditions_info({"translation"}, force=False)

        data = json.loads((corpus_dir / "traditions_info.json").read_text())
        assert data == {}

    def test_adds_missing_color(self, tmp_path, monkeypatch):
        items = [{"title": "Edda", "type": "original", "tradition": "Norse"}]
        corpus_dir = self._setup(tmp_path, monkeypatch, items)

        existing = {"Norse": {"description": "Norse myths", "books": ["Edda"]}}
        (corpus_dir / "traditions_info.json").write_text(json.dumps(existing))

        _update_traditions_info({"original"}, force=False)

        data = json.loads((corpus_dir / "traditions_info.json").read_text())
        assert data["Norse"]["color"].startswith("#")
        assert data["Norse"]["description"] == "Norse myths"

    def test_uses_item_tid_for_books(self, tmp_path, monkeypatch):
        items = [
            {"id": "book_42", "type": "translation", "tradition": "Egyptian"},
        ]
        corpus_dir = self._setup(tmp_path, monkeypatch, items)

        _update_traditions_info({"translation"}, force=False)

        data = json.loads((corpus_dir / "traditions_info.json").read_text())
        assert data["Egyptian"]["books"] == ["book_42"]
