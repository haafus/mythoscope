"""The projection build must rebuild when its input embeddings change (added texts),
not skip on mere file existence — the fp sidecar gates that."""

from collections import defaultdict

import numpy as np

from projections import PROJECTION_METHODS
from projections import build_projections as bp
from projections.analyzer import ModelData


def _model_data(ids, out_dir):
    data = [{"id": i, "chunk_index": 0, "tradition": "X"} for i in ids]
    return ModelData("bge", data, np.zeros((len(ids), 3)), out_dir)


def test_input_fingerprint_order_stable_but_content_sensitive(tmp_path):
    a = bp._input_fingerprint(_model_data(["a:0", "b:1"], tmp_path))
    reordered = bp._input_fingerprint(_model_data(["b:1", "a:0"], tmp_path))
    with_new = bp._input_fingerprint(_model_data(["a:0", "b:1", "c:0"], tmp_path))
    assert a == reordered      # order of chunks doesn't matter
    assert a != with_new       # an added text does


def test_generate_plots_rebuilds_on_new_inputs(tmp_path, monkeypatch):
    calls = []

    def fake_gen(data, embeddings, output_path, **kwargs):
        calls.append(output_path.name)
        output_path.write_text("{}", encoding="utf-8")

    chart_types = {m["chart_type"] for m in PROJECTION_METHODS}
    monkeypatch.setattr(bp, "CHART_GENERATORS", {ct: fake_gen for ct in chart_types})
    monkeypatch.setattr(bp, "SCATTER_TRANSFORMS", defaultdict(lambda: None))

    md = _model_data(["a:0", "b:0"], tmp_path)
    bp._generate_plots(md)
    assert len(calls) == len(PROJECTION_METHODS)   # first build makes them all
    assert (tmp_path / ".input-fp").exists()

    calls.clear()
    bp._generate_plots(md)                          # unchanged input
    assert calls == []                              # → skipped

    calls.clear()
    bp._generate_plots(_model_data(["a:0", "b:0", "c:0"], tmp_path))  # a new text
    assert len(calls) == len(PROJECTION_METHODS)    # → rebuilt

    calls.clear()
    bp._generate_plots(_model_data(["a:0", "b:0", "c:0"], tmp_path), force=True)
    assert len(calls) == len(PROJECTION_METHODS)    # force always rebuilds
