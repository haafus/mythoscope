from settings import lazy_module_getattr

_LAZY_IMPORTS = {
    "generate_and_save_graph": (".graph_generator", "generate_and_save_graph"),
    "LLMProcessor": (".llm_processing", "LLMProcessor"),
    "load_prompts": (".prompts_loader", "load_prompts"),
    "run_generate_graphs": (".run_graph_generation", "run_generate_graphs"),
}

__all__ = list(_LAZY_IMPORTS)
__getattr__ = lazy_module_getattr(__name__, _LAZY_IMPORTS)
