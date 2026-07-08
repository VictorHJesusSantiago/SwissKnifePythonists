from __future__ import annotations

import ast
from pathlib import Path

from swissknife.core.utils import atomic_write


def generate(source: str | Path, output: str | Path) -> dict[str, object]:
    sections, modules = ["# Referência da API\n"], 0
    for path in sorted(Path(source).rglob("*.py")):
        if path.name.startswith("_"):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        modules += 1
        sections.append(f"\n## `{path.as_posix()}`\n")
        if ast.get_docstring(tree):
            sections.append(f"\n{ast.get_docstring(tree)}\n")
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
                kind = "Classe" if isinstance(node, ast.ClassDef) else "Função"
                sections.append(f"\n### {kind} `{node.name}`\n")
                sections.append(f"\n{ast.get_docstring(node) or '_Sem descrição._'}\n")
    atomic_write(output, "".join(sections))
    return {"modules": modules, "output": str(output)}
