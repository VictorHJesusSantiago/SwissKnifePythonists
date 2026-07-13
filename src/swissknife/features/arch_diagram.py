from __future__ import annotations

import ast
from pathlib import Path


def _module_name(source_root: Path, path: Path) -> str:
    relative = path.relative_to(source_root).with_suffix("")
    parts = relative.parts
    if parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def build_dependency_graph(source_root: str | Path) -> dict[str, list[str]]:
    root = Path(source_root)
    modules = {path: _module_name(root, path) for path in root.rglob("*.py")}
    top_level_packages = {name.split(".")[0] for name in modules.values() if name}
    graph: dict[str, list[str]] = {name: [] for name in modules.values()}
    for path, module in modules.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            candidates: list[str] = []
            if isinstance(node, ast.Import):
                candidates.extend(alias.name for alias in node.names if alias.name.split(".")[0] in top_level_packages)
            elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in top_level_packages:
                for alias in node.names:
                    submodule = f"{node.module}.{alias.name}"
                    candidates.append(submodule if submodule in modules.values() else node.module)
            for imported in candidates:
                if imported == module:
                    continue
                graph.setdefault(module, [])
                if imported not in graph[module]:
                    graph[module].append(imported)
    return graph


def to_mermaid(graph: dict[str, list[str]]) -> str:
    lines = ["graph LR"]
    for module, dependencies in graph.items():
        safe = module.replace(".", "_")
        if not dependencies:
            lines.append(f'  {safe}["{module}"]')
        for dependency in dependencies:
            safe_dep = dependency.replace(".", "_")
            lines.append(f'  {safe}["{module}"] --> {safe_dep}["{dependency}"]')
    return "\n".join(lines) + "\n"
