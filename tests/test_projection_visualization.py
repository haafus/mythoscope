import importlib.util
import os
import sys
import types

import numpy as np

_src = os.path.join(os.path.dirname(__file__), "..", "src")

# Stub plotly/pandas ONLY for the duration of loading visualization.py.
# Leaving a fake `pandas` in sys.modules session-wide breaks sklearn, which
# sniffs sys.modules to decide whether pandas support is available.
_px = types.ModuleType("plotly.express")
_px.colors = types.SimpleNamespace(qualitative=types.SimpleNamespace(Plotly=["#111111", "#222222", "#333333"]))


class _FakeScatter:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


_go = types.ModuleType("plotly.graph_objects")
_go.Scatter = _FakeScatter
_go.Figure = type("Figure", (), {})

_subplots = types.ModuleType("plotly.subplots")
_subplots.make_subplots = lambda *a, **kw: None

_pd = types.ModuleType("pandas")
_pd.DataFrame = type("DataFrame", (), {})  # type: ignore[attr-defined]

_proj_pkg = types.ModuleType("projection")
_proj_pkg.__path__ = [os.path.join(_src, "projection")]  # type: ignore[attr-defined]

_added_stubs: list[str] = []
for _name, _module in [
    ("plotly", types.ModuleType("plotly")),
    ("plotly.express", _px),
    ("plotly.graph_objects", _go),
    ("plotly.subplots", _subplots),
    ("pandas", _pd),
    ("projection", _proj_pkg),
]:
    if _name not in sys.modules:
        sys.modules[_name] = _module
        _added_stubs.append(_name)

try:
    _spec = importlib.util.spec_from_file_location(
        "projection.visualization",
        os.path.join(_src, "projection", "visualization.py"),
    )
    assert _spec is not None and _spec.loader is not None
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
finally:
    for _name in _added_stubs:
        sys.modules.pop(_name, None)

_traditions_of = _mod._traditions_of
_get_color_map = _mod._get_color_map
_add_tradition_scatter_traces = _mod._add_tradition_scatter_traces


class _FakeFig:
    def __init__(self):
        self.traces: list[tuple] = []

    def add_trace(self, trace, row=None, col=None):
        self.traces.append((trace, row, col))


class TestTraditionsOf:
    def test_extracts_traditions(self):
        data = [{"tradition": "greek"}, {"tradition": "norse"}, {}]
        assert _traditions_of(data) == ["greek", "norse", "unknown"]


class TestGetColorMap:
    def test_prefers_colors_from_data(self):
        data = [{"tradition": "greek", "color": "#ff0000"}, {"tradition": "norse"}]
        cmap = _get_color_map(data)
        assert cmap["greek"] == "#ff0000"
        assert cmap["norse"] in ["#111111", "#222222", "#333333"]


class TestAddTraditionScatterTraces:
    def _run(self, **kwargs):
        fig = _FakeFig()
        coords = np.array([[0.0, 0.0], [1.0, 1.0], [2.0, 2.0]])
        traditions = np.array(["greek", "norse", "greek"])
        color_map = {"greek": "#ff0000", "norse": "#00ff00"}
        _add_tradition_scatter_traces(
            fig, coords, traditions, color_map, row=2, col=3, show_legend=True, **kwargs
        )
        return fig

    def test_one_trace_per_tradition(self):
        fig = self._run()
        assert len(fig.traces) == 2
        names = {trace.kwargs["name"] for trace, _, _ in fig.traces}
        assert names == {"greek", "norse"}

    def test_points_grouped_by_tradition(self):
        fig = self._run()
        greek = next(t for t, _, _ in fig.traces if t.kwargs["name"] == "greek")
        assert list(greek.kwargs["x"]) == [0.0, 2.0]
        assert greek.kwargs["marker"]["color"] == "#ff0000"

    def test_placed_in_requested_subplot(self):
        fig = self._run()
        assert all((row, col) == (2, 3) for _, row, col in fig.traces)

    def test_legend_hidden_when_disabled(self):
        fig = _FakeFig()
        coords = np.array([[0.0, 0.0]])
        _add_tradition_scatter_traces(
            fig, coords, np.array(["greek"]), {"greek": "#ff0000"}, row=1, col=1, show_legend=False
        )
        trace = fig.traces[0][0]
        assert trace.kwargs["showlegend"] is False
        assert trace.kwargs["name"] is None

    def test_marker_extra_overrides_defaults(self):
        fig = _FakeFig()
        coords = np.array([[0.0, 0.0]])
        _add_tradition_scatter_traces(
            fig, coords, np.array(["greek"]), {"greek": "#ff0000"},
            row=1, col=1, show_legend=True, marker_extra={"size": 6},
        )
        assert fig.traces[0][0].kwargs["marker"]["size"] == 6

    def test_custom_axis_labels_in_hover(self):
        fig = _FakeFig()
        coords = np.array([[0.0, 0.0]])
        _add_tradition_scatter_traces(
            fig, coords, np.array(["greek"]), {"greek": "#ff0000"},
            row=1, col=1, show_legend=True, x_label="UMAP component 1", y_label="UMAP component 2",
        )
        hover = fig.traces[0][0].kwargs["hovertemplate"]
        assert "UMAP component 1" in hover
        assert "UMAP component 2" in hover
