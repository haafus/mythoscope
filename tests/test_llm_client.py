import types

from llm.client import LLMProcessor


class _NoopGovernor:
    def acquire(self, est_tokens):
        pass

    def reconcile(self, est_tokens, actual_tokens):
        pass

    def note_success(self):
        pass

    def note_rate_limited(self):
        return False


def _processor(content, *, use_json_mode=True):
    """An LLMProcessor wired to a fake client that returns `content`, no network/config."""
    p = LLMProcessor.__new__(LLMProcessor)
    p.model_name = "fake"
    p.use_json_mode = use_json_mode
    p.temperature = 0.1
    p.max_retries = 1
    p.governor = _NoopGovernor()
    response = types.SimpleNamespace(
        choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=content))],
        usage=None,
    )
    completions = types.SimpleNamespace(create=lambda **kwargs: response)
    p.client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=completions))
    return p


class TestNullContent:
    def test_ask_json_treats_null_content_as_empty_not_failure(self):
        # None content is a successful-but-empty response: ask_json must return [] (a
        # valid empty result that gets cached), never None (which means "retry").
        assert _processor(None).ask_json("sys", "user") == []

    def test_ask_text_returns_empty_string_for_null_content(self):
        assert _processor(None, use_json_mode=False).ask_text("sys", "user") == ""

    def test_valid_json_still_parses(self):
        assert _processor('{"data": [{"a": 1}]}').ask_json("sys", "user") == [{"a": 1}]
