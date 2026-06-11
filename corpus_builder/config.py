from settings import settings


def __getattr__(name):
    _MAP = {
        "DOWNLOAD_LIST_FILE": lambda: str(settings.download_list_file),
        "CORPUS_DIR": lambda: settings.corpus_dir,
        "METADATA_FILE": lambda: settings.corpus_metadata_path,
        "CATALOG_FILE": lambda: settings.corpus_catalog_path,
        "PROCESSED_URLS_FILE": lambda: settings.processed_urls_path,
    }
    if name in _MAP:
        return _MAP[name]()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
