import json
from pathlib import Path

from settings import Settings
from ui_server.config import paths


def model_to_key(model_name: str) -> str:
    return Settings.safe_model_name(model_name or "")


def key_to_model(model_key: str, models: list[str] | None = None) -> str:
    if not model_key:
        return model_key

    if "/" in model_key:
        return model_key

    candidates = models if models is not None else list_models_raw()
    for model in candidates:
        if model_to_key(model) == model_key:
            return model

    return model_key.replace("_", "/")


def list_models_raw() -> list[str]:
    models_path = paths.analysis_dir / "models.json"
    if models_path.exists():
        with models_path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, list):
            return [str(item) for item in data]

    return _models_from_analysis_dirs()


def list_model_summaries() -> list[dict[str, str]]:
    return [
        {
            "name": model,
            "key": model_to_key(model),
            "safe_dir": model_to_key(model),
        }
        for model in list_models_raw()
    ]


def get_model_output_dir(model_key: str) -> Path:
    model_name = key_to_model(model_key)
    return paths.analysis_dir / model_to_key(model_name)


def get_model_info(model_key: str) -> dict:
    info_path = get_model_output_dir(model_key) / "model_info.json"
    if not info_path.exists():
        return {}

    with info_path.open("r", encoding="utf-8") as handle:
        result: dict = json.load(handle)
        return result


def _models_from_analysis_dirs() -> list[str]:
    if not paths.analysis_dir.exists():
        return []

    models = []
    for item in sorted(paths.analysis_dir.iterdir()):
        if item.is_dir() and (item / "model_info.json").exists():
            info_path = item / "model_info.json"
            try:
                with info_path.open("r", encoding="utf-8") as handle:
                    model_info = json.load(handle)
                model_name = model_info.get("model_name")
                models.append(model_name or item.name.replace("_", "/"))
            except Exception:
                models.append(item.name.replace("_", "/"))

    return models
