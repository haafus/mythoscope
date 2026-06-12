import json
from pathlib import Path
from typing import Any

import yaml


class ConfigManager:
    PACKAGE_CONFIG = Path(__file__).resolve().parent.parent.parent / "config" / "embedding.yaml"

    @staticmethod
    def _build_defaults() -> dict:
        from settings import settings as _settings

        return {
            "paths": {
                "corpus_dir": str(_settings.corpus_dir),
                "out_dir": str(_settings.analysis_dir),
                "chroma_path": str(_settings.chroma_dir),
                "cache_dir": str(_settings.cache_dir),
                "chunked_dir": str(_settings.corpus_chunked_dir),
            },
            "embedding": {
                "default_model": _settings.default_embedding_model,
                "default_chunking": _settings.default_chunking,
                "text_type": "all",
                "batch_size": 32,
                "cache_batch_size": 50,
                "chroma_batch_size": 100,
                "max_workers": 16,
                "queue_maxsize": 10,
            },
            "logging": {
                "level": "INFO",
                "file": "outputs/logs/embedding.log",
                "max_bytes": 10485760,
                "backup_count": 5,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "performance": {
                "enable_metrics": True,
                "track_memory": True,
                "metrics_file": "outputs/analysis/performance_metrics.json",
            },
            "cache": {"validation": "crc32", "max_size_mb": 1024, "ttl_days": 30},
        }

    def __init__(self, config_path: str | None = None):
        self.config_path = self._resolve_config_path(config_path)
        self._config = self._build_defaults()

        if self.config_path and self.config_path.exists():
            self._load()

    @classmethod
    def _resolve_config_path(cls, config_path: str | None) -> Path | None:
        if config_path is None:
            return cls.PACKAGE_CONFIG if cls.PACKAGE_CONFIG.exists() else None

        path = Path(config_path)
        if path.exists():
            return path
        if path.name == "config.yaml" and cls.PACKAGE_CONFIG.exists():
            return cls.PACKAGE_CONFIG
        return path

    def _load(self) -> None:
        if not self.config_path or not self.config_path.exists():
            return

        loaded: dict | None = None
        with open(self.config_path, encoding="utf-8") as f:
            if self.config_path.suffix in [".yaml", ".yml"]:
                raw = yaml.safe_load(f)
                loaded = raw if isinstance(raw, dict) else None
            elif self.config_path.suffix == ".json":
                raw = json.load(f)
                loaded = raw if isinstance(raw, dict) else None
            else:
                raise ValueError(f"Unsupported config format: {self.config_path.suffix}")

        if isinstance(loaded, dict):
            self._merge_config(self._config, loaded)

    def _merge_config(self, base: dict, override: dict) -> None:
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key_path: str, default: Any = None) -> Any:
        keys = key_path.split(".")
        value: Any = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value
