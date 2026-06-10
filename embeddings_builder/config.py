from settings import settings

DEFAULTS = {
    "corpus_dir": str(settings.corpus_dir),
    "out_dir": str(settings.analysis_dir),
    "chroma_path": str(settings.chroma_dir),
    "cache_dir": str(settings.cache_dir),
    "embedding_model": settings.default_embedding_model,
    "chunking": "paragraph_based",
    "text_type": "both",
}

CORPUS_METADATA_PATH = str(settings.corpus_metadata_path)
CHROMA_PATH = str(settings.chroma_dir)
OUTPUT_DIR = str(settings.analysis_dir)


def get_model_output_dir(base_out_dir: str, model_name: str) -> str:
    if not model_name:
        return base_out_dir
    safe_name = model_name.replace("/", "_").replace("\\", "_")
    path = settings.analysis_dir / safe_name
    path.mkdir(parents=True, exist_ok=True)
    return str(path)
