import importlib

_LAZY_IMPORTS = {
    "EmbeddingAnalyzer": (".analyzer", "EmbeddingAnalyzer"),
    "AnalyzerConfig": (".config", "AnalyzerConfig"),
    "get_analyzer_config": (".config", "get_analyzer_config"),
    "get_chroma_path": (".config", "get_chroma_path"),
    "get_model_output_dir": (".config", "get_model_output_dir"),
    "get_output_dir": (".config", "get_output_dir"),
    "set_paths": (".config", "set_paths"),
    "setup_logging": (".config", "setup_logging"),
    "analyze_embeddings": (".visualization", "analyze_embeddings"),
    "plot_comparison_dashboard": (".visualization", "plot_comparison_dashboard"),
    "plot_distance_heatmap": (".visualization", "plot_distance_heatmap"),
    "plot_interactive_2d": (".visualization", "plot_interactive_2d"),
    "plot_tradition_distribution": (".visualization", "plot_tradition_distribution"),
    "save_models_list": (".visualization", "save_models_list"),
    "save_summary_to_files": (".visualization", "save_summary_to_files"),
}

__all__ = list(_LAZY_IMPORTS)


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_path, attr = _LAZY_IMPORTS[name]
        mod = importlib.import_module(module_path, __name__)
        val = getattr(mod, attr)
        globals()[name] = val
        return val
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
