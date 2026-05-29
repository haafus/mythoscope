import logging
import os
import yaml
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)

class AnalyzerConfig:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = self._resolve_config_path(config_path)
        self.project_root = Path(__file__).resolve().parent.parent
        self._config = self._load_config()

    @staticmethod
    def _resolve_config_path(config_path: str) -> Path:
        path = Path(config_path)
        package_config = Path(__file__).with_name("config.yaml")
        if path.exists():
            return path
        if path.name == "config.yaml" and package_config.exists():
            return package_config
        return path

    def _resolve_project_path(self, path_value: str) -> str:
        path = Path(path_value)
        if path.is_absolute():
            return str(path)
        return str(self.project_root / path)

    @staticmethod
    def _windows_short_path(path: Path) -> Path:
        if os.name != "nt":
            return path

        def get_short(existing_path: Path) -> Optional[Path]:
            try:
                import ctypes

                buffer = ctypes.create_unicode_buffer(32768)
                length = ctypes.windll.kernel32.GetShortPathNameW(
                    str(existing_path),
                    buffer,
                    len(buffer),
                )
                if length:
                    return Path(buffer.value)
            except Exception:
                return None
            return None

        if path.exists():
            return get_short(path) or path

        if path.parent.exists():
            short_parent = get_short(path.parent)
            if short_parent:
                return short_parent / path.name

        return path

    def _load_config(self):
        if self.config_path.exists():
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        return {}

    @property
    def chroma_path(self) -> str:
        resolved_path = Path(
            self._resolve_project_path(
                self._config.get('paths', {}).get('chroma_path', './chroma_db')
            )
        )
        return str(self._windows_short_path(resolved_path))

    @property
    def output_dir(self) -> str:
        return self._config.get('paths', {}).get('out_dir', 'analysis')

    @property
    def corpus_dir(self) -> str:
        return self._config.get('paths', {}).get('corpus_dir', 'corpus')

    @property
    def corpus_metadata_path(self) -> str:
        return os.path.join(self.corpus_dir, 'corpus_metadata.json')

    @property
    def visualization_params(self) -> dict:
        return self._config.get('visualization', {})

    @property
    def umap_configs(self) -> list:
        default = [
            {'n_neighbors': 5, 'min_dist': 0.1},
            {'n_neighbors': 15, 'min_dist': 0.1},
            {'n_neighbors': 50, 'min_dist': 0.1},
            {'n_neighbors': 15, 'min_dist': 0.5},
            {'n_neighbors': 15, 'min_dist': 0.8}
        ]
        return self.visualization_params.get('umap_configs', default)

    @property
    def tsne_configs(self) -> list:
        default = [
            {'perplexity': 5},
            {'perplexity': 30},
            {'perplexity': 50}
        ]
        return self.visualization_params.get('tsne_configs', default)

    @property
    def pca_configs(self) -> list:
        default = [{}]
        return self.visualization_params.get('pca_configs', default)

    @property
    def baseline_configs(self) -> dict:
        default = {
            'umap': {'n_neighbors': 15, 'min_dist': 0.1},
            'tsne': {'perplexity': 30},
            'pca': {}
        }
        return self.visualization_params.get('baseline_configs', default)


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

def CHROMA_PATH():
    return get_chroma_path()


def OUTPUT_DIR():
    return get_output_dir()

def setup_logging(log_dir: str = "logs", log_filename: str = "analyzer.log", clear_handlers: bool = False):
    """Set up logging to file and console."""
    
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_filename)

    
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    
    file_handler = RotatingFileHandler(log_path, maxBytes=5*1024*1024, backupCount=3, encoding='utf-8')
    file_handler.setFormatter(formatter)

    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    
    if clear_handlers and root_logger.hasHandlers():
        root_logger.handlers.clear()

    log_path_resolved = os.path.abspath(log_path)
    has_file_handler = any(
        isinstance(handler, RotatingFileHandler)
        and getattr(handler, "baseFilename", None) == log_path_resolved
        for handler in root_logger.handlers
    )
    has_console_handler = any(
        isinstance(handler, logging.StreamHandler)
        and not isinstance(handler, logging.FileHandler)
        for handler in root_logger.handlers
    )

    if not has_file_handler:
        root_logger.addHandler(file_handler)
    if not has_console_handler:
        root_logger.addHandler(console_handler)
