import os
import yaml
from pathlib import Path
from typing import Optional


class AnalyzerConfig:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = Path(config_path)
        self._config = self._load_config()

    def _load_config(self):
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    @property
    def chroma_path(self) -> str:
        return self._config.get('paths', {}).get('chroma_path', './chroma_db')

    @property
    def output_dir(self) -> str:
        return self._config.get('paths', {}).get('out_dir', 'analysis')

    @property
    def corpus_dir(self) -> str:
        return self._config.get('paths', {}).get('corpus_dir', 'corpus')

    @property
    def corpus_metadata_path(self) -> str:
        return os.path.join(self.corpus_dir, 'corpus_metadata.json')


_analyzer_config = None


def get_analyzer_config() -> AnalyzerConfig:
    global _analyzer_config
    if _analyzer_config is None:
        _analyzer_config = AnalyzerConfig()
    return _analyzer_config


def get_corpus_metadata_path() -> str:
    return get_analyzer_config().corpus_metadata_path


def get_chroma_path() -> str:
    return get_analyzer_config().chroma_path


def get_output_dir() -> str:
    return get_analyzer_config().output_dir


def set_paths(chroma_path: Optional[str] = None,
              output_dir: Optional[str] = None,
              corpus_dir: Optional[str] = None):
    config = get_analyzer_config()
    config_path = config.config_path

    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            full_config = yaml.safe_load(f) or {}
    else:
        full_config = {}

    if 'paths' not in full_config:
        full_config['paths'] = {}

    if chroma_path:
        full_config['paths']['chroma_path'] = chroma_path
    if output_dir:
        full_config['paths']['out_dir'] = output_dir
    if corpus_dir:
        full_config['paths']['corpus_dir'] = corpus_dir

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(full_config, f, allow_unicode=True, default_flow_style=False)

    global _analyzer_config
    _analyzer_config = AnalyzerConfig(str(config_path))


def get_model_output_dir(model_name: str) -> str:
    config = get_analyzer_config()
    safe_name = model_name.replace("/", "_").replace("\\", "_")
    return os.path.join(config.output_dir, safe_name)


def CORPUS_METADATA_PATH():
    return get_corpus_metadata_path()


def CHROMA_PATH():
    return get_chroma_path()


def OUTPUT_DIR():
    return get_output_dir()