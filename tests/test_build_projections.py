"""The projection build must rebuild when its input embeddings change (added texts),
not skip on mere file existence — the fp sidecar gates that."""

from collections import defaultdict

import numpy as np

from projections import PROJECTION_METHODS
from projections import build_projections as bp
from projections.analyzer import ModelData


def _model_data(chunks, out_dir):
    # chunks: (document_id, chunk_index, fingerprint) tuples
    data = [{"id": d, "chunk_index": i, "fingerprint": fp, "tradition": "X"} for d, i, fp in chunks]
    return ModelData("bge", data, np.zeros((len(chunks), 3)), out_dir)


def test_input_fingerprint_order_stable_but_content_sensitive(tmp_path):
    base = [("a", 0, "fa"), ("b", 0, "fb")]
    a = bp._input_fingerprint(_model_data(base, tmp_path))
    reordered = bp._input_fingerprint(_model_data(list(reversed(base)), tmp_path))
    with_new = bp._input_fingerprint(_model_data([*base, ("c", 0, "fc")], tmp_path))
    edited = bp._input_fingerprint(_model_data([("a", 0, "fa2"), ("b", 0, "fb")], tmp_path))
    assert a == reordered      # chunk order doesn't matter
    assert a != with_new       # an added text does
    assert a != edited         # an edit to an existing text (same id, new fp) does too


def test_generate_plots_rebuilds_on_new_inputs(tmp_path, monkeypatch):
    calls = []

    def fake_gen(data, embeddings, output_path, **kwargs):
        calls.append(output_path.name)
        output_path.write_text("{}", encoding="utf-8")

    chart_types = {m["chart_type"] for m in PROJECTION_METHODS}
    monkeypatch.setattr(bp, "CHART_GENERATORS", {ct: fake_gen for ct in chart_types})
    monkeypatch.setattr(bp, "SCATTER_TRANSFORMS", defaultdict(lambda: None))

    md = _model_data([("a", 0, "fa"), ("b", 0, "fb")], tmp_path)
    bp._generate_plots(md)
    assert len(calls) == len(PROJECTION_METHODS)   # first build makes them all
    assert (tmp_path / ".input-fp").exists()

    calls.clear()
    bp._generate_plots(md)                          # unchanged input
    assert calls == []                              # → skipped

    calls.clear()
    grown = _model_data([("a", 0, "fa"), ("b", 0, "fb"), ("c", 0, "fc")], tmp_path)  # a new text
    bp._generate_plots(grown)
    assert len(calls) == len(PROJECTION_METHODS)    # → rebuilt

    calls.clear()
    bp._generate_plots(grown, force=True)
    assert len(calls) == len(PROJECTION_METHODS)    # force always rebuilds
