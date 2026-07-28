"""EmbeddingsStage: desired() folds the corpus output fp into the transform key; actual()
reads the per-doc fingerprint back from Chroma metadata. Fake collection — no model, no DB."""

import pipeline.stages.embeddings as emb_mod
from embeddings.transform import chunk_fingerprint, transform_version
from pipeline import plan
from pipeline.stages import EmbeddingsStage
from settings import settings

CFG = {"key": "v1", "model": "m", "document_prefix": "", "preprocess_prompt": ""}


def _tv():
    return transform_version(CFG, settings.embedding.chunk_size, settings.embedding.chunk_overlap)


def _fp(content_fp: str) -> str:
    return chunk_fingerprint(content_fp, _tv())


class FakeCorpus:
    name, store = "corpus", None

    def __init__(self, fps):
        self._fps = fps

    def inputs(self):
        return []

    def doc_fingerprints(self):
        return dict(self._fps)

    # unused by these tests, but Stage is abstract
    desired = actual = lambda self: {}
    build = delete = lambda self, keys: None


class FakeCollection:
    def __init__(self, rows):  # rows: (chunk_id, document_id, fingerprint[, n_chunks])
        self._rows = rows
        self.deleted = []

    def get(self, include=None):
        metas = []
        for r in self._rows:
            m = {"document_id": r[1], "fingerprint": r[2]}
            if len(r) > 3 and r[3] is not None:  # legacy rows omit n_chunks
                m["n_chunks"] = r[3]
            metas.append(m)
        return {"ids": [r[0] for r in self._rows], "metadatas": metas}

    def delete(self, ids):
        self.deleted.extend(ids)


def _stage(monkeypatch, corpus_fps, collection):
    monkeypatch.setattr(emb_mod, "embedding_config", lambda k: CFG)
    if collection is None:
        monkeypatch.setattr(emb_mod.chroma_manager, "get_collection",
                            lambda k: (_ for _ in ()).throw(ValueError("no collection")))
    else:
        monkeypatch.setattr(emb_mod.chroma_manager, "get_collection", lambda k: collection)
    return EmbeddingsStage("v1", FakeCorpus(corpus_fps), store=object())


def test_clean_when_stored_fp_matches_folded_corpus_fp(monkeypatch):
    col = FakeCollection([("a::0", "a", _fp("cfA")), ("a::1", "a", _fp("cfA")), ("b::0", "b", _fp("cfB"))])
    stage = _stage(monkeypatch, {"a": "cfA", "b": "cfB"}, col)
    assert plan(stage).clean


def test_missing_when_document_not_embedded(monkeypatch):
    col = FakeCollection([("a::0", "a", _fp("cfA"))])
    stage = _stage(monkeypatch, {"a": "cfA", "b": "cfB"}, col)
    assert plan(stage).missing == {"b"}


def test_stale_when_corpus_text_changed(monkeypatch):
    # Stored fp was for the old corpus content; corpus now reports a new content fp.
    col = FakeCollection([("a::0", "a", _fp("OLD"))])
    stage = _stage(monkeypatch, {"a": "NEW"}, col)
    assert plan(stage).stale == {"a"}


def test_orphan_when_document_left_the_corpus(monkeypatch):
    col = FakeCollection([("a::0", "a", _fp("cfA")), ("gone::0", "gone", _fp("x"))])
    stage = _stage(monkeypatch, {"a": "cfA"}, col)
    assert plan(stage).orphans == {"gone"}


def test_actual_empty_without_a_collection(monkeypatch):
    stage = _stage(monkeypatch, {"a": "cfA"}, None)
    assert plan(stage).missing == {"a"}


def test_delete_drops_the_documents_chunks(monkeypatch):
    col = FakeCollection([("a::0", "a", "x"), ("a::1", "a", "x"), ("b::0", "b", "y")])
    stage = _stage(monkeypatch, {"a": "cfA", "b": "cfB"}, col)
    stage.delete({"a"})
    assert set(col.deleted) == {"a::0", "a::1"}


# --- completeness gate (n_chunks): a partially-embedded document is not "clean" ---

def test_complete_document_is_clean_with_n_chunks(monkeypatch):
    col = FakeCollection([("a::0", "a", _fp("cfA"), 2), ("a::1", "a", _fp("cfA"), 2)])
    stage = _stage(monkeypatch, {"a": "cfA"}, col)
    assert plan(stage).clean


def test_plain_hole_missing_tail_chunk_is_not_clean(monkeypatch):
    # Prefix written (0), tail (1) never embedded — n_chunks=2 but only 1 chunk present.
    col = FakeCollection([("a::0", "a", _fp("cfA"), 2)])
    stage = _stage(monkeypatch, {"a": "cfA"}, col)
    assert plan(stage).missing == {"a"}


def test_preprocess_hole_in_middle_is_not_clean_then_fills(monkeypatch):
    # Middle chunk (index 1) deferred (empty LLM transform); last present. count 2 != 3.
    holed = FakeCollection([("a::0", "a", _fp("cfA"), 3), ("a::2", "a", _fp("cfA"), 3)])
    assert plan(_stage(monkeypatch, {"a": "cfA"}, holed)).missing == {"a"}
    # Once the hole fills → all 3 present → clean.
    filled = FakeCollection([("a::0", "a", _fp("cfA"), 3), ("a::1", "a", _fp("cfA"), 3),
                             ("a::2", "a", _fp("cfA"), 3)])
    assert plan(_stage(monkeypatch, {"a": "cfA"}, filled)).clean


def test_mid_edit_fingerprint_mix_is_not_clean(monkeypatch):
    # One chunk re-embedded at the new fp, the other still old — never report a single fp.
    col = FakeCollection([("a::0", "a", _fp("NEW"), 2), ("a::1", "a", _fp("OLD"), 2)])
    stage = _stage(monkeypatch, {"a": "NEW"}, col)
    assert "a" in (plan(stage).missing | plan(stage).stale)


def test_legacy_chunks_without_n_chunks_stay_clean(monkeypatch):
    # Migration: pre-n_chunks rows fall back to any-chunk-with-fp — no rebuild, no loop.
    col = FakeCollection([("a::0", "a", _fp("cfA"))])  # no n_chunks element
    stage = _stage(monkeypatch, {"a": "cfA"}, col)
    assert plan(stage).clean
