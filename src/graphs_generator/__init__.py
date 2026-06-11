import importlib

_LAZY_IMPORTS = {
    "generate_and_save_graph": (".graph_generator", "generate_and_save_graph"),
    "LLMProcessor": (".llm_processing", "LLMProcessor"),
    "load_prompts": (".prompts_loader", "load_prompts"),
    "run_generate_graphs": (".run_graph_generation", "run_generate_graphs"),
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
