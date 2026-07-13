from __future__ import annotations

import importlib
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


@dataclass(slots=True)
class Plugin:
    name: str
    module: Any
    register: Callable[..., Any]


def discover_plugins(plugins_dir: str | Path) -> list[Plugin]:
    directory = Path(plugins_dir)
    plugins: list[Plugin] = []
    if not directory.exists():
        return plugins
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        spec = importlib.util.spec_from_file_location(f"skp_plugin_{path.stem}", path)
        if spec is None or spec.loader is None:
            continue
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        register = getattr(module, "register", None)
        if callable(register):
            plugins.append(Plugin(path.stem, module, register))
    return plugins


def load_into(app: Any, plugins_dir: str | Path) -> list[str]:
    loaded = []
    for plugin in discover_plugins(plugins_dir):
        plugin.register(app)
        loaded.append(plugin.name)
    return loaded
