import gc
import logging
import os
import shutil
from pathlib import Path
from typing import Any

import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from model_registry import embedding_config
from settings import settings

logger = logging.getLogger(__name__)

ST_OVERRIDES = settings.config_dir / "st_overrides"

_DTYPES = {
    "float32": torch.float32, "fp32": torch.float32,
    "float16": torch.float16, "fp16": torch.float16,
    "bfloat16": torch.bfloat16, "bf16": torch.bfloat16,
}


def _resolve_dtype(dtype_cfg: str | None) -> torch.dtype | None:
    """Torch dtype to load in. ``None`` means leave the default (fp32). ``auto`` picks
    bf16/fp16 on GPU (never on CPU, where low precision is not faster)."""
    if dtype_cfg and dtype_cfg != "auto":
        return _DTYPES.get(dtype_cfg.lower())
    if torch.cuda.is_available():
        return torch.bfloat16 if torch.cuda.is_bf16_supported() else torch.float16
    return None


def _prepare_snapshot(alias: str, hf_id: str) -> str:
    """Ensure the model is on disk and, if it ships no sentence-transformers config of
    its own, inject the vendored ST scaffolding from ``config/st_overrides/<alias>/``
    (last-token pooling + normalize) so it is not loaded with the wrong default pooling."""
    from huggingface_hub import snapshot_download

    try:  # cache first — no network when the model is already downloaded
        local = Path(snapshot_download(hf_id, local_files_only=True))
    except Exception:
        logger.info(f"Model '{hf_id}' not fully cached; fetching from the hub")
        local = Path(snapshot_download(hf_id))
    if (local / "modules.json").exists():
        return str(local)

    override = ST_OVERRIDES / alias
    if override.exists():
        for f in override.rglob("*"):
            if f.is_file() and f.name != "README.md":
                dst = local / f.relative_to(override)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(f, dst)
        logger.info(f"Injected ST config overrides for '{alias}' from {override}")
    else:
        logger.warning(
            f"ST overrides expected for '{alias}' (no native ST config) but not found "
            f"at {override}; loading as-is (pooling may be wrong)"
        )
    return str(local)


def _memory_info(device: str) -> str:
    try:
        if device.startswith("cuda"):
            free, total = torch.cuda.mem_get_info(device)
            return f"VRAM: {free / 2**30:.1f} / {total / 2**30:.1f} GB free"
        if device == "mps":
            total = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
            return f"RAM: {total / 2**30:.1f} GB total (shared)"
        import psutil
        mem = psutil.virtual_memory()
        return f"RAM: {mem.available / 2**30:.1f} / {mem.total / 2**30:.1f} GB available"
    except Exception:
        return ""


class EmbeddingEncoder:
    def __init__(self) -> None:
        self.model_name: str | None = None
        self.config: dict[str, Any] | None = None
        self._model: Any = None
        self._loaded_hf: str | None = None

    def load(self, key: str) -> None:
        cfg = embedding_config(key)
        hf_id = cfg["model"]

        # Config always refreshes — two variants can share one HF model (raw vs preprocessed),
        # and reusing the loaded weights must not carry the previous variant's config.
        self.config = cfg
        self.model_name = hf_id
        if self._model is not None and self._loaded_hf == hf_id:
            return

        self.unload()
        dtype = _resolve_dtype(cfg["dtype"])
        local = _prepare_snapshot(cfg["alias"], hf_id)
        logger.info(f"Loading model '{hf_id}' (dtype={dtype or 'float32'}) into device...")
        kwargs: dict[str, Any] = {"trust_remote_code": True}
        if dtype is not None:
            kwargs["model_kwargs"] = {"torch_dtype": dtype}
        self._model = SentenceTransformer(local, **kwargs)
        self._loaded_hf = hf_id
        self.model_name = hf_id
        self.config = cfg
        device = str(self._model.device)
        mem = _memory_info(device)
        logger.info(f"Model '{hf_id}' loaded on {device}{f' ({mem})' if mem else ''}.")

    def encode(self, texts: list[str], **kwargs) -> np.ndarray:
        if self._model is None:
            raise RuntimeError("No model loaded. Call load() first.")
        return self._model.encode(texts, **kwargs)

    def release_cache(self) -> None:
        """Return cached device memory to the OS (MPS bloats shared RAM over a run).

        CUDA keeps its separate VRAM cache (clearing only adds overhead); CPU has
        no device cache. So only MPS is emptied here.
        """
        gc.collect()
        if self._model is not None and str(self._model.device) == "mps":
            torch.mps.empty_cache()

    def unload(self) -> None:
        if self._model is None:
            return
        device = str(self._model.device)
        logger.info(f"Unloading model from {device}...")
        self._model = None
        self.model_name = None
        self.config = None
        self._loaded_hf = None
        gc.collect()
        if device.startswith("cuda"):
            torch.cuda.empty_cache()
        elif device == "mps":
            torch.mps.empty_cache()
        logger.info("Model unloaded from memory")
