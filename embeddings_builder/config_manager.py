import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional, List
from copy import deepcopy


class ConfigManager:
    """Manages configuration from YAML/JSON files with defaults"""

    DEFAULTS = {
        "paths": {
            "corpus_dir": "corpus",
            "out_dir": "analysis",
            "chroma_path": "./chroma_db",
            "cache_dir": "./cache"
        },
        "embedding": {
            "default_model": "BAAI/bge-m3",
            "default_chunking": "paragraph",
            "text_type": "both",
            "batch_size": 32,
            "clear_existing": True
        },
        "chunking": {
            "fixed_size": {"chunk_size": 512, "chunk_overlap": 64},
            "sentence_based": {"chunk_size": 512, "chunk_overlap": 64},
            "paragraph_based": {"chunk_size": 512, "chunk_overlap": 64}
        },
        "logging": {
            "level": "INFO",
            "file": "logs/embedding.log",
            "max_bytes": 10485760,
            "backup_count": 5,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        },
        "performance": {
            "enable_metrics": True,
            "track_memory": True,
            "metrics_file": "analysis/performance_metrics.json"
        },
        "cache": {
            "validation": "crc32",
            "max_size_mb": 1024,
            "ttl_days": 30
        }
    }

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = Path(config_path) if config_path else None
        self._config = deepcopy(self.DEFAULTS)

        if self.config_path and self.config_path.exists():
            self.load()

    def load(self) -> None:
        """Load configuration from file"""
        if not self.config_path or not self.config_path.exists():
            return

        with open(self.config_path, 'r', encoding='utf-8') as f:
            if self.config_path.suffix in ['.yaml', '.yml']:
                loaded = yaml.safe_load(f)
            elif self.config_path.suffix == '.json':
                loaded = json.load(f)
            else:
                raise ValueError(f"Unsupported config format: {self.config_path.suffix}")

        self._merge_config(self._config, loaded or {})

    def _merge_config(self, base: Dict, override: Dict) -> None:
        """Deep merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def save(self, path: Optional[str] = None) -> None:
        """Save configuration to file"""
        save_path = Path(path) if path else self.config_path
        if not save_path:
            raise ValueError("No save path specified")

        save_path.parent.mkdir(parents=True, exist_ok=True)

        with open(save_path, 'w', encoding='utf-8') as f:
            if save_path.suffix in ['.yaml', '.yml']:
                yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)
            else:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get(self, key_path: str, default: Any = None) -> Any:
        """Get value by dot-separated key path"""
        keys = key_path.split('.')
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value

    def set(self, key_path: str, value: Any) -> None:
        """Set value by dot-separated key path"""
        keys = key_path.split('.')
        target = self._config
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value

    def get_all(self) -> Dict:
        """Get complete configuration"""
        return deepcopy(self._config)

    def validate(self) -> List[str]:
        """Validate configuration and return list of issues"""
        issues = []

        # Validate paths
        corpus_dir = self.get('paths.corpus_dir')
        if not Path(corpus_dir).exists():
            issues.append(f"Корневая директория не существует: {corpus_dir}")

        out_dir = self.get('paths.out_dir')
        if out_dir:
            try:
                Path(out_dir).mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"Не удалось создать выходную директорию {out_dir}: {e}")

        # Validate embedding parameters
        batch_size = self.get('embedding.batch_size')
        if not isinstance(batch_size, int) or batch_size < 1 or batch_size > 1024:
            issues.append(f"batch_size должен быть между 1 и 1024, получено: {batch_size}")

        text_type = self.get('embedding.text_type')
        if text_type not in ['original', 'translate', 'both']:
            issues.append(f"Некорректный text_type: {text_type}. Допустимые значения: original, translate, both")

        # Validate chunking strategy
        chunking = self.get('embedding.default_chunking')
        valid_strategies = ['character', 'sentence', 'paragraph']
        if chunking not in valid_strategies:
            issues.append(f"Некорректная стратегия чанкинга: {chunking}. Допустимые: {valid_strategies}")

        # Validate cache settings
        cache_validation = self.get('cache.validation')
        if cache_validation not in ['crc32', 'md5', 'none']:
            issues.append(f"Некорректный метод валидации кэша: {cache_validation}")

        ttl_days = self.get('cache.ttl_days')
        if not isinstance(ttl_days, int) or ttl_days < 0:
            issues.append(f"ttl_days должен быть неотрицательным целым числом, получено: {ttl_days}")

        return issues