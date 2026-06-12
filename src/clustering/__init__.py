from settings import lazy_module_getattr

_LAZY_IMPORTS = {
    "get_clustering_model": (".models", "get_clustering_model"),
    "list_available_models": (".models", "list_available_models"),
    "calculate_clustering_metrics": (".metrics", "calculate_clustering_metrics"),
    "run_clustering_analysis": (".run_clustering", "run_clustering_analysis"),
    "run_all_clustering_models": (".run_clustering", "run_all_clustering_models"),
}

__all__ = list(_LAZY_IMPORTS)
__getattr__ = lazy_module_getattr(__name__, _LAZY_IMPORTS)
