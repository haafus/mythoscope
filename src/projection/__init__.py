from settings import lazy_module_getattr

_LAZY_IMPORTS = {
    "EmbeddingAnalyzer": (".analyzer", "EmbeddingAnalyzer"),
    "analyze_embeddings": (".visualization", "analyze_embeddings"),
    "plot_comparison_dashboard": (".visualization", "plot_comparison_dashboard"),
    "plot_distance_heatmap": (".visualization", "plot_distance_heatmap"),
    "plot_interactive_2d": (".visualization", "plot_interactive_2d"),
    "plot_tradition_distribution": (".visualization", "plot_tradition_distribution"),
    "save_models_list": (".visualization", "save_models_list"),
    "save_summary_to_files": (".visualization", "save_summary_to_files"),
}

__all__ = list(_LAZY_IMPORTS)
__getattr__ = lazy_module_getattr(__name__, _LAZY_IMPORTS)
