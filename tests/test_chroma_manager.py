from embeddings.chroma_manager import ChromaCollection


class _FakeCollection:
    def __init__(self, result):
        self._result = result

    def get(self, **kwargs):
        return self._result


class TestLoadData:
    def test_exposes_document_id_as_id_without_mutating_source(self):
        # B1: the chunk carries document_id (not text_id); load_data surfaces it as `id`.
        meta = {"document_id": "doc-fp", "chunk_index": 0}
        result = {"metadatas": [meta], "documents": ["hello"], "embeddings": [[0.1, 0.2]]}

        records, embeddings = ChromaCollection(_FakeCollection(result)).load_data()

        assert records[0]["id"] == "doc-fp"
        assert "document_id" not in records[0]  # surfaced as id, not duplicated
        assert records[0]["text"] == "hello"
        assert "document_id" in meta  # source dict left untouched
        assert embeddings.shape == (1, 2)

    def test_missing_document_id_does_not_crash(self):
        result = {"metadatas": [{"chunk_index": 2}], "documents": ["d"], "embeddings": [[1.0]]}

        records, _ = ChromaCollection(_FakeCollection(result)).load_data()

        assert records[0]["id"] == ""
        assert records[0]["chunk_index"] == 2
