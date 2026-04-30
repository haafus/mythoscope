import os
import gc
import logging
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator
from contextlib import contextmanager
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

import chromadb
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

from .cache_utils import load_from_cache, save_to_cache, cleanup_cache, get_cache_key
from .chroma_manager import save_to_chroma_collection, query_chroma_collection, delete_collection
from .chunking import create_chunking_strategies
from .models_repository import MODELS
from .performance_metrics import PerformanceMetrics

logger = logging.getLogger(__name__)


def _get_model_output_dir(base_out_dir: str, model_name: str) -> str:
    """Get model-specific output directory"""
    if not model_name:
        return base_out_dir
    safe_name = model_name.replace("/", "_").replace("\\", "_")
    model_dir = os.path.join(base_out_dir, safe_name)
    os.makedirs(model_dir, exist_ok=True)
    return model_dir


class EmbeddingBuilder:

    def __init__(
            self,
            corpus_dir: str,
            out_dir: str,
            chroma_path: str = "./chroma_db",
            cache_dir: str = "./cache",
            embedding_model: str = "BAAI/bge-m3",
            chunking: str = "paragraph",
            text_type: str = "translate",
            batch_size: int = 32,
            metrics: Optional[PerformanceMetrics] = None,
    ):


        self.corpus_dir = Path(corpus_dir)
        self.base_out_dir = Path(out_dir)
        self.chroma_path = Path(chroma_path)
        self.cache_dir = Path(cache_dir)
        if batch_size is None:
            batch_size = self.get_optimal_batch_size(embedding_model)

        self.batch_size = batch_size

        if metrics is None:
            self.metrics = PerformanceMetrics(
                metrics_file=Path(out_dir) / "performance_metrics.json",
                track_memory=True
            )
        else:
            self.metrics = metrics

        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if text_type not in {"original", "translate", "both"}:
            raise ValueError("text_type должен быть одним из: 'original', 'translate', 'both'")
        self.text_type = text_type

        self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_path))
        self._current_collection = None

        self.chunking_strategies = create_chunking_strategies()
        self.set_chunking_strategy(chunking)

        self.model_registry = MODELS
        self.set_model(embedding_model)

        # Cleanup old cache on initialization
        cleanup_cache(
            self.cache_dir,
            max_size_mb=1024,
            ttl_days=30
        )

    def _update_output_dir(self):
        out_dir_str = _get_model_output_dir(str(self.base_out_dir), self.model_name)
        self.out_dir = Path(out_dir_str)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Папка для результатов: {self.out_dir}")

    def list_models(self) -> List[str]:
        return list(self.model_registry.keys())

    def add_model(self, model_name: str, model_path: str, dimension: int = 384, model_type: str = "local"):
        if model_name in self.model_registry:
            raise ValueError(f"Модель '{model_name}' уже существует.")
        self.model_registry[model_name] = {
            "path": model_path,
            "model": None,
            "loaded": False,
            "dim": dimension,
            "type": model_type,
        }

    def remove_model(self, model_name: str):
        if model_name not in self.model_registry:
            raise KeyError(f"Модель '{model_name}' не найдена в реестре.")
        if self.model_registry[model_name]["loaded"]:
            del self.model_registry[model_name]["model"]
            self.model_registry[model_name]["loaded"] = False
        del self.model_registry[model_name]
        if hasattr(self, 'model_name') and self.model_name == model_name:
            available = self.list_models()
            if available:
                self.set_model(available[0])
            else:
                raise RuntimeError("Нет доступных моделей после удаления.")

    def unload_model(self, model_name: Optional[str] = None):
        """Выгрузка модели из памяти"""
        if model_name is None:
            model_name = self.get_current_model()
        if model_name and model_name in self.model_registry:
            if self.model_registry[model_name]["loaded"]:
                del self.model_registry[model_name]["model"]
                self.model_registry[model_name]["loaded"] = False
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                gc.collect()
                logger.info(f"Модель '{model_name}' выгружена из памяти")

    def update_model(self, model_name: str, model_path: str = None, dimension: int = None, model_type: str = None):
        if model_name not in self.model_registry:
            raise KeyError(f"Модель '{model_name}' не найдена. Используйте add_model().")
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
                    raise KeyError(f"Модель '{model_name}' не зарегистрирована.")
                if self.model_registry[model_name]["loaded"]:
                    return

                # Выгружаем предыдущую модель
                if hasattr(self, 'model_name') and self.model_name != model_name:
                    self.unload_model(self.model_name)

                model_info = self.model_registry[model_name]
                path = model_info["path"]
                try:
                    device = "cuda" if torch.cuda.is_available() else "cpu"
                    model = SentenceTransformer(path, device=device)
                    self.model_registry[model_name]["model"] = model
                    self.model_registry[model_name]["loaded"] = True
                    logger.info(f"Модель '{model_name}' успешно загружена на {device}.")
                except Exception as e:
                    # Fallback на локальную копию если есть
                    local_path = Path.home() / ".cache" / "huggingface" / "models" / model_name.replace("/", "_")
                    if local_path.exists():
                        logger.info(f"Попытка загрузить модель из локального кэша: {local_path}")
                        model = SentenceTransformer(str(local_path), device=device)
                        self.model_registry[model_name]["model"] = model
                        self.model_registry[model_name]["loaded"] = True
                        logger.info(f"Модель '{model_name}' загружена из локального кэша.")
                    else:
                        raise RuntimeError(f"Не удалось загрузить модель '{model_name}' из {path}: {e}")
                break
            except Exception as e:
                if attempt == retries - 1:
                    raise
                logger.warning(f"Попытка {attempt + 1} не удалась: {e}")
                time.sleep(2 ** attempt)

    def set_model(self, model_name: str):
        if model_name not in self.model_registry:
            available = self.list_models()
            raise ValueError(f"Модель '{model_name}' не найдена в реестре. Доступные: {available}")
        self._load_model(model_name)
        self.model_name = model_name
        self.model = self.model_registry[model_name]["model"]
        self.model_dim = self.model_registry[model_name]["dim"]
        self.model_type = self.model_registry[model_name]["type"]
        self._update_output_dir()

    @contextmanager
    def use_model(self, model_name: str):
        """Context manager for temporary model switching"""
        original_model = self.get_current_model()
        try:
            self.set_model(model_name)
            yield self
        finally:
            if original_model:
                self.set_model(original_model)

    def get_current_model(self) -> Optional[str]:
        return getattr(self, 'model_name', None)

    def get_model_info(self, model_name: str = None) -> Dict[str, Any]:
        if model_name is None:
            model_name = self.get_current_model()
        if model_name not in self.model_registry:
            return {"error": f"Модель '{model_name}' не найдена"}
        info = self.model_registry[model_name].copy()
        info["name"] = model_name
        return info

    @staticmethod
    def get_optimal_batch_size(model_name: str, model_dim: int = None) -> int:
        """Определение оптимального batch_size на основе модели"""
        # Если размерность не указана, пробуем получить из реестра
        if model_dim is None:
            if model_name in MODELS:
                model_dim = MODELS[model_name].get("dim", 768)
            else:
                model_dim = 768

        if model_dim >= 3072:  # Qwen3-Embedding
            return 8
        elif model_dim >= 1024:  # BGE-M3, E5-large
            return 16
        elif model_dim >= 768:  # Jina, Nomic, LaBSE
            return 24
        else:  # MiniLM и другие
            return 32

    def set_chunking_strategy(self, strategy_name: str):
        if strategy_name not in self.chunking_strategies:
            available = list(self.chunking_strategies.keys())
            raise ValueError(f"Стратегия '{strategy_name}' не найдена. Доступные: {available}")
        self.current_chunking = self.chunking_strategies[strategy_name]

    def get_current_chunking_strategy(self) -> Optional[str]:
        return getattr(self, 'current_chunking', None).name if hasattr(self, 'current_chunking') else None

    def _get_cache_key(self, text: str) -> str:
        if not isinstance(text, str):
            raise TypeError("Текст должен быть строкой")
        return get_cache_key(text, self.model_name, self.current_chunking)

    def _chunk_text(self, text: str) -> List[str]:
        if not text or not text.strip():
            return []
        return self.current_chunking(text)

    def _load_single_cache(self, key: str) -> Optional[np.ndarray]:
        """Helper method for parallel cache loading"""
        cache_file = self.cache_dir / f"{key}.pkl"
        if cache_file.exists():
            # We need to load without text parameter since we only have key
            try:
                import pickle
                with open(cache_file, 'rb') as f:
                    data = pickle.load(f)
                return data['embedding']
            except Exception:
                return None
        return None

    def _batch_load_from_cache(self, cache_keys: List[str]) -> List[Optional[np.ndarray]]:
        """Групповая загрузка из кэша с использованием многопоточности"""
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self._load_single_cache, key) for key in cache_keys]
            return [f.result() for f in futures]

    def _generate_embeddings(self, sentences: List[str]) -> np.ndarray:
        if not sentences:
            return np.array([])

        with self.metrics.track("generate_embeddings"):
            # Используем меньший batch_size для кэширования
            CACHE_BATCH_SIZE = 50

            final_embeddings = np.empty((len(sentences), self.model_dim), dtype=np.float32)
            to_compute_indices = []
            to_compute_text = []

            # Групповая проверка кэша с лимитом
            for i in range(0, len(sentences), CACHE_BATCH_SIZE):
                batch = sentences[i:i + CACHE_BATCH_SIZE]
                cache_keys = [self._get_cache_key(text) for text in batch]
                cached_embeddings = self._batch_load_from_cache(cache_keys)

                for j, (text, cache_key, cached) in enumerate(zip(batch, cache_keys, cached_embeddings)):
                    global_idx = i + j
                    if cached is not None:
                        final_embeddings[global_idx] = cached
                    else:
                        to_compute_indices.append(global_idx)
                        to_compute_text.append(text)

                # Очищаем временные данные
                del cache_keys
                del cached_embeddings

            # Вычисляем недостающие эмбеддинги
            if to_compute_text:
                # Разбиваем на подбатчи для экономии памяти
                for k in range(0, len(to_compute_text), self.batch_size):
                    batch_text = to_compute_text[k:k + self.batch_size]
                    batch_indices = to_compute_indices[k:k + self.batch_size]

                    computed = self.model.encode(
                        batch_text,
                        batch_size=len(batch_text),
                        show_progress_bar=False,
                        normalize_embeddings=True
                    )

                    for idx, text, emb in zip(batch_indices, batch_text, computed):
                        final_embeddings[idx] = emb
                        save_to_cache(text, emb, self.model_name, self.current_chunking, self.cache_dir)

                    # Очищаем после каждого батча
                    del computed
                    del batch_text
                    gc.collect()

            return final_embeddings

    def build_embeddings(self, text: str, chunking_strategy: str = None, batch_size: int = None) -> Dict[str, Any]:
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

    def compare_models_and_strategies(self, text: str, models: List[str] = None, strategies: List[str] = None) -> Dict[
        str, Any]:
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
                    results[f"{model_name}__{strategy_name}"] = result
        return results

    def save_embeddings_to_chroma(
            self, text: str, collection_name: str, metadata: Optional[Dict[str, Any]] = None, batch_size: int = None
    ) -> Dict[str, Any]:
        result = self.build_embeddings(text, batch_size=batch_size)
        chunks = result["chunks"]
        embeddings = result["embeddings"]

        if len(chunks) == 0:
            logger.warning("Нет чанков для сохранения.")
            return {"collection": collection_name, "added": 0}

        if metadata is None:
            metadata = {"filename": "unknown", "tradition": "unknown"}

        filename = metadata.get("filename", "unknown").replace(".txt", "")
        tradition = metadata.get("tradition", "unknown")
        text_id = Path(metadata.get("path", "")).stem or "unknown"
        ids = [f"{collection_name}_{text_id}_{i}" for i in range(len(chunks))]

        metadatas = [
            {
                "filename": filename,
                "tradition": tradition,
                "chunk_index": i,
                "model": self.model_name,
                "chunking": self.current_chunking.name,
                "text": chunk,
                "text_id": text_id,
            }
            for i, chunk in enumerate(chunks)
        ]

        collection = self.chroma_client.get_or_create_collection(name=collection_name)

        # Исправление: отдельный batch size для Chroma
        CHROMA_BATCH_SIZE = 100
        batch_size_chroma = min(CHROMA_BATCH_SIZE, len(chunks))

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
                f"  Сохранен батч {i // batch_size_chroma + 1}/{(len(chunks) - 1) // batch_size_chroma + 1} в Chroma")

        return {"collection": collection_name, "added": len(chunks)}

    def _iter_corpus_files(self) -> Generator[Dict[str, Any], None, None]:
        """Генератор для потоковой загрузки файлов (оптимизация памяти)"""
        for txt_file in self.corpus_dir.rglob("*.txt"):
            if self.text_type == "original" and not txt_file.name.endswith("_orig.txt"):
                continue
            if self.text_type == "translate" and not txt_file.name.endswith("_trans.txt"):
                continue
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    yield {
                        "filename": txt_file.name,
                        "content": f.read(),
                        "path": str(txt_file),
                        "tradition": txt_file.parent.name
                    }
            except Exception as e:
                logger.warning(f"Не удалось прочитать файл {txt_file}: {e}")
                continue

    def save_all_corpus_to_chroma(self, collection_name: str = "corpus", clear_existing: bool = True):
        with self.metrics.track("save_all_corpus_to_chroma"):
            file_generator = self._iter_corpus_files()

            # Собираем файлы в список с метаданными без чтения содержимого
            files_info = []
            for file_info in file_generator:
                files_info.append({
                    'path': file_info['path'],
                    'filename': file_info['filename'],
                    'tradition': file_info['tradition']
                })

            total_files = len(files_info)

            # Создаем новый генератор для обработки
            file_generator = self._iter_corpus_files()

        if total_files == 0:
            logger.warning("Файлы в corpus/ не найдены. Проверьте структуру папки.")
            return

        if clear_existing:
            try:
                delete_collection(self.chroma_client, collection_name)
                logger.info(f"Коллекция '{collection_name}' очищена перед записью.")
            except Exception as e:
                logger.warning(f"Не удалось очистить коллекцию: {e}")

        logger.info(f"Сохраняю {total_files} файлов в коллекцию '{collection_name}'...")
        logger.info(f"Используется модель: {self.model_name}")

        added_total = 0

        # Добавлен прогресс-бар
        with tqdm(total=total_files, desc="Обработка файлов", unit="файл") as pbar:
            for idx, file_info in enumerate(files_info, 1):
                try:
                    # Читаем файл только сейчас
                    with open(file_info['path'], 'r', encoding='utf-8') as f:
                        content = f.read()

                    result = self.save_embeddings_to_chroma(
                        text=content,
                        collection_name=collection_name,
                        metadata=file_info
                    )

                    # Явно удаляем content из памяти
                    del content

                    added_total += result["added"]

                    # Более агрессивная очистка памяти
                    if idx % 5 == 0:  # Каждые 5 файлов
                        gc.collect()
                        if torch.cuda.is_available():
                            torch.cuda.empty_cache()

                except Exception as e:
                    logger.error(f"Ошибка при обработке {file_info.get('filename', 'unknown')}: {e}")
                    pbar.update(1)

        logger.info(f"Всего добавлено: {added_total} чанков в коллекцию '{collection_name}'")
        self.metrics.save()

    def query_chroma(self, query: str, collection_name: str, top_k: int = 5) -> List[Dict[str, Any]]:
        try:
            self._current_collection = self.chroma_client.get_collection(name=collection_name)
        except chromadb.errors.CollectionNotFoundException:
            raise RuntimeError(f"Коллекция '{collection_name}' не найдена в ChromaDB.")

        query_embedding = self._generate_embeddings([query])[0]
        results = query_chroma_collection(
            collection=self._current_collection,
            query_embedding=query_embedding.tolist(),
            top_k=top_k,
        )
        return results

    def __del__(self):
        """Destructor to clean up GPU memory"""
        if hasattr(self, 'model_name'):
            self.unload_model(self.model_name)