from importlib import import_module

_LAZY_IMPORTS = {
    "EmbeddingBuilder": (".builder", "EmbeddingBuilder"),
    "build_embeddings": (".build_embeddings", "build_embeddings"),
    "ConfigManager": (".config_manager", "ConfigManager"),
    "PerformanceMetrics": (".performance_metrics", "PerformanceMetrics"),
    "CacheValidator": (".cache_validator", "CacheValidator"),
    "save_to_cache": (".cache_utils", "save_to_cache"),
    "cleanup_cache": (".cache_utils", "cleanup_cache"),
    "get_cache_key": (".cache_utils", "get_cache_key"),
    "MODELS": (".models_repository", "MODELS"),
    "create_chunking_strategies": (".chunking", "create_chunking_strategies"),
    "ChunkingStrategy": (".chunking", "ChunkingStrategy"),
    "collection_name_for_model": (".chroma_manager", "collection_name_for_model"),
    "delete_collection": (".chroma_manager", "delete_collection"),
    "is_model_collection_name": (".chroma_manager", "is_model_collection_name"),
    "query_chroma_collection": (".chroma_manager", "query_chroma_collection"),
    "save_to_chroma_collection": (".chroma_manager", "save_to_chroma_collection"),
}

__all__ = [
    "EmbeddingBuilder",
    "build_embeddings",
    "ConfigManager",
    "PerformanceMetrics",
    "CacheValidator",
    "save_to_cache",
    "cleanup_cache",
    "get_cache_key",
    "MODELS",
    "create_chunking_strategies",
    "ChunkingStrategy",
    "save_to_chroma_collection",
    "delete_collection",
    "query_chroma_collection",
    "collection_name_for_model",
    "is_model_collection_name",
]


def __getattr__(name):
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attr_name = _LAZY_IMPORTS[name]
    value = getattr(import_module(module_name, __name__), attr_name)
    globals()[name] = value
    return value
