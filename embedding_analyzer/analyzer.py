import os
import json
import numpy as np
from typing import Dict, List, Any
from .loader import EmbeddingDataLoader
from .utils import safe_numpy_array
from embeddings_builder.config import get_model_output_dir, OUTPUT_DIR


class EmbeddingAnalyzer:
    def __init__(self, collection_name: str = "default", model_name: str = None):
        self.loader = EmbeddingDataLoader(collection_name)
        self.df = self.loader.get_data()
        self.model_name = model_name
        self.output_dir = OUTPUT_DIR
        self.available_models = self._detect_models()

        if model_name:
            self.set_model(model_name)
        elif self.df:
            models_in_data = {item.get("model", "unknown") for item in self.df if
                              item.get("model", "unknown") != "unknown"}
            if len(models_in_data) == 1:
                self.set_model(list(models_in_data)[0])
            elif len(models_in_data) > 1:
                print(f"Внимание: в данных найдено несколько моделей: {models_in_data}")
                print(f"Используйте set_model() для выбора конкретной модели.")

    def _detect_models(self) -> List[str]:
        if not self.df:
            return []
        models = {item.get("model", "unknown") for item in self.df}
        return sorted([m for m in models if m != "unknown"])

    def set_model(self, model_name: str):
        self.model_name = model_name
        self.output_dir = get_model_output_dir(OUTPUT_DIR, model_name)
        print(f"Выбрана модель: {model_name}")
        print(f"Директория для сохранения: {self.output_dir}")

    def get_available_models(self) -> List[str]:
        return self.available_models

    def filter_by_model(self, model_name: str = None) -> List[Dict[str, Any]]:
        if model_name is None:
            model_name = self.model_name
        if not model_name:
            return self.df
        return [item for item in self.df if item.get("model") == model_name]

    def get_statistics(self) -> Dict:
        if not self.df:
            raise RuntimeError("Данные не загружены.")

        data = self.filter_by_model()
        if not data:
            raise RuntimeError(f"Нет данных для модели '{self.model_name}'.")

        embeddings = np.stack([item["embedding"] for item in data])
        traditions = {item["tradition"] for item in data}

        return {
            "n_samples": len(data),
            "embedding_dim": embeddings.shape[1],
            "traditions": len(traditions),
            "tradition_counts": {
                t: sum(1 for item in data if item["tradition"] == t) for t in traditions
            },
            "model": self.model_name,
            "total_chunks_in_db": len(self.df),
        }

    def print_statistics(self):
        stats = self.get_statistics()
        print(f"\n{'=' * 50}")
        print(f"Статистика эмбеддингов:")
        print(f"{'=' * 50}")
        if self.model_name:
            print(f"   • Модель: {self.model_name}")
        print(f"   • Чанков (всего в БД): {stats['total_chunks_in_db']}")
        print(f"   • Чанков (выбранная модель): {stats['n_samples']}")
        print(f"   • Размерность: {stats['embedding_dim']}")
        print(f"   • Традиций: {stats['traditions']}")
        print(f"   • Распределение по традициям:")
        for trad, count in sorted(stats['tradition_counts'].items(), key=lambda x: -x[1]):
            print(f"     {trad:<20}: {count:>4}")
        print(f"{'=' * 50}\n")

    def save_summary(self):
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

        print(f"Информация о модели сохранена: {info_path}")

    def save_models_list(self, output_dir: str = None):
        if output_dir is None:
            output_dir = OUTPUT_DIR

        os.makedirs(output_dir, exist_ok=True)

        list_path = os.path.join(output_dir, "models.json")

        existing_models = []
        if os.path.exists(list_path):
            try:
                with open(list_path, 'r', encoding='utf-8') as f:
                    existing_models = json.load(f)
            except:
                pass

        all_models = list(set(existing_models + self.available_models))
        all_models.sort()

        with open(list_path, 'w', encoding='utf-8') as f:
            json.dump(all_models, f, ensure_ascii=False, indent=2)

        print(f"Список моделей сохранен: {list_path}")
        return list_path