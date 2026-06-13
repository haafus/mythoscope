import importlib
import logging
import sys
from collections.abc import Callable
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

# ---------------------------------------------------------------------------
# Sub-models (BaseModel — not BaseSettings, nested inside Settings)
# ---------------------------------------------------------------------------


class CorpusSettings(BaseModel):
    max_workers: int = 10
    timeout_connect: int = 10
    timeout_read: int = 30
    retry_total: int = 4
    retry_backoff_factor: float = 1.5
    retry_status_forcelist: list[int] = [429, 500, 502, 503, 504]
    html_include_comments: bool = False
    html_include_tables: bool = True
    pdf_extract_tables: bool = False
    pdf_preserve_layout: bool = True


class EmbeddingSettings(BaseModel):
    default_model: str = "BAAI/bge-m3"
    default_chunking: str = "paragraph"
    text_type: str = "all"
    batch_size: int = 32
    cache_batch_size: int = 50
    chroma_batch_size: int = 100
    max_workers: int = 16
    queue_maxsize: int = 10
    models: list[str] = []
    metrics_file: str = "outputs/analysis/performance_metrics.json"
    cache_max_size_mb: int = 1024
    cache_ttl_days: int = 30


class GraphsSettings(BaseModel):
    mode: str = "local"
    api_key: str = ""
    model_name: str = "gpt-4o-mini"
    base_url: str = "https://api.openai.com/v1"
    use_json_mode: bool = True
    local_api_key: str = "dummy-key"
    local_model_name: str = "google/gemma-4-e4b"
    local_base_url: str = "http://127.0.0.1:1234/v1/"
    local_use_json_mode: bool = False
    chunk_size: int = 4000
    chunk_overlap: int = 1000
    temperature: float = 0.1
    max_retries: int = 5
    retry_backoff_factor: float = 5.0

    @property
    def active_llm_config(self) -> dict:
        if self.mode == "local":
            return {
                "api_key": self.local_api_key,
                "model_name": self.local_model_name,
                "base_url": self.local_base_url,
                "use_json_mode": self.local_use_json_mode,
            }
        return {
            "api_key": self.api_key,
            "model_name": self.model_name,
            "base_url": self.base_url,
            "use_json_mode": self.use_json_mode,
        }


class ProjectionSettings(BaseModel):
    umap_configs: list[dict] = [
        {"n_neighbors": 5, "min_dist": 0.1},
        {"n_neighbors": 15, "min_dist": 0.1},
        {"n_neighbors": 50, "min_dist": 0.1},
        {"n_neighbors": 15, "min_dist": 0.5},
        {"n_neighbors": 15, "min_dist": 0.8},
    ]
    tsne_configs: list[dict] = [{"perplexity": 5}, {"perplexity": 30}, {"perplexity": 50}]
    pca_configs: list[dict] = [{}]
    baseline_configs: dict = {
        "umap": {"n_neighbors": 15, "min_dist": 0.1},
        "tsne": {"perplexity": 30},
        "pca": {},
    }


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    gzip_minimum_size: int = 1024
    cache_max_age: int = 86400
    search_job_ttl_seconds: int = 1800
    search_max_workers: int = 1


# ---------------------------------------------------------------------------
# Root settings
# ---------------------------------------------------------------------------


class Settings(BaseSettings):
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent.parent)

    corpus_dir: Path = Path("outputs/corpus")
    corpus_chunked_dir: Path = Path("outputs/corpus_chunked")
    chroma_dir: Path = Path("outputs/chroma_db")
    cache_dir: Path = Path("outputs/cache")
    analysis_dir: Path = Path("outputs/analysis")
    logs_dir: Path = Path("outputs/logs")
    graphs_dir: Path = Path("outputs/graphs")
    download_list_file: Path = Path("config/download_list.json")

    log_level: str = "INFO"

    # sub-settings
    corpus: CorpusSettings = CorpusSettings()
    embedding: EmbeddingSettings = EmbeddingSettings()
    graphs: GraphsSettings = GraphsSettings()
    projection: ProjectionSettings = ProjectionSettings()
    server: ServerSettings = ServerSettings()

    model_config = {
        "env_file": [".env", "config/.env"],
        "env_prefix": "MYTHO_",
        "env_nested_delimiter": "__",
        "extra": "ignore",
    }

    @property
    def corpus_metadata_path(self) -> Path:
        return self.corpus_dir / "corpus_metadata.json"

    @property
    def corpus_catalog_path(self) -> Path:
        return self.corpus_dir / "corpus_catalog.csv"

    @property
    def processed_urls_path(self) -> Path:
        return self.corpus_dir / "processed_urls.json"

    @staticmethod
    def safe_model_name(model_name: str) -> str:
        return model_name.replace("/", "_").replace("\\", "_")

    def model_output_dir(self, model_name: str) -> Path:
        return self.analysis_dir / self.safe_model_name(model_name)

    def ensure_dirs(self) -> None:
        for d in (
            self.corpus_dir,
            self.corpus_chunked_dir,
            self.cache_dir,
            self.analysis_dir,
            self.logs_dir,
            self.graphs_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()


# ---------------------------------------------------------------------------
# Shared utilities
# ---------------------------------------------------------------------------


def lazy_module_getattr(module_name: str, lazy_imports: dict[str, tuple[str, str]]) -> Callable[[str], object]:
    def __getattr__(name: str) -> object:
        if name in lazy_imports:
            module_path, attr = lazy_imports[name]
            value = getattr(importlib.import_module(module_path, module_name), attr)
            sys.modules[module_name].__dict__[name] = value
            return value
        raise AttributeError(f"module {module_name!r} has no attribute {name!r}")

    return __getattr__


def setup_logging(
    log_filename: str = "app.log",
    log_dir: str | None = None,
    level: str | None = None,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    clear_handlers: bool = False,
) -> None:
    log_path = Path(log_dir or str(settings.logs_dir))
    log_path.mkdir(parents=True, exist_ok=True)

    log_level = getattr(logging, (level or settings.log_level).upper(), logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    file_handler = RotatingFileHandler(
        log_path / log_filename, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    if clear_handlers:
        root_logger.handlers.clear()

    log_file_path = str(file_handler.baseFilename)
    if not any(
        isinstance(h, RotatingFileHandler) and str(h.baseFilename) == log_file_path for h in root_logger.handlers
    ):
        root_logger.addHandler(file_handler)
    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in root_logger.handlers
    ):
        root_logger.addHandler(console_handler)
