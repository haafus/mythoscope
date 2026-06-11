import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_root: Path = Field(default_factory=lambda: Path(__file__).resolve().parent)

    corpus_dir: Path = Path("corpus")
    corpus_chunked_dir: Path = Path("corpus_chunked")
    chroma_dir: Path = Path("chroma_db")
    cache_dir: Path = Path("cache")
    analysis_dir: Path = Path("analysis")
    logs_dir: Path = Path("logs")
    graphs_dir: Path = Path("graphs")
    download_list_file: Path = Path("download_list.json")

    default_embedding_model: str = "BAAI/bge-m3"
    default_chunking: str = "paragraph"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    llm_model_name: str = "gpt-4o-mini"

    log_level: str = "INFO"

    model_config = {"env_file": ".env", "env_prefix": "MYTHO_", "extra": "ignore"}

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

    root_logger.addHandler(file_handler)
    if not any(
        isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler) for h in root_logger.handlers
    ):
        root_logger.addHandler(console_handler)
