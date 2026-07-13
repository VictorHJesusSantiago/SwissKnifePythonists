from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

TYPE_MAP: dict[str, type | tuple[type, ...]] = {
    "string": str,
    "integer": int,
    "number": (int, float),
    "boolean": bool,
    "array": list,
    "object": dict,
}


@dataclass(slots=True)
class FieldSchema:
    name: str
    type: str
    required: bool = True
    nullable: bool = False


@dataclass(slots=True)
class Schema:
    fields: list[FieldSchema] = field(default_factory=list)


@dataclass(slots=True)
class ValidationError:
    row_index: int
    field: str
    reason: str


def validate_row(row: dict[str, Any], schema: Schema, row_index: int = 0) -> list[ValidationError]:
    errors: list[ValidationError] = []
    for field_schema in schema.fields:
        present = field_schema.name in row
        value = row.get(field_schema.name)
        if not present or value is None:
            if field_schema.required and not field_schema.nullable:
                errors.append(ValidationError(row_index, field_schema.name, "campo obrigatório ausente"))
            continue
        expected = TYPE_MAP.get(field_schema.type)
        if expected and not isinstance(value, expected):
            errors.append(
                ValidationError(row_index, field_schema.name, f"tipo inválido: esperado {field_schema.type}, obtido {type(value).__name__}")
            )
    extra = set(row.keys()) - {item.name for item in schema.fields}
    for name in extra:
        errors.append(ValidationError(row_index, name, "campo não previsto no schema"))
    return errors


def validate_dataset(rows: list[dict[str, Any]], schema: Schema) -> dict[str, object]:
    all_errors: list[ValidationError] = []
    for index, row in enumerate(rows):
        all_errors.extend(validate_row(row, schema, index))
    return {
        "rows": len(rows),
        "valid": len(all_errors) == 0,
        "error_count": len(all_errors),
        "errors": [asdict(error) for error in all_errors],
    }
