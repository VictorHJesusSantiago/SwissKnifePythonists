from __future__ import annotations

import ast
from pathlib import Path


def analyze_file(path: Path) -> dict[str, object]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    blank = sum(1 for line in lines if not line.strip())
    comments = sum(1 for line in lines if line.strip().startswith("#"))
    code_lines = len(lines) - blank - comments
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return {
            "path": str(path),
            "lines": len(lines),
            "code_lines": code_lines,
            "comment_lines": comments,
            "blank_lines": blank,
            "functions": 0,
            "classes": 0,
            "avg_function_length": 0.0,
        }
    functions = [node for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
    classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
    lengths = []
    for func in functions:
        end = getattr(func, "end_lineno", func.lineno)
        lengths.append(end - func.lineno + 1)
    comment_ratio = round(comments / len(lines), 4) if lines else 0.0
    return {
        "path": str(path),
        "lines": len(lines),
        "code_lines": code_lines,
        "comment_lines": comments,
        "blank_lines": blank,
        "comment_ratio": comment_ratio,
        "functions": len(functions),
        "classes": len(classes),
        "avg_function_length": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
    }


def analyze_tree(root: str | Path) -> dict[str, object]:
    files = []
    for path in Path(root).rglob("*.py"):
        if any(part.startswith(".") for part in path.parts):
            continue
        files.append(analyze_file(path))
    total_lines = sum(item["lines"] for item in files)  # type: ignore[misc]
    total_code = sum(item["code_lines"] for item in files)  # type: ignore[misc]
    return {"file_count": len(files), "total_lines": total_lines, "total_code_lines": total_code, "files": files}
