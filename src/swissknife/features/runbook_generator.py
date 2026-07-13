from __future__ import annotations

import ast
from pathlib import Path


def _extract_summary(path: Path) -> tuple[str, list[str]]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "", []
    module_doc = ast.get_docstring(tree) or ""
    steps: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
            doc = ast.get_docstring(node) or "sem descrição"
            steps.append(f"`{node.name}()` — {doc.splitlines()[0]}")
    return module_doc, steps


def generate(script_path: str | Path, title: str = "") -> str:
    path = Path(script_path)
    module_doc, steps = _extract_summary(path)
    title = title or f"Runbook: {path.stem}"
    lines = [f"# {title}", "", f"Script de origem: `{path}`", ""]
    if module_doc:
        lines.extend(["## Objetivo", module_doc, ""])
    lines.append("## Pré-requisitos")
    lines.append(f"- Ambiente com acesso ao arquivo `{path.name}`")
    lines.append("- Permissões necessárias validadas previamente")
    lines.append("")
    lines.append("## Procedimento")
    if steps:
        lines.extend(f"{index}. {step}" for index, step in enumerate(steps, 1))
    else:
        lines.append("1. Nenhuma função pública identificada; documentar manualmente.")
    lines.append("")
    lines.append("## Verificação pós-execução")
    lines.append("- Conferir logs e métricas relevantes")
    lines.append("- Confirmar que o resultado esperado foi alcançado")
    lines.append("")
    lines.append("## Rollback")
    lines.append("- Reverter para o último estado íntegro conhecido, se necessário")
    return "\n".join(lines) + "\n"
