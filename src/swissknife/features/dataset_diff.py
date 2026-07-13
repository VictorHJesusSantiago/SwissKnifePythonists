from __future__ import annotations

from typing import Any


def diff(
    left: list[dict[str, Any]],
    right: list[dict[str, Any]],
    key_field: str,
) -> dict[str, object]:
    left_index = {row[key_field]: row for row in left}
    right_index = {row[key_field]: row for row in right}
    added_keys = right_index.keys() - left_index.keys()
    removed_keys = left_index.keys() - right_index.keys()
    common_keys = left_index.keys() & right_index.keys()

    modified = []
    for key in common_keys:
        left_row, right_row = left_index[key], right_index[key]
        changed_fields = {
            field_name: {"before": left_row.get(field_name), "after": right_row.get(field_name)}
            for field_name in left_row.keys() | right_row.keys()
            if left_row.get(field_name) != right_row.get(field_name)
        }
        if changed_fields:
            modified.append({key_field: key, "changes": changed_fields})

    return {
        "left_count": len(left),
        "right_count": len(right),
        "added": [right_index[key] for key in added_keys],
        "removed": [left_index[key] for key in removed_keys],
        "modified": modified,
        "unchanged_count": len(common_keys) - len(modified),
    }


def schema_diff(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> dict[str, object]:
    left_columns = {key for row in left for key in row}
    right_columns = {key for row in right for key in row}
    return {
        "added_columns": sorted(right_columns - left_columns),
        "removed_columns": sorted(left_columns - right_columns),
        "common_columns": sorted(left_columns & right_columns),
    }
