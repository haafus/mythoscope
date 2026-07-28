"""Regression: a click on a scatter point must show *that* chunk as the head, even when a
duplicate/degenerate embedding makes the ANN query rank a different chunk first (the bug where
Popol Vuh #76 showed Ramayan #1709). get_point pins the clicked chunk fetched by id."""

from corpus.utils import chunk_id
from server.services.similarity import SimilarityService

CLICKED = ("popolvuh_docid", 76, "Popol Vuh chunk 76 text")
DUP = ("ramayan_docid", 1709, "Ramayan chunk 1709 text")   # near-identical embedding, ranks first


class _FakeCollection:
    """get(ids) returns the clicked chunk; query() returns the duplicate FIRST, then self."""

    def get(self, ids, include=None):
        assert ids == [chunk_id(CLICKED[0], CLICKED[1])]
        return {
            "ids": ids,
            "embeddings": [[0.1, 0.2, 0.3]],
            "metadatas": [{"document_id": CLICKED[0], "chunk_index": CLICKED[1]}],
            "documents": [CLICKED[2]],
        }

    def query(self, query_embeddings, n_results, include=None, where=None):
        rows = [  # DUP outranks self (both distance 0) — the exact condition that broke the head
            ({"document_id": DUP[0], "chunk_index": DUP[1]}, DUP[2], 0.0),
            ({"document_id": CLICKED[0], "chunk_index": CLICKED[1]}, CLICKED[2], 0.0),
            ({"document_id": "other_docid", "chunk_index": 3}, "other text", 0.4),
        ][:n_results]
        return {
            "metadatas": [[m for m, _, _ in rows]],
            "documents": [[d for _, d, _ in rows]],
            "distances": [[dist for _, _, dist in rows]],
        }


def test_get_point_head_is_the_clicked_chunk_despite_duplicate(monkeypatch):
    svc = SimilarityService()
    monkeypatch.setattr(svc, "_get_collection", lambda _key: _FakeCollection())

    results = svc.get_point("m", CLICKED[0], CLICKED[1], top_k=6, cross_tradition=False)

    head = results[0]
    assert (head["document_id"], head["chunk_index"]) == (CLICKED[0], CLICKED[1])  # the clicked chunk, not DUP
    assert head["text"] == CLICKED[2]

    neighbors = results[1:]
    # the clicked chunk is never listed among its own neighbours...
    assert all((n["document_id"], n["chunk_index"]) != (CLICKED[0], CLICKED[1]) for n in neighbors)
    # ...and the genuine near-duplicate surfaces as a neighbour instead of hijacking the head.
    assert any((n["document_id"], n["chunk_index"]) == (DUP[0], DUP[1]) for n in neighbors)
