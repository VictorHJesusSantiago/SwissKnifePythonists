from __future__ import annotations

from typing import Any


def _infer_type(values: list[Any]) -> str:
    types = {type(value) for value in values if value is not None}
    if types <= {int}:
        return "integer"
    if types <= {int, float}:
        return "number"
    if types <= {bool}:
        return "boolean"
    if types <= {list}:
        return "array"
    if types <= {dict}:
        return "object"
    return "string"


def generate(rows: list[dict[str, Any]]) -> dict[str, object]:
    columns: dict[str, list[Any]] = {}
    for row in rows:
        for key, value in row.items():
            columns.setdefault(key, []).append(value)
    fields = []
    for name, values in columns.items():
        non_null = [value for value in values if value is not None]
        samples = list(dict.fromkeys(str(value) for value in non_null))[:5]
        fields.append(
            {
                "name": name,
                "type": _infer_type(values),
                "nullable": len(non_null) < len(values),
                "null_count": len(values) - len(non_null),
                "distinct_samples": samples,
                "cardinality": len({str(value) for value in non_null}),
            }
        )
    return {"row_count": len(rows), "fields": fields}


def to_markdown(dictionary: dict[str, object]) -> str:
    lines = ["| Campo | Tipo | Nulo? | Cardinalidade | Amostras |", "| --- | --- | --- | --- | --- |"]
    for item in dictionary["fields"]:  # type: ignore[index]
        samples = ", ".join(item["distinct_samples"])
        lines.append(f"| {item['name']} | {item['type']} | {'sim' if item['nullable'] else 'não'} | {item['cardinality']} | {samples} |")
    return "\n".join(lines) + "\n"
