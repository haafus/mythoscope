import json
import os
import re
from typing import Any

from settings import settings

_registry: dict[str, Any] | None = None

# A variant key is the collection name / folder / URL segment / dropdown value, so it must
# satisfy the intersection of Chroma, filesystem and URL constraints.
_KEY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]$")


def _load_registry() -> dict[str, Any]:
    global _registry
    if _registry is None:
        path = settings.config_dir / "models.json"
        _registry = json.loads(path.read_text(encoding="utf-8"))
    return _registry


def _entry_model(entry: Any) -> str:
    """The HF id of an embedding entry, which may be a bare string or an object."""
    return entry["model"] if isinstance(entry, dict) else entry


def _embedding_section() -> dict[str, Any]:
    return _load_registry().get("embedding", {})


def _find_embedding_entry(key_or_id: str) -> tuple[str, Any]:
    """(key, entry) for a name that may be a variant key or a raw HF id, looked up in the
    visible ``models`` section only (``inactive`` is invisible to code)."""
    models = _embedding_section().get("models", {})
    if key_or_id in models:
        return key_or_id, models[key_or_id]
    for key, entry in models.items():
        if _entry_model(entry) == key_or_id:
            return key, entry
    return key_or_id, None


def humanize_label(key: str) -> str:
    tokens = [t for t in re.split(r"[._-]+", key) if t]
    return " · ".join(t[:1].upper() + t[1:] for t in tokens) or key


def valid_key(key: str) -> bool:
    return bool(_KEY_RE.match(key))


def embedding_config(key_or_id: str) -> dict[str, Any]:
    """Normalized config for one embedding variant. The argument is the variant key (the
    ``models.json`` alias) or a raw HF id passed straight in. Only ``model`` is guaranteed.

    ``query_prefix``/``document_prefix`` are the model's inline input formatting (they fall
    back to the legacy ``query_prompt``/``document_prompt`` names); ``preprocess_prompt`` is a
    name resolved in ``config/prompts.json`` that turns this into a chunk-preprocessing variant."""
    key, entry = _find_embedding_entry(key_or_id)
    if entry is None:
        # An explicitly-targeted inactive variant still resolves (inactive means
        # "not built by default", not "unresolvable"); only unknown ids fall through.
        inactive = _embedding_section().get("inactive", {})
        if key_or_id in inactive:
            key, entry = key_or_id, inactive[key_or_id]
    if entry is None:
        entry = {"model": key_or_id}
    elif not isinstance(entry, dict):
        entry = {"model": entry}
    return {
        "key": key,
        "alias": key,
        "model": entry["model"],
        "label": entry.get("label") or humanize_label(key),
        "dtype": entry.get("dtype", "auto"),
        "batch_size": entry.get("batch_size"),
        "query_prefix": entry.get("query_prefix", entry.get("query_prompt", "")),
        "document_prefix": entry.get("document_prefix", entry.get("document_prompt", "")),
        "preprocess_prompt": entry.get("preprocess_prompt"),
    }


def embedding_variants(include_inactive: bool = False) -> list[str]:
    """Variant keys (the ``models.json`` aliases) — the pipeline's unit of iteration."""
    emb = _embedding_section()
    keys = list(emb.get("models", {}).keys())
    if include_inactive:
        keys += list(emb.get("inactive", {}).keys())
    return keys


def resolve_embedding_model(name: str) -> str:
    _, entry = _find_embedding_entry(name)
    return _entry_model(entry) if entry is not None else name


def model_name_for_key(key: str) -> str:
    """Variant key -> HF model id (to load the encoder). Falls through unchanged."""
    emb = _embedding_section()
    for section in ("models", "inactive"):
        entry = emb.get(section, {}).get(key)
        if entry is not None:
            return _entry_model(entry)
    return key


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
    return [_entry_model(v) for v in _embedding_section().get("models", {}).values()]


def list_embedding_aliases() -> dict[str, str]:
    return {k: _entry_model(v) for k, v in _embedding_section().get("models", {}).items()}
