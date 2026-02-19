import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
import numpy as np
from sentence_transformers import SentenceTransformer

from .cache_manager import load_from_cache, save_to_cache
from .chroma_manager import save_to_chroma_collection, query_chroma_collection
from .chunking import create_chunking_strategies
from .models_repository import MODELS

logger = logging.getLogger(__name__)


class EmbeddingBuilder:

    def __init__(
            self,
            corpus_dir: str,
            out_dir: str,
            chroma_path: str = "./chroma_db",
            cache_dir: str = "./cache",
            embedding_model: str = "BAAI/bge-m3",
            chunking: str = "fixed_size",
            text_type: str = "translate",
    ):
        self.corpus_dir = Path(corpus_dir)
        self.out_dir = Path(out_dir)
        self.chroma_path = Path(chroma_path)
        self.cache_dir = Path(cache_dir)

        for path in [self.out_dir, self.chroma_path, self.cache_dir]:
            path.mkdir(parents=True, exist_ok=True)

        if text_type not in {"original", "translate", "both"}:
            raise ValueError("text_type должен быть одним из: 'original', 'translate', 'both'")
        self.text_type = text_type

        self.chroma_client = chromadb.PersistentClient(path=str(self.chroma_path))
        self._current_collection = None

        self.chunking_strategies = create_chunking_strategies()
        self.set_chunking_strategy(chunking)

        self.model_registry = MODELS
        self.set_model(embedding_model)

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

    def update_model(self, model_name: str, model_path: str = None, dimension: int = None, model_type: str = None):
        if model_name not in self.model_registry:
            raise KeyError(f"Модель '{model_name}' не найдена. Используйте add_model().")
        if model_path is not None:
            self.model_registry[model_name]["path"] = model_path
        if dimension is not None:
            self.model_registry[model_name]["dim"] = dimension
        if model_type is not None:
            self.model_registry[model_name]["type"] = model_type

    def _load_model(self, model_name: str):
        if model_name not in self.model_registry:
            raise KeyError(f"Модель '{model_name}' не зарегистрирована.")
        if self.model_registry[model_name]["loaded"]:
            return
        model_info = self.model_registry[model_name]
        path = model_info["path"]
        try:
            model = SentenceTransformer(path)
            self.model_registry[model_name]["model"] = model
            self.model_registry[model_name]["loaded"] = True
            logger.info(f"Модель '{model_name}' успешно загружена.")
        except Exception as e:
            raise RuntimeError(f"Не удалось загрузить модель '{model_name}' из {path}: {e}")

    def set_model(self, model_name: str):
        if model_name not in self.model_registry:
            available = self.list_models()
            raise ValueError(f"Модель '{model_name}' не найдена в реестре. Доступные: {available}")
        self._load_model(model_name)
        self.model_name = model_name
        self.model = self.model_registry[model_name]["model"]
        self.model_dim = self.model_registry[model_name]["dim"]
        self.model_type = self.model_registry[model_name]["type"]

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
        key_str = f"{text}|{self.model_name}|{self.current_chunking.name}|{self.current_chunking.chunk_size}|{self.current_chunking.chunk_overlap}"
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()

    def _chunk_text(self, text: str) -> List[str]:
        return self.current_chunking(text)

    def _generate_embeddings(self, sentences: List[str]) -> np.ndarray:
        if not sentences:
            return np.array([])
        embeddings = []
        for sent in sentences:
            if not sent.strip():
                continue
            cached = load_from_cache(sent, self.model_name, self.current_chunking, self.cache_dir)
            if cached is not None:
                embeddings.append(cached)
            else:
                try:
                    emb = self.model.encode(sent, normalize_embeddings=True)
                    save_to_cache(sent, emb, self.model_name, self.current_chunking, self.cache_dir)
                    embeddings.append(emb)
                except Exception as e:
                    raise RuntimeError(f"Ошибка при генерации эмбеддинга для текста '{sent[:50]}...': {e}")
        return np.array(embeddings) if embeddings else np.array([])

    def build_embeddings(self, text: str, chunking_strategy: str = None) -> Dict[str, Any]:
        if chunking_strategy:
            self.set_chunking_strategy(chunking_strategy)
        chunks = self._chunk_text(text)
        embeddings = self._generate_embeddings(chunks)
        return {
            "chunks": chunks,
            "embeddings": embeddings,
            "model": self.model_name,
            "chunking": self.current_chunking.name,
            "num_chunks": len(chunks),
            "embedding_dim": self.model_dim,
        }

    def compare_models_and_strategies(self, text: str, models: List[str] = None, strategies: List[str] = None) -> Dict[
        str, Any]:
        if models is None:
            models = self.list_models()
        if strategies is None:
            strategies = list(self.chunking_strategies.keys())
        results = {}
        for model_name in models:
            self.set_model(model_name)
            for strategy_name in strategies:
                self.set_chunking_strategy(strategy_name)
                result = self.build_embeddings(text)
                results[f"{model_name}__{strategy_name}"] = result
        return results

    def save_embeddings_to_chroma(
            self, text: str, collection_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        result = self.build_embeddings(text)
        chunks = result["chunks"]
        embeddings = result["embeddings"]
        if len(chunks) == 0:
            raise ValueError("Нет чанков для сохранения.")

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

        save_to_chroma_collection(
            client=self.chroma_client,
            collection_name=collection_name,
            ids=ids,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
            documents=chunks,
        )

        return {"collection": collection_name, "added": len(chunks)}

    def save_all_corpus_to_chroma(self, collection_name: str = "default"):
        texts = self._load_corpus_files()
        if not texts:
            logger.warning("Файлы в corpus/ не найдены. Проверьте структуру папки.")
            return

        logger.info(f"Сохраняю {len(texts)} файлов в коллекцию '{collection_name}'...")

        added_total = 0
        for idx, text_data in enumerate(texts, 1):
            try:
                result = self.save_embeddings_to_chroma(
                    text=text_data["content"],
                    collection_name=collection_name,
                    metadata=text_data
                )
                added_total += result["added"]
                logger.info(f"[{idx}/{len(texts)}] {text_data['filename']} ({result['added']} чанков)")
            except Exception as e:
                logger.error(f"[{idx}/{len(texts)}] Ошибка при обработке {text_data.get('filename', 'unknown')}: {e}")

        logger.info(f"Всего добавлено: {added_total} чанков в коллекцию '{collection_name}'")

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

    def _load_corpus_files(self) -> List[Dict[str, Any]]:
        texts = []
        for txt_file in self.corpus_dir.rglob("*.txt"):
            try:
                with open(txt_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.strip():
                        continue
                    if self.text_type == "original" and not txt_file.name.endswith("_orig.txt"):
                        continue
                    if self.text_type == "translate" and not txt_file.name.endswith("_trans.txt"):
                        continue
                    tradition = txt_file.parent.name
                    texts.append({
                        "filename": txt_file.name,
                        "content": content,
                        "path": str(txt_file),
                        "tradition": tradition
                    })
            except Exception as e:
                logger.warning(f"Не удалось прочитать файл {txt_file}: {e}")
                continue
        return texts
