import importlib.util
import os
import sys
import types

import pytest

pd = pytest.importorskip("pandas")

_src = os.path.join(os.path.dirname(__file__), "..", "src")

# Stub chromadb so projection.loader can be imported without the real package.
_chromadb = types.ModuleType("chromadb")
_chromadb.Client = type("Client", (), {})  # type: ignore[attr-defined]

_proj_pkg = types.ModuleType("projection")
_proj_pkg.__path__ = [os.path.join(_src, "projection")]  # type: ignore[attr-defined]

_loader_stub = types.ModuleType("projection.loader")
_loader_stub.EmbeddingDataLoader = type(  # type: ignore[attr-defined]
    "EmbeddingDataLoader", (), {"get_available_models": lambda self: [], "load_data": lambda self, **kw: []},
)

_added: list[str] = []
for _name, _mod in [
    ("chromadb", _chromadb),
    ("projection", _proj_pkg),
    ("projection.loader", _loader_stub),
]:
    if _name not in sys.modules:
        sys.modules[_name] = _mod
        _added.append(_name)

try:
    _spec = importlib.util.spec_from_file_location(
        "projection.analyzer",
        os.path.join(_src, "projection", "analyzer.py"),
    )
    assert _spec is not None and _spec.loader is not None
    _analyzer_mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_analyzer_mod)
finally:
    for _name in _added:
        sys.modules.pop(_name, None)

_save_summary_to_files = _analyzer_mod._save_summary_to_files


def _sample_stats():
    return {
        "n_samples": 3,
        "embedding_dim": 128,
        "traditions": 2,
        "tradition_counts": {"greek": 2, "norse": 1},
        "model": "test-model",
        "total_chunks_in_db": 10,
    }


def _sample_data():
    return [
        {"id": "a", "tradition": "greek", "text": "hello", "embedding": [0.1, 0.2]},
        {"id": "b", "tradition": "norse", "text": "world", "embedding": [0.3, 0.4]},
        {"id": "c", "tradition": "greek", "text": "foo", "embedding": [0.5, 0.6]},
    ]


class TestSaveSummaryToFiles:
    def test_creates_csv_and_txt(self, tmp_path):
        _save_summary_to_files(_sample_data(), _sample_stats(), tmp_path)
        assert (tmp_path / "embeddings_data.csv").exists()
        assert (tmp_path / "analysis_summary.txt").exists()

    def test_csv_excludes_embedding_column(self, tmp_path):
        _save_summary_to_files(_sample_data(), _sample_stats(), tmp_path)
        df = pd.read_csv(tmp_path / "embeddings_data.csv")
        assert "embedding" not in df.columns
        assert "id" in df.columns
        assert "tradition" in df.columns
        assert len(df) == 3

    def test_txt_contains_model_and_stats(self, tmp_path):
        _save_summary_to_files(_sample_data(), _sample_stats(), tmp_path)
        txt = (tmp_path / "analysis_summary.txt").read_text()
        assert "test-model" in txt
        assert "128" in txt
        assert "greek" in txt
        assert "norse" in txt

    def test_txt_tradition_percentages(self, tmp_path):
        _save_summary_to_files(_sample_data(), _sample_stats(), tmp_path)
        txt = (tmp_path / "analysis_summary.txt").read_text()
        assert "66.7%" in txt
        assert "33.3%" in txt

    def test_txt_omits_model_when_missing(self, tmp_path):
        stats = _sample_stats()
        stats["model"] = None
        _save_summary_to_files(_sample_data(), stats, tmp_path)
        txt = (tmp_path / "analysis_summary.txt").read_text()
        assert "Model:" not in txt

    def test_creates_output_dir_if_needed(self, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        _save_summary_to_files(_sample_data(), _sample_stats(), nested)
        assert (nested / "embeddings_data.csv").exists()
