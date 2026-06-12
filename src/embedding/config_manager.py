from __future__ import annotations

from dataclasses import dataclass, field

from settings import load_yaml_config, settings


@dataclass
class EmbeddingConfig:
    default_model: str = field(default_factory=lambda: settings.default_embedding_model)
    default_chunking: str = field(default_factory=lambda: settings.default_chunking)
    text_type: str = "all"
    batch_size: int = 32
    cache_batch_size: int = 50
    chroma_batch_size: int = 100
    max_workers: int = 16
    queue_maxsize: int = 10
    models: list[str] = field(default_factory=list)

    metrics_file: str = "outputs/analysis/performance_metrics.json"

    max_size_mb: int = 1024
    ttl_days: int = 30

    @property
    def corpus_dir(self) -> str:
        return str(settings.corpus_dir)

    @property
    def out_dir(self) -> str:
        return str(settings.analysis_dir)

    @property
    def chroma_path(self) -> str:
        return str(settings.chroma_dir)

    @property
    def cache_dir(self) -> str:
        return str(settings.cache_dir)

    @property
    def chunked_dir(self) -> str:
        return str(settings.corpus_chunked_dir)


def load_embedding_config(config_path: str | None = None) -> EmbeddingConfig:
    return load_yaml_config(EmbeddingConfig, "embedding", config_path)
