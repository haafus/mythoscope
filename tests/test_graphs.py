from chunk_cache import append_cache, chunk_hash, clear_cache, load_cache
from graphs.extraction import deduplicate_entities, deduplicate_relations, extract_from_chunk


class TestDeduplicateEntities:
    def test_empty_list(self):
        assert deduplicate_entities([]) == []

    def test_no_duplicates(self):
        entities = [{"name": "Zeus"}, {"name": "Hera"}]
        result = deduplicate_entities(entities)
        assert len(result) == 2

    def test_removes_duplicates(self):
        entities = [{"name": "Zeus"}, {"name": "zeus"}, {"name": "ZEUS"}]
        result = deduplicate_entities(entities)
        assert len(result) == 1

    def test_merges_properties(self):
        entities = [
            {"name": "Zeus", "type": "god"},
            {"name": "zeus", "description": "king of gods"},
        ]
        result = deduplicate_entities(entities)
        assert len(result) == 1


class TestDeduplicateRelations:
    def test_empty_list(self):
        assert deduplicate_relations([]) == []

    def test_no_duplicates(self):
        rels = [
            {"subject": "Zeus", "object": "Hera", "relation": "married"},
            {"subject": "Zeus", "object": "Athena", "relation": "father"},
        ]
        result = deduplicate_relations(rels)
        assert len(result) == 2

    def test_removes_duplicates(self):
        rels = [
            {"subject": "Zeus", "object": "Hera", "relation": "married"},
            {"subject": "zeus", "object": "hera", "relation": "married"},
        ]
        result = deduplicate_relations(rels)
        assert len(result) == 1


class TestChunkCache:
    def test_roundtrip(self, tmp_path):
        p = tmp_path / "cache.jsonl"
        append_cache(p, "h1", {"beings": [{"Name": "Zeus"}]})
        append_cache(p, "h2", {"beings": []})
        cache = load_cache(p)
        assert cache["h1"] == {"beings": [{"Name": "Zeus"}]}
        assert set(cache) == {"h1", "h2"}

    def test_missing_returns_empty(self, tmp_path):
        assert load_cache(tmp_path / "nope.jsonl") == {}

    def test_skips_torn_last_line(self, tmp_path):
        p = tmp_path / "cache.jsonl"
        append_cache(p, "h1", 1)
        with open(p, "a", encoding="utf-8") as f:
            f.write('{"hash": "h2", "value": ')  # crash mid-write, no newline
        assert load_cache(p) == {"h1": 1}

    def test_clear_is_idempotent(self, tmp_path):
        p = tmp_path / "cache.jsonl"
        append_cache(p, "h1", 1)
        clear_cache(p)
        assert load_cache(p) == {}
        clear_cache(p)

    def test_hash_is_deterministic(self):
        assert chunk_hash("abc") == chunk_hash("abc")
        assert chunk_hash("abc") != chunk_hash("abd")


class _FakeLLM:
    def ask_json(self, system_prompt, user_content):
        if system_prompt == "c":
            return [{"Name": "Zeus"}]
        if system_prompt == "r":
            return [{"Subject": "Zeus", "Object": "Hera", "Relation": "spouse"}]
        if system_prompt == "l":
            return [{"Name": "Olympus"}]
        if system_prompt == "t":
            return "not-a-list"
        return []


class TestExtractFromChunk:
    def test_collects_all_entity_types(self):
        prompts = {"beings": "c", "relations": "r", "locations": "l", "time": "t"}
        out = extract_from_chunk(_FakeLLM(), "some text", prompts)

        assert out["beings"] == [{"Name": "Zeus"}]
        assert out["relations"][0]["Subject"] == "Zeus"
        assert out["locations"] == [{"Name": "Olympus"}]
        assert out["times"] == []
