import importlib
import sys
from collections.abc import Callable


def lazy_module_getattr(module_name: str, lazy_imports: dict[str, tuple[str, str]]) -> Callable[[str], object]:
    def __getattr__(name: str) -> object:
        if name in lazy_imports:
            module_path, attr = lazy_imports[name]
            value = getattr(importlib.import_module(module_path, module_name), attr)
            sys.modules[module_name].__dict__[name] = value
            return value
        raise AttributeError(f"module {module_name!r} has no attribute {name!r}")

    return __getattr__
