import zipfile

import pytest

import export_bundle as eb


@pytest.fixture
def built_outputs(tmp_path, monkeypatch):
    """A small fake outputs/ tree with products, caches, raw scrape and logs."""
    from settings import settings

    out = tmp_path / "outputs"
    dirs = {
        "corpus_dir": out / "corpus",
        "embeddings_dir": out / "embeddings",
        "projections_dir": out / "projections",
        "graphs_dir": out / "graphs",
        "motifs_dir": out / "motifs",
        "logs_dir": out / "logs",
    }
    for attr, path in dirs.items():
        monkeypatch.setattr(settings, attr, path)
    # Isolate local file: sources under an (empty by default) sources/ dir.
    monkeypatch.setattr(settings, "sources_dir", tmp_path / "sources")

    def write(path, text="x"):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    # products
    write(dirs["corpus_dir"] / "corpus.json", "[]")
    write(dirs["corpus_dir"] / "Major" / "Trad" / "Book.txt", "text")
    write(dirs["embeddings_dir"] / "chroma.sqlite3", "db")
    write(dirs["projections_dir"] / "model" / "umap.json", "{}")
    write(dirs["graphs_dir"] / "Book_id" / "beings.json", "{}")
    write(dirs["motifs_dir"] / "berezkin.json", "{}")
    # caches (excluded by default)
    write(dirs["projections_dir"] / "model" / "summaries.jsonl", "")
    write(dirs["graphs_dir"] / "Book_id" / "extraction_cache.jsonl", "")
    write(dirs["motifs_dir"] / "raw" / "berezkin" / "a1.html", "<html>")
    # logs (never included)
    write(dirs["logs_dir"] / "run.log", "log")
    return tmp_path


def _names(result):
    with zipfile.ZipFile(result.path) as zf:
        return set(zf.namelist())


class TestExport:
    def test_excludes_caches_and_logs_by_default(self, built_outputs):
        result = eb.export_outputs(out_dir=built_outputs, timestamp="T")
        names = _names(result)
        assert names == {
            "outputs/corpus/corpus.json",
            "outputs/corpus/Major/Trad/Book.txt",
            "outputs/embeddings/chroma.sqlite3",
            "outputs/projections/model/umap.json",
            "outputs/graphs/Book_id/beings.json",
            "outputs/motifs/berezkin.json",
        }

    def test_caches_flag_includes_caches_but_not_logs(self, built_outputs):
        result = eb.export_outputs(out_dir=built_outputs, timestamp="T", include_caches=True)
        names = _names(result)
        assert "outputs/projections/model/summaries.jsonl" in names
        assert "outputs/graphs/Book_id/extraction_cache.jsonl" in names
        assert "outputs/motifs/raw/berezkin/a1.html" in names
        # logs are never bundled
        assert not any(n.startswith("outputs/logs/") for n in names)

    def test_archive_name_and_layout(self, built_outputs):
        result = eb.export_outputs(out_dir=built_outputs, timestamp="20260629-120000")
        assert result.path.name == "mythoscope-20260629-120000.zip"
        assert all(n.startswith("outputs/") for n in _names(result))
        assert set(result.components) == {"corpus", "embeddings", "projections", "graphs", "motifs"}

    def test_archive_name_caches_tag(self, built_outputs):
        result = eb.export_outputs(out_dir=built_outputs, timestamp="20260629-120000", include_caches=True)
        assert result.path.name == "mythoscope-caches-20260629-120000.zip"

    def test_partial_staging_is_cache(self):
        from pathlib import Path
        assert eb._is_cache("corpus", Path("raw/abc.partial"))     # validate-before-commit staging
        assert eb._is_cache("motifs", Path("x.tmp"))
        assert not eb._is_cache("corpus", Path("Region/Trad/Book.txt"))

    def test_includes_file_sources(self, built_outputs):
        from settings import settings

        src = settings.sources_dir
        src.mkdir(parents=True)
        (src / "myth.txt").write_text("local source text", encoding="utf-8")
        (src / "sub" / "epic.pdf").parent.mkdir(parents=True)
        (src / "sub" / "epic.pdf").write_bytes(b"%PDF-1.4 ...")

        result = eb.export_outputs(out_dir=built_outputs, timestamp="T")
        names = _names(result)
        assert "sources/myth.txt" in names
        assert "sources/sub/epic.pdf" in names
        assert "sources" in result.components

    def test_nothing_to_export(self, tmp_path, monkeypatch):
        from settings import settings

        for attr in ("corpus_dir", "embeddings_dir", "projections_dir", "graphs_dir", "motifs_dir", "sources_dir"):
            monkeypatch.setattr(settings, attr, tmp_path / "empty" / attr)
        result = eb.export_outputs(out_dir=tmp_path, timestamp="T")
        assert result.path is None
        assert not list(tmp_path.glob("*.zip"))


class TestOrphanSummary:
    """orphan_summary formats the driver's dry-run reap (a document removed from config, a
    dropped model's store artifact). Disk strays are no longer a category — build self-prunes."""

    def _stub(self, monkeypatch, level1, level2):
        import pipeline
        from pipeline.driver import CleanReport
        monkeypatch.setattr(pipeline, "build_pipeline", lambda: [])
        monkeypatch.setattr(pipeline, "clean", lambda stages, apply=False: CleanReport(level1=level1, level2=level2))

    def test_reports_level1_and_level2(self, monkeypatch):
        self._stub(monkeypatch, {"corpus": {"docX"}}, {"ChromaStore": {"dropped_model"}})
        lines = eb.orphan_summary()
        assert "corpus: orphan document docX" in lines
        assert "ChromaStore: orphan artifact dropped_model" in lines

    def test_scope_filters_to_family(self, monkeypatch):
        self._stub(monkeypatch, {"corpus": {"docX"}, "graphs": {"docY"}}, {"ChromaStore": {"dropped_model"}})
        lines = eb.orphan_summary(scope=("graphs",))
        assert lines == ["graphs: orphan document docY"]  # corpus filtered out; L2 only when unscoped
