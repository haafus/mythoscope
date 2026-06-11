from dataclasses import dataclass, field
from pathlib import Path

from config_loader import load_yaml_config
from settings import settings


@dataclass
class CorpusBuilderConfig:
    # build
    max_workers: int = 10

    # downloader
    timeout_connect: int = 10
    timeout_read: int = 30
    retry_total: int = 4
    retry_backoff_factor: float = 1.5
    retry_status_forcelist: list[int] = field(default_factory=lambda: [429, 500, 502, 503, 504])

    # parsing
    html_include_comments: bool = False
    html_include_tables: bool = True
    pdf_extract_tables: bool = False
    pdf_preserve_layout: bool = True

    # paths (always from settings, not overridable via YAML)
    @property
    def corpus_dir(self) -> Path:
        return settings.corpus_dir

    @property
    def download_list_file(self) -> Path:
        return Path(str(settings.download_list_file))

    @property
    def metadata_file(self) -> Path:
        return settings.corpus_metadata_path

    @property
    def catalog_file(self) -> Path:
        return settings.corpus_catalog_path

    @property
    def processed_urls_file(self) -> Path:
        return settings.processed_urls_path


def load_config(config_path: str | None = None) -> CorpusBuilderConfig:
    return load_yaml_config(CorpusBuilderConfig, "corpus_builder", config_path)


config = load_config()

DOWNLOAD_LIST_FILE = config.download_list_file
CORPUS_DIR = config.corpus_dir
METADATA_FILE = config.metadata_file
CATALOG_FILE = config.catalog_file
PROCESSED_URLS_FILE = config.processed_urls_file
