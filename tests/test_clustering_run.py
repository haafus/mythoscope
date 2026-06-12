import importlib.util
import os
import sys
import types

import numpy as np

_src = os.path.join(os.path.dirname(__file__), "..", "src")

# Load run_clustering.py without executing clustering/__init__.py or importing
# heavy optional deps (plotly, chromadb): stub the parent package and the two
# modules that pull them in.
_clustering_pkg = types.ModuleType("clustering")
_clustering_pkg.__path__ = [os.path.join(_src, "clustering")]  # type: ignore[attr-defined]

_viz_stub = types.ModuleType("clustering.visualization")
for _fn in [
    "plot_clustering_results_2d",
    "plot_confusion_matrix_heatmap",
    "plot_metrics_dashboard",
    "reduce_dimensions",
]:
    setattr(_viz_stub, _fn, lambda *a, **kw: None)

_proj_pkg = types.ModuleType("projection")
_proj_pkg.__path__ = [os.path.join(_src, "projection")]  # type: ignore[attr-defined]

_analyzer_stub = types.ModuleType("projection.analyzer")
_analyzer_stub.EmbeddingAnalyzer = type("EmbeddingAnalyzer", (), {})  # type: ignore[attr-defined]

# Stubs live in sys.modules only while run_clustering.py is being loaded,
# so they cannot leak into other test modules in the same pytest session.
_added_stubs: list[str] = []
for _name, _module in [
    ("clustering", _clustering_pkg),
    ("clustering.visualization", _viz_stub),
    ("projection", _proj_pkg),
    ("projection.analyzer", _analyzer_stub),
]:
    if _name not in sys.modules:
        sys.modules[_name] = _module
        _added_stubs.append(_name)

try:
    _spec = importlib.util.spec_from_file_location(
        "clustering.run_clustering",
        os.path.join(_src, "clustering", "run_clustering.py"),
    )
    assert _spec is not None and _spec.loader is not None
    _mod = importlib.util.module_from_spec(_spec)
    sys.modules["clustering.run_clustering"] = _mod
    _spec.loader.exec_module(_mod)
finally:
    for _name in _added_stubs + ["clustering.run_clustering"]:
        sys.modules.pop(_name, None)

_params_for = _mod._params_for
_get_num_clusters = _mod._get_num_clusters
_prepare_model_data = _mod._prepare_model_data


class TestParamsFor:
    def test_kmeans_spectral_birch_use_n_clusters(self):
        for name in ("kmeans", "spectral", "birch"):
            assert _params_for(name, 5) == {"n_clusters": 5}

    def test_gmm_uses_n_components(self):
        assert _params_for("gmm", 4) == {"n_components": 4}

    def test_density_models_need_no_cluster_count(self):
        for name in ("hdbscan", "meanshift", "optics"):
            assert _params_for(name, 7) == {}


class TestGetNumClusters:
    def test_empty_labels(self):
        assert _get_num_clusters([]) == 0

    def test_single_sample(self):
        assert _get_num_clusters(["greek"]) == 1

    def test_counts_unique_labels(self):
        assert _get_num_clusters(["greek", "norse", "greek", "norse", "slavic"]) == 3

    def test_minimum_two_clusters(self):
        assert _get_num_clusters(["greek", "greek", "greek"]) == 2

    def test_unknown_labels_excluded(self):
        assert _get_num_clusters(["greek", "norse", "unknown", "unknown", "unknown"]) == 2


class _FakeAnalyzer:
    def __init__(self, models=None, data=None):
        self.available_models = models or []
        self._data = data or []
        self.model_name = self.available_models[0] if self.available_models else None
        self.set_model_calls: list[str] = []

    def set_model(self, name):
        self.model_name = name
        self.set_model_calls.append(name)

    def filter_by_model(self):
        return self._data


def _sample_data(n=4):
    return [{"embedding": np.ones(8) * i, "tradition": f"trad{i % 2}"} for i in range(n)]


class TestPrepareModelData:
    def test_no_models_returns_none(self):
        assert _prepare_model_data(None, _FakeAnalyzer(models=[])) is None

    def test_defaults_to_first_model(self):
        analyzer = _FakeAnalyzer(models=["m1", "m2"], data=_sample_data())
        result = _prepare_model_data(None, analyzer)
        assert result is not None
        model_name, embeddings, labels = result
        assert model_name == "m1"
        assert analyzer.set_model_calls == ["m1"]
        assert embeddings.shape == (4, 8)
        assert set(labels) == {"trad0", "trad1"}

    def test_switches_to_requested_model(self):
        analyzer = _FakeAnalyzer(models=["m1", "m2"], data=_sample_data())
        result = _prepare_model_data("m2", analyzer)
        assert result is not None
        assert result[0] == "m2"
        assert analyzer.set_model_calls == ["m2"]

    def test_no_data_returns_none(self):
        analyzer = _FakeAnalyzer(models=["m1"], data=[])
        assert _prepare_model_data("m1", analyzer) is None
