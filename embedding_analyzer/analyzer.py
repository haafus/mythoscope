import numpy as np
from typing import Dict, List
from .loader import EmbeddingDataLoader
from .utils import safe_numpy_array

class EmbeddingAnalyzer:
    def __init__(self, collection_name: str = "default"):
        self.loader = EmbeddingDataLoader(collection_name)
        self.df = self.loader.get_data()

    def get_statistics(self) -> Dict:
        if not self.df:
            raise RuntimeError("Данные не загружены.")
        embeddings = np.stack([item["embedding"] for item in self.df])
        traditions = {item["tradition"] for item in self.df}
        return {
            "n_samples": len(self.df),
            "embedding_dim": embeddings.shape[1],
            "traditions": len(traditions),
            "tradition_counts": {
                t: sum(1 for item in self.df if item["tradition"] == t) for t in traditions
            },
        }

    def print_statistics(self):
        stats = self.get_statistics()
        print(f"Статистика эмбеддингов:")
        print(f"   • Чанков: {stats['n_samples']}")
        print(f"   • Размерность: {stats['embedding_dim']}")
        print(f"   • Традиций: {stats['traditions']}")
        print(f"   • Распределение по традициям:")
        for trad, count in sorted(stats['tradition_counts'].items(), key=lambda x: -x[1]):
            print(f"     {trad:<20}: {count:>4}")

    def save_summary(self):
        from .visualization import save_summary_to_files
        save_summary_to_files(self.df, self.get_statistics())
