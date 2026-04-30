import os
import json
import numpy as np
from typing import Dict, List, Optional, Any
from .loader import EmbeddingDataLoader
from .config import get_analyzer_config, get_model_output_dir  # ДОБАВЛЕН ИМПОРТ
import logging

logger = logging.getLogger(__name__)


class EmbeddingAnalyzer:
    def __init__(self, collection_name: str = "corpus", model_name: Optional[str] = None):
        self.config = get_analyzer_config()
        self.loader = EmbeddingDataLoader(collection_name)
        self.collection_name = collection_name
        self.model_name: Optional[str] = None
        self.available_models = self.loader.get_available_models()
        self.data: List[Dict[str, Any]] = []
        self._is_loaded = False

        if not self.available_models:
            logger.warning("Нет доступных моделей в базе данных Chroma")
            return

        if model_name:
            self.set_model(model_name)
        elif len(self.available_models) == 1:
            self.set_model(self.available_models[0])
        else:
            logger.info(f"Доступные модели: {self.available_models}")
            logger.info(f"Используйте .set_model('имя_модели') для загрузки данных")
            # ИСПРАВЛЕНО: Не вызываем set_model автоматически если моделей несколько
            # self.set_model(self.available_models[0])  # УБРАНО

    def set_model(self, model_name: str) -> None:
        """Меняет модель и перезагружает данные из Chroma"""
        if model_name not in self.available_models:
            raise ValueError(
                f"Модель '{model_name}' не найдена. "
                f"Доступные модели: {self.available_models}"
            )

        self.model_name = model_name
        # ИСПРАВЛЕНО: Используем get_model_output_dir для консистентности
        self.output_dir = get_model_output_dir(model_name)
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(f"Загрузка данных для модели: {model_name}...")
        self.data = self.loader.load_data(model_name=model_name)
        self._is_loaded = bool(self.data)

        if not self.data:
            logger.warning(f"Для модели '{model_name}' не найдено данных")
        else:
            logger.info(f"Загружено чанков: {len(self.data)}")


    def filter_by_model(self) -> List[Dict[str, Any]]:
        """Возвращает данные для текущей модели"""
        if not self._is_loaded or not self.data:
            raise RuntimeError("Данные не загружены. Вызовите .set_model() сначала.")
        return self.data

    def get_statistics(self) -> Dict[str, Any]:
        if not self._is_loaded or not self.data:
            raise RuntimeError("Данные не загружены. Вызовите .set_model() сначала.")

        embeddings = np.stack([item["embedding"] for item in self.data])
        traditions = {item["tradition"] for item in self.data}

        return {
            "n_samples": len(self.data),
            "embedding_dim": embeddings.shape[1],
            "traditions": len(traditions),
            "tradition_counts": {
                t: sum(1 for item in self.data if item["tradition"] == t)
                for t in traditions
            },
            "model": self.model_name,
            "total_chunks_in_db": len(self.data),
        }

    def print_statistics(self) -> None:
        if not self._is_loaded or not self.data:
            print("\n" + "=" * 50)
            print("Нет загруженных данных!")
            if self.available_models:
                print(f"Доступные модели: {self.available_models}")
                print(f"Используйте .set_model('имя_модели') для загрузки данных.")
            print("=" * 50 + "\n")
            return

        stats = self.get_statistics()
        print(f"\n{'=' * 50}")
        print(f"Статистика эмбеддингов:")
        print(f"{'=' * 50}")
        print(f"   • Модель: {self.model_name}")
        print(f"   • Чанков: {stats['n_samples']}")
        print(f"   • Размерность: {stats['embedding_dim']}")
        print(f"   • Традиций: {stats['traditions']}")
        print(f"   • Распределение по традициям:")
        for trad, count in sorted(stats['tradition_counts'].items(), key=lambda x: -x[1]):
            print(f"     {trad:<20}: {count:>4}")
        print(f"{'=' * 50}\n")

    def save_summary(self) -> None:
        if not self._is_loaded or not self.data:
            logger.warning("Нет данных для сохранения")
            return

        # Отложенный импорт для избежания циркулярной зависимости
        from .visualization import save_summary_to_files

        os.makedirs(self.output_dir, exist_ok=True)
        stats = self.get_statistics()
        save_summary_to_files(self.filter_by_model(), stats, self.output_dir)

        model_info = {
            "model_name": self.model_name,
            "output_dir": self.output_dir,
            "statistics": stats,
            "available_models": self.available_models,
        }

        info_path = os.path.join(self.output_dir, "model_info.json")
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)

        logger.info(f"Информация о модели сохранена: {info_path}")

    def save_models_list(self, output_dir: Optional[str] = None) -> str:
        """Сохраняет список доступных моделей"""
        if output_dir is None:
            output_dir = self.config.output_dir

        os.makedirs(output_dir, exist_ok=True)
        list_path = os.path.join(output_dir, "models.json")

        # Загружаем существующие модели
        existing_models = self._load_existing_models(list_path)

        # Объединяем с текущими
        all_models = sorted(set(existing_models + self.available_models))

        with open(list_path, 'w', encoding='utf-8') as f:
            json.dump(all_models, f, ensure_ascii=False, indent=2)

        logger.info(f"Список моделей сохранен: {list_path}")
        return list_path

    @staticmethod
    def _load_existing_models(list_path: str) -> List[str]:
        """Загружает существующий список моделей"""
        if not os.path.exists(list_path):
            return []

        try:
            with open(list_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Не удалось загрузить {list_path}: {e}")
            return []