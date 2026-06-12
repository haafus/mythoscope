from settings import ProjectionSettings, settings


def get_analyzer_config() -> ProjectionSettings:
    return settings.projection


def get_chroma_path() -> str:
    return str(settings.chroma_dir)


def get_output_dir() -> str:
    return str(settings.analysis_dir)


def get_model_output_dir(model_name: str) -> str:
    path = settings.model_output_dir(model_name)
    path.mkdir(parents=True, exist_ok=True)
    return str(path)
