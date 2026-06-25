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


def _error_message(e: Exception) -> str:
    body = getattr(e, "body", None)
    if isinstance(body, dict):
        return (body.get("error") or {}).get("message") or str(e)
    return getattr(e, "message", None) or str(e)


def _error_codes(e: Exception) -> set:
    """Identifier strings (code/type) from the error, wherever the SDK placed them.

    OpenAI nests them as body["error"]["code"], so e.code can be None.
    """
    codes = {getattr(e, attr, None) for attr in ("code", "type")}
    body = getattr(e, "body", None)
    if isinstance(body, dict):
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


class LLMProcessor:
    def __init__(
        self,
        model_alias: str | None = None,
        use_json_mode: bool = True,
        request_timeout: float = 120.0,
    ):
        from model_registry import resolve_llm_provider
        from settings import settings

        cfg = settings.llm
        provider = resolve_llm_provider(model_alias or cfg.model)

        self.model_name = provider["model"]
        self.use_json_mode = use_json_mode
        self.temperature = cfg.temperature
        self.max_retries = cfg.max_retries

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

    def ask_json(self, system_prompt: str, user_content: str) -> list[dict]:
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
            return []
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

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.chat.completions.create(**kwargs)
                return response.choices[0].message.content.strip()
            except Exception as e:
                kind = _classify(e)
                code = getattr(e, "status_code", None) or getattr(e, "code", None)
                message = _error_message(e)

                if kind == "fatal":
                    raise FatalLLMError(f"{message} (model={self.model_name}, code={code})") from e

                if kind == "transient" and attempt < self.max_retries:
                    delay = _retry_delay(e, attempt)
                    logger.warning(
                        f"LLM call failed (model={self.model_name}, code={code}); "
                        f"retry {attempt + 1}/{self.max_retries} in {delay:.1f}s: {message}"
                    )
                    time.sleep(delay)
                    continue

                logger.error(f"LLM call failed (model={self.model_name}, code={code}): {message}")
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
