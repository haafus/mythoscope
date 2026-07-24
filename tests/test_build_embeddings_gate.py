"""The embeddings sync must decide there is nothing to encode — and prune stale chunks —
without loading the model (torch/sentence-transformers). The gate runs on cheap ops only."""

from embeddings import build_embeddings as be
from model_registry import embedding_variants


class _FakeCollection:
    name = "variant"

    def __init__(self):
        self.deleted: list[str] = []
        self.modified: dict | None = None

    def get(self, include=None):
        return {"ids": [], "metadatas": []}

    def delete(self, ids):
        self.deleted.extend(ids)

    def modify(self, metadata):
        self.modified = metadata


class _FakeFile:
    def __init__(self, doc_id):
        self.document_id = doc_id
        self.filename = f"{doc_id}.txt"

    def read_text(self):
        return "hello world"

    def content_fingerprint(self):
        return f"fp-{self.document_id}"


def _wire(monkeypatch, coll, plan):
    monkeypatch.setattr(be, "iter_files", lambda _d: [_FakeFile("a"), _FakeFile("b")])
    monkeypatch.setattr(be.chroma_manager, "get_or_create_collection", lambda *a, **k: coll)
    monkeypatch.setattr(be, "orphan_chunk_ids", lambda *a, **k: [])
    monkeypatch.setattr(be, "embed_plan", lambda *a, **k: plan)


def test_no_encode_no_model_load(monkeypatch):
    key = embedding_variants()[0]
    coll = _FakeCollection()
    _wire(monkeypatch, coll, ([], []))          # nothing to embed, nothing stale

    # encoder=None in, and returned unchanged → the model was never constructed/loaded.
    assert be._save_corpus_to_chroma(key, None) is None
    assert coll.modified is not None            # metadata still stamped


def test_stale_pruned_without_model(monkeypatch):
    key = embedding_variants()[0]
    coll = _FakeCollection()
    _wire(monkeypatch, coll, ([], ["a:9"]))     # only stale to delete, still nothing to encode

    assert be._save_corpus_to_chroma(key, None) is None   # no model loaded
    assert "a:9" in coll.deleted                          # but stale was pruned
