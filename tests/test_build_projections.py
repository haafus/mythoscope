"""Projections must rebuild when the input embeddings change, and — crucially — must decide
that from chunk metadata alone, without loading the (large) embedding vectors, when current."""

import settings as settings_mod
from projections import PROJECTION_METHODS
from projections import build_projections as bp
from projections.analyzer import ModelData


def _metas(chunks):
    # chunks: (document_id, chunk_index, fingerprint) tuples
    return [{"document_id": d, "chunk_index": i, "fingerprint": fp} for d, i, fp in chunks]


def test_fingerprint_from_metas_order_stable_but_content_sensitive():
    f = bp._fingerprint_from_metas
    base = _metas([("a", 0, "fa"), ("b", 0, "fb")])
    assert f(base) == f(list(reversed(base)))                       # order doesn't matter
    assert f(base) != f(_metas([("a", 0, "fa"), ("b", 0, "fb"), ("c", 0, "fc")]))  # a new text
    assert f(base) != f(_metas([("a", 0, "fa2"), ("b", 0, "fb")]))  # an edit (same id, new fp)


class _FakeCollection:
    def __init__(self, metas):
        self._metas = metas

    def get(self, include=None):
        return {"metadatas": self._metas}


def test_build_projections_skips_vector_load_when_current(tmp_path, monkeypatch):
    import embeddings.chroma_manager as cm

    metas_box = {"metas": _metas([("a", 0, "fa"), ("b", 0, "fb")])}
    monkeypatch.setattr(settings_mod.settings, "projections_dir", tmp_path)
    monkeypatch.setattr(cm, "get_available_models", lambda: ["v1"])
    monkeypatch.setattr(cm, "get_collection", lambda key: _FakeCollection(metas_box["metas"]))

    loads = []

    def fake_load(key):
        loads.append(key)
        (tmp_path / key).mkdir(parents=True, exist_ok=True)
        return ModelData(model_name=key, data=[], embeddings=None, output_dir=tmp_path / key)

    monkeypatch.setattr(bp, "load_model_data", fake_load)

    def gen(name):
        def _g(data, embeddings, output_path, **kwargs):
            output_path.write_text("{}", encoding="utf-8")
        return _g

    monkeypatch.setattr(bp, "CHART_GENERATORS", {m["chart_type"]: gen(m["chart_type"]) for m in PROJECTION_METHODS})
    monkeypatch.setattr(bp, "SCATTER_TRANSFORMS", {m["key"]: None for m in PROJECTION_METHODS})

    bp.build_projections()
    assert loads == ["v1"]                                   # first run loads vectors + generates
    assert (tmp_path / "v1" / ".input-fp").exists()

    loads.clear()
    bp.build_projections()                                   # inputs unchanged
    assert loads == []                                       # → skipped WITHOUT loading vectors

    loads.clear()
    metas_box["metas"] = _metas([("a", 0, "fa"), ("b", 0, "fb"), ("c", 0, "fc")])  # a new text
    bp.build_projections()
    assert loads == ["v1"]                                   # → vectors loaded again, rebuilt
