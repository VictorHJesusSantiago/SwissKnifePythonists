from __future__ import annotations

import ast
from pathlib import Path


def _module_path(source_root: Path, path: Path) -> str:
    relative = path.relative_to(source_root).with_suffix("")
    return ".".join(relative.parts)


def _function_signatures(path: Path) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    return [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    ]


def generate(source_file: str | Path, source_root: str | Path = "src") -> str:
    path = Path(source_file)
    module = _module_path(Path(source_root), path)
    functions = _function_signatures(path)
    lines = [f"from {module} import (", *(f"    {func.name}," for func in functions), ")", "", ""]
    if not functions:
        lines = [f"import {module}", "", ""]
    for func in functions:
        args = [arg.arg for arg in func.args.args if arg.arg != "self"]
        call_args = ", ".join(f"{name}=None" for name in args)
        lines.append(f"def test_{func.name}() -> None:")
        lines.append(f"    result = {func.name}({call_args})")
        lines.append("    assert result is not None  # TODO: revisar asserção")
        lines.append("")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
