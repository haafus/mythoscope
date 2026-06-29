import types

from llm.client import LLMProcessor


class _NoopGovernor:
    def acquire(self, est_tokens):
        pass

    def reconcile(self, est_tokens, actual_tokens):
        pass

    def refund(self, est_tokens):
        pass

    def note_success(self):
        pass

    def note_rate_limited(self):
        return False


class _SpyGovernor(_NoopGovernor):
    def __init__(self):
        self.acquires = 0
        self.refunds = 0

    def acquire(self, est_tokens):
        self.acquires += 1

    def refund(self, est_tokens):
        self.refunds += 1


def _processor_seq(behaviors, governor):
    """A processor whose client yields each behavior in turn (Exception -> raise, str -> content)."""
    p = LLMProcessor.__new__(LLMProcessor)
    p.model_name = "fake"
    p.use_json_mode = False
    p.temperature = 0.1
    p.max_retries = len(behaviors) - 1
    p.governor = governor
    it = iter(behaviors)

    def create(**kwargs):
        item = next(it)
        if isinstance(item, Exception):
            raise item
        return types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(content=item))], usage=None
        )

    p.client = types.SimpleNamespace(chat=types.SimpleNamespace(completions=types.SimpleNamespace(create=create)))
    return p


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


class TestRefundOnFailure:
    def test_permanent_failure_refunds_once(self):
        spy = _SpyGovernor()
        result = _processor_seq([ValueError("boom")], spy).ask_text("sys", "user")
        assert result == ""  # permanent failure -> None -> ask_text returns ""
        assert spy.acquires == 1 and spy.refunds == 1

    def test_transient_retry_refunds_each_failed_attempt(self, monkeypatch):
        import httpx
        from openai import APITimeoutError

        monkeypatch.setattr("llm.client.time.sleep", lambda _s: None)  # no real backoff wait
        timeout = APITimeoutError(request=httpx.Request("POST", "http://x"))
        spy = _SpyGovernor()
        result = _processor_seq([timeout, "recovered"], spy).ask_text("sys", "user")
        assert result == "recovered"
        assert spy.acquires == 2  # one failed + one successful attempt
        assert spy.refunds == 1  # only the failed attempt is refunded; success is reconciled
