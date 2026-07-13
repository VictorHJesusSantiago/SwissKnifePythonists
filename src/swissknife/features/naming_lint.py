from __future__ import annotations

import ast
import re
from dataclasses import asdict, dataclass
from pathlib import Path

SNAKE_CASE = re.compile(r"^_{0,2}[a-z][a-z0-9_]*_{0,2}$")
PASCAL_CASE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
CONSTANT_CASE = re.compile(r"^_{0,2}[A-Z][A-Z0-9_]*$")


@dataclass(slots=True)
class NamingViolation:
    path: str
    line: int
    name: str
    kind: str
    reason: str


def lint_file(path: Path) -> list[NamingViolation]:
    violations: list[NamingViolation] = []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
    except SyntaxError:
        return violations
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not SNAKE_CASE.match(node.name) and not (node.name.startswith("__") and node.name.endswith("__")):
                violations.append(NamingViolation(str(path), node.lineno, node.name, "função", "esperado snake_case"))
        elif isinstance(node, ast.ClassDef):
            if not PASCAL_CASE.match(node.name):
                violations.append(NamingViolation(str(path), node.lineno, node.name, "classe", "esperado PascalCase"))
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            name = node.targets[0].id
            if not (SNAKE_CASE.match(name) or CONSTANT_CASE.match(name) or name.startswith("_")):
                violations.append(NamingViolation(str(path), node.lineno, name, "variável de módulo", "esperado snake_case ou CONSTANT_CASE"))
    return violations


def lint_tree(root: str | Path) -> dict[str, object]:
    all_violations: list[NamingViolation] = []
    for path in Path(root).rglob("*.py"):
        if any(part.startswith(".") for part in path.parts):
            continue
        all_violations.extend(lint_file(path))
    return {"violation_count": len(all_violations), "violations": [asdict(violation) for violation in all_violations]}
