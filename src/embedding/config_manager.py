import json
from copy import deepcopy
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
            "chunking": {
                "fixed_size": {"chunk_size": 512, "chunk_overlap": 64},
                "sentence_based": {"chunk_size": 512, "chunk_overlap": 64},
                "paragraph_based": {"chunk_size": 512, "chunk_overlap": 64},
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
            self.load()

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

    def load(self) -> None:
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

    def save(self, path: str | None = None) -> None:
        save_path = Path(path) if path else self.config_path
        if not save_path:
            raise ValueError("No save path specified")

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, "w", encoding="utf-8") as f:
            if save_path.suffix in [".yaml", ".yml"]:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

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

    def set(self, key_path: str, value: Any) -> None:
        keys = key_path.split(".")
        target = self._config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value

    def get_all(self) -> dict:
        return deepcopy(self._config)

    def validate(self) -> list[str]:
        issues = []

        corpus_dir = self.get("paths.corpus_dir")
        if not Path(corpus_dir).exists():
            issues.append(f"Root directory does not exist: {corpus_dir}")

        out_dir = self.get("paths.out_dir")
        if out_dir:
            try:
                Path(out_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Failed to create output directory {out_dir}: {e}")

        batch_size = self.get("embedding.batch_size")
        if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 1024:
            issues.append(f"batch_size must be between 1 and 1024, got: {batch_size}")

        text_type = self.get("embedding.text_type")
        if text_type not in ["original", "translate", "translation", "all", "both"]:
            issues.append(f"Invalid text_type: {text_type}. Allowed values: original, translate, all")

        chunking = self.get("embedding.default_chunking")
        valid_strategies = ["character", "sentence", "paragraph"]
        if chunking not in valid_strategies:
            issues.append(f"Invalid chunking strategy: {chunking}. Allowed: {valid_strategies}")

        cache_validation = self.get("cache.validation")
        if cache_validation not in ["crc32", "md5", "none"]:
            issues.append(f"Invalid cache validation method: {cache_validation}")

        ttl_days = self.get("cache.ttl_days")
        if not isinstance(ttl_days, int) or ttl_days < 0:
            issues.append(f"ttl_days must be a non-negative integer, got: {ttl_days}")

        return issues
