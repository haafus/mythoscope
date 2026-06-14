import gc
import logging
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import torch
from sentence_transformers import SentenceTransformer

from .models_repository import MODELS

logger = logging.getLogger(__name__)

BATCH_SIZE_THRESHOLDS = [(3072, 8), (1024, 16), (768, 24)]
DEFAULT_BATCH_SIZE = 32


def get_optimal_batch_size(model_dim: int) -> int:
    for min_dim, opt_batch in BATCH_SIZE_THRESHOLDS:
        if model_dim >= min_dim:
            return opt_batch
    return DEFAULT_BATCH_SIZE


def _select_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


class ModelManager:
    def __init__(self, *, batch_size: int | None = None):
        self.registry: dict[str, dict[str, Any]] = {name: dict(info) for name, info in MODELS.items()}
        self.model_name: str | None = None
        self.model: Any = None
        self.model_dim: int = 0
        self._override_batch_size = batch_size is not None
        self.batch_size: int = batch_size if batch_size is not None else DEFAULT_BATCH_SIZE

    def list_models(self) -> list[str]:
        return list(self.registry.keys())

    def unload_model(self, model_name: str | None = None) -> None:
        if model_name is None:
            model_name = self.model_name
        if model_name and model_name in self.registry and self.registry[model_name]["model"] is not None:
            self.registry[model_name]["model"] = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                torch.mps.empty_cache()
            gc.collect()
            logger.info(f"Model '{model_name}' unloaded from memory")

    def _load_model(self, model_name: str, retries: int = 3) -> None:
        for attempt in range(retries):
            try:
                if model_name not in self.registry:
                    raise KeyError(f"Model '{model_name}' is not registered.")
                if self.registry[model_name]["model"] is not None:
                    return

                if self.model_name and self.model_name != model_name:
                    self.unload_model(self.model_name)

                device = _select_device()
                try:
                    model = SentenceTransformer(model_name, device=device)
                    self.registry[model_name]["model"] = model
                    logger.info(f"Model '{model_name}' loaded successfully on {device}.")
                except Exception as e:
                    local_path = Path.home() / ".cache" / "huggingface" / "models" / model_name.replace("/", "_")
                    if local_path.exists():
                        logger.info(f"Trying to load model from local cache: {local_path}")
                        try:
                            model = SentenceTransformer(str(local_path), device=device)
                            self.registry[model_name]["model"] = model
                            logger.info(f"Model '{model_name}' loaded from local cache.")
                        except Exception as fallback_error:
                            raise RuntimeError(
                                f"Failed to load model '{model_name}' ({e}) and local cache ({fallback_error})"
                            ) from e
                    else:
                        raise RuntimeError(f"Failed to load model '{model_name}': {e}") from e
                break
            except Exception as e:
                if attempt == retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2**attempt)

    def set_model(self, model_name: str) -> None:
        if model_name not in self.registry:
            raise ValueError(f"Model '{model_name}' not found in registry. Available: {self.list_models()}")

        self._load_model(model_name)
        self.model_name = model_name
        self.model = self.registry[model_name]["model"]
        self.model_dim = self.model.get_sentence_embedding_dimension()
        if not self._override_batch_size:
            self.batch_size = get_optimal_batch_size(self.model_dim)
            logger.info(f"Batch size automatically set to {self.batch_size} for model {model_name}")
        else:
            logger.info(f"Using default batch size: {self.batch_size}")

    @contextmanager
    def use_model(self, model_name: str) -> Iterator["ModelManager"]:
        original_model = self.model_name
        try:
            self.set_model(model_name)
            yield self
        finally:
            if original_model:
                self.set_model(original_model)

    def close(self) -> None:
        if self.model_name:
            self.unload_model(self.model_name)
