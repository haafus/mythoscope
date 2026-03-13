import os

DEFAULTS = {
    "corpus_dir": "corpus",
    "out_dir": "analysis",
    "chroma_path": "./chroma_db",
    "cache_dir": "./cache",
    "embedding_model": "BAAI/bge-m3",
    "chunking": "paragraph_based",
    "text_type": "translate",
}

CORPUS_METADATA_PATH = "corpus/corpus_metadata.json"
CHROMA_PATH = "./chroma_db"
OUTPUT_DIR = "analysis"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def set_paths(
        corpus_metadata: str = None,
        chroma_path: str = None,
        output_dir: str = None,
):
    global CORPUS_METADATA_PATH, CHROMA_PATH, OUTPUT_DIR
    if corpus_metadata:
        CORPUS_METADATA_PATH = corpus_metadata
    if chroma_path:
        CHROMA_PATH = chroma_path
    if output_dir:
        OUTPUT_DIR = output_dir
        os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_model_output_dir(base_out_dir: str, model_name: str) -> str:
    if not model_name:
        return base_out_dir
    safe_name = model_name.replace("/", "_").replace("\\", "_")
    model_dir = os.path.join(base_out_dir, safe_name)
    os.makedirs(model_dir, exist_ok=True)
    return model_dir