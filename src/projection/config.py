import logging
from dataclasses import dataclass, field
from pathlib import Path

from settings import load_yaml_config, settings

logger = logging.getLogger(__name__)


@dataclass
class AnalyzerConfig:
    # visualization parameters
    umap_configs: list[dict] = field(
        default_factory=lambda: [
            {"n_neighbors": 5, "min_dist": 0.1},
            {"n_neighbors": 15, "min_dist": 0.1},
            {"n_neighbors": 50, "min_dist": 0.1},
            {"n_neighbors": 15, "min_dist": 0.5},
            {"n_neighbors": 15, "min_dist": 0.8},
        ]
    )
    tsne_configs: list[dict] = field(
        default_factory=lambda: [{"perplexity": 5}, {"perplexity": 30}, {"perplexity": 50}]
    )
    pca_configs: list[dict] = field(default_factory=lambda: [{}])
    baseline_configs: dict = field(
        default_factory=lambda: {
            "umap": {"n_neighbors": 15, "min_dist": 0.1},
            "tsne": {"perplexity": 30},
            "pca": {},
        }
    )

    # paths (always from settings)
    @property
    def chroma_path(self) -> str:
        return str(settings.chroma_dir)

    @property
    def output_dir(self) -> str:
        return str(settings.analysis_dir)

    @property
    def corpus_dir(self) -> str:
        return str(settings.corpus_dir)

    @property
    def corpus_metadata_path(self) -> str:
        return str(settings.corpus_metadata_path)


def load_analyzer_config(config_path: str | None = None) -> AnalyzerConfig:
    if config_path:
        return load_yaml_config(AnalyzerConfig, "projection", config_path)
    return load_yaml_config(AnalyzerConfig, "projection")


_analyzer_config: AnalyzerConfig | None = None


def get_analyzer_config() -> AnalyzerConfig:
    global _analyzer_config
    if _analyzer_config is None:
        _analyzer_config = load_analyzer_config()
    return _analyzer_config


def get_corpus_metadata_path() -> str:
    return str(settings.corpus_metadata_path)


def get_chroma_path() -> str:
    return str(settings.chroma_dir)


def get_output_dir() -> str:
    return str(settings.analysis_dir)


def set_paths(chroma_path: str | None = None, output_dir: str | None = None, corpus_dir: str | None = None):
    if chroma_path:
        settings.chroma_dir = Path(chroma_path)
    if output_dir:
        settings.analysis_dir = Path(output_dir)
    if corpus_dir:
        settings.corpus_dir = Path(corpus_dir)

    global _analyzer_config
    _analyzer_config = None


def get_model_output_dir(model_name: str) -> str:
    path = settings.model_output_dir(model_name)
    path.mkdir(parents=True, exist_ok=True)
    return str(path)


