import importlib.util
import os
import sys
import types

for stub in ["pymupdf", "trafilatura", "bs4", "fake_useragent"]:
    sys.modules.setdefault(stub, types.ModuleType(stub))
bs4_mod = sys.modules["bs4"]
if not hasattr(bs4_mod, "BeautifulSoup"):
    bs4_mod.BeautifulSoup = type("BeautifulSoup", (), {})  # type: ignore[attr-defined]

sys.modules.setdefault("corpus", types.ModuleType("corpus"))

_spec = importlib.util.spec_from_file_location(
    "corpus.catalog",
    os.path.join(os.path.dirname(__file__), "..", "src", "corpus", "catalog.py"),
)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)

clear_catalog = _mod.clear_catalog
add_to_catalog = _mod.add_to_catalog
catalog_rows = _mod.catalog_rows
_seen_urls = _mod._seen_urls


class TestClearCatalog:
    def test_clears_rows(self):
        catalog_rows.append(["test", "data"])
        clear_catalog()
        assert len(catalog_rows) == 0

    def test_clears_seen_urls(self):
        _seen_urls.add("http://example.com")
        clear_catalog()
        assert len(_seen_urls) == 0

    def test_double_clear(self):
        clear_catalog()
        clear_catalog()
        assert len(catalog_rows) == 0


class TestAddToCatalog:
    def setup_method(self):
        clear_catalog()

    def test_adds_entry(self):
        add_to_catalog("t1", "major", "trad", "en", "translate", "http://x.com", True, 100, 10, "#FF0000")
        assert len(catalog_rows) == 1
        assert catalog_rows[0].tid == "t1"

    def test_skips_duplicate_url(self):
        add_to_catalog("t1", "major", "trad", "en", "translate", "http://x.com", True, 100, 10, "#FF0000")
        add_to_catalog("t2", "major", "trad", "en", "translate", "http://x.com", True, 200, 20, "#00FF00")
        assert len(catalog_rows) == 1

    def test_allows_different_urls(self):
        add_to_catalog("t1", "major", "trad", "en", "translate", "http://a.com", True, 100, 10, "#FF0000")
        add_to_catalog("t2", "major", "trad", "en", "translate", "http://b.com", True, 200, 20, "#00FF00")
        assert len(catalog_rows) == 2

    def test_entry_fields(self):
        add_to_catalog("tid", "maj", "trad", "ru", "original", "http://z.com", True, 50, 5, "#AABBCC", "desc")
        row = catalog_rows[0]
        assert row.tid == "tid"
        assert row.major_tradition == "maj"
        assert row.tradition == "trad"
        assert row.language == "ru"
        assert row.ftype == "original"
        assert row.url == "http://z.com"
        assert row.available is True
        assert row.word_count == 50
        assert row.sentence_count == 5
        assert row.color == "#AABBCC"
        assert row.description == "desc"

    def test_as_csv_row_matches_header_order(self):
        add_to_catalog("tid", "maj", "trad", "ru", "original", "http://z.com", True, 50, 5, "#AABBCC", "desc")
        csv_row = catalog_rows[0].as_csv_row()
        assert len(csv_row) == len(_mod.CSV_HEADER)
        assert csv_row == ["tid", "maj", "trad", "ru", "original", "http://z.com", True, 50, 5, "#AABBCC", "desc"]
