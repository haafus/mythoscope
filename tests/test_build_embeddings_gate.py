"""The embeddings sync must decide there is nothing to encode — and prune stale chunks —
without loading the model (torch/sentence-transformers). The gate runs on cheap ops only."""

import numpy as np

from embeddings import build_embeddings as be
from model_registry import embedding_variants


class _FakeCollection:
    name = "variant"

    def __init__(self, existing=None):
        self.deleted: list[str] = []
        self.modified: dict | None = None
        self.upserted: list[str] = []
        self._existing = existing or {"ids": [], "metadatas": []}

    def get(self, include=None):
        return self._existing

    def count(self):
        return len(self._existing["ids"])

    def delete(self, ids):
        self.deleted.extend(ids)

    def upsert(self, ids, embeddings, metadatas, documents):
        self.upserted.extend(ids)

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
    assert be._save_corpus_to_chroma(key, None, rebuild={"a", "b"}) is None
    assert coll.modified is not None            # metadata still stamped


def test_stale_pruned_without_model(monkeypatch):
    key = embedding_variants()[0]
    coll = _FakeCollection()
    _wire(monkeypatch, coll, ([], ["a:9"]))     # only stale to delete, still nothing to encode

    assert be._save_corpus_to_chroma(key, None, rebuild={"a", "b"}) is None   # no model loaded
    assert "a:9" in coll.deleted                          # but stale was pruned


class _FakeEncoder:
    model_name = "fake"

    def load(self, key):
        pass

    def encode(self, inputs, **kwargs):
        return np.zeros((len(inputs), 3), dtype=np.float32)

    def release_cache(self):
        pass

    def unload(self):
        pass


def test_rebuilt_document_that_shrank_reaps_its_old_tail(monkeypatch):
    """A rebuild-listed doc that now chunks to FEWER chunks must have its stale tail deleted.

    Regression: the rebuild step nulls each rebuild-doc chunk's stored fp but must KEEP the
    chunk-id key, because embed_plan derives the tail-to-delete by scanning existing_fp for
    indices >= the new n_chunks. Popping the keys blinded that and stranded the old tail
    (rows exceeding n_chunks — the Poetic Edda 1035-vs-986 leftover)."""
    # 'a' was stored with 4 chunks; 'b' (not rebuilt) with 2. 'a' now re-chunks to 2.
    existing = {
        "ids": ["a::0", "a::1", "a::2", "a::3", "b::0", "b::1"],
        "metadatas": [
            *({"document_id": "a", "fingerprint": "oldfp", "chunk_index": i, "n_chunks": 4} for i in range(4)),
            *({"document_id": "b", "fingerprint": "gfp", "chunk_index": i, "n_chunks": 2} for i in range(2)),
        ],
    }
    coll = _FakeCollection(existing)
    monkeypatch.setattr(be, "iter_files", lambda _d: [_FakeFile("a"), _FakeFile("b")])
    monkeypatch.setattr(be.chroma_manager, "get_or_create_collection", lambda *a, **k: coll)
    monkeypatch.setattr(be, "orphan_chunk_ids", lambda *a, **k: [])
    monkeypatch.setattr(be, "embedding_config",
                        lambda key: {"key": key, "model": "m", "preprocess_prompt": "", "document_prefix": ""})
    monkeypatch.setattr(be, "chunk_text", lambda content, size, overlap: ["c0", "c1"])  # doc now 2 chunks

    be._save_corpus_to_chroma("variant", _FakeEncoder(), rebuild={"a"})

    assert set(coll.deleted) == {"a::2", "a::3"}   # the shrunk tail is reaped
    assert coll.upserted == ["a::0", "a::1"]       # both surviving chunks re-embedded
    assert not any(cid.startswith("b::") for cid in coll.deleted)   # 'b' (not rebuilt) untouched
