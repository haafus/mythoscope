from embeddings.chroma_manager import ChromaCollection


class _FakeCollection:
    def __init__(self, result):
        self._result = result

    def get(self, **kwargs):
        return self._result


class TestLoadData:
    def test_renames_text_id_without_mutating_source(self):
        meta = {"text_id": "Book", "tradition": "Greek", "chunk_index": 0}
        result = {"metadatas": [meta], "documents": ["hello"], "embeddings": [[0.1, 0.2]]}

        records, embeddings = ChromaCollection(_FakeCollection(result)).load_data()

        assert records[0]["id"] == "Book"
        assert "text_id" not in records[0]  # renamed, not duplicated
        assert records[0]["tradition"] == "Greek"
        assert records[0]["text"] == "hello"
        assert "text_id" in meta  # source dict left untouched
        assert embeddings.shape == (1, 2)

    def test_missing_text_id_does_not_crash(self):
        result = {"metadatas": [{"tradition": "X"}], "documents": ["d"], "embeddings": [[1.0]]}

        records, _ = ChromaCollection(_FakeCollection(result)).load_data()

        assert records[0]["id"] == ""
        assert records[0]["tradition"] == "X"
