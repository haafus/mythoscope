import os

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
