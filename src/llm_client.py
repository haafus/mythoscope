import json
import logging

from openai import OpenAI

logger = logging.getLogger(__name__)


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

        kwargs: dict = {
            "base_url": provider["base_url"],
            "timeout": request_timeout,
            "max_retries": cfg.max_retries,
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

        try:
            response = self.client.chat.completions.create(**kwargs)
            return response.choices[0].message.content.strip()
        except Exception as e:
            code = getattr(e, "status_code", None) or getattr(e, "code", None)
            message = getattr(e, "message", None) or str(e)
            logger.error(f"LLM call failed (model={self.model_name}, code={code}): {message}")
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
