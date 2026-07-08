from __future__ import annotations

import csv
import html
import statistics
from pathlib import Path

from swissknife.core.utils import atomic_write


def generate(input_csv: str | Path, output_html: str | Path) -> dict[str, object]:
    with Path(input_csv).open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    numeric: dict[str, list[float]] = {}
    for row in rows:
        for key, value in row.items():
            try:
                numeric.setdefault(key, []).append(float(value))
            except (TypeError, ValueError):
                pass
    summary = {
        key: {"count": len(values), "mean": statistics.fmean(values), "min": min(values), "max": max(values)}
        for key, values in numeric.items()
    }
    headers = list(rows[0]) if rows else []
    table = "".join(
        "<tr>" + "".join(f"<td>{html.escape(str(row.get(key, '')))}</td>" for key in headers) + "</tr>"
        for row in rows
    )
    document = f"""<!doctype html><html lang="pt-BR"><meta charset="utf-8">
    <title>Relatório gerencial</title><style>body{{font:14px system-ui;margin:2rem}}
    table{{border-collapse:collapse;width:100%}}th,td{{border:1px solid #ddd;padding:.5rem}}
    th{{background:#183153;color:white}}</style><h1>Relatório gerencial</h1>
    <p>{len(rows)} registros processados.</p><pre>{html.escape(str(summary))}</pre>
    <table><thead><tr>{''.join(f'<th>{html.escape(x)}</th>' for x in headers)}</tr></thead>
    <tbody>{table}</tbody></table></html>"""
    atomic_write(output_html, document)
    return {"rows": len(rows), "columns": headers, "summary": summary, "output": str(output_html)}
