import json
import logging
import time

from openai import (
    APIConnectionError,
    APITimeoutError,
    AuthenticationError,
    InternalServerError,
    NotFoundError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)

from .rate_limiter import DailyLimitReached

logger = logging.getLogger(__name__)

# Account/config-level failures: every subsequent call fails identically,
# so abort the run instead of retrying or skipping chunk by chunk.
_FATAL_CODES = {
    "insufficient_quota",
    "billing_hard_limit_reached",
    "invalid_api_key",
    "account_deactivated",
    "organization_restricted",
    "model_not_found",
    "model_not_available",
    "model_terminated",
}


class FatalLLMError(Exception):
    """Unrecoverable LLM error (quota, auth, missing model) — stops the whole run."""


def _estimate_tokens(messages: list[dict], output_estimate: int = 800) -> int:
    """Conservative pre-flight token estimate for the rate limiter.

    ASCII ~4 chars/token; non-ASCII (CJK/Indic/Cyrillic) ~1 token/char, where a flat chars//4
    badly under-counts and lets the TPM bucket over-admit. Deliberate over-estimate — reconcile()
    corrects the running total from real usage, so only the in-flight gate stays cautious.
    """
    ascii_chars = wide_chars = 0
    for message in messages:
        for ch in message.get("content", ""):
            if ord(ch) < 128:
                ascii_chars += 1
            else:
                wide_chars += 1
    return ascii_chars // 4 + wide_chars + output_estimate


def _error_body(e: Exception) -> dict:
    """The error body as a dict — from e.body, or the response if the SDK typed it."""
    body = getattr(e, "body", None)
    if isinstance(body, dict):
        return body
    response = getattr(e, "response", None)
    if response is not None:
        try:
            data = response.json()
        except Exception:
            data = None
        if isinstance(data, dict):
            return data
    return {}


def _error_message(e: Exception) -> str:
    body = _error_body(e)
    err = body.get("error")
    if isinstance(err, dict) and err.get("message"):
        return err["message"]
    if body.get("message"):
        return body["message"]
    return getattr(e, "message", None) or str(e)


def _error_codes(e: Exception) -> set:
    """Identifier strings (code/type) from the error, wherever the SDK placed them.

    OpenAI nests them as body["error"]["code"], so e.code can be None.
    """
    codes = {getattr(e, attr, None) for attr in ("code", "type")}
    body = _error_body(e)
    src = body.get("error") if isinstance(body.get("error"), dict) else body
    codes |= {src.get("code"), src.get("type")}
    return {c for c in codes if c}


def _classify(e: Exception) -> str:
    """Classify an exception as 'fatal', 'transient', or 'permanent'."""
    fatal_code = bool(_error_codes(e) & _FATAL_CODES)
    if isinstance(e, RateLimitError):
        return "fatal" if fatal_code else "transient"
    if isinstance(e, (APITimeoutError, APIConnectionError, InternalServerError)):
        return "transient"
    if isinstance(e, (AuthenticationError, PermissionDeniedError, NotFoundError)):
        return "fatal"
    if fatal_code:
        return "fatal"
    return "permanent"


def _retry_delay(e: Exception, attempt: int) -> float:
    response = getattr(e, "response", None)
    if response is not None:
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
    return min(2.0 ** attempt, 30.0)


# Our own error-aware retry loop (`_complete`) drives this; the SDK's retries are off.
MAX_RETRIES = 5


class LLMProcessor:
    def __init__(
        self,
        model_alias: str,
        *,
        temperature: float,
        use_json_mode: bool = True,
        request_timeout: float = 120.0,
    ):
        from model_registry import resolve_llm_provider

        from .rate_limiter import get_governor

        provider = resolve_llm_provider(model_alias)

        self.model_name = provider["model"]
        self.use_json_mode = use_json_mode
        self.temperature = temperature
        self.max_retries = MAX_RETRIES

        # One shared budget per underlying model across all callers (graphs, summaries, …).
        self.governor = get_governor(
            f"{provider['base_url']}::{provider['model']}",
            provider["model"],
            rpm=provider.get("rpm"),
            tpm=provider.get("tpm"),
            rpd=provider.get("rpd"),
        )

        kwargs: dict = {
            "base_url": provider["base_url"],
            "timeout": request_timeout,
            "max_retries": 0,  # retries handled in _complete (error-type aware)
        }
        if provider.get("api_key"):
            kwargs["api_key"] = provider["api_key"]
        self.client = OpenAI(**kwargs)

    def ask_text(self, system_prompt: str, user_content: str) -> str:
        content = self._complete(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
        )
        return content or ""

    def ask_json(self, system_prompt: str, user_content: str) -> list[dict] | None:
        """Return the parsed list, or None if the call produced no usable response.

        None lets callers tell a failed call apart from a valid-but-empty result
        (so a failure can be retried instead of cached as []).
        """
        content = self._complete(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                    + "\nOutput strictly valid JSON with a 'data' key containing the list of objects.",
                },
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"} if self.use_json_mode else None,
        )
        if content is None:
            return None
        return self._parse_json_list(content)

    def _complete(self, messages: list[dict], response_format: dict | None = None) -> str | None:
        """Run a chat completion, returning the message content or None on failure."""
        kwargs: dict = {
            "model": self.model_name,
            "messages": messages,
            "temperature": self.temperature,
        }
        if response_format is not None:
            kwargs["response_format"] = response_format

        est_tokens = _estimate_tokens(messages)

        for attempt in range(self.max_retries + 1):
            self.governor.acquire(est_tokens)  # raises DailyLimitReached if the breaker tripped
            t0 = time.monotonic()
            try:
                response = self.client.chat.completions.create(**kwargs)
                elapsed = time.monotonic() - t0
                usage = getattr(response, "usage", None)
                # Diagnostic: real server-side cost + latency. A runaway/looping generation
                # shows as a huge completion_tokens and an elapsed near the request timeout —
                # the signature of a call that is billed yet often lost to a client timeout.
                comp = getattr(usage, "completion_tokens", 0) or 0
                prompt_tok = getattr(usage, "prompt_tokens", 0) or 0
                (logger.warning if elapsed > 30 else logger.debug)(
                    "LLM ok (model=%s) in %.1fs: prompt=%d completion=%d tokens%s",
                    self.model_name, elapsed, prompt_tok, comp,
                    "  <- slow/large: possible runaway output" if elapsed > 30 else "",
                )
                self.governor.reconcile(est_tokens, getattr(usage, "total_tokens", 0) or 0)
                self.governor.note_success()
                # A successful call can still carry null content (refusal / tool-stop /
                # JSON-mode edge). Treat that as an empty result, not a failed call —
                # `.strip()` on None would raise and be misclassified as a failure,
                # so the chunk would never cache and would retry forever.
                content = response.choices[0].message.content
                return content.strip() if content else ""
            except Exception as e:
                elapsed = time.monotonic() - t0
                # This attempt spent no usable tokens *locally*; return its pre-charged estimate
                # so retries don't compound the TPM charge (reconcile only runs on success).
                # NB: this refund is our local governor only — a client timeout still lets the
                # server finish and BILL the generation, so `elapsed` near the request timeout
                # means this retry likely cost real money for a response we threw away.
                self.governor.refund(est_tokens)
                kind = _classify(e)
                code = getattr(e, "status_code", None) or getattr(e, "code", None)
                message = _error_message(e)

                if kind == "fatal":
                    raise FatalLLMError(f"{message} (model={self.model_name}, code={code})") from e

                if kind == "transient" and attempt < self.max_retries:
                    delay = _retry_delay(e, attempt)
                    logger.warning(
                        f"LLM call failed after {elapsed:.1f}s (model={self.model_name}, code={code}); "
                        f"retry {attempt + 1}/{self.max_retries} in {delay:.1f}s: {message}"
                    )
                    time.sleep(delay)
                    continue

                # Persistent rate limiting (not a transient blip): feed the breaker so
                # the run stops cleanly instead of grinding every chunk into errors.
                if isinstance(e, RateLimitError) and self.governor.note_rate_limited():
                    raise DailyLimitReached(
                        f"rate limit not recovering (model={self.model_name})"
                    ) from e

                logger.error(
                    f"LLM call failed after {elapsed:.1f}s, giving up "
                    f"(model={self.model_name}, code={code}): {message}"
                )
                return None
        return None

    @staticmethod
    def _parse_json_list(raw: str) -> list[dict]:
        try:
            result = json.loads(raw)
        except json.JSONDecodeError:
            cleaned = raw.replace("```json", "").replace("```", "").strip()
            try:
                result = json.loads(cleaned)
            except json.JSONDecodeError:
                logger.error(f"LLM returned invalid JSON (first 300 chars): {raw[:300]!r}")
                return []

        if isinstance(result, list):
            return result

        if isinstance(result, dict):
            if "data" in result and isinstance(result["data"], list):
                return result["data"]

            list_values = [v for v in result.values() if isinstance(v, list)]
            if len(list_values) == 1:
                return list_values[0]

            logger.warning(f"Unexpected JSON structure with {len(list_values)} list keys: {list(result.keys())}")

        return []
