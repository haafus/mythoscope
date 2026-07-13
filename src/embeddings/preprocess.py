"""Chunk preprocessing for embedding variants.

A variant whose ``models.json`` entry has ``preprocess_prompt`` embeds an LLM-transformed
version of each chunk (e.g. a culture-neutral plot summary) instead of the raw text. The
transformed texts are cached content-addressed by ``(prompt-hash, chunk-hash)`` in a file
shared across all models, so a given prompt transforms each chunk once regardless of how
many models embed it, and editing the prompt invalidates only the affected entries.
"""
import hashlib
import json
import logging
import re
from pathlib import Path

from chunk_cache import append_cache, chunk_hash, load_cache
from llm import map_concurrent
from settings import settings

logger = logging.getLogger(__name__)

MAX_INPUT_CHARS = 4000


def load_prompt(name: str) -> str:
    path = settings.config_dir / "prompts.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))[name]
    except Exception as e:
        raise RuntimeError(f"Failed to load prompt '{name}' from {path}: {e}") from e


def prompt_hash(text: str) -> str:
    """Content hash of the normalised prompt — the cache/identity key for a prompt version."""
    normalized = re.sub(r"\s+", " ", text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:12]


def cache_path(prompt_name: str, phash: str) -> Path:
    settings.preprocessed_dir.mkdir(parents=True, exist_ok=True)
    return settings.preprocessed_dir / f"{prompt_name}.{phash}.jsonl"


def preprocess_texts(texts: list[str], prompt_name: str) -> list[str]:
    """Transform each chunk through ``prompt_name``; returns outputs aligned with ``texts``
    (empty string where a chunk failed or the daily limit was hit — the caller skips those)."""
    from llm import LLMProcessor

    prompt = load_prompt(prompt_name)
    path = cache_path(prompt_name, prompt_hash(prompt))
    cache = load_cache(path)

    uncached = list(dict.fromkeys(t for t in texts if t.strip() and chunk_hash(t) not in cache))
    if uncached:
        llm = LLMProcessor(
            model_alias=settings.embedding.llm,
            temperature=settings.embedding.temperature,
            use_json_mode=False,
        )
        logger.info(
            f"Preprocessing {len(uncached)} chunks with '{prompt_name}' "
            f"(concurrency={settings.projections.max_concurrent})..."
        )

        def _store(text: str, out: str) -> None:
            if out:
                key = chunk_hash(text)
                append_cache(path, key, out)
                cache[key] = out

        completed = map_concurrent(
            uncached,
            lambda t: llm.ask_text(prompt, t[:MAX_INPUT_CHARS]),
            settings.projections.max_concurrent,
            on_result=_store,
        )
        if not completed:
            logger.warning("Daily rate limit reached — some chunks are not preprocessed; rerun to resume.")
        if llm.governor.stats()["requests"]:
            logger.info(f"LLM usage: {llm.governor.summary()}")

    return [cache.get(chunk_hash(t), "") for t in texts]
