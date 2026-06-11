from dataclasses import dataclass, field
from pathlib import Path

from config_loader import load_yaml_config
from settings import settings


@dataclass
class GraphsConfig:
    # llm mode (mapped from llm.mode in YAML)
    mode: str = "local"

    # api settings
    api_api_key: str = ""
    api_model_name: str = "gpt-4o-mini"
    api_base_url: str = "https://api.openai.com/v1"
    api_use_json_mode: bool = True

    # local settings
    local_api_key: str = "dummy-key"
    local_model_name: str = "google/gemma-4-e4b"
    local_base_url: str = "http://127.0.0.1:1234/v1/"
    local_use_json_mode: bool = False

    # processing
    chunk_size: int = 4000
    chunk_overlap: int = 1000

    # llm call parameters
    temperature: float = 0.1
    max_retries: int = 5
    retry_backoff_factor: float = 5.0

    # execution
    force_overwrite: bool = False

    # paths (from settings, not overridable via YAML)
    @property
    def metadata_path(self) -> Path:
        return settings.corpus_metadata_path

    @property
    def prompts_path(self) -> str:
        return str(settings.project_root / "config" / "graphs_prompts.txt")

    @property
    def output_base_dir(self) -> Path:
        return settings.graphs_dir

    @property
    def logs_dir(self) -> Path:
        return settings.logs_dir

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
            "api_key": self.api_api_key,
            "model_name": self.api_model_name,
            "base_url": self.api_base_url,
            "use_json_mode": self.api_use_json_mode,
        }


def load_config(config_path: str | None = None) -> GraphsConfig:
    return load_yaml_config(GraphsConfig, "graphs", config_path)
