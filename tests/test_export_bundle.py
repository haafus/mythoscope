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

    def test_orphan_summary_reports_level2_for_scoped_export(self, monkeypatch):
        import pipeline
        from pipeline.driver import CleanReport

        class _S:
            def __init__(self, name):
                self.name = name

        stages = [_S("embeddings:m1"), _S("projections:m1")]
        captured = {}

        def fake_clean(sgs, *, apply=False, targets=None):
            captured["targets"] = targets
            return CleanReport(level2={"ChromaStore": {"m2"}})   # a disabled model's orphan collection

        monkeypatch.setattr(pipeline, "build_pipeline", lambda: stages)
        monkeypatch.setattr(pipeline, "clean", fake_clean)

        lines = eb.orphan_summary(("embeddings",))
        assert captured["targets"] == {"embeddings:m1"}          # scope → driver targets (family match)
        assert any("ChromaStore" in ln and "m2" in ln for ln in lines)   # level-2 surfaced for a scoped export

    def test_raw_tier_and_staging_gates(self):
        from pathlib import Path
        # corpus + motifs raw are both the cache/raw tier (shipped only with --caches)
        assert eb._is_cache("corpus", Path("raw/page.html")) and eb._is_cache("motifs", Path("raw/x.html"))
        # .partial/.tmp are crash debris — staging, excluded even with --caches (separate gate)
        assert eb._is_staging(Path("raw/abc.partial")) and eb._is_staging(Path("x.tmp"))
        # a built product is neither
        assert not eb._is_staging(Path("Region/Trad/Book.txt"))
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
        cap = {}

        def fake_clean(stages, *, apply=False, targets=None):
            cap["targets"] = targets           # scope is delegated to the driver's targets now
            return CleanReport(level1=level1, level2=level2)

        monkeypatch.setattr(pipeline, "build_pipeline", lambda: [])
        monkeypatch.setattr(pipeline, "clean", fake_clean)
        return cap

    def test_reports_level1_and_level2(self, monkeypatch):
        cap = self._stub(monkeypatch, {"corpus": {"docX"}}, {"ChromaStore": {"dropped_model"}})
        lines = eb.orphan_summary()
        assert "corpus: orphan document docX" in lines
        assert "ChromaStore: orphan artifact dropped_model" in lines
        assert cap["targets"] is None          # unscoped → no driver targets (both levels, all stages)
