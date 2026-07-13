from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import cast


def _complexity(node: ast.AST) -> int:
    branching = (ast.If, ast.For, ast.AsyncFor, ast.While, ast.Try, ast.BoolOp, ast.IfExp, ast.Match)
    return 1 + sum(isinstance(child, branching) for child in ast.walk(node))


def scan(root: str | Path, threshold: int = 10) -> dict[str, object]:
    functions: list[dict[str, object]] = []
    markers: list[dict[str, object]] = []
    for path in Path(root).rglob("*.py"):
        if any(part.startswith(".") for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), 1):
            if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", line, re.I):
                markers.append({"path": str(path), "line": line_number, "text": line.strip()})
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                score = _complexity(node)
                if score >= threshold:
                    functions.append({"path": str(path), "line": node.lineno, "function": node.name, "complexity": score})
    complexity_score = sum(cast(int, item["complexity"]) for item in functions)
    return {"complex_functions": functions, "markers": markers, "score": len(markers) + complexity_score}
