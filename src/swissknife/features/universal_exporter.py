from __future__ import annotations

import csv
import html
import io
import json
from pathlib import Path
from typing import Any

from swissknife.core.utils import atomic_write


def to_markdown_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_Sem dados._\n"
    columns = list(rows[0].keys())
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")) for column in columns) + " |")
    return "\n".join(lines) + "\n"


def to_html(rows: list[dict[str, Any]], title: str = "Relatório") -> str:
    columns = list(rows[0].keys()) if rows else []
    header = "".join(f"<th>{html.escape(str(column))}</th>" for column in columns)
    body_rows = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(row.get(column, '')))}</td>" for column in columns) + "</tr>"
        for row in rows
    )
    return (
        f"<html><head><meta charset='utf-8'><title>{html.escape(title)}</title></head>"
        f"<body><h1>{html.escape(title)}</h1><table border='1' cellpadding='4' cellspacing='0'>"
        f"<thead><tr>{header}</tr></thead><tbody>{body_rows}</tbody></table></body></html>"
    )


def to_csv(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return ""
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buffer.getvalue()


FORMATS = {
    "markdown": to_markdown_table,
    "html": to_html,
    "csv": to_csv,
    "json": lambda rows, **_: json.dumps(rows, indent=2, ensure_ascii=False, default=str),
}


def export(rows: list[dict[str, Any]], output: str | Path, format_name: str, title: str = "Relatório") -> dict[str, object]:
    if format_name not in FORMATS:
        raise ValueError(f"Formato desconhecido: {format_name}. Opções: {', '.join(FORMATS)}")
    renderer = FORMATS[format_name]
    content = renderer(rows, title=title) if format_name == "html" else renderer(rows)
    atomic_write(output, content)
    return {"path": str(output), "format": format_name, "rows": len(rows)}
