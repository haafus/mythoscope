from lazy_imports import lazy_module_getattr

_LAZY_IMPORTS = {
    "EmbeddingBuilder": (".builder", "EmbeddingBuilder"),
    "build_embeddings": (".build_embeddings", "build_embeddings"),
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

__all__ = list(_LAZY_IMPORTS)
__getattr__ = lazy_module_getattr(__name__, _LAZY_IMPORTS)
