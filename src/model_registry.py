import json
import os
from typing import Any

from settings import settings

_registry: dict[str, Any] | None = None


def _load_registry() -> dict[str, Any]:
    global _registry
    if _registry is None:
        path = settings.config_dir / "models.json"
        _registry = json.loads(path.read_text(encoding="utf-8"))
    return _registry


def _entry_model(entry: Any) -> str:
    """The HF id of an embedding entry, which may be a bare string or an object."""
    return entry["model"] if isinstance(entry, dict) else entry


def _find_embedding_entry(name_or_id: str) -> tuple[str, Any]:
    """(alias, entry) for a name that may be an alias or a HF id, looked up in the
    visible ``models`` section only (``inactive`` is invisible to code)."""
    models = _load_registry().get("embedding", {}).get("models", {})
    if name_or_id in models:
        return name_or_id, models[name_or_id]
    for alias, entry in models.items():
        if _entry_model(entry) == name_or_id:
            return alias, entry
    return name_or_id, None


def resolve_embedding_model(name: str) -> str:
    _, entry = _find_embedding_entry(name)
    return _entry_model(entry) if entry is not None else name


def embedding_config(name_or_id: str) -> dict[str, Any]:
    """Normalized per-model embedding config (the argument may be an alias or a HF id
    passed straight in). Only ``model`` is guaranteed; the rest are optional defaults."""
    alias, entry = _find_embedding_entry(name_or_id)
    if entry is None:
        entry = {"model": name_or_id}
    elif not isinstance(entry, dict):
        entry = {"model": entry}
    return {
        "alias": alias,
        "model": entry["model"],
        "dtype": entry.get("dtype", "auto"),
        "query_prompt": entry.get("query_prompt", ""),
        "document_prompt": entry.get("document_prompt", ""),
        "batch_size": entry.get("batch_size"),
    }


def resolve_llm_provider(name: str) -> dict[str, Any]:
    registry = _load_registry()
    models = registry.get("llm", {}).get("models", {})
    if name not in models:
        available = ", ".join(sorted(models.keys()))
        raise ValueError(f"LLM provider '{name}' not found. Available: {available}")
    entry = models[name]
    api_key = None
    env_key = entry.get("env_key")
    if env_key:
        api_key = os.environ.get(env_key)
    return {
        "base_url": entry["base_url"],
        "model": entry["model"],
        "api_key": api_key,
        # Optional per-model rate limits (None when unset).
        "rpm": entry.get("rpm"),
        "tpm": entry.get("tpm"),
        "rpd": entry.get("rpd"),
    }


def list_llm_providers() -> list[str]:
    return sorted(_load_registry().get("llm", {}).get("models", {}).keys())


def active_embedding_models() -> list[str]:
    models = _load_registry().get("embedding", {}).get("models", {})
    return [_entry_model(v) for v in models.values()]


def list_embedding_aliases() -> dict[str, str]:
    models = _load_registry().get("embedding", {}).get("models", {})
    return {k: _entry_model(v) for k, v in models.items()}


def model_to_key(model_name: str) -> str:
    return (model_name or "").replace("/", "_")


def model_name_for_key(key: str) -> str:
    emb = _load_registry().get("embedding", {})
    for section in ("models", "inactive"):
        for entry in emb.get(section, {}).values():
            model = _entry_model(entry)
            if model_to_key(model) == key:
                return model
    return key
