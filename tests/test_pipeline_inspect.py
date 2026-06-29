import types

from click.testing import CliRunner

from graphs.completion import GRAPH_FILES, is_book_complete
from pipeline_inspect import GRAPHS_CACHE, SUMMARIES_CACHE, cache_files, graphs_status


def _settings(tmp_path):
    return types.SimpleNamespace(
        graphs_dir=tmp_path / "graphs",
        projections_dir=tmp_path / "projections",
        corpus_dir=tmp_path / "corpus",
        embeddings_dir=tmp_path / "embeddings",
    )


def _complete_book(d):
    d.mkdir(parents=True, exist_ok=True)
    for name in GRAPH_FILES:
        (d / name).write_text("[]")


class TestCompletion:
    def test_incomplete_when_one_graph_missing(self, tmp_path):
        b = tmp_path / "B"
        b.mkdir()
        (b / "beings.json").write_text("[]")
        (b / "realms.json").write_text("[]")  # ages.json missing
        assert not is_book_complete(b)

    def test_complete_with_all_three(self, tmp_path):
        b = tmp_path / "B"
        _complete_book(b)
        assert is_book_complete(b)


class TestCacheFiles:
    def test_finds_all_including_partial(self, tmp_path):
        s = _settings(tmp_path)
        complete = s.graphs_dir / "A"
        _complete_book(complete)
        (complete / GRAPHS_CACHE).write_text("x")
        partial = s.graphs_dir / "B"
        partial.mkdir(parents=True)
        (partial / GRAPHS_CACHE).write_text("y")  # no graphs -> partial book
        (s.projections_dir / "m").mkdir(parents=True)
        (s.projections_dir / "m" / SUMMARIES_CACHE).write_text("z")

        owners = sorted(p.parent.name for p, _ in cache_files(s))
        assert owners == ["A", "B", "m"]  # complete + partial graph caches + summaries


class TestGraphsStatus:
    def test_counts_only_complete_books(self, tmp_path):
        s = _settings(tmp_path)
        _complete_book(s.graphs_dir / "A")
        partial = s.graphs_dir / "B"
        partial.mkdir(parents=True)
        (partial / "beings.json").write_text("[]")
        assert graphs_status(s)["count"] == 1

    def test_size_excludes_cache(self, tmp_path):
        s = _settings(tmp_path)
        a = s.graphs_dir / "A"
        _complete_book(a)
        (a / GRAPHS_CACHE).write_text("X" * 1000)
        assert graphs_status(s)["total_size"] < 1000  # cache bytes not counted


class TestCleanCaches:
    def _point_settings(self, monkeypatch, tmp_path):
        from settings import settings
        for attr in ("graphs_dir", "projections_dir", "corpus_dir", "embeddings_dir"):
            monkeypatch.setattr(settings, attr, tmp_path / attr.replace("_dir", ""))
        book = settings.graphs_dir / "A"
        book.mkdir(parents=True)
        (book / GRAPHS_CACHE).write_text("cache")
        return book

    def test_caches_shown_but_kept_without_flag(self, tmp_path, monkeypatch):
        book = self._point_settings(monkeypatch, tmp_path)
        out = CliRunner().invoke(__import__("cli").mytho, ["clean"]).output
        assert "Caches" in out
        assert "--caches" in out
        assert (book / GRAPHS_CACHE).exists()  # not removed without the flag

    def test_caches_removed_with_flag_and_apply(self, tmp_path, monkeypatch):
        book = self._point_settings(monkeypatch, tmp_path)
        CliRunner().invoke(__import__("cli").mytho, ["clean", "--caches", "--apply"])
        assert not (book / GRAPHS_CACHE).exists()  # removed
