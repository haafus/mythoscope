from dataclasses import fields
from pathlib import Path
from typing import TypeVar

import yaml

from settings import settings

T = TypeVar("T")


def load_yaml_config(config_cls: type[T], config_name: str, config_path: str | None = None) -> T:
    overrides = _load_yaml(config_name, config_path)
    flat: dict[str, object] = {}
    for section_val in overrides.values():
        if isinstance(section_val, dict):
            flat.update(_flatten(section_val))
        else:
            pass
    valid_fields = {f.name for f in fields(config_cls)}  # type: ignore[arg-type]
    kwargs = {k: v for k, v in flat.items() if k in valid_fields}
    return config_cls(**kwargs)  # type: ignore[return-value]


def _load_yaml(config_name: str, config_path: str | None) -> dict:
    candidates = (
        [Path(config_path)]
        if config_path
        else [
            Path(f"config/{config_name}.yaml"),
            settings.project_root / "config" / f"{config_name}.yaml",
        ]
    )
    for path in candidates:
        if path.exists():
            with open(path, encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
    return {}


def _flatten(d: dict, parent_key: str = "", sep: str = "_") -> dict:
    items: list[tuple[str, object]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)
