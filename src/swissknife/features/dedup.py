from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any


def _normalize(value: Any) -> str:
    return " ".join(str(value).strip().lower().split())


def _similarity(left: dict[str, Any], right: dict[str, Any], fields: list[str]) -> float:
    scores = []
    for name in fields:
        left_value = _normalize(left.get(name, ""))
        right_value = _normalize(right.get(name, ""))
        scores.append(SequenceMatcher(None, left_value, right_value).ratio())
    return sum(scores) / len(scores) if scores else 0.0


def find_duplicates(rows: list[dict[str, Any]], fields: list[str], threshold: float = 0.9) -> list[dict[str, object]]:
    groups: list[dict[str, object]] = []
    assigned: set[int] = set()
    for index, row in enumerate(rows):
        if index in assigned:
            continue
        cluster = [index]
        for other_index in range(index + 1, len(rows)):
            if other_index in assigned:
                continue
            score = _similarity(row, rows[other_index], fields)
            if score >= threshold:
                cluster.append(other_index)
                assigned.add(other_index)
        if len(cluster) > 1:
            assigned.update(cluster)
            groups.append({"indices": cluster, "representative": row, "size": len(cluster)})
    return groups


def deduplicate(rows: list[dict[str, Any]], fields: list[str], threshold: float = 0.9) -> dict[str, object]:
    groups = find_duplicates(rows, fields, threshold)
    duplicate_indices = {index for group in groups for index in group["indices"][1:]}  # type: ignore[index]
    cleaned = [row for index, row in enumerate(rows) if index not in duplicate_indices]
    return {"original_count": len(rows), "duplicate_count": len(duplicate_indices), "clean_count": len(cleaned), "groups": groups, "rows": cleaned}
