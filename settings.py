from pathlib import Path
from typing import Optional

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

    def model_output_dir(self, model_name: str) -> Path:
        safe_name = model_name.replace("/", "_").replace("\\", "_")
        return self.analysis_dir / safe_name

    def ensure_dirs(self) -> None:
        for d in (self.corpus_dir, self.corpus_chunked_dir, self.cache_dir,
                  self.analysis_dir, self.logs_dir, self.graphs_dir):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
