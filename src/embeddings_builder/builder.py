import csv
import gc
import logging
import os
import queue
import re
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

import chromadb
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from tqdm import tqdm

from .cache_utils import cleanup_cache, get_cache_key, save_to_cache
from .chroma_manager import (
    collection_name_for_model,
    ensure_chroma_writable,
    query_chroma_collection,
    save_to_chroma_collection,
)
from .chunking import create_chunking_strategies
from .models_repository import MODELS
from .performance_metrics import PerformanceMetrics

logger = logging.getLogger(__name__)


def _normalize_text_type(text_type: str) -> str:
    aliases = {
        "both": "all",
        "translation": "translate",
    }
    return aliases.get(text_type, text_type)


def _normalize_catalog_id(value: Any) -> str:
    return re.sub(r"\s+", "_", str(value or "").strip())


def _safe_id_part(value: Any) -> str:
    return re.sub(r"[^0-9A-Za-z_.-]+", "_", str(value or "unknown")).strip("_") or "unknown"


def _get_model_output_dir(base_out_dir: str, model_name: str) -> str:
    if not model_name:
        return base_out_dir
    from settings import Settings

    model_dir = os.path.join(base_out_dir, Settings.safe_model_name(model_name))
    os.makedirs(model_dir, exist_ok=True)
    return model_dir


class EmbeddingBuilder:
    BATCH_SIZE_THRESHOLDS = [(3072, 8), (1024, 16), (768, 24)]
    DEFAULT_BATCH_SIZE = 32

    def __init__(
        self,
        corpus_dir: str,
        out_dir: str,
        chroma_path: str = "outputs/chroma_db",
        cache_dir: str = "outputs/cache",
        chunked_dir: str = "outputs/corpus_chunked",
        embedding_model: str = "BAAI/bge-m3",
        chunking: str = "paragraph",
        text_type: str = "translate",
        batch_size: int = None,
        cache_batch_size: int = 50,
        chroma_batch_size: int = 100,
        metrics: PerformanceMetrics | None = None,
    ):
        self.corpus_dir = Path(corpus_dir)
        self.base_out_dir = Path(out_dir)
        self.chroma_path = ensure_chroma_writable(chroma_path)
        self.cache_dir = Path(cache_dir)
        self.chunked_dir = Path(chunked_dir)
        self.chunked_dir.mkdir(parents=True, exist_ok=True)
        self.cache_batch_size = cache_batch_size
        self.chroma_batch_size = chroma_batch_size

        self._executor = ThreadPoolExecutor(max_workers=16)

        self._override_batch_size = batch_size is not None

        if self._override_batch_size:
            self.batch_size = batch_size
        else:
            self.batch_size = self.DEFAULT_BATCH_SIZE

        if metrics is None:
            self.metrics = PerformanceMetrics(
                metrics_file=Path(out_dir) / "performance_metrics.json", track_memory=True
            )
        else:
            self.metrics = metrics

        self.cache_dir.mkdir(parents=True, exist_ok=True)

        text_type = _normalize_text_type(text_type)
        if text_type not in {"original", "translate", "all"}:
            raise ValueError("text_type must be one of: 'original', 'translate', 'all'")
        self.text_type = text_type

        self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_path))
        self._current_collection = None

        self.chunking_strategies = create_chunking_strategies()
        self.set_chunking_strategy(chunking)

        self.model_registry = MODELS
        self.set_model(embedding_model)

        cleanup_cache(self.cache_dir, max_size_mb=1024, ttl_days=30)

    def _update_output_dir(self):
        out_dir_str = _get_model_output_dir(str(self.base_out_dir), self.model_name)
        self.out_dir = Path(out_dir_str)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Results directory: {self.out_dir}")

    def list_models(self) -> list[str]:
        return list(self.model_registry.keys())

    def add_model(self, model_name: str, model_path: str, dimension: int = 384, model_type: str = "local"):
        if model_name in self.model_registry:
            raise ValueError(f"Model '{model_name}' already exists.")
        self.model_registry[model_name] = {
            "path": model_path,
            "model": None,
            "loaded": False,
            "dim": dimension,
            "type": model_type,
        }

    def remove_model(self, model_name: str):
        if model_name not in self.model_registry:
            raise KeyError(f"Model '{model_name}' not found in registry.")
        if self.model_registry[model_name]["loaded"]:
            del self.model_registry[model_name]["model"]
            self.model_registry[model_name]["loaded"] = False
        del self.model_registry[model_name]

        if hasattr(self, "model_name") and self.model_name == model_name:
            self.model_name = None
            logger.info("Active model removed. Set a new one with set_model().")

    def unload_model(self, model_name: str | None = None):
        if model_name is None:
            model_name = self.get_current_model()
        if model_name and model_name in self.model_registry and self.model_registry[model_name]["loaded"]:
            del self.model_registry[model_name]["model"]
            self.model_registry[model_name]["loaded"] = False
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                torch.mps.empty_cache()
            gc.collect()
            logger.info(f"Model '{model_name}' unloaded from memory")

    def update_model(self, model_name: str, model_path: str = None, dimension: int = None, model_type: str = None):
        if model_name not in self.model_registry:
            raise KeyError(f"Model '{model_name}' not found. Use add_model().")
        if model_path is not None:
            self.model_registry[model_name]["path"] = model_path
        if dimension is not None:
            self.model_registry[model_name]["dim"] = dimension
        if model_type is not None:
            self.model_registry[model_name]["type"] = model_type

    def _load_model(self, model_name: str, retries: int = 3):
        for attempt in range(retries):
            try:
                if model_name not in self.model_registry:
                    raise KeyError(f"Model '{model_name}' is not registered.")
                if self.model_registry[model_name]["loaded"]:
                    return

                if hasattr(self, "model_name") and self.model_name != model_name:
                    self.unload_model(self.model_name)

                model_info = self.model_registry[model_name]
                path = model_info["path"]
                try:
                    if torch.cuda.is_available():
                        device = "cuda"
                    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                        device = "mps"
                    else:
                        device = "cpu"

                    model = SentenceTransformer(path, device=device)
                    self.model_registry[model_name]["model"] = model
                    self.model_registry[model_name]["loaded"] = True
                    logger.info(f"Model '{model_name}' loaded successfully on {device}.")
                except Exception as e:
                    local_path = Path.home() / ".cache" / "huggingface" / "models" / model_name.replace("/", "_")
                    if local_path.exists():
                        logger.info(f"Trying to load model from local cache: {local_path}")
                        try:
                            model = SentenceTransformer(str(local_path), device=device)
                            self.model_registry[model_name]["model"] = model
                            self.model_registry[model_name]["loaded"] = True
                            logger.info(f"Model '{model_name}' loaded from local cache.")
                        except Exception as fallback_error:
                            raise RuntimeError(
                                f"Failed to load model from {path} ({e}) and local cache ({fallback_error})"
                            ) from e
                    else:
                        raise RuntimeError(f"Failed to load model '{model_name}' from {path}: {e}") from e
                break
            except Exception as e:
                if attempt == retries - 1:
                    raise
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(2**attempt)

    def set_model(self, model_name: str):
        if model_name not in self.model_registry:
            available = self.list_models()
            raise ValueError(f"Model '{model_name}' not found in registry. Available: {available}")

        self._load_model(model_name)
        self.model_name = model_name
        self.model = self.model_registry[model_name]["model"]
        self.model_dim = self.model_registry[model_name]["dim"]
        self.model_type = self.model_registry[model_name]["type"]

        if not self._override_batch_size:
            model_batch = self.model_registry[model_name].get("batch_size")
            if model_batch:
                self.batch_size = model_batch
            else:
                self.batch_size = self.get_optimal_batch_size(model_name, self.model_dim)
            logger.info(f"Batch size automatically set to {self.batch_size} for model {model_name}")
        else:
            logger.info(f"Using default batch size: {self.batch_size}")

        self._update_output_dir()

    @contextmanager
    def use_model(self, model_name: str):
        original_model = self.get_current_model()
        try:
            self.set_model(model_name)
            yield self
        finally:
            if original_model:
                self.set_model(original_model)

    def get_current_model(self) -> str | None:
        return getattr(self, "model_name", None)

    def get_model_info(self, model_name: str = None) -> dict[str, Any]:
        if model_name is None:
            model_name = self.get_current_model()
        if model_name not in self.model_registry:
            return {"error": f"Model '{model_name}' not found"}
        info = self.model_registry[model_name].copy()
        info["name"] = model_name
        return info

    @classmethod
    def get_optimal_batch_size(cls, model_name: str, model_dim: int = None) -> int:
        if model_dim is None:
            model_dim = MODELS.get(model_name, {}).get("dim", 768)

        for min_dim, opt_batch in cls.BATCH_SIZE_THRESHOLDS:
            if model_dim >= min_dim:
                return opt_batch
        return cls.DEFAULT_BATCH_SIZE

    def set_chunking_strategy(self, strategy_name: str):
        if strategy_name not in self.chunking_strategies:
            available = list(self.chunking_strategies.keys())
            raise ValueError(f"Strategy '{strategy_name}' not found. Available: {available}")
        self.current_chunking = self.chunking_strategies[strategy_name]

    def get_current_chunking_strategy(self) -> str | None:
        return getattr(self, "current_chunking", None).name if hasattr(self, "current_chunking") else None

    def _get_cache_key(self, text: str) -> str:
        return get_cache_key(text, self.model_name, self.current_chunking)

    def _chunk_text(self, text: str) -> list[str]:
        if not text or not text.strip():
            return []
        return [chunk for chunk in self.current_chunking(text) if chunk.strip()]

    def _load_single_cache(self, key: str) -> np.ndarray | None:
        cache_npy_file = self.cache_dir / f"{key}.npy"
        cache_json_file = self.cache_dir / f"{key}.json"

        if cache_npy_file.exists() and cache_json_file.exists():
            try:
                return np.load(cache_npy_file)
            except Exception:
                return None
        return None

    def _batch_load_from_cache(self, cache_keys: list[str]) -> list[np.ndarray | None]:
        futures = [self._executor.submit(self._load_single_cache, key) for key in cache_keys]
        return [f.result() for f in futures]

    def _generate_embeddings(self, sentences: list[str]) -> np.ndarray:
        if not sentences:
            return np.array([])

        with self.metrics.track("generate_embeddings"):
            final_embeddings = np.empty((len(sentences), self.model_dim), dtype=np.float32)
            to_compute_indices = []
            to_compute_text = []

            for i in range(0, len(sentences), self.cache_batch_size):
                batch = sentences[i : i + self.cache_batch_size]
                cache_keys = [self._get_cache_key(text) for text in batch]
                cached_embeddings = self._batch_load_from_cache(cache_keys)

                for j, (text, cached) in enumerate(zip(batch, cached_embeddings, strict=False)):
                    global_idx = i + j
                    if cached is not None:
                        final_embeddings[global_idx] = cached
                    else:
                        to_compute_indices.append(global_idx)
                        to_compute_text.append(text)

            if to_compute_text:
                for k in range(0, len(to_compute_text), self.batch_size):
                    batch_text = to_compute_text[k : k + self.batch_size]
                    batch_indices = to_compute_indices[k : k + self.batch_size]

                    computed = self.model.encode(
                        batch_text, batch_size=len(batch_text), show_progress_bar=False, normalize_embeddings=True
                    )

                    for idx, text, emb in zip(batch_indices, batch_text, computed, strict=False):
                        final_embeddings[idx] = emb
                        save_to_cache(text, emb, self.model_name, self.current_chunking, self.cache_dir)
            return final_embeddings

    def build_embeddings(self, text: str, chunking_strategy: str = None, batch_size: int = None) -> dict[str, Any]:
        if chunking_strategy:
            self.set_chunking_strategy(chunking_strategy)

        original_batch_size = self.batch_size
        if batch_size is not None:
            self.batch_size = batch_size

        try:
            chunks = self._chunk_text(text)
            if not chunks:
                return {
                    "chunks": [],
                    "embeddings": np.array([]),
                    "model": self.model_name,
                    "chunking": self.current_chunking.name,
                    "num_chunks": 0,
                    "embedding_dim": self.model_dim,
                    "batch_size_used": self.batch_size,
                }
            embeddings = self._generate_embeddings(chunks)
            return {
                "chunks": chunks,
                "embeddings": embeddings,
                "model": self.model_name,
                "chunking": self.current_chunking.name,
                "num_chunks": len(chunks),
                "embedding_dim": self.model_dim,
                "batch_size_used": self.batch_size,
            }
        finally:
            if batch_size is not None:
                self.batch_size = original_batch_size

    def compare_models_and_strategies(
        self, text: str, models: list[str] = None, strategies: list[str] = None
    ) -> dict[str, Any]:
        if models is None:
            models = self.list_models()
        if strategies is None:
            strategies = list(self.chunking_strategies.keys())
        results = {}
        for model_name in models:
            with self.use_model(model_name):
                for strategy_name in strategies:
                    self.set_chunking_strategy(strategy_name)
                    result = self.build_embeddings(text)
                    results[f"{model_name}____{strategy_name}"] = result
        return results

    def save_embeddings_to_chroma(
        self, text: str, metadata: dict[str, Any] | None = None, batch_size: int = None
    ) -> dict[str, Any]:
        """Synchronous save kept for backward compatibility when called directly"""
        collection_name = collection_name_for_model(self.model_name)
        result = self.build_embeddings(text, batch_size=batch_size)
        chunks = result["chunks"]
        embeddings = result["embeddings"]

        if len(chunks) == 0:
            logger.warning("No chunks to save.")
            return {"collection": collection_name, "added": 0}

        if metadata is None:
            metadata = {}

        def _safe_meta(val):
            return "" if val is None else val

        filename = metadata.get("filename", "unknown").replace(".txt", "")
        tradition = metadata.get("tradition", "unknown")
        major_tradition = metadata.get("major_tradition", "unknown")
        text_id = metadata.get("text_id") or Path(metadata.get("path", "")).stem or "unknown"
        doc_type = metadata.get("doc_type", "unknown")
        color = metadata.get("color", "#CCCCCC")
        language = metadata.get("language", "unknown")
        url = metadata.get("url", "")

        model_id = _safe_id_part(self.model_name)
        text_id_safe = _safe_id_part(text_id)

        ids = [f"{text_id_safe}_{model_id}_{i}" for i in range(len(chunks))]

        metadatas = [
            {
                "filename": _safe_meta(filename) or "unknown",
                "tradition": _safe_meta(tradition),
                "major_tradition": _safe_meta(major_tradition),
                "chunk_index": i,
                "model": _safe_meta(self.model_name),
                "chunking": _safe_meta(self.current_chunking.name),
                "text_id": _safe_meta(text_id),
                "doc_type": _safe_meta(doc_type),
                "color": _safe_meta(color),
                "language": _safe_meta(language),
                "url": _safe_meta(url),
            }
            for i in range(len(chunks))
        ]

        collection = self.chroma_client.get_or_create_collection(name=collection_name)
        batch_size_chroma = min(self.chroma_batch_size, len(chunks))

        for i in range(0, len(chunks), batch_size_chroma):
            batch_end = min(i + batch_size_chroma, len(chunks))
            save_to_chroma_collection(
                collection=collection,
                ids=ids[i:batch_end],
                embeddings=embeddings[i:batch_end].tolist(),
                metadatas=metadatas[i:batch_end],
                documents=chunks[i:batch_end],
            )
            logger.debug(
                f"  Saved batch {i // batch_size_chroma + 1}/{(len(chunks) - 1) // batch_size_chroma + 1} to Chroma"
            )

        return {"collection": collection_name, "added": len(chunks), "chunks": chunks}

    def _iter_corpus_files(self) -> Generator[dict[str, Any], None, None]:
        catalog_file = self.corpus_dir / "corpus_catalog.csv"
        text_info = {}

        if catalog_file.exists():
            try:
                with open(catalog_file, encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        tid = row.get("id") or row.get("tid")
                        if not tid:
                            continue
                        row_info = {
                            "text_id": _normalize_catalog_id(tid),
                            "catalog_id": tid,
                            "type": row.get("type", "unknown"),
                            "color": row.get("color", "#CCCCCC"),
                            "major_tradition": row.get("major_tradition", "unknown"),
                            "tradition": row.get("tradition", "unknown"),
                            "language": row.get("language", "unknown"),
                            "url": row.get("url", ""),
                        }
                        text_info[str(tid)] = row_info
                        text_info[_normalize_catalog_id(tid)] = row_info
            except Exception as e:
                logger.error(f"Error reading {catalog_file}: {e}")
        else:
            logger.warning(f"File {catalog_file} not found.")

        for txt_file in self.corpus_dir.rglob("*.txt"):
            tid = txt_file.stem

            info = text_info.get(tid, {})
            doc_type = info.get("type", "unknown")
            color = info.get("color", "#CCCCCC")

            if self.text_type == "original" and doc_type != "original":
                continue
            if self.text_type in ["translate", "translation"] and doc_type not in ["translate", "translation"]:
                continue

            try:
                rel_parts = txt_file.relative_to(self.corpus_dir).parts
                major_tradition = info.get("major_tradition") or (rel_parts[0] if len(rel_parts) > 1 else "unknown")
                tradition = info.get("tradition") or (rel_parts[1] if len(rel_parts) > 2 else major_tradition)
            except ValueError:
                major_tradition = "unknown"
                tradition = txt_file.parent.name

            try:
                with open(txt_file, encoding="utf-8") as f:
                    yield {
                        "filename": txt_file.name,
                        "content": f.read(),
                        "path": str(txt_file),
                        "text_id": info.get("text_id", tid),
                        "catalog_id": info.get("catalog_id", tid),
                        "major_tradition": major_tradition,
                        "tradition": tradition,
                        "doc_type": doc_type,
                        "color": color,
                        "language": info.get("language", "unknown"),
                        "url": info.get("url", ""),
                    }
            except Exception as e:
                logger.warning(f"Failed to read file {txt_file}: {e}")
                continue

    def _chroma_writer_worker(self, collection, write_queue: queue.Queue):
        """Background thread for asynchronous writes to ChromaDB"""
        while True:
            batch = write_queue.get()

            if batch is None:
                write_queue.task_done()
                break

            ids, embeddings, metadatas, documents = batch

            try:
                save_to_chroma_collection(
                    collection=collection,
                    ids=ids,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    documents=documents,
                )
                logger.debug(f"Background thread saved a batch of {len(ids)} chunks.")
            except Exception as e:
                logger.error(f"Background Chroma write error: {e}")
            finally:
                write_queue.task_done()

    def save_all_corpus_to_chroma(self):
        collection_name = collection_name_for_model(self.model_name)
        with self.metrics.track("save_all_corpus_to_chroma"):
            files_info = list(self._iter_corpus_files())
            total_files = len(files_info)

        if total_files == 0:
            logger.warning("No files found in corpus/. Check the folder structure.")
            return

        traditions_file = self.corpus_dir / "traditions_info.json"
        if traditions_file.exists():
            try:
                dest_file = self.chunked_dir / "traditions_info.json"
                self.chunked_dir.mkdir(parents=True, exist_ok=True)
                shutil.copy2(traditions_file, dest_file)
                logger.info(f"File {traditions_file.name} copied successfully to {self.chunked_dir}")
            except Exception as e:
                logger.warning(f"Failed to copy {traditions_file.name}: {e}")

        # deleted = delete_collection(self.chroma_client, collection_name)
        # if deleted:
        # logger.info(f"Collection '{collection_name}' cleared before writing.")
        # else:
        # logger.info(f"Collection '{collection_name}' does not exist yet; writing from scratch.")

        collection = self.chroma_client.get_or_create_collection(name=collection_name)

        write_queue = queue.Queue(maxsize=10)
        writer_thread = threading.Thread(target=self._chroma_writer_worker, args=(collection, write_queue), daemon=True)
        writer_thread.start()

        logger.info(f"Saving {total_files} files to collection '{collection_name}'")
        added_total = 0

        with tqdm(total=total_files, desc="Processing files", unit="file") as pbar:
            for file_info in files_info:
                try:
                    with open(file_info["path"], encoding="utf-8") as f:
                        content = f.read()

                    result = self.build_embeddings(content, batch_size=self.batch_size)
                    chunks = result.get("chunks", [])
                    embeddings = result.get("embeddings", [])

                    if not chunks:
                        continue

                    text_id = file_info.get("text_id") or Path(file_info.get("path", "")).stem or "unknown"
                    text_id_safe = _safe_id_part(text_id)
                    model_id = _safe_id_part(self.model_name)

                    ids = [f"{text_id_safe}_{model_id}_{i}" for i in range(len(chunks))]

                    def _safe_meta(val):
                        return "" if val is None else val

                    metadatas = [
                        {
                            "filename": _safe_meta(file_info.get("filename", "unknown")) or "unknown",
                            "tradition": _safe_meta(file_info.get("tradition", "unknown")),
                            "major_tradition": _safe_meta(file_info.get("major_tradition", "unknown")),
                            "chunk_index": i,
                            "model": _safe_meta(self.model_name),
                            "chunking": _safe_meta(self.current_chunking.name),
                            "text_id": _safe_meta(text_id),
                            "doc_type": _safe_meta(file_info.get("doc_type", "unknown")),
                            "color": _safe_meta(file_info.get("color", "#CCCCCC")),
                            "language": _safe_meta(file_info.get("language", "unknown")),
                            "url": _safe_meta(file_info.get("url", "")),
                        }
                        for i in range(len(chunks))
                    ]

                    batch_size_chroma = min(self.chroma_batch_size, len(chunks))
                    for i in range(0, len(chunks), batch_size_chroma):
                        batch_end = min(i + batch_size_chroma, len(chunks))

                        write_queue.put(
                            (
                                ids[i:batch_end],
                                embeddings[i:batch_end].tolist(),
                                metadatas[i:batch_end],
                                chunks[i:batch_end],
                            )
                        )

                    added_total += len(chunks)

                    rel_path = Path(file_info["path"]).relative_to(self.corpus_dir)
                    out_file_path = self.chunked_dir / rel_path
                    out_file_path.parent.mkdir(parents=True, exist_ok=True)

                    with open(out_file_path, "w", encoding="utf-8") as out_f:
                        for i, chunk in enumerate(chunks, 1):
                            out_f.write(f"=== [ CHUNK {i} | Size: {len(chunk)} chars ] ===\n")
                            out_f.write(chunk)
                            out_f.write("\n\n")

                except Exception as e:
                    logger.error(f"Error processing {file_info.get('filename', 'unknown')}: {e}")
                finally:
                    pbar.update(1)

        logger.info("Generation complete. Waiting for final batches to be written to disk...")
        write_queue.put(None)
        writer_thread.join()

        logger.info(f"Total added: {added_total} chunks to collection '{collection_name}'")
        self.metrics.save()

    def query_chroma(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        collection_name = collection_name_for_model(self.model_name)
        try:
            self._current_collection = self.chroma_client.get_collection(name=collection_name)
        except Exception as err:
            raise RuntimeError(f"Collection '{collection_name}' not found in ChromaDB.") from err

        query_embedding = self._generate_embeddings([query])[0]
        return query_chroma_collection(
            collection=self._current_collection,
            query_embedding=query_embedding.tolist(),
            top_k=top_k,
        )

    def close(self):
        """Explicit resource release: stop threads and unload models"""
        if hasattr(self, "_executor"):
            self._executor.shutdown(wait=True, cancel_futures=True)

        if hasattr(self, "model_name") and self.model_name:
            self.unload_model(self.model_name)

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
