from __future__ import annotations

import statistics
from typing import Any


def _is_numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def profile_column(values: list[Any]) -> dict[str, object]:
    total = len(values)
    non_null = [value for value in values if value is not None]
    null_count = total - len(non_null)
    profile: dict[str, object] = {
        "count": total,
        "null_count": null_count,
        "null_percent": round((null_count / total) * 100, 2) if total else 0.0,
        "distinct_count": len({str(value) for value in non_null}),
    }
    numeric = [value for value in non_null if _is_numeric(value)]
    if numeric and len(numeric) == len(non_null):
        profile.update(
            min=min(numeric),
            max=max(numeric),
            mean=round(statistics.fmean(numeric), 4),
            stdev=round(statistics.pstdev(numeric), 4) if len(numeric) > 1 else 0.0,
            outliers=_outliers(numeric),
        )
    else:
        lengths = [len(str(value)) for value in non_null]
        profile.update(
            min_length=min(lengths) if lengths else 0,
            max_length=max(lengths) if lengths else 0,
            top_values=_top_values(non_null),
        )
    return profile


def _outliers(values: list[float], z_threshold: float = 3.0) -> list[float]:
    if len(values) < 2:
        return []
    mean = statistics.fmean(values)
    stdev = statistics.pstdev(values)
    if stdev == 0:
        return []
    return [value for value in values if abs((value - mean) / stdev) >= z_threshold]


def _top_values(values: list[Any], limit: int = 5) -> list[dict[str, object]]:
    counts: dict[str, int] = {}
    for value in values:
        key = str(value)
        counts[key] = counts.get(key, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [{"value": value, "count": count} for value, count in ranked]


def profile_dataset(rows: list[dict[str, Any]]) -> dict[str, object]:
    columns: dict[str, list[Any]] = {}
    for row in rows:
        for key, value in row.items():
            columns.setdefault(key, []).append(value)
    quality_score = 100.0
    profiles = {}
    for name, values in columns.items():
        profile = profile_column(values)
        profiles[name] = profile
        quality_score -= float(profile["null_percent"]) * 0.5  # type: ignore[arg-type]
    return {"row_count": len(rows), "columns": profiles, "quality_score": round(max(quality_score, 0.0), 2)}
