import types

import httpx
from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)

from llm.client import LLMProcessor, _classify, _retry_delay


def _response(status: int, *, headers=None, body=None):
    return httpx.Response(
        status,
        request=httpx.Request("POST", "http://x"),
        headers=headers or {},
        json=body if body is not None else {},
    )


def _status_error(cls, status, *, codes=None):
    body = {"error": {"code": codes}} if codes else {}
    return cls("boom", response=_response(status, body=body), body=body.get("error") or {})


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


class TestClassify:
    def test_rate_limit_is_transient(self):
        assert _classify(_status_error(RateLimitError, 429)) == "transient"

    def test_rate_limit_with_fatal_code_is_fatal(self):
        # A 429 whose body carries a quota/billing code is not a passing blip —
        # retrying never recovers, so it must abort the run, not back off.
        err = _status_error(RateLimitError, 429, codes="insufficient_quota")
        assert _classify(err) == "fatal"

    def test_timeout_connection_server_are_transient(self):
        assert _classify(APITimeoutError(request=httpx.Request("POST", "http://x"))) == "transient"
        assert _classify(APIConnectionError(request=httpx.Request("POST", "http://x"))) == "transient"
        assert _classify(_status_error(InternalServerError, 500)) == "transient"

    def test_auth_permission_notfound_are_fatal(self):
        assert _classify(_status_error(AuthenticationError, 401)) == "fatal"
        assert _classify(_status_error(PermissionDeniedError, 403)) == "fatal"
        assert _classify(_status_error(NotFoundError, 404)) == "fatal"

    def test_unknown_error_with_fatal_code_is_fatal(self):
        err = RuntimeError("nope")
        err.code = "model_not_found"
        assert _classify(err) == "fatal"

    def test_plain_error_is_permanent(self):
        assert _classify(ValueError("malformed")) == "permanent"


class TestRetryDelay:
    def test_honors_retry_after_header(self):
        err = RuntimeError()
        err.response = _response(429, headers={"retry-after": "7"})
        assert _retry_delay(err, attempt=0) == 7.0

    def test_invalid_retry_after_falls_back_to_backoff(self):
        err = RuntimeError()
        err.response = _response(429, headers={"retry-after": "soon"})
        assert _retry_delay(err, attempt=2) == 4.0

    def test_exponential_backoff_without_response(self):
        assert _retry_delay(ValueError(), attempt=0) == 1.0
        assert _retry_delay(ValueError(), attempt=3) == 8.0

    def test_backoff_capped_at_30(self):
        assert _retry_delay(ValueError(), attempt=20) == 30.0


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
