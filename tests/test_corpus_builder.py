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

from corpus import builder
from corpus.builder import _build_metadata, _update_traditions, build_corpus

_BASE_ITEM = {
    "major_tradition": "Greek",
    "tradition": "Hellenic",
    "url": "http://example.com/text",
    "description": "",
}


class TestBuildMetadata:
    def test_date_downloaded_is_timezone_aware(self):
        stats = {"md5": "abc", "char_count": 10, "word_count": 2, "sentence_count": 1}
        item = {**_BASE_ITEM, "title": "Iliad"}
        meta = _build_metadata(item, path="/tmp/x.txt", stats=stats)
        parsed = datetime.fromisoformat(meta["date_downloaded"])
        assert parsed.tzinfo is not None


class TestBuildMetadataFields:
    def test_word_count(self):
        stats = {"md5": "abc", "char_count": 10, "word_count": 500, "sentence_count": 40}
        item = {**_BASE_ITEM, "title": "Iliad"}
        meta = _build_metadata(item, path="/tmp/x.txt", stats=stats)
        assert meta["word_count"] == 500

    def test_description_from_item(self):
        stats = {"md5": "abc", "char_count": 10, "word_count": 10, "sentence_count": 1}
        item = {**_BASE_ITEM, "title": "Iliad", "description": "An epic poem"}
        meta = _build_metadata(item, path="/tmp/x.txt", stats=stats)
        assert meta["description"] == "An epic poem"

    def test_empty_description(self):
        stats = {"md5": "abc", "char_count": 10, "word_count": 10, "sentence_count": 1}
        item = {**_BASE_ITEM, "title": "Iliad"}
        meta = _build_metadata(item, path="/tmp/x.txt", stats=stats)
        assert meta["description"] == ""




class TestBuildCorpusForce:
    """Which items build_corpus re-processes vs. reuses from a previous run."""

    def _setup(self, tmp_path, monkeypatch, items, *, existing=None):
        from settings import settings

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        sources_dir = tmp_path / "sources"
        sources_dir.mkdir()
        # A valid canon tree: place every used tradition under a canon region so the
        # build-time fail-loud validation (§2.12) passes.
        used = sorted({i.get("tradition") for i in items if i.get("tradition")})
        (config_dir / "traditions.json").write_text(
            json.dumps({"Europe": {"traditions": {t: {} for t in used}}})
        )
        monkeypatch.setattr(settings, "config_dir", config_dir)
        monkeypatch.setattr(settings, "corpus_dir", corpus_dir)
        monkeypatch.setattr(settings, "sources_dir", sources_dir)

        monkeypatch.setattr(builder, "load_download_list", lambda: [dict(i) for i in items])
        if existing is not None:
            (corpus_dir / "corpus.json").write_text(json.dumps(existing))

        # Record which titles get (re)processed; write a file so the path check passes.
        processed = []

        def fake_process(item, force=False):
            processed.append(item["title"])
            path = corpus_dir / f"{item['title']}.txt"
            path.write_text("content")
            return {**item, "path": f"{item['title']}.txt"}

        monkeypatch.setattr(builder, "_download_and_process", fake_process)
        return corpus_dir, processed

    def test_fresh_build_processes_all(self, tmp_path, monkeypatch):
        items = [{"title": "Iliad", "tradition": "Greek"}, {"title": "Edda", "tradition": "Norse"}]
        _, processed = self._setup(tmp_path, monkeypatch, items)

        build_corpus(force=False)
        assert sorted(processed) == ["Edda", "Iliad"]

    def test_cached_item_with_existing_file_is_skipped(self, tmp_path, monkeypatch):
        items = [{"title": "Iliad", "tradition": "Greek"}]
        existing = [{"title": "Iliad", "tradition": "Greek", "path": "Iliad.txt"}]
        corpus_dir, processed = self._setup(tmp_path, monkeypatch, items, existing=existing)
        (corpus_dir / "Iliad.txt").write_text("old")  # the cached file is on disk

        build_corpus(force=False)
        assert processed == []  # reused, not re-downloaded

    def test_stale_metadata_missing_file_is_reprocessed(self, tmp_path, monkeypatch):
        # corpus.json references a file that no longer exists -> don't trust it.
        items = [{"title": "Iliad", "tradition": "Greek"}]
        existing = [{"title": "Iliad", "tradition": "Greek", "path": "Iliad.txt"}]
        _, processed = self._setup(tmp_path, monkeypatch, items, existing=existing)

        build_corpus(force=False)
        assert processed == ["Iliad"]

    def test_force_reprocesses_even_when_cached(self, tmp_path, monkeypatch):
        items = [{"title": "Iliad", "tradition": "Greek"}]
        existing = [{"title": "Iliad", "tradition": "Greek", "path": "Iliad.txt"}]
        corpus_dir, processed = self._setup(tmp_path, monkeypatch, items, existing=existing)
        (corpus_dir / "Iliad.txt").write_text("old")  # present, but force ignores the cache

        build_corpus(force=True)
        assert processed == ["Iliad"]

    def test_web_source_cached_is_skipped(self, tmp_path, monkeypatch):
        items = [{"title": "Iliad", "tradition": "Greek", "url": "https://example.com/iliad"}]
        existing = [{"title": "Iliad", "tradition": "Greek", "url": "https://example.com/iliad", "path": "Iliad.txt"}]
        corpus_dir, processed = self._setup(tmp_path, monkeypatch, items, existing=existing)
        (corpus_dir / "Iliad.txt").write_text("old")

        build_corpus(force=False)
        assert processed == []  # web source with present output is reused

    def test_file_source_unchanged_is_skipped(self, tmp_path, monkeypatch):
        # File source whose content matches the previous raw snapshot is reused.
        from fetch_cache import cache_path

        items = [{"title": "Local", "tradition": "Greek", "url": "file:local.txt"}]
        existing = [{"title": "Local", "tradition": "Greek", "url": "file:local.txt", "path": "Local.txt"}]
        corpus_dir, processed = self._setup(tmp_path, monkeypatch, items, existing=existing)
        (corpus_dir / "Local.txt").write_text("out")  # output present
        (tmp_path / "sources" / "local.txt").write_bytes(b"same content")
        raw = cache_path(corpus_dir / "raw", "file:local.txt")
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(b"same content")  # snapshot matches the source

        build_corpus(force=False)
        assert processed == []  # unchanged -> reused

    def test_file_source_changed_is_reprocessed(self, tmp_path, monkeypatch):
        # File source whose content differs from the raw snapshot is re-ingested.
        from fetch_cache import cache_path

        items = [{"title": "Local", "tradition": "Greek", "url": "file:local.txt"}]
        existing = [{"title": "Local", "tradition": "Greek", "url": "file:local.txt", "path": "Local.txt"}]
        corpus_dir, processed = self._setup(tmp_path, monkeypatch, items, existing=existing)
        (corpus_dir / "Local.txt").write_text("out")
        (tmp_path / "sources" / "local.txt").write_bytes(b"new content")
        raw = cache_path(corpus_dir / "raw", "file:local.txt")
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(b"old content")  # snapshot differs from the edited source

        build_corpus(force=False)
        assert processed == ["Local"]

    def test_file_source_without_snapshot_is_reprocessed(self, tmp_path, monkeypatch):
        # No previous raw snapshot (e.g. first file build) -> treat as changed.
        items = [{"title": "Local", "tradition": "Greek", "url": "file:local.txt"}]
        existing = [{"title": "Local", "tradition": "Greek", "url": "file:local.txt", "path": "Local.txt"}]
        corpus_dir, processed = self._setup(tmp_path, monkeypatch, items, existing=existing)
        (corpus_dir / "Local.txt").write_text("out")
        (tmp_path / "sources" / "local.txt").write_bytes(b"content")

        build_corpus(force=False)
        assert processed == ["Local"]


class TestFileSourceDispatch:
    """The real _download_and_process reads a local file: source end to end."""

    def test_reads_local_file_source(self, tmp_path, monkeypatch):
        from settings import settings

        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        sources_dir = tmp_path / "sources"
        sources_dir.mkdir()
        (sources_dir / "myth.txt").write_text("Once upon a time there was a hero. The end.")
        monkeypatch.setattr(settings, "corpus_dir", corpus_dir)
        monkeypatch.setattr(settings, "sources_dir", sources_dir)

        item = {
            "title": "Local Myth",
            "tradition": "Greek",
            "major_tradition": "Hellenic",
            "url": "file:myth.txt",
            "description": "",
        }
        meta = builder._download_and_process(item)

        assert meta is not None
        assert meta["word_count"] > 0
        assert (corpus_dir / meta["path"]).exists()
        # raw snapshot cached under corpus/raw for reproducibility
        assert list((corpus_dir / "raw").iterdir())

    def test_missing_local_file_returns_none(self, tmp_path, monkeypatch):
        from settings import settings

        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        sources_dir = tmp_path / "sources"
        sources_dir.mkdir()
        monkeypatch.setattr(settings, "corpus_dir", corpus_dir)
        monkeypatch.setattr(settings, "sources_dir", sources_dir)

        item = {
            "title": "Missing",
            "tradition": "Greek",
            "major_tradition": "Hellenic",
            "url": "file:nope.txt",
            "description": "",
        }
        assert builder._download_and_process(item) is None


class TestFinalizeText:
    def test_stores_blake2b_fingerprint(self):
        from corpus.builder import _finalize_text
        from corpus.utils import content_fingerprint

        data, stats = _finalize_text("Hello world.", "http://x", "T")
        assert "md5" not in stats  # the broken hash is dropped from the catalog (D2)
        assert stats["fingerprint"] == content_fingerprint(data)

    def test_fingerprint_changes_with_text(self):
        from corpus.builder import _finalize_text

        _, a = _finalize_text("The hero sailed home.", "http://x", "T")
        _, b = _finalize_text("The hero stayed home.", "http://x", "T")
        assert a["fingerprint"] != b["fingerprint"]  # a text edit → new fp → re-embed


class TestDocumentIdInCatalog:
    def test_build_metadata_persists_document_id(self):
        from corpus.builder import _build_metadata
        from corpus.locator import document_id

        item = {**_BASE_ITEM, "title": "Iliad", "url": "http://example.com/iliad"}
        meta = _build_metadata(item, path="x.txt", stats={"fingerprint": "f"})
        assert meta["document_id"] == document_id("http://example.com/iliad")

    def test_rename_keeps_document_id_stable(self):
        # document_id anchors on the locator, so a title/tradition change must not move it.
        from corpus.builder import _build_metadata

        a = _build_metadata({**_BASE_ITEM, "title": "Iliad", "url": "http://x/i"}, path="a", stats={})
        b = _build_metadata({**_BASE_ITEM, "title": "The Iliad", "tradition": "Roman", "url": "http://x/i"},
                            path="b", stats={})
        assert a["document_id"] == b["document_id"]


class TestPinnedRaw:
    def test_force_does_not_refetch(self, tmp_path, monkeypatch):
        # --force rebuilds derived from the pinned raw; it must NOT re-fetch upstream.
        from fetch_cache import cache_path
        from settings import settings

        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        monkeypatch.setattr(settings, "corpus_dir", corpus_dir)
        monkeypatch.setattr(settings, "sources_dir", tmp_path / "sources")

        raw = cache_path(corpus_dir / "raw", "https://example.com/iliad")
        raw.parent.mkdir(parents=True, exist_ok=True)
        raw.write_bytes(b"pinned raw text")

        def boom(url, auth=None):
            raise AssertionError("build re-fetched upstream — raw must be pinned")

        import corpus.downloader as dl
        monkeypatch.setattr(dl, "download_file", boom)

        item = {"title": "Iliad", "tradition": "Greek", "major_tradition": "Hellenic",
                "url": "https://example.com/iliad", "description": ""}
        meta = builder._download_and_process(item)
        assert meta is not None  # rebuilt from pinned raw, no network


class TestUpdateTraditions:
    def _setup(self, tmp_path, monkeypatch, *, books=None, traditions=None):
        from settings import settings

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()

        (config_dir / "corpus.json").write_text(json.dumps(books or []))
        (config_dir / "traditions.json").write_text(json.dumps(traditions or {}))

        monkeypatch.setattr(settings, "config_dir", config_dir)
        monkeypatch.setattr(settings, "corpus_dir", corpus_dir)
        return corpus_dir

    def test_merges_config_with_color(self, tmp_path, monkeypatch):
        traditions = {"Indo-European": {"traditions": {"Greek": {"description": "Ancient Greek mythology", "coordinates": [37.9, 23.7]}}}}
        books = [{"title": "Iliad", "tradition": "Greek"}]
        corpus_dir = self._setup(tmp_path, monkeypatch, books=books, traditions=traditions)

        _update_traditions(force=False)

        data = json.loads((corpus_dir / "traditions.json").read_text())
        assert data["Greek"]["description"] == "Ancient Greek mythology"
        assert data["Greek"]["coordinates"] == [37.9, 23.7]
        assert data["Greek"]["color"].startswith("#")

    def test_creates_stub_for_unknown_tradition(self, tmp_path, monkeypatch):
        books = [{"title": "Edda", "tradition": "Norse"}]
        corpus_dir = self._setup(tmp_path, monkeypatch, books=books)

        _update_traditions(force=False)

        data = json.loads((corpus_dir / "traditions.json").read_text())
        assert "Norse" in data
        assert data["Norse"]["description"] == ""
        assert data["Norse"]["color"].startswith("#")

    def test_includes_traditions_from_both_sources(self, tmp_path, monkeypatch):
        traditions = {"Indo-European": {"traditions": {"Celtic": {"description": "Celtic myths", "coordinates": [53.1, -7.7]}}}}
        books = [{"title": "Edda", "tradition": "Norse"}]
        corpus_dir = self._setup(tmp_path, monkeypatch, books=books, traditions=traditions)

        _update_traditions(force=False)

        data = json.loads((corpus_dir / "traditions.json").read_text())
        assert "Celtic" in data
        assert "Norse" in data

    def test_no_sources(self, tmp_path, monkeypatch):
        from settings import settings

        config_dir = tmp_path / "empty_config"
        corpus_dir = tmp_path / "corpus"
        corpus_dir.mkdir()
        monkeypatch.setattr(settings, "config_dir", config_dir)
        monkeypatch.setattr(settings, "corpus_dir", corpus_dir)

        _update_traditions(force=False)

        data = json.loads((corpus_dir / "traditions.json").read_text())
        assert data == {}


class TestLoadDownloadListExclude:
    def test_excluded_items_are_filtered(self, tmp_path, monkeypatch):
        from corpus.downloader import load_download_list
        from settings import settings

        config_dir = tmp_path / "config"
        config_dir.mkdir()
        items = [
            {"title": "Keep", "url": "http://x/1"},
            {"title": "Drop", "url": "http://x/2", "exclude": True},
        ]
        (config_dir / "corpus.json").write_text(json.dumps(items))
        monkeypatch.setattr(settings, "config_dir", config_dir)

        titles = [i["title"] for i in load_download_list()]
        assert titles == ["Keep"]
