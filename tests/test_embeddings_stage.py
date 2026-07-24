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
    def __init__(self, rows):  # rows: (chunk_id, document_id, fingerprint)
        self._rows = rows
        self.deleted = []

    def get(self, include=None):
        return {
            "ids": [r[0] for r in self._rows],
            "metadatas": [{"document_id": r[1], "fingerprint": r[2]} for r in self._rows],
        }

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
