import json
import logging
import os
from typing import Any

import numpy as np

from settings import settings

from .loader import EmbeddingDataLoader

logger = logging.getLogger(__name__)


class EmbeddingAnalyzer:
    def __init__(self, model_name: str | None = None):
        self.loader = EmbeddingDataLoader()
        self.model_name: str | None = None
        self.available_models = self.loader.get_available_models()
        self.data: list[dict[str, Any]] = []
        self._is_loaded = False

        if not self.available_models:
            logger.warning("No available models in the Chroma database")
            return

        if model_name:
            self.set_model(model_name)
        elif len(self.available_models) == 1:
            self.set_model(self.available_models[0])
        else:
            logger.info(f"Available models: {self.available_models}")
            logger.info("Use .set_model('model_name') to load data")

    def set_model(self, model_name: str) -> None:
        if model_name not in self.available_models:
            raise ValueError(f"Model '{model_name}' not found. Available models: {self.available_models}")

        self.model_name = model_name
        self.output_dir = str(settings.model_output_dir(model_name))
        os.makedirs(self.output_dir, exist_ok=True)

        logger.info(f"Loading data for model: {model_name}...")
        self.data = self.loader.load_data(model_name=model_name)
        self._is_loaded = bool(self.data)

        if not self.data:
            logger.warning(f"No data found for model '{model_name}' ")
        else:
            logger.info(f"Chunks loaded: {len(self.data)}")

    def filter_by_model(self) -> list[dict[str, Any]]:
        if not self._is_loaded or not self.data:
            raise RuntimeError("Data is not loaded. Call .set_model() first.")
        return self.data

    def get_statistics(self) -> dict[str, Any]:
        if not self._is_loaded or not self.data:
            raise RuntimeError("Data is not loaded. Call .set_model() first.")

        embeddings = np.stack([item["embedding"] for item in self.data])
        traditions = {item["tradition"] for item in self.data}

        return {
            "n_samples": len(self.data),
            "embedding_dim": embeddings.shape[1],
            "traditions": len(traditions),
            "tradition_counts": {t: sum(1 for item in self.data if item["tradition"] == t) for t in traditions},
            "model": self.model_name,
            "total_chunks_in_db": len(self.data),
        }

    def print_statistics(self) -> None:
        if not self._is_loaded or not self.data:
            print("No data loaded!")
            if self.available_models:
                print(f"Available models: {self.available_models}")
                print("Use .set_model('model_name') to load data.")
            print()
            return

        stats = self.get_statistics()
        print("Embedding statistics:")
        print(f"   • Model: {self.model_name}")
        print(f"   • Chunks: {stats['n_samples']}")
        print(f"   • Dimension: {stats['embedding_dim']}")
        print(f"   • Traditions: {stats['traditions']}")
        print("   • Tradition Distribution:")
        for trad, count in sorted(stats["tradition_counts"].items(), key=lambda x: -x[1]):
            print(f"     {trad:<20}: {count:>4}")

    def save_summary(self) -> None:
        if not self._is_loaded or not self.data:
            logger.warning("No data to save")
            return

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
        with open(info_path, "w", encoding="utf-8") as f:
            json.dump(model_info, f, ensure_ascii=False, indent=2)

        logger.info(f"Model information saved: {info_path}")

    def save_models_list(self, output_dir: str | None = None) -> str:
        if output_dir is None:
            output_dir = str(settings.analysis_dir)

        os.makedirs(output_dir, exist_ok=True)
        list_path = os.path.join(output_dir, "models.json")

        existing_models = self._load_existing_models(list_path)
        all_models = sorted(set(existing_models + self.available_models))

        with open(list_path, "w", encoding="utf-8") as f:
            json.dump(all_models, f, ensure_ascii=False, indent=2)

        logger.info(f"Model list saved: {list_path}")
        return list_path

    @staticmethod
    def _load_existing_models(list_path: str) -> list[str]:
        if not os.path.exists(list_path):
            return []

        try:
            with open(list_path, encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except (OSError, json.JSONDecodeError) as e:
            logger.warning(f"Failed to load {list_path}: {e}")
            return []
