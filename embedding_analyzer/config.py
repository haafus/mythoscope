import logging
from pathlib import Path

import yaml

from settings import settings
from settings import setup_logging as _shared_setup_logging

logger = logging.getLogger(__name__)


class AnalyzerConfig:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = self._resolve_config_path(config_path)
        self._config = self._load_config()

    @staticmethod
    def _resolve_config_path(config_path: str) -> Path:
        path = Path(config_path)
        package_config = Path(__file__).with_name("config.yaml")
        if path.exists():
            return path
        if path.name == "config.yaml" and package_config.exists():
            return package_config
        return path

    def _load_config(self):
        if self.config_path.exists():
            with open(self.config_path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

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

    @property
    def visualization_params(self) -> dict:
        return self._config.get("visualization", {})

    @property
    def umap_configs(self) -> list:
        default = [
            {"n_neighbors": 5, "min_dist": 0.1},
            {"n_neighbors": 15, "min_dist": 0.1},
            {"n_neighbors": 50, "min_dist": 0.1},
            {"n_neighbors": 15, "min_dist": 0.5},
            {"n_neighbors": 15, "min_dist": 0.8},
        ]
        return self.visualization_params.get("umap_configs", default)

    @property
    def tsne_configs(self) -> list:
        default = [{"perplexity": 5}, {"perplexity": 30}, {"perplexity": 50}]
        return self.visualization_params.get("tsne_configs", default)

    @property
    def pca_configs(self) -> list:
        default = [{}]
        return self.visualization_params.get("pca_configs", default)

    @property
    def baseline_configs(self) -> dict:
        default = {"umap": {"n_neighbors": 15, "min_dist": 0.1}, "tsne": {"perplexity": 30}, "pca": {}}
        return self.visualization_params.get("baseline_configs", default)


_analyzer_config = None


def get_analyzer_config() -> AnalyzerConfig:
    global _analyzer_config
    if _analyzer_config is None:
        _analyzer_config = AnalyzerConfig()
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


def setup_logging(log_dir: str | None = None, log_filename: str = "analyzer.log", clear_handlers: bool = False) -> None:
    _shared_setup_logging(
        log_filename=log_filename,
        log_dir=log_dir,
        max_bytes=5 * 1024 * 1024,
        backup_count=3,
        clear_handlers=clear_handlers,
    )
