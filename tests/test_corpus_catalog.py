import importlib.util
import logging
import os
import sys
import types

for stub in ["pymupdf", "trafilatura", "bs4", "fake_useragent"]:
    sys.modules.setdefault(stub, types.ModuleType(stub))
bs4_mod = sys.modules["bs4"]
if not hasattr(bs4_mod, "BeautifulSoup"):
    bs4_mod.BeautifulSoup = type("BeautifulSoup", (), {})  # type: ignore[attr-defined]

cb = types.ModuleType("corpus_builder")
cb.logger = logging.getLogger("corpus_builder")  # type: ignore[attr-defined]
sys.modules.setdefault("corpus_builder", cb)

_spec = importlib.util.spec_from_file_location(
    "corpus_builder.catalog",
    os.path.join(os.path.dirname(__file__), "..", "src", "corpus_builder", "catalog.py"),
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
        assert catalog_rows[0][0] == "t1"

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
        assert row[0] == "tid"
        assert row[1] == "maj"
        assert row[2] == "trad"
        assert row[3] == "ru"
        assert row[4] == "original"
        assert row[5] == "http://z.com"
        assert row[6] is True
        assert row[7] == 50
        assert row[8] == 5
        assert row[9] == "#AABBCC"
        assert row[10] == "desc"
